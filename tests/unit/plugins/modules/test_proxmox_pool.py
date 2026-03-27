#
# Copyright (c) 2026, Emmanuel Jamet <emmanueljamet@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


import sys
from unittest.mock import MagicMock as MagicMike
from unittest.mock import Mock, patch

import pytest

# Skip tests if proxmoxer is not available
proxmoxer = pytest.importorskip("proxmoxer")

# Handle different import paths for different test environments
try:
    import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
    from ansible_collections.community.proxmox.plugins.modules import proxmox_pool
except ImportError:
    sys.path.insert(0, "plugins/modules")
    import proxmox_pool

    sys.path.insert(0, "plugins/module_utils")
    import proxmox as proxmox_utils


from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise SystemExit(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs["failed"] = True
    raise SystemExit(kwargs)


def _get_mock(**kwargs):
    poolid = kwargs.get("poolid")
    for pool in SAMPLE_POOLS:
        if pool["poolid"] == poolid:
            return pool


SAMPLE_POOL_1 = {"poolid": "1", "comment": "Existing pool", "members": []}

SAMPLE_POOL_2 = {
    "poolid": "2",
    "comment": "Existing pool 2",
    "members": [
        {
            "id": "1",
            "node": "node01",
            "vmid": "101",
            "type": "qemu",
        },
        {
            "id": "2",
            "node": "node02",
            "storage": "local-lvm",
        },
        {
            "id": "3",
            "node": "node01",
            "vmid": "102",
            "type": "lxc",
        },
    ],
}

SAMPLE_POOLS = [SAMPLE_POOL_1, SAMPLE_POOL_2]


class TestProxmoxPoolModule(ModuleTestCase):
    """Test cases for proxmox_pool module using ModuleTestCase pattern."""

    # Common test data
    BASIC_MODULE_ARGS = {
        "api_host": "test.proxmox.com",
        "api_user": "root@pam",
        "api_password": "secret",
    }

    TEST_SCENARIOS = [
        {  # No change
            "args": {"poolid": "1", "comment": "Existing pool"},
            "expected": {"poolid": "1", "members": []},
            "changed": False,
        },
        {  # Comment modified
            "args": {"poolid": "1", "comment": "Modified pool"},
            "expected": {"poolid": "1", "members": []},
            "changed": True,
        },
        {  # Members not specified - no change
            "args": {"poolid": "2", "comment": "Existing pool 2"},
            "expected": {
                "poolid": "2",
                "members": [
                    {
                        "id": "1",
                        "node": "node01",
                        "vmid": "101",
                        "type": "qemu",
                    },
                    {
                        "id": "2",
                        "node": "node02",
                        "storage": "local-lvm",
                    },
                    {
                        "id": "3",
                        "node": "node01",
                        "vmid": "102",
                        "type": "lxc",
                    },
                ],
            },
            "changed": False,
        },  # FIXME
        # {  # Member marked as absent - removed
        #     "args": {
        #         "poolid": "2",
        #         "comment": "Existing pool 2",
        #         "members_state": "absent",
        #         "vms": [102],
        #         "storage": ["local-lvm"],
        #     },
        #     "expected": dict(poolid="2", members=[{"id": "1", "node": "node01", "vmid": "101", "type": "qemu"}]),
        #     "changed": True,
        # },
        # TODO: write more end-to-end tests
    ]

    def setUp(self):
        super().setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_pool

        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect"
        ).start()
        self.connect_mock.return_value = MagicMike()
        self.connect_mock.return_value.pools.get = _get_mock

        self.fail_json_patcher = patch(
            "ansible.module_utils.basic.AnsibleModule.fail_json", new=Mock(side_effect=fail_json)
        ).start()

        self.exit_json_patcher = patch("ansible.module_utils.basic.AnsibleModule.exit_json", new=exit_json)
        self.exit_json_patcher.start()

    def tearDown(self):
        self.connect_mock.stop()
        self.fail_json_patcher.stop()
        self.exit_json_patcher.stop()
        super().tearDown()

    def _create_module_args(self, **kwargs):
        """Helper to create module arguments with defaults."""
        args = self.BASIC_MODULE_ARGS.copy()
        args.update(kwargs)
        return args

    def test_pool_module(self):
        """Test pool module."""
        for scenario in self.TEST_SCENARIOS:
            with self.subTest(scenario=scenario):
                module_args = self._create_module_args(**scenario["args"])

                with pytest.raises(SystemExit) as exc_info, set_module_args(module_args):
                    self.module.main()

                result = exc_info.value.args[0]
                assert "failed" not in result
                assert result["changed"] == scenario["changed"]
                assert result["poolid"] == scenario["expected"]["poolid"]
                assert result["members"] == scenario["expected"]["members"]


