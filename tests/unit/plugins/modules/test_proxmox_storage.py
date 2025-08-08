# -*- coding: utf-8 -*-
# Copyright (c) 2025, Florian Paul Azim Hoberg (@gyptazy) <florian.hoberg@credativ.de>
#
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
from unittest.mock import MagicMock, patch
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.proxmox.plugins.modules import proxmox_storage
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import ProxmoxAnsible


@pytest.fixture
def pbs_storage_args():
    return {
        "api_host": "localhost",
        "api_user": "root@pam",
        "api_password": "secret",
        "validate_certs": False,
        "node_name": "pve01",
        "nodes": ["pve01", "pve02"],
        "state": "present",
        "name": "pbs-backup",
        "type": "pbs",
        "pbs_options": {
            "server": "backup.local",
            "username": "backup@pbs",
            "password": "secret",
            "datastore": "backup01",
            "fingerprint": "FA:KE:FI:NG:ER:PR:IN:T0:01"
        },
        "content": ["backup"]
    }


@pytest.fixture
def nfs_storage_args():
    return {
        "api_host": "localhost",
        "api_user": "root@pam",
        "api_password": "secret",
        "validate_certs": False,
        "node_name": "pve01",
        "nodes": ["pve01", "pve02"],
        "state": "present",
        "name": "nfs-share",
        "type": "nfs",
        "nfs_options": {
            "server": "10.10.10.10",
            "export": "/mnt/nfs"
        },
        "content": ["images"]
    }


@pytest.fixture
def existing_storages():
    return [
        {"storage": "existing-storage"},
        {"storage": "nfs-share"}
    ]


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_add_pbs_storage(mock_api, mock_init, pbs_storage_args):
    module = MagicMock(spec=AnsibleModule)
    module.params = pbs_storage_args
    module.check_mode = False

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance
    mock_api_instance.nodes.get.return_value = [{"node": "pve01", "status": "online"}]
    mock_api_instance.storage.get.return_value = []
    mock_api_instance.storage.post.return_value = {}

    proxmox = proxmox_storage.ProxmoxNodeAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    changed, msg = proxmox.add_storage()

    assert changed is True
    assert "created successfully" in msg


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_add_nfs_storage_check_mode(mock_api, mock_init, nfs_storage_args, existing_storages):
    module = MagicMock(spec=AnsibleModule)
    module.params = nfs_storage_args
    module.check_mode = True

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance
    mock_api_instance.nodes.get.return_value = [{"node": "pve01", "status": "online"}]
    mock_api_instance.storage.get.return_value = existing_storages

    module.exit_json = lambda **kwargs: (result for result in ()).throw(SystemExit(kwargs))
    module.fail_json = lambda **kwargs: (result for result in ()).throw(SystemExit(kwargs))

    proxmox = proxmox_storage.ProxmoxNodeAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    with pytest.raises(SystemExit) as exc:
        proxmox.add_storage()

    result = exc.value.args[0]
    assert result["changed"] is True
    assert "would be created" in result["msg"]


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_remove_existing_storage(mock_api, mock_init, nfs_storage_args):
    nfs_storage_args["state"] = "absent"

    module = MagicMock(spec=AnsibleModule)
    module.params = nfs_storage_args
    module.check_mode = False

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance
    mock_api_instance.nodes.get.return_value = [{"node": "pve01", "status": "online"}]
    mock_api_instance.storage.get.return_value = [{"storage": "nfs-share"}]

    proxmox = proxmox_storage.ProxmoxNodeAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    changed, msg = proxmox.remove_storage()

    assert changed is True
    assert "removed successfully" in msg
    mock_api_instance.storage("nfs-share").delete.assert_called_once()


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_remove_nonexistent_storage(mock_api, mock_init, nfs_storage_args):
    nfs_storage_args["state"] = "absent"
    nfs_storage_args["name"] = "nonexistent"

    module = MagicMock(spec=AnsibleModule)
    module.params = nfs_storage_args
    module.check_mode = False

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance
    mock_api_instance.nodes.get.return_value = [{"node": "pve01", "status": "online"}]
    mock_api_instance.storage.get.return_value = [{"storage": "something-else"}]

    proxmox = proxmox_storage.ProxmoxNodeAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    changed, msg = proxmox.remove_storage()

    assert changed is False
    assert "does not exist" in msg


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_add_pbs_missing_required_fields(mock_api, mock_init, pbs_storage_args):
    del pbs_storage_args["pbs_options"]["datastore"]  # simulate missing datastore

    module = MagicMock(spec=AnsibleModule)
    module.params = pbs_storage_args
    module.check_mode = False

    module.fail_json = lambda **kwargs: (result for result in ()).throw(SystemExit(kwargs))

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance
    mock_api_instance.nodes.get.return_value = [{"node": "pve01", "status": "online"}]

    proxmox = proxmox_storage.ProxmoxNodeAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    with pytest.raises(SystemExit) as exc:
        proxmox.add_storage()

    result = exc.value.args[0]
    assert "PBS storage requires" in result["msg"]


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_add_cephfs_storage(mock_api, mock_init):
    cephfs_args = {
        "api_host": "localhost",
        "api_user": "root@pam",
        "api_password": "secret",
        "validate_certs": False,
        "node_name": "pve01",
        "nodes": ["pve01", "pve02"],
        "state": "present",
        "name": "cephfs-storage",
        "type": "cephfs",
        "cephfs_options": {
            "monhost": ["10.0.0.1", "10.0.0.2"],
            "username": "admin",
            "password": "secretpass",
            "path": "/",
            "subdir": "mydata",
            "client_keyring": "AQ==",
            "fs_name": "mycephfs"
        },
        "content": ["images", "rootdir"]
    }

    module = MagicMock(spec=AnsibleModule)
    module.params = cephfs_args
    module.check_mode = False

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance
    mock_api_instance.nodes.get.return_value = [{"node": "pve01", "status": "online"}]
    mock_api_instance.storage.get.return_value = []
    mock_api_instance.storage.post.return_value = {}

    proxmox = proxmox_storage.ProxmoxNodeAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    changed, msg = proxmox.add_storage()

    assert changed is True
    assert "created successfully" in msg
