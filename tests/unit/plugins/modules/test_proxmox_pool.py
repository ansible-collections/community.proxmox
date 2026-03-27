#
# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("proxmoxer")

from ansible.module_utils import basic
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)

import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
from ansible_collections.community.proxmox.plugins.modules import proxmox_pool

POOL_ID = "test-pool"


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
        "poolid": POOL_ID,
        "state": state,
        **overrides,
    }


# -- Pure helpers (module-level functions)


class TestProxmoxPoolHelpers:
    def test_members_result_from_api_vm_and_storage(self):
        raw = [
            {"type": "qemu", "vmid": 100},
            {"type": "storage", "storage": "local"},
        ]
        out = proxmox_pool._members_result_from_api(raw)
        assert out == [
            {"id": 100, "type": "vm"},
            {"id": "local", "type": "storage"},
        ]

    def test_parse_members_from_api(self):
        raw = [
            {"type": "qemu", "vmid": 100},
            {"type": "storage", "storage": "local"},
        ]
        vms, storages = proxmox_pool._parse_members(raw)
        assert vms == [100]
        assert storages == ["local"]

    def test_desired_members_from_params(self):
        vms, storages = proxmox_pool._desired_members_from_params(
            [
                {"vm_id": 100},
                {"storage_id": "local"},
            ]
        )
        assert vms == [100]
        assert storages == ["local"]

    def test_desired_members_empty(self):
        assert proxmox_pool._desired_members_from_params(None) == ([], [])
        assert proxmox_pool._desired_members_from_params([]) == ([], [])


# -- Module integration


