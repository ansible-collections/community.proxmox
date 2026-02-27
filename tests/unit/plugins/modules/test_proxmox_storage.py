# Copyright (c) 2025, Florian Paul Azim Hoberg (@gyptazy) <florian.hoberg@credativ.de>
#
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest.mock import MagicMock, patch

import pytest
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.errors import AnsibleValidationError

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import ProxmoxAnsible
from ansible_collections.community.proxmox.plugins.modules import proxmox_storage
from ansible_collections.community.proxmox.plugins.modules.proxmox_storage import validate_storage_type_options


@pytest.fixture
def dir_storage_args():
    return {
        "api_host": "localhost",
        "api_user": "root@pam",
        "api_password": "secret",
        "validate_certs": False,
        "node_name": "pve01",
        "nodes": ["pve01", "pve02"],
        "state": "present",
        "name": "dir-storage",
        "type": "dir",
        "dir_options": {
            "path": "/dir",
        },
        "content": ["images"],
    }


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
            "fingerprint": "FA:KE:FI:NG:ER:PR:IN:T0:01",
        },
        "content": ["backup"],
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
        "nfs_options": {"server": "10.10.10.10", "export": "/mnt/nfs"},
        "content": ["images"],
    }


@pytest.fixture
def zfspool_storage_args():
    return {
        "api_host": "localhost",
        "api_user": "root@pam",
        "api_password": "secret",
        "validate_certs": False,
        "node_name": "pve01",
        "nodes": ["pve01", "pve02"],
        "state": "present",
        "name": "zfspool-storage",
        "type": "zfspool",
        "zfspool_options": {
            "pool": "mypool",
        },
        "content": ["images"],
    }


@pytest.fixture
def existing_storages():
    return [{"storage": "existing-storage"}, {"storage": "nfs-share"}]


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_add_dir_storage(mock_api, mock_init, dir_storage_args):
    module = MagicMock(spec=AnsibleModule)
    module.params = dir_storage_args
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
            "fs_name": "mycephfs",
        },
        "content": ["images", "rootdir"],
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


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_add_zfspool_storage(mock_api, mock_init, zfspool_storage_args):
    module = MagicMock(spec=AnsibleModule)
    module.params = zfspool_storage_args
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


def test_validate_pbs_missing_required_options(pbs_storage_args):
    del pbs_storage_args["pbs_options"]["datastore"]  # Missing 'datastore' parameter

    with pytest.raises(AnsibleValidationError) as exc:
        validate_storage_type_options("pbs", pbs_storage_args["pbs_options"])

    assert "PBS storage requires" in str(exc.value)
    assert "datastore" in str(exc.value)


def test_validate_dir_missing_required_options():
    dir_options = {}  # Missing 'path' parameter

    with pytest.raises(AnsibleValidationError) as exc:
        validate_storage_type_options("dir", dir_options)

    assert "Directory storage requires" in str(exc.value)
    assert "path" in str(exc.value)


def test_validate_zfspool_missing_required_options():
    zfspool_options = {}  # Missing 'pool' parameter

    with pytest.raises(AnsibleValidationError) as exc:
        validate_storage_type_options("zfspool", zfspool_options)

    assert "ZFS storage requires" in str(exc.value)
    assert "pool" in str(exc.value)


def test_validate_cifs_missing_required_options():
    cifs_options = {"server": "10.0.0.1"}  # Missing 'share' parameter

    with pytest.raises(AnsibleValidationError) as exc:
        validate_storage_type_options("cifs", cifs_options)

    assert "CIFS storage requires" in str(exc.value)
    assert "server" in str(exc.value)
    assert "share" in str(exc.value)


def test_validate_iscsi_missing_required_options():
    iscsi_options = {"portal": "10.0.0.1"}  # Missing 'target' parameter

    with pytest.raises(AnsibleValidationError) as exc:
        validate_storage_type_options("iscsi", iscsi_options)

    assert "iSCSI storage requires" in str(exc.value)
    assert "portal" in str(exc.value)
    assert "target" in str(exc.value)


def test_validate_nfs_missing_required_options():
    nfs_options = {"server": "10.0.0.1"}  # Missing 'export' parameter

    with pytest.raises(AnsibleValidationError) as exc:
        validate_storage_type_options("nfs", nfs_options)

    assert "NFS storage requires" in str(exc.value)
    assert "server" in str(exc.value)
    assert "export" in str(exc.value)
