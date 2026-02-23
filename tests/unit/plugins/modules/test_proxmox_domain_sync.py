#
# Copyright (c) 2025, teslamania <nicolas.vial@protonmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


from unittest.mock import Mock, patch

import pytest
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)

import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
from ansible_collections.community.proxmox.plugins.modules import (
    proxmox_domain_sync,
)

proxmoxer = pytest.importorskip("proxmoxer")

RAW_DOMAINS = [
    {"type": "pve", "comment": "Proxmox VE authentication server", "realm": "pve"},
    {"realm": "ad", "comment": "comment test", "type": "ad"},
    {"realm": "openid", "type": "openid"},
    {"type": "pam", "realm": "pam", "comment": "Linux PAM standard authentication"},
    {"realm": "example.test", "default": 1, "type": "ldap"},
]


def exit_json(*args, **kwargs):
    """function to patch over exit_json;
    package return data into an exception"""
    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise SystemExit(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json;
    package return data into an exception"""
    kwargs["failed"] = True
    raise SystemExit(kwargs)


def build_sync_arg(realm, check=False):
    args = {
        "api_user": "root@pam",
        "api_password": "secret",
        "api_host": "192.168.1.21",
        "realm": realm,
        "scope": "both",
        "enable_new": True,
        "remove_vanished": "acl;properties;entry",
    }
    if check:
        args["_ansible_check_mode"] = True
    return args


class TestProxmoxDomainSync(ModuleTestCase):
    def setUp(self):
        super().setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_domain_sync

        self.fail_json_patcher = patch(
            "ansible.module_utils.basic.AnsibleModule.fail_json", new=Mock(side_effect=fail_json)
        )
        self.exit_json_patcher = patch("ansible.module_utils.basic.AnsibleModule.exit_json", new=exit_json)

        self.fail_json_mock = self.fail_json_patcher.start()
        self.exit_json_patcher.start()

        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()

        mock_obj = self.connect_mock.return_value
        mock_obj.access.domains.get.return_value = RAW_DOMAINS

    def tearDown(self):
        self.connect_mock.stop()
        self.exit_json_patcher.stop()
        self.fail_json_patcher.stop()
        super().tearDown()

    def test_domain_sync_check_mode(self):
        args = build_sync_arg("example.test", True)
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain_sync.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Domain example.test would be synced."

    def test_domain_sync(self):
        args = build_sync_arg("example.test", False)
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain_sync.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Domain example.test synced."

    def test_domain_sync_not_present(self):
        args = build_sync_arg("not_exist", True)
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain_sync.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert result["msg"] == "Domain not_exist not present."