class TestProxmoxPoolModule(ModuleTestCase):
    def setUp(self):
        super().setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_pool

        self.mock_module_helper = patch.multiple(
            basic.AnsibleModule,
            exit_json=exit_json,
            fail_json=fail_json,
        )
        self.mock_module_helper.start()

        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()

        self.mock_api = self.connect_mock.return_value
        self.mock_api.version.get.return_value = {"version": "8.0.0"}
        self.mock_pools = self.mock_api.pools
        self.pool_binding = MagicMock()
        self.mock_pools.return_value = self.pool_binding

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

    # -- validation

    def test_member_requires_vm_or_storage(self):
        result = self._run_module(build_module_args(members=[{}]))
        assert result["failed"] is True
        assert "vm_id or storage_id" in result["msg"]

    def test_member_rejects_vm_and_storage_together(self):
        result = self._run_module(
            build_module_args(members=[{"vm_id": 100, "storage_id": "local"}]),
        )
        assert result["failed"] is True
        assert "vm_id or storage_id" in result["msg"]

    # -- state=present: create

    def test_pool_create(self):
        self.mock_pools.get.side_effect = [
            None,
            {
                "poolid": POOL_ID,
                "comment": "c",
                "members": [
                    {"type": "qemu", "vmid": 100},
                    {"type": "storage", "storage": "local"},
                ],
            },
        ]

        result = self._run_module(
            build_module_args(
                comment="c",
                members=[{"vm_id": 100}, {"storage_id": "local"}],
            )
        )

        assert result["changed"] is True
        assert "successfully created" in result["msg"]
        assert result["poolid"] == POOL_ID
        assert result["comment"] == "c"
        assert {"id": 100, "type": "vm"} in result["members"]
        assert {"id": "local", "type": "storage"} in result["members"]
        self.mock_pools.post.assert_called_once_with(poolid=POOL_ID)
        self.pool_binding.put.assert_called()

    def test_pool_create_api_failure(self):
        self.mock_pools.get.return_value = None
        self.mock_pools.post.side_effect = Exception("api error")

        result = self._run_module(build_module_args(members=[{"vm_id": 1}]))

        assert result["failed"] is True
        assert "Failed to create pool" in result["msg"]

    def test_pool_create_check_mode(self):
        self.mock_pools.get.return_value = None

        result = self._run_module(
            self._check_mode(
                comment="new",
                members=[{"vm_id": 100}],
            )
        )

        assert result["changed"] is True
        assert "would be created" in result["msg"]
        assert result["poolid"] == POOL_ID
        assert result["comment"] == "new"
        assert result["members"] == [{"vm_id": 100, "storage_id": None}]
        self.mock_pools.post.assert_not_called()

    # -- state=present: exists without members param

    def test_pool_exists_no_members_param_unchanged(self):
        self.mock_pools.get.return_value = {
            "poolid": POOL_ID,
            "comment": "x",
            "members": [{"type": "qemu", "vmid": 50}],
        }

        result = self._run_module(build_module_args())

        assert result["changed"] is False
        assert "already exists" in result["msg"]
        assert result["members"] == [{"id": 50, "type": "vm"}]

    # -- state=present: update

    def test_pool_update_members_and_comment(self):
        before = {
            "poolid": POOL_ID,
            "comment": "old",
            "members": [
                {"type": "qemu", "vmid": 50},
                {"type": "storage", "storage": "oldstore"},
            ],
        }
        after = {
            "poolid": POOL_ID,
            "comment": "new",
            "members": [
                {"type": "qemu", "vmid": 100},
                {"type": "storage", "storage": "local"},
            ],
        }
        self.mock_pools.get.side_effect = [before, after]

        result = self._run_module(
            build_module_args(
                comment="new",
                members=[{"vm_id": 100}, {"storage_id": "local"}],
            )
        )

        assert result["changed"] is True
        assert "successfully updated" in result["msg"]
        assert result["comment"] == "new"
        self.pool_binding.put.assert_called()

    def test_pool_already_up_to_date(self):
        pool = {
            "poolid": POOL_ID,
            "comment": "same",
            "members": [
                {"type": "qemu", "vmid": 100},
                {"type": "storage", "storage": "local"},
            ],
        }
        self.mock_pools.get.return_value = pool

        result = self._run_module(
            build_module_args(
                comment="same",
                members=[{"vm_id": 100}, {"storage_id": "local"}],
            )
        )

        assert result["changed"] is False
        assert "already up to date" in result["msg"]
        self.pool_binding.put.assert_not_called()

    def test_pool_update_check_mode(self):
        pool = {
            "poolid": POOL_ID,
            "comment": "old",
            "members": [{"type": "qemu", "vmid": 50}],
        }
        self.mock_pools.get.return_value = pool

        result = self._run_module(
            self._check_mode(
                comment="new",
                members=[{"vm_id": 100}],
            )
        )

        assert result["changed"] is True
        assert "would be updated" in result["msg"]
        assert result["comment"] == "new"
        assert result["members"] == [{"vm_id": 100, "storage_id": None}]
        self.pool_binding.put.assert_not_called()

    def test_pool_update_api_failure(self):
        pool = {
            "poolid": POOL_ID,
            "comment": "",
            "members": [],
        }
        self.mock_pools.get.return_value = pool
        self.pool_binding.put.side_effect = Exception("update failed")

        result = self._run_module(build_module_args(members=[{"vm_id": 1}]))

        assert result["failed"] is True
        assert "Failed to update pool" in result["msg"]

    # -- state=present: get pool errors

    def test_pool_get_unexpected_failure(self):
        self.mock_pools.get.side_effect = Exception()

        result = self._run_module(build_module_args())

        assert result["failed"] is True
        assert "Failed to retrieve pool" in result["msg"]

    # -- state=absent

    def test_pool_absent_deleted(self):
        pool = {
            "poolid": POOL_ID,
            "comment": "x",
            "members": [{"type": "qemu", "vmid": 10}],
        }
        self.mock_pools.get.return_value = pool

        result = self._run_module(build_module_args(state="absent"))

        assert result["changed"] is True
        assert "successfully deleted" in result["msg"]
        assert result["members"] == []
        assert result["comment"] == ""
        self.mock_pools.delete.assert_called_once_with(poolid=POOL_ID)

    def test_pool_absent_missing(self):
        self.mock_pools.get.side_effect = Exception("does not exist")

        result = self._run_module(build_module_args(state="absent"))

        assert result["changed"] is False
        assert "doesn't exist" in result["msg"]
        self.mock_pools.delete.assert_not_called()

    def test_pool_absent_check_mode(self):
        pool = {
            "poolid": POOL_ID,
            "comment": "x",
            "members": [],
        }
        self.mock_pools.get.return_value = pool

        result = self._run_module(self._check_mode(state="absent"))

        assert result["changed"] is True
        assert "would be deleted" in result["msg"]
        self.mock_pools.delete.assert_not_called()

    def test_pool_absent_delete_failure(self):
        self.mock_pools.get.return_value = {"poolid": POOL_ID, "members": []}
        self.mock_pools.delete.side_effect = Exception("delete failed")

        result = self._run_module(build_module_args(state="absent"))

        assert result["failed"] is True
        assert "Failed to delete pool" in result["msg"]
