#
# Copyright (c) 2026, Emmanuel Jamet <emmanueljamet@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


from unittest.mock import patch

import pytest

proxmoxer = pytest.importorskip("proxmoxer")

from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleExitJson,
    ModuleTestCase,
    set_module_args,
)

import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
from ansible_collections.community.proxmox.plugins.modules import (
    proxmox_user_info,
)


class TestProxmoxUserInfoModule(ModuleTestCase):
    """Test cases for proxmox_user_info module using ModuleTestCase pattern."""

    # Common test data
    BASIC_MODULE_ARGS = {
        "api_host": "test.proxmox.com",
        "api_user": "root@pam",
        "api_password": "secret",
    }

    SAMPLE_USER = {
        "userid": "testuser@pam",
        "comment": "Test User",
        "email": "test@example.com",
        "enable": 1,
        "expire": 0,
        "firstname": "John",
        "lastname": "Doe",
        "groups": ["admins"],
        "tokens": [{"expire": 0, "privsep": 0, "tokenid": "test"}],
        "keys": "",
    }

    EXPECTED_USER = {
        "userid": "testuser@pam",
        "user": "testuser",
        "domain": "pam",
        "comment": "Test User",
        "email": "test@example.com",
        "enabled": True,
        "expire": 0,
        "firstname": "John",
        "lastname": "Doe",
        "groups": ["admins"],
        "tokens": [{"expire": 0, "privsep": False, "tokenid": "test"}],
        "keys": "",
    }

    TEST_SCENARIOS = [
        {"args": {"userid": "testuser@pam"}, "expected": EXPECTED_USER},
        {"args": {"user": "testuser"}, "expected": EXPECTED_USER},
        {"args": {"domain": "pam"}, "expected": EXPECTED_USER},
        {"args": {"userid": "nobody@pam"}, "expected": []},
    ]

    def setUp(self):
        super().setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_user_info

        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()
        self.connect_mock.return_value.proxmox_api.access.users.get.return_value = self.SAMPLE_USER

    def tearDown(self):
        self.connect_mock.stop()
        super().tearDown()

    def _create_module_args(self, **kwargs):
        """Helper to create module arguments with defaults."""
        args = self.BASIC_MODULE_ARGS.copy()
        args.update(kwargs)
        return args

    def test_user_info(self):
        """Test user info retrieval."""
        for scenario in self.TEST_SCENARIOS:
            with self.subTest(scenario=scenario):
                module_args = self._create_module_args(**scenario["args"])

                with pytest.raises(AnsibleExitJson) as exc_info, set_module_args(module_args):
                    self.module.main()

                    result = exc_info.value.args[0]
                    assert not result["changed"]
                    assert not result["failed"]
                    assert result["proxmox_users"] == [scenario["expected"]]
