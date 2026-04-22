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
    from ansible_collections.community.proxmox.plugins.modules import proxmox_pool_member
except ImportError:
    sys.path.insert(0, "plugins/modules")
    import proxmox_pool_member  # type: ignore[import]

    sys.path.insert(0, "plugins/module_utils")
    import proxmox as proxmox_utils  # type: ignore[import]


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


def _get_pool_mock(**kwargs):
    poolid = kwargs.get("poolid")
    for pool in SAMPLE_POOLS:
        if pool["poolid"] == poolid:
            return [pool]


def _get_vmid_mock(vm):
    try:
        return str(int(vm))
    except (ValueError, TypeError):
        return "123"


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
            "type": "storage",
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


class TestProxmoxPoolMemberModule(ModuleTestCase):
    """Test cases for proxmox_pool_member module using ModuleTestCase pattern."""

    # Common test data
    BASIC_MODULE_ARGS = {
        "api_host": "test.proxmox.com",
        "api_user": "root@pam",
        "api_password": "secret",
    }

    TEST_SCENARIOS = [
        {  # Add vm and storage members
            "name": "Add vm and storage members",
            "args": {
                "poolid": "1",
                "members": [
                    {"vm": "101"},
                    {"vm": "pxe.home.arpa"},
                    {"storage": "zfs-data"},
                ],
            },
            "expected": {
                "poolid": "1",
                "members": [
                    {"vm": "101"},
                    {"vm": "123"},
                    {"storage": "zfs-data"},
                ],
            },
            "changed": True,
        },
        {  # Remove vm and storage members
            "name": "Remove vm and storage members",
            "args": {
                "poolid": "2",
                "state": "absent",
                "members": [
                    {"vm": "101"},
                    {"storage": "local-lvm"},
                ],
            },
            "expected": {"poolid": "2", "members": [{"vm": "102"}]},
            "changed": True,
        },
        {  # Remove storage and add vm members - exclusive mode
            "name": "Remove vm and storage members - exclusive mode",
            "args": {
                "poolid": "2",
                "members": [
                    {"vm": "102"},
                    {"vm": "103"},
                ],
                "exclusive": "true",
            },
            "expected": {
                "poolid": "2",
                "members": [
                    {"vm": "102"},
                    {"vm": "103"},
                ],
            },
            "changed": True,
        },
        {  # No change - exclusive mode
            "name": "No change - exclusive mode",
            "args": {
                "poolid": "2",
                "members": [
                    {"vm": "101"},
                    {"storage": "local-lvm"},
                    {"vm": "102"},
                ],
                "exclusive": "true",
            },
            "expected": {
                "poolid": "2",
                "members": [
                    {"vm": "101"},
                    {"vm": "102"},
                    {"storage": "local-lvm"},
                ],
            },
            "changed": False,
        },
    ]

    def setUp(self):
        super().setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_pool_member

        proxmox_api = MagicMike()
        proxmox_api.pools.get.side_effect = _get_pool_mock

        for patcher in [
            patch(
                "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
                return_value=proxmox_api,
            ),
            patch.multiple(
                proxmox_utils.ProxmoxAnsible,
                get_vmid=Mock(side_effect=_get_vmid_mock),
                get_storages=Mock(return_value=[{"storage": "zfs-data"}, {"storage": "local-lvm"}]),
            ),
            patch("ansible.module_utils.basic.AnsibleModule.fail_json", new=Mock(side_effect=fail_json)),
            patch("ansible.module_utils.basic.AnsibleModule.exit_json", new=exit_json),
        ]:
            patcher.start()
            self.addCleanup(patcher.stop)

    def _create_module_args(self, **kwargs):
        """Helper to create module arguments with defaults."""
        args = self.BASIC_MODULE_ARGS.copy()
        args.update(kwargs)
        return args

    def test_pool_member_module(self):
        """Test pool_member module."""
        for scenario in self.TEST_SCENARIOS:
            with self.subTest(scenario=scenario):
                module_args = self._create_module_args(**scenario["args"])

                with pytest.raises(SystemExit) as exc_info, set_module_args(module_args):
                    self.module.main()

                result = exc_info.value.args[0]
                assert result.get("failed", False) is not True
                assert result["changed"] == scenario["changed"]
                assert result["poolid"] == scenario["expected"]["poolid"]
                assert result["members"] == scenario["expected"]["members"]
