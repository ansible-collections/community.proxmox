# Copyright (c) 2025, Florian Paul Azim Hoberg (@gyptazy) <florian.hoberg@credativ.de>
#
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest.mock import patch

import pytest
from ansible.module_utils import basic
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)

from ansible_collections.community.proxmox.plugins.modules import proxmox_storage

# -- Fixtures

CEPHFS_ARGS = {
    "name": "cephfs-storage",
    "type": "cephfs",
    "nodes": ["pve01", "pve02"],
    "content": ["images", "rootdir"],
    "cephfs_options": {
        "monhost": ["10.0.0.1", "10.0.0.2"],
        "username": "admin",
        "password": "secretpass",
        "path": "/",
        "subdir": "mydata",
        "client_keyring": "AQ==",
        "fs_name": "mycephfs",
    },
}

CIFS_ARGS = {
    "name": "cifs-storage",
    "type": "cifs",
    "nodes": ["pve01", "pve02"],
    "content": ["images"],
    "cifs_options": {
        "server": "10.0.0.1",
        "share": "myshare",
        "username": "user",
        "password": "secret",
    },
}

DIR_ARGS = {
    "name": "dir-storage",
    "type": "dir",
    "nodes": ["pve01", "pve02"],
    "content": ["images"],
    "dir_options": {"path": "/dir"},
}

ISCSI_ARGS = {
    "name": "iscsi-storage",
    "type": "iscsi",
    "nodes": ["pve01", "pve02"],
    "content": ["images"],
    "iscsi_options": {
        "portal": "10.0.0.1",
        "target": "iqn.example:444",
    },
}

NFS_ARGS = {
    "name": "nfs-share",
    "type": "nfs",
    "nodes": ["pve01", "pve02"],
    "content": ["images"],
    "nfs_options": {"server": "10.10.10.10", "export": "/mnt/nfs"},
}

PBS_ARGS = {
    "name": "pbs-backup",
    "type": "pbs",
    "nodes": ["pve01", "pve02"],
    "content": ["backup"],
    "pbs_options": {
        "server": "backup.local",
        "username": "backup@pbs",
        "password": "secret",
        "datastore": "backup01",
        "fingerprint": "21:67:27:63:3c:e5:73",
    },
}

ZFSPOOL_ARGS = {
    "name": "zfspool-storage",
    "type": "zfspool",
    "nodes": ["pve01", "pve02"],
    "content": ["images"],
    "zfspool_options": {"pool": "mypool"},
}


# -- Helpers


def exit_json(*args, **kwargs):
    kwargs.setdefault("changed", False)
    raise SystemExit(kwargs)


def fail_json(*args, **kwargs):
    kwargs["failed"] = True
    raise SystemExit(kwargs)


def build_module_args(state="present", **overrides):
    return {
        "api_host": "host",
        "api_user": "user",
        "api_password": "password",
        "state": state,
        **overrides,
    }


# -- Module tests


