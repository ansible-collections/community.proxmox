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
    proxmox_domain,
)

proxmoxer = pytest.importorskip("proxmoxer")

RAW_DOMAINS = [
    {"type": "pve", "comment": "Proxmox VE authentication server", "realm": "pve"},
    {"realm": "ad", "comment": "comment test", "type": "ad"},
    {"realm": "openid", "type": "openid"},
    {"type": "pam", "realm": "pam", "comment": "Linux PAM standard authentication"},
    {"realm": "example.test", "default": 1, "type": "ldap"},
]

RAW_LDAP = {
    "mode": "ldaps",
    "sync-defaults-options": "enable-new=1,remove-vanished=acl;properties;entry,scope=both",
    "user_attr": "uid",
    "group_name_attr": "cn",
    "default": 1,
    "type": "ldap",
    "base_dn": "cn=accounts,dc=example,dc=test",
    "digest": "c21f05ca10e3c1c4f0a69095072d2b8a060fe83d",
    "bind_dn": "uid=sa-proxmox,cn=users,cn=accounts,dc=example,dc=test",
    "group_filter": "cn=admins-proxmox",
    "server1": "ipa.example.test",
    "filter": "memberof=cn=admins-proxmox,cn=groups,cn=accounts,dc=example,dc=test",
    "verify": 0,
}

RAW_OPENID = {
    "type": "openid",
    "client-key": "keyoftheclient",
    "digest": "e21f05c910e5c5c6f082b81a072d2b8b9d9a147c",
    "issuer-url": "https://example.test/openid-server",
    "client-id": "idoftheclient",
}

RAW_AD = {
    "group_filter": "cn=admins-proxmox",
    "digest": "91ac19ca27eaccc4a057ca97072dab7b9603aa19",
    "filter": "memberof=cn=admins-proxmox,cn=groups,cn=accounts,dc=example,dc=test",
    "comment": "ad domain",
    "server1": "srv-ad.example.test",
    "group_name_attr": "cn",
    "mode": "ldap",
    "domain": "ADDOMAINNAME",
    "sync-defaults-options": "enable-new=1,remove-vanished=acl;properties;entry,scope=both",
    "bind_dn": "uid=sa-ad,cn=users,cn=accounts,dc=example,dc=test",
    "case-sensitive": 1,
    "verify": 0,
    "type": "ad",
}


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


def build_base_arg(state, realm, check=False):
    args = {
        "api_user": "root@pam",
        "api_password": "secret",
        "api_host": "192.168.1.21",
        "state": state,
        "realm": realm,
    }
    if check:
        args["_ansible_check_mode"] = True
    return args


def build_ldap_arg(state, realm, check=False):
    args = build_base_arg(state, realm, check)
    args["base_dn"] = "cn=accounts,dc=example,dc=test"
    args["bind_dn"] = "uid=sa-proxmox,cn=users,cn=accounts,dc=example,dc=test"
    args["default"] = True
    args["filter"] = "memberof=cn=admins-proxmox,cn=groups,cn=accounts,dc=example,dc=test"
    args["group_filter"] = "cn=admins-proxmox"
    args["group_name_attr"] = "cn"
    args["mode"] = "ldaps"
    args["password"] = "password"
    args["server1"] = "ipa.example.test"
    args["type"] = "ldap"
    args["user_attr"] = "uid"
    args["verify"] = False
    args["sync_defaults_options"] = {"scope": "both", "enable_new": True, "remove_vanished": "acl;properties;entry"}
    return args


def build_openid_arg(state, realm, check=False):
    args = build_base_arg(state, realm, check)
    args["type"] = "openid"
    args["client_id"] = "idoftheclient"
    args["client_key"] = "keyoftheclient"
    args["issuer_url"] = "https://example.test/openid-server"
    return args


def build_ad_arg(state, realm, check=False):
    args = build_base_arg(state, realm, check)
    args["type"] = "ad"
    args["group_filter"] = "cn=admins-proxmox"
    args["filter"] = "memberof=cn=admins-proxmox,cn=groups,cn=accounts,dc=example,dc=test"
    args["comment"] = "ad domain"
    args["server1"] = "srv-ad.example.test"
    args["group_name_attr"] = "cn"
    args["mode"] = "ldap"
    args["domain"] = "ADDOMAINNAME"
    args["sync_defaults_options"] = {"scope": "both", "enable_new": True, "remove_vanished": "acl;properties;entry"}
    args["bind_dn"] = "uid=sa-ad,cn=users,cn=accounts,dc=example,dc=test"
    args["case_sensitive"] = True
    args["verify"] = False
    args["type"] = "ad"
    return args


