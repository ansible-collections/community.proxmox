# -*- coding: utf-8 -*-
# Copyright (c) 2025, Florian Paul Azim Hoberg (@gyptazy) <florian.hoberg@credativ.de>
#
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
from unittest.mock import MagicMock, patch
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.proxmox.plugins.modules import proxmox_cluster
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import ProxmoxAnsible
from ansible_collections.community.proxmox.plugins.modules.proxmox_cluster import validate_cluster_name


@pytest.fixture
def module_args_join():
    return {
        "api_host": "10.10.10.76",
        "api_user": "root@pam",
        "api_password": "secret",
        "state": "present",
        "master_ip": "10.10.10.75",
        "fingerprint": "BD:D0:A4:04:E6:05:30:74:30:E6:5A:83:78:A8:8F:F7:4C:25:71:DB:07:92:7C:A1:04:B9:CB:12:BB:3C:BE:4D",
        "cluster_name": "devcluster"
    }


@pytest.fixture
def module_args_create():
    return {
        "api_host": "10.10.10.76",
        "api_user": "root@pam",
        "api_password": "secret",
        "state": "present",
        "cluster_name": "devcluster",
        "link0": "10.10.1.1",
        "link1": "10.10.2.1",
    }


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_cluster_join(mock_api, mock_init, module_args_join):
    module = MagicMock(spec=AnsibleModule)
    module.params = module_args_join
    module.check_mode = False

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance
    mock_api_instance.cluster.config.join.post.return_value = {}

    module.exit_json = lambda **kwargs: (x for x in ()).throw(SystemExit(kwargs))
    module.fail_json = lambda **kwargs: (x for x in ()).throw(SystemExit(kwargs))

    proxmox = proxmox_cluster.ProxmoxClusterAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    with pytest.raises(SystemExit) as exc:
        proxmox.cluster_join()

    result = exc.value.args[0]
    assert result["changed"] is True
    assert result["msg"] == "Node joined the cluster."
    assert result["cluster"] == "devcluster"

    mock_api_instance.cluster.config.join.post.assert_called_once_with(
        hostname="10.10.10.75",
        fingerprint=module_args_join["fingerprint"],
        password="secret"
    )


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_cluster_create(mock_api, mock_init, module_args_create):
    module = MagicMock(spec=AnsibleModule)
    module.params = module_args_create
    module.check_mode = False

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance
    mock_api_instance.cluster.config.nodes.get.return_value = []
    mock_api_instance.cluster.config.post.return_value = {}

    module.exit_json = lambda **kwargs: (x for x in ()).throw(SystemExit(kwargs))
    module.fail_json = lambda **kwargs: (x for x in ()).throw(SystemExit(kwargs))

    proxmox = proxmox_cluster.ProxmoxClusterAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    with pytest.raises(SystemExit) as exc:
        proxmox.cluster_create()

    result = exc.value.args[0]
    assert result["changed"] is True
    assert result["msg"] == "Cluster 'devcluster' created."
    assert result["cluster"] == "devcluster"

    expected_payload = {
        "clustername": module_args_create["cluster_name"],
        "link0": module_args_create["link0"],
        "link1": module_args_create["link1"],
    }

    mock_api_instance.cluster.config.post.assert_called_once_with(**expected_payload)


def test_validate_cluster_name_valid(module_args_create):
    module = MagicMock(spec=AnsibleModule)
    module.params = module_args_create

    validate_cluster_name(module)