class TestProxmoxStorageModule(ModuleTestCase):
    def setUp(self):
        super().setUp()
        self.module = proxmox_storage

        self.mock_module_helper = patch.multiple(
            basic.AnsibleModule,
            exit_json=exit_json,
            fail_json=fail_json,
        )
        self.mock_module_helper.start()

        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()

        self.mock_api_storage = self.connect_mock.return_value.storage

    def tearDown(self):
        self.connect_mock.stop()
        self.mock_module_helper.stop()
        super().tearDown()

    def _run_module(self, args):
        with pytest.raises(SystemExit) as exc_info, set_module_args(args):
            self.module.main()
        return exc_info.value.args[0]

    def _check_mode(self, **kwargs):
        return {**build_module_args(**kwargs), "_ansible_check_mode": True}

    def _run_add_storage_success(self, args, expected_payload_subset):
        self.mock_api_storage.post.return_value = {}

        result = self._run_module(args)

        assert result["changed"] is True
        assert "created successfully" in result["msg"]
        assert self.mock_api_storage.post.called

        actual_payload = self.mock_api_storage.post.call_args[1]
        for key, value in expected_payload_subset.items():
            if value is None:
                assert key not in actual_payload
            else:
                assert actual_payload.get(key) == value

    def _run_add_storage_missing_required(self, args, missing_field):
        result = self._run_module(args)

        assert result["failed"] is True
        assert missing_field in result["msg"]
        assert "required" in result["msg"].lower()
        assert not self.mock_api_storage.post.called

    # -- API errors

    def test_add_storage_post_api_failure(self):
        self.mock_api_storage.post.side_effect = Exception()

        result = self._run_module(build_module_args(**NFS_ARGS))

        assert result["failed"] is True
        assert "Failed to create storage" in result["msg"]

    def test_remove_storage_get_api_failure(self):
        self.mock_api_storage.get.side_effect = Exception()

        result = self._run_module(build_module_args(state="absent", name="nfs-share", type="nfs"))

        assert result["failed"] is True
        assert "Failed to delete storage" in result["msg"]

    def test_remove_storage_delete_api_failure(self):
        self.mock_api_storage.get.return_value = [{"storage": "nfs-share"}]
        self.mock_api_storage.return_value.delete.side_effect = Exception()

        result = self._run_module(build_module_args(state="absent", name="nfs-share", type="nfs"))

        assert result["failed"] is True
        assert "Failed to delete storage" in result["msg"]

    # -- state=present

    def test_add_cephfs_storage(self):
        self._run_add_storage_success(
            build_module_args(**CEPHFS_ARGS),
            {
                "storage": "cephfs-storage",
                "type": "cephfs",
                "monhost": ["10.0.0.1", "10.0.0.2"],
                "fs-name": "mycephfs",
                "keyring": "AQ==",
                "subdir": "mydata",
            },
        )

    def test_add_cifs_storage(self):
        self._run_add_storage_success(
            build_module_args(**CIFS_ARGS),
            {
                "storage": "cifs-storage",
                "type": "cifs",
                "server": "10.0.0.1",
                "share": "myshare",
            },
        )

    def test_add_dir_storage(self):
        self._run_add_storage_success(
            build_module_args(**DIR_ARGS),
            {"storage": "dir-storage", "type": "dir", "path": "/dir"},
        )

    def test_add_iscsi_storage(self):
        self._run_add_storage_success(
            build_module_args(**ISCSI_ARGS),
            {
                "storage": "iscsi-storage",
                "type": "iscsi",
                "portal": "10.0.0.1",
                "target": "iqn.example:444",
            },
        )

    def test_add_nfs_storage(self):
        self._run_add_storage_success(
            build_module_args(**NFS_ARGS),
            {
                "storage": "nfs-share",
                "type": "nfs",
                "server": "10.10.10.10",
                "export": "/mnt/nfs",
            },
        )

    def test_add_pbs_storage(self):
        self._run_add_storage_success(
            build_module_args(**PBS_ARGS),
            {
                "storage": "pbs-backup",
                "type": "pbs",
                "server": "backup.local",
                "datastore": "backup01",
                "fingerprint": "21:67:27:63:3c:e5:73",
            },
        )

    def test_add_zfspool_storage(self):
        self._run_add_storage_success(
            build_module_args(**ZFSPOOL_ARGS),
            {"storage": "zfspool-storage", "type": "zfspool", "pool": "mypool"},
        )

    def test_add_storage_already_exists(self):
        self.mock_api_storage.post.side_effect = Exception("already defined")

        result = self._run_module(build_module_args(**NFS_ARGS))

        assert result["changed"] is False
        assert "already present" in result["msg"]

    def test_add_storage_check_mode_new(self):
        self.mock_api_storage.get.return_value = [{"storage": "other-storage"}]

        result = self._run_module(self._check_mode(**NFS_ARGS))

        assert result["changed"] is True
        assert "would be created" in result["msg"]
        assert not self.mock_api_storage.post.called

    def test_add_storage_check_mode_already_exists(self):
        self.mock_api_storage.get.return_value = [{"storage": "nfs-share"}]

        result = self._run_module(self._check_mode(**NFS_ARGS))

        assert result["changed"] is False
        assert "already present" in result["msg"]
        assert not self.mock_api_storage.post.called

    def test_add_cifs_storage_missing_share(self):
        self._run_add_storage_missing_required(
            build_module_args(**{**CIFS_ARGS, "cifs_options": {"server": "10.0.0.1"}}),
            missing_field="share",
        )

    def test_add_dir_storage_missing_path(self):
        self._run_add_storage_missing_required(
            build_module_args(**{**DIR_ARGS, "dir_options": {}}),
            missing_field="path",
        )

    def test_add_iscsi_storage_missing_target(self):
        self._run_add_storage_missing_required(
            build_module_args(**{**ISCSI_ARGS, "iscsi_options": {"portal": "10.0.0.1"}}),
            missing_field="target",
        )

    def test_add_nfs_storage_missing_export(self):
        self._run_add_storage_missing_required(
            build_module_args(**{**NFS_ARGS, "nfs_options": {"server": "10.0.0.1"}}),
            missing_field="export",
        )

    def test_add_pbs_storage_missing_datastore(self):
        self._run_add_storage_missing_required(
            build_module_args(**{**PBS_ARGS, "pbs_options": {"server": "s", "username": "u", "password": "p"}}),
            missing_field="datastore",
        )

    def test_add_zfspool_storage_missing_pool(self):
        self._run_add_storage_missing_required(
            build_module_args(**{**ZFSPOOL_ARGS, "zfspool_options": {}}),
            missing_field="pool",
        )

    # -- state=absent

    def test_remove_existing_storage(self):
        self.mock_api_storage.get.return_value = [{"storage": "nfs-share"}]

        result = self._run_module(build_module_args(state="absent", name="nfs-share", type="nfs"))

        assert result["changed"] is True
        assert "removed successfully" in result["msg"]
        self.mock_api_storage.assert_called_with("nfs-share")
        self.mock_api_storage.return_value.delete.assert_called_once_with()

    def test_remove_nonexistent_storage(self):
        self.mock_api_storage.get.return_value = [{"storage": "other-storage"}]

        result = self._run_module(build_module_args(state="absent", name="nonexistent", type="nfs"))

        assert result["changed"] is False
        assert "does not exist" in result["msg"]
        self.mock_api_storage.return_value.delete.assert_not_called()

    def test_remove_storage_check_mode_existing(self):
        self.mock_api_storage.get.return_value = [{"storage": "nfs-share"}]

        result = self._run_module(self._check_mode(state="absent", name="nfs-share", type="nfs"))

        assert result["changed"] is True
        assert "would be deleted" in result["msg"]
        self.mock_api_storage.return_value.delete.assert_not_called()

    def test_remove_storage_check_mode_nonexistent(self):
        self.mock_api_storage.get.return_value = [{"storage": "other-storage"}]

        result = self._run_module(self._check_mode(state="absent", name="nonexistent", type="nfs"))

        assert result["changed"] is False
        assert "does not exist" in result["msg"]
        self.mock_api_storage.return_value.delete.assert_not_called()