class TestProxmoxDomain(ModuleTestCase):
    def setUp(self):
        super().setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_domain

        self.fail_json_patcher = patch(
            "ansible.module_utils.basic.AnsibleModule.fail_json", new=Mock(side_effect=fail_json)
        )
        self.exit_json_patcher = patch("ansible.module_utils.basic.AnsibleModule.exit_json", new=exit_json)

        self.fail_json_mock = self.fail_json_patcher.start()
        self.exit_json_patcher.start()

        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()

        self.mock_obj = self.connect_mock.return_value

    def tearDown(self):
        self.connect_mock.stop()
        self.exit_json_patcher.stop()
        self.fail_json_patcher.stop()
        super().tearDown()

    def test_add_domain_check_mode(self):
        self.mock_obj.access.domains.get.side_effect = [RAW_DOMAINS, RAW_LDAP]

        args = build_ldap_arg("present", "other_realm", True)
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Domain other_realm would be added."

    def test_add_ldap_domain(self):
        self.mock_obj.access.domains.get.side_effect = [RAW_DOMAINS, RAW_LDAP]

        args = build_ldap_arg("present", "other_realm", False)
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Domain other_realm added."

    def test_add_ldap_domain_idempotent(self):
        self.mock_obj.access.domains.get.side_effect = [RAW_DOMAINS, RAW_LDAP]

        args = build_ldap_arg("present", "example.test", False)
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["msg"] == "Domain example.test already exists."
        assert result["changed"] is False

    def test_edit_ldap_domain_check_mode(self):
        self.mock_obj.access.domains.get.side_effect = [RAW_DOMAINS, RAW_LDAP]

        args = build_ldap_arg("present", "example.test", True)
        args["mode"] = "ldap"
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["msg"] == "Domain example.test would be edited."
        assert result["changed"] is True

    def test_edit_ldap_domain(self):
        self.mock_obj.access.domains.get.side_effect = [RAW_DOMAINS, RAW_LDAP]

        args = build_ldap_arg("present", "example.test", False)
        args["mode"] = "ldap"
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["msg"] == "Domain example.test edited."
        assert result["changed"] is True

    def test_del_domain_check_mode(self):
        self.mock_obj.access.domains.get.side_effect = [RAW_DOMAINS, RAW_LDAP]

        args = build_base_arg("absent", "example.test", True)
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["msg"] == "Domain example.test would be deleted."
        assert result["changed"] is True

    def test_del_domain(self):
        self.mock_obj.access.domains.get.side_effect = [RAW_DOMAINS, RAW_LDAP]

        args = build_base_arg("absent", "example.test", False)
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["msg"] == "Domain example.test deleted."
        assert result["changed"] is True

    def test_del_domain_not_present(self):
        self.mock_obj.access.domains.get.side_effect = [RAW_DOMAINS, RAW_LDAP]

        args = build_base_arg("absent", "other_realm", False)
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["msg"] == "Domain other_realm not present."
        assert result["changed"] is False

    def test_add_openid_domain(self):
        self.mock_obj.access.domains.get.side_effect = [RAW_DOMAINS, RAW_OPENID]

        args = build_openid_arg("present", "openid2", False)
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["msg"] == "Domain openid2 added."
        assert result["changed"] is True

    def test_add_openid_domain_idempotent(self):
        self.mock_obj.access.domains.get.side_effect = [RAW_DOMAINS, RAW_OPENID]

        args = build_openid_arg("present", "openid", False)
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["msg"] == "Domain openid already exists."
        assert result["changed"] is False

    def test_edit_openid_domain(self):
        self.mock_obj.access.domains.get.side_effect = [RAW_DOMAINS, RAW_OPENID]

        args = build_openid_arg("present", "openid", False)
        args["issuer_url"] = "https://example.test/openid-server2"
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["msg"] == "Domain openid edited."
        assert result["changed"] is True

    def test_add_ad_domain(self):
        self.mock_obj.access.domains.get.side_effect = [RAW_DOMAINS, RAW_AD]

        args = build_ad_arg("present", "second_ad", False)
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["msg"] == "Domain second_ad added."
        assert result["changed"] is True

    def test_add_ad_domain_idempotent(self):
        self.mock_obj.access.domains.get.side_effect = [RAW_DOMAINS, RAW_AD]

        args = build_ad_arg("present", "ad", False)
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["msg"] == "Domain ad already exists."
        assert result["changed"] is False

    def test_edit_ad_domain(self):
        self.mock_obj.access.domains.get.side_effect = [RAW_DOMAINS, RAW_AD]

        args = build_ad_arg("present", "ad", False)
        args["case_sensitive"] = False
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["msg"] == "Domain ad edited."
        assert result["changed"] is True
