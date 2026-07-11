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
TEST_SCENARIOS = [
    {
        "args": {
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
        },
        "expected_payload": {
            "storage": "cephfs-storage",
            "type": "cephfs",
            "nodes": ["pve01", "pve02"],
            "content": ["images", "rootdir"],
            "monhost": ["10.0.0.1", "10.0.0.2"],
            "fs-name": "mycephfs",
            "keyring": "AQ==",
            "subdir": "mydata",
            "username": "admin",
            "password": "secretpass",
            "path": "/",
        },
    },
    {
        "args": {
            "name": "cifs-storage",
            "type": "cifs",
            "nodes": ["pve01", "pve02"],
            "content": ["images"],
            "cifs_options": {
                "server": "10.0.0.1",
                "share": "myshare",
                "username": "user",
                "password": "secret",
                "subdirectory": "path",
            },
        },
        "expected_payload": {
            "storage": "cifs-storage",
            "type": "cifs",
            "nodes": ["pve01", "pve02"],
            "content": ["images"],
            "server": "10.0.0.1",
            "share": "myshare",
            "username": "user",
            "password": "secret",
            "subdir": "path",
        },
    },
    {
        "args": {
            "name": "dir-storage",
            "type": "dir",
            "nodes": ["pve01", "pve02"],
            "content": ["images"],
            "dir_options": {"path": "/dir"},
        },
        "expected_payload": {
            "storage": "dir-storage",
            "type": "dir",
            "nodes": ["pve01", "pve02"],
            "content": ["images"],
            "path": "/dir",
        },
    },
    {
        "args": {
            "name": "iscsi-storage",
            "type": "iscsi",
            "nodes": ["pve01", "pve02"],
            "content": ["images"],
            "iscsi_options": {
                "portal": "10.0.0.1",
                "target": "iqn.example:444",
            },
        },
        "expected_payload": {
            "storage": "iscsi-storage",
            "type": "iscsi",
            "nodes": ["pve01", "pve02"],
            "content": ["images"],
            "portal": "10.0.0.1",
            "target": "iqn.example:444",
        },
    },
    {
        "args": {
            "name": "lvm-storage",
            "type": "lvm",
            "nodes": ["pve01", "pve02"],
            "content": ["images"],
            "lvm_options": {
                "vgname": "myvg",
                "wipe_remove": True,
                "saferemove_throughput": "-1024",
                "snapshot_as_volume_chain": True,
            },
        },
        "expected_payload": {
            "storage": "lvm-storage",
            "type": "lvm",
            "nodes": ["pve01", "pve02"],
            "content": ["images"],
            "vgname": "myvg",
            "saferemove": True,
            "saferemove_throughput": "-1024",
            "snapshot-as-volume-chain": True,
        },
    },
    {
        "args": {
            "name": "lvmthin-storage",
            "type": "lvmthin",
            "nodes": ["pve01", "pve02"],
            "content": ["images"],
            "lvmthin_options": {"vgname": "myvg", "thinpool": "mypool"},
        },
        "expected_payload": {
            "storage": "lvmthin-storage",
            "type": "lvmthin",
            "nodes": ["pve01", "pve02"],
            "content": ["images"],
            "vgname": "myvg",
            "thinpool": "mypool",
        },
    },
    {
        "args": {
            "name": "nfs-share",
            "type": "nfs",
            "nodes": ["pve01", "pve02"],
            "content": ["images"],
            "nfs_options": {"server": "10.10.10.10", "export": "/mnt/nfs"},
        },
        "expected_payload": {
            "storage": "nfs-share",
            "type": "nfs",
            "nodes": ["pve01", "pve02"],
            "content": ["images"],
            "server": "10.10.10.10",
            "export": "/mnt/nfs",
        },
    },
    {
        "args": {
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
        },
        "expected_payload": {
            "storage": "pbs-backup",
            "type": "pbs",
            "nodes": ["pve01", "pve02"],
            "content": ["backup"],
            "server": "backup.local",
            "datastore": "backup01",
            "fingerprint": "21:67:27:63:3c:e5:73",
            "username": "backup@pbs",
            "password": "secret",
        },
    },
    {
        "args": {
            "name": "rbd-storage",
            "type": "rbd",
            "nodes": ["pve01", "pve02"],
            "content": ["images"],
            "rbd_options": {"pool": "mypool"},
        },
        "expected_payload": {
            "storage": "rbd-storage",
            "type": "rbd",
            "pool": "mypool",
            "nodes": ["pve01", "pve02"],
            "content": ["images"],
        },
    },
    {
        "args": {
            "name": "zfspool-storage",
            "type": "zfspool",
            "nodes": ["pve01", "pve02"],
            "content": ["images"],
            "zfspool_options": {"pool": "mypool"},
        },
        "expected_payload": {
            "storage": "zfspool-storage",
            "type": "zfspool",
            "pool": "mypool",
            "nodes": ["pve01", "pve02"],
            "content": ["images"],
        },
    },
]


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

    # -- API errors

    def test_add_storage_post_api_failure(self):
        self.mock_api_storage.get.return_value = None
        self.mock_api_storage.post.side_effect = Exception()

        result = self._run_module(build_module_args(**TEST_SCENARIOS[0]["args"]))

        assert result["failed"] is True
        assert "Failed to create storage" in result["msg"]

    def test_remove_storage_get_api_failure(self):
        self.mock_api_storage.get.side_effect = Exception("connection failed")

        result = self._run_module(build_module_args(state="absent", name="nfs-share", type="nfs"))

        assert result["failed"] is True
        assert "Failed to retrieve storage" in result["msg"]

    def test_remove_storage_delete_api_failure(self):
        self.mock_api_storage.get.return_value = {"storage": "nfs-share"}
        self.mock_api_storage.return_value.delete.side_effect = Exception()

        result = self._run_module(build_module_args(state="absent", name="nfs-share", type="nfs"))

        assert result["failed"] is True
        assert "Failed to delete storage" in result["msg"]

    # -- state=present

    def test_add_storage(self):
        for scenario in TEST_SCENARIOS:
            with self.subTest(name=scenario["args"]["name"], type=scenario["args"]["type"]):
                self.mock_api_storage.get.return_value = None
                self.mock_api_storage.post.return_value = {}

                result = self._run_module(build_module_args(**scenario["args"]))

                assert result["changed"] is True
                assert "created successfully" in result["msg"]
                assert self.mock_api_storage.post.called

                actual_payload = self.mock_api_storage.post.call_args[1]
                assert actual_payload == scenario["expected_payload"]

    def test_add_storage_already_exists(self):
        self.mock_api_storage.get.return_value = TEST_SCENARIOS[0]["expected_payload"]

        result = self._run_module(build_module_args(**TEST_SCENARIOS[0]["args"]))

        assert result["changed"] is False
        assert "already present" in result["msg"]
        assert not self.mock_api_storage.post.called

    def test_add_storage_check_mode_new(self):
        self.mock_api_storage.get.side_effect = Exception("storage does not exist")

        result = self._run_module(self._check_mode(**TEST_SCENARIOS[0]["args"]))

        assert result["changed"] is True
        assert "would be created" in result["msg"]
        assert not self.mock_api_storage.post.called

    def test_add_storage_check_mode_already_exists(self):
        self.mock_api_storage.get.return_value = TEST_SCENARIOS[0]["expected_payload"]

        result = self._run_module(self._check_mode(**TEST_SCENARIOS[0]["args"]))

        assert result["changed"] is False
        assert "already present" in result["msg"]
        assert not self.mock_api_storage.post.called

    def test_add_storage_missing_argument(self):
        for scenario in TEST_SCENARIOS:
            with self.subTest(name=scenario["args"]["name"], type=scenario["args"]["type"]):
                result = self._run_module(
                    build_module_args(**{**scenario["args"], f"{scenario['args']['type']}_options": {}})
                )

                assert result["failed"] is True
                assert "missing required arguments" in result["msg"]
                assert "required" in result["msg"].lower()
                assert not self.mock_api_storage.post.called

    # -- state=absent

    def test_remove_existing_storage(self):
        self.mock_api_storage.get.return_value = {"storage": "nfs-share"}

        result = self._run_module(build_module_args(state="absent", name="nfs-share", type="nfs"))

        assert result["changed"] is True
        assert "removed successfully" in result["msg"]
        self.mock_api_storage.assert_called_with("nfs-share")
        self.mock_api_storage.return_value.delete.assert_called_once_with()

    def test_remove_nonexistent_storage(self):
        self.mock_api_storage.get.side_effect = Exception("storage does not exist")

        result = self._run_module(build_module_args(state="absent", name="nonexistent", type="nfs"))

        assert result["changed"] is False
        assert "does not exist" in result["msg"]
        self.mock_api_storage.return_value.delete.assert_not_called()

    def test_remove_storage_check_mode_existing(self):
        self.mock_api_storage.get.return_value = {"storage": "nfs-share"}

        result = self._run_module(self._check_mode(state="absent", name="nfs-share", type="nfs"))

        assert result["changed"] is True
        assert "would be deleted" in result["msg"]
        self.mock_api_storage.return_value.delete.assert_not_called()

    def test_remove_storage_check_mode_nonexistent(self):
        self.mock_api_storage.get.side_effect = Exception("storage does not exist")

        result = self._run_module(self._check_mode(state="absent", name="nonexistent", type="nfs"))

        assert result["changed"] is False
        assert "does not exist" in result["msg"]
        self.mock_api_storage.return_value.delete.assert_not_called()