# Tests for internal methods and business logic
class TestProxmoxPoolInternals:
    @pytest.fixture
    def pool_manager(self):
        """Create a ProxmoxPoolAnsible instance for internal testing."""
        module = MagicMike()
        module.check_mode = False
        module.exit_json = MagicMike()
        module.fail_json = MagicMike()

        with patch.object(proxmox_utils.ProxmoxAnsible, "__init__", return_value=None):
            manager = proxmox_pool.ProxmoxPoolAnsible(module)
            manager.module = module
            manager.proxmox_api = MagicMike()
            manager.proxmox_api.pools.get = _get_mock
            return manager

    """Test cache_pool method"""

    def test_cache_pool(self, pool_manager):
        pool_manager.cache_pool("1")
        assert bool(pool_manager.pool) is True

    def test_cache_pool_false(self, pool_manager):
        pool_manager.cache_pool("wrong")
        assert bool(pool_manager.pool) is False

    def test_cache_pool_refresh_new(self, pool_manager):
        # Simulate pool not found
        pool_manager.pool = proxmox_pool.ProxmoxPool({})
        pool_manager.pool_not_found = True
        assert bool(pool_manager.pool) is False

        pool_manager.cache_pool("2")
        assert bool(pool_manager.pool) is False

        pool_manager.cache_pool("2", refresh=True)
        assert bool(pool_manager.pool) is True

    def test_cache_pool_refresh_incomplete(self, pool_manager):
        # Simulate pool out-of-date
        pool_manager.pool = proxmox_pool.ProxmoxPool({"poolid": "2", "comment": "", "members": []})
        pool_manager.pool_not_found = False

        pool_manager.cache_pool("2")
        assert pool_manager.pool.members == []
        assert pool_manager.pool.comment == ""

        pool_manager.cache_pool("2", refresh=True)
        assert pool_manager.pool.members != []
        assert pool_manager.pool.comment != ""

    """Test is_pool_existing method"""

    def test_is_pool_existing_true(self, pool_manager):
        # Test case: pool exists
        assert pool_manager.is_pool_existing("1") is True

    def test_is_pool_existing_tfalse(self, pool_manager):
        # Test case: pool exists
        assert pool_manager.is_pool_existing("wrong") is False

    """Test get_pool_members method"""

    def test_get_pool_members(self, pool_manager):
        members = pool_manager.get_pool_members("2")
        assert members == [
            {
                "id": "1",
                "node": "node01",
                "vmid": "101",
                "type": "qemu",
            },
            {
                "id": "2",
                "node": "node02",
                "storage": "local-lvm",
            },
            {
                "id": "3",
                "node": "node01",
                "vmid": "102",
                "type": "lxc",
            },
        ]

    def test_get_pool_members_empty(self, pool_manager):
        members = pool_manager.get_pool_members("1")
        assert members == []

    """Test flush_pool_members method"""

    def test_flush_pool_members(self, pool_manager):
        pool_manager.cache_pool("2")
        pool_manager.flush_pool_members("2")
        pool_manager.proxmox_api.pools.put.assert_called_once_with(
            poolid="2",
            vms=["101", "102"],
            storage=["local-lvm"],
            delete=1,
        )

    """Test create_pool method"""

    def test_create_pool(self, pool_manager):
        pool_manager.create_pool("3", "New pool")
        pool_manager.proxmox_api.pools.post.assert_called_once_with(
            poolid="3",
            comment="New pool",
        )

    def test_create_pool_exists(self, pool_manager):
        pool_manager.create_pool("2", "Existing pool")
        pool_manager.proxmox_api.pools.post.assert_not_called()

    """Test delete_pool method"""

    def test_delete_pool_empty(self, pool_manager):
        pool_manager.delete_pool("1")
        pool_manager.flush_pool_members.assert_not_called()
        pool_manager.proxmox_api.pools.delete.assert_called_once_with(
            poolid="1",
        )

    def test_delete_pool_not_empty(self, pool_manager):
        pool_manager.delete_pool("2")
        pool_manager.flush_pool_members.assert_called_once_with(poolid="2")
        pool_manager.proxmox_api.pools.delete.assert_called_once_with(
            poolid="1",
        )

    """Test pool_needs_update method"""

    def test_pool_needs_update_no_change(self, pool_manager):
        # Test case: No update needed - identical data
        assert pool_manager.pool_needs_update("1", "Existing pool", [], [], "present") is False

    def test_pool_needs_update_comment_update(self, pool_manager):
        # Test case: Update needed - different comment
        assert pool_manager.pool_needs_update("1", "Modified pool", [], [], "present") is True

    def test_pool_needs_update_new_vms_member(self, pool_manager):
        # Test case: Update needed - new vms member
        assert pool_manager.pool_needs_update("1", "Existing pool", ["101"], [], "present") is True

    def test_pool_needs_update_new_storage_member(self, pool_manager):
        # Test case: Update needed - new storage member
        assert pool_manager.pool_needs_update("1", "Existing pool", [], ["local"], "present") is True

    def test_pool_needs_update_members(self, pool_manager):
        # Test case: Update needed - new vms & storage members
        assert pool_manager.pool_needs_update("1", "Existing pool", ["101"], ["local"], "present") is True

    def test_pool_needs_update_no_removal(self, pool_manager):
        # Test case: No update needed - ensure inexistent members are absent
        assert pool_manager.pool_needs_update("2", "Existing pool 2", ["103"], ["local"], "absent") is False

    def test_pool_needs_update_vms_removal(self, pool_manager):
        # Test case: Update needed - ensure vms member is absent
        assert pool_manager.pool_needs_update("2", "Existing pool 2", ["101"], [], "absent") is True

    def test_pool_needs_update_storage_removal(self, pool_manager):
        # Test case: Update needed - ensure storage member is absent
        assert pool_manager.pool_needs_update("2", "Existing pool 2", [], ["local-lvm"], "absent") is True

    def test_pool_needs_update_members_removal(self, pool_manager):
        # Test case: Update needed - ensure vms & storage members are absent
        assert pool_manager.pool_needs_update("2", "Existing pool 2", ["101"], ["local-lvm"], "absent") is True

    """Test update_pool method"""

    # TODO: write unit tests for update_pool
