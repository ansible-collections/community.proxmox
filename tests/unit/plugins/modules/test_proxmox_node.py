# -*- coding: utf-8 -*-
# Copyright (c) 2025, Florian Paul Azim Hoberg (@gyptazy) <florian.hoberg@credativ.de>
#
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
from unittest.mock import MagicMock, patch
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.proxmox.plugins.modules import proxmox_node
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import ProxmoxAnsible


@pytest.fixture
def module_args_power_on():
    return {
        "api_host": "proxmoxhost",
        "api_user": "root@pam",
        "api_password": "secret",
        "validate_certs": False,
        "node_name": "test-node",
        "power_state": "online",
    }


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_power_state_present(mock_api, mock_init, module_args_power_on):
    module = MagicMock(spec=AnsibleModule)
    module.params = module_args_power_on
    module.check_mode = False

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance

    nodes = {
        "nodes": {
            "test-node": {
                "name": "test-node",
                "status": "offline"
            }
        }
    }

    module.exit_json = lambda **kwargs: (x for x in ()).throw(SystemExit(kwargs))
    module.fail_json = lambda **kwargs: (x for x in ()).throw(SystemExit(kwargs))

    proxmox = proxmox_node.ProxmoxNodeAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    with patch.object(mock_api_instance.nodes("test-node").wakeonlan, 'post') as mock_post:
        changed, msg = proxmox.power_state(nodes)

    assert changed is True
    assert "powered on" in msg
    mock_post.assert_called_once_with(node_name="test-node")


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_power_state_already_online(mock_api, mock_init, module_args_power_on):
    module = MagicMock(spec=AnsibleModule)
    module.params = module_args_power_on
    module.check_mode = False

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance

    nodes = {
        "nodes": {
            "test-node": {
                "name": "test-node",
                "status": "online"
            }
        }
    }

    proxmox = proxmox_node.ProxmoxNodeAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    changed, msg = proxmox.power_state(nodes)

    assert changed is False
    assert "already online" in msg


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_subscription_present_new_key(mock_api, mock_init):
    module = MagicMock(spec=AnsibleModule)
    module.params = {
        "node_name": "test-node",
        "subscription": {
            "state": "present",
            "key": "ABCD-1234"
        }
    }
    module.check_mode = False

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance
    mock_api_instance.nodes("test-node").subscription.get.return_value = {"key": "OLD-KEY"}

    module.exit_json = lambda **kwargs: (x for x in ()).throw(SystemExit(kwargs))
    module.fail_json = lambda **kwargs: (x for x in ()).throw(SystemExit(kwargs))

    proxmox = proxmox_node.ProxmoxNodeAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    changed, msg = proxmox.subscription()

    assert changed is True
    assert "uploaded" in msg
    mock_api_instance.nodes("test-node").subscription.put.assert_called_once_with(key="ABCD-1234")


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_subscription_already_present(mock_api, mock_init):
    module = MagicMock(spec=AnsibleModule)
    module.params = {
        "node_name": "test-node",
        "subscription": {
            "state": "present",
            "key": "ABCD-1234"
        }
    }
    module.check_mode = False

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance
    mock_api_instance.nodes("test-node").subscription.get.return_value = {"key": "ABCD-1234"}

    proxmox = proxmox_node.ProxmoxNodeAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    changed, msg = proxmox.subscription()

    assert changed is False
    assert msg == "Unchanged"
    mock_api_instance.nodes("test-node").subscription.put.assert_not_called()
