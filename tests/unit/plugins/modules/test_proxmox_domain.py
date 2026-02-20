# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, teslamania <nicolas.vial@protonmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


from unittest.mock import patch, Mock
import pytest

from ansible_collections.community.proxmox.plugins.modules import (
    proxmox_domain,
)
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)
import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils

proxmoxer = pytest.importorskip("proxmoxer")

RAW_DOMAINS = [
    {
        'type': 'pve',
        'comment': 'Proxmox VE authentication server',
        'realm': 'pve'
    },
    {
        'realm': 'ad',
        'comment': "comment test",
        'type': 'ad'
    },
    {
        'realm': 'openid',
        'type': 'openid'
    },
    {
        'type': 'pam',
        'realm': 'pam',
        'comment': 'Linux PAM standard authentication'
    },
    {
        'realm': 'example.test',
        'default': 1,
        'type': 'ldap'
    }
]

RAW_LDAP = {
    'mode': 'ldaps',
    'sync-defaults-options': 'enable-new=1,remove-vanished=acl;properties;entry,scope=both',
    'user_attr': 'uid',
    'group_name_attr': 'cn',
    'default': 1,
    'type': 'ldap',
    'base_dn': 'cn=accounts,dc=example,dc=test',
    'digest': 'c21f05ca10e3c1c4f047e095072d2b8b960fa83d',
    'bind_dn': 'uid=sa-proxmox,cn=users,cn=accounts,dc=example,dc=test',
    'group_filter': 'cn=admins-proxmox',
    'server1': 'ipa.example.test',
    'filter': 'memberof=cn=admins-proxmox,cn=groups,cn=accounts,dc=example,dc=test',
    'verify': 0
}


def exit_json(*args, **kwargs):
    """function to patch over exit_json;
        package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise SystemExit(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json;
        package return data into an exception"""
    kwargs['failed'] = True
    raise SystemExit(kwargs)


def build_base_arg(state, check=False):
    args = {
        "api_user": "root@pam",
        "api_password": "secret",
        "api_host": "192.168.1.21",
        "state": state
    }
    if check:
        args["_ansible_check_mode"] = True
    return args

def build_ldap_arg(state, realm, check=False):
    args = build_base_arg(state, check)
    args["realm"] = realm
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
    args["sync_defaults_options"] = {
      "scope": "both",
      "enable_new": True,
      "remove_vanished": "acl;properties;entry"
    }
    return args


class TestProxmoxDomain(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxDomain, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_domain

        self.fail_json_patcher = patch(
            'ansible.module_utils.basic.AnsibleModule.fail_json',
            new=Mock(side_effect=fail_json)
        )
        self.exit_json_patcher = patch(
            'ansible.module_utils.basic.AnsibleModule.exit_json',
            new=exit_json)

        self.fail_json_mock = self.fail_json_patcher.start()
        self.exit_json_patcher.start()

        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()

        mock_obj = self.connect_mock.return_value
        #mock_obj.access.domains.get.return_value = (
        #    RAW_DOMAINS
        #)
        #mock_obj.access.domains.return_value.get.return_value = (
        #    RAW_LDAP
        #)
        mock_obj.access.domains.get.side_effect = (
            [RAW_DOMAINS, RAW_LDAP]
        )

    def tearDown(self):
        self.connect_mock.stop()
        self.exit_json_patcher.stop()
        self.fail_json_patcher.stop()
        super(TestProxmoxDomain, self).tearDown()

    def test_add_domain_check_mode(self):
        with set_module_args(build_ldap_arg("present", "other_realm", True)):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Domain other_realm would be added."

    def test_add_ldap_domain(self):
        with set_module_args(build_ldap_arg("present", "other_realm", False)):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Domain other_realm added."

    def test_add_ldap_domain_idempotent(self):
        with set_module_args(build_ldap_arg("present", "example.test", False)):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_domain.main()

        result = exc_info.value.args[0]

        assert result["msg"] == "Domain example.test already exists."
        assert result["changed"] is False

