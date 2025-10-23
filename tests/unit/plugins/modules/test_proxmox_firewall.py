# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Jana Hoch <janahoch91@proton.me>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import patch

import pytest

proxmoxer = pytest.importorskip("proxmoxer")

from ansible.module_utils import basic
from ansible_collections.community.proxmox.plugins.modules import proxmox_firewall
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)
import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils

RAW_FIREWALL_RULES = [
    {
        "ipversion": 4,
        "digest": "245f9fb31d5f59543dedc5a84ba7cd6afa4dbcc0",
        "log": "nolog",
        "action": "ACCEPT",
        "enable": 1,
        "type": "out",
        "source": "1.1.1.1",
        "pos": 0
    },
    {
        "enable": 1,
        "pos": 1,
        "source": "1.0.0.1",
        "type": "out",
        "action": "ACCEPT",
        "digest": "245f9fb31d5f59543dedc5a84ba7cd6afa4dbcc0",
        "ipversion": 4
    }
]

RAW_GROUPS = [
    {
        "digest": "fdb62dec01018d4f35c83ecc2ae3f110a8b3bd62",
        "group": "test1"
    },
    {
        "group": "test2",
        "digest": "fdb62dec01018d4f35c83ecc2ae3f110a8b3bd62"
    }
]

RAW_IPSET = [
    {
        "digest": "48671c29c6503157990fc99354b78f32e8654c78",
        "name": "test_ipset"
    }
]

RAW_IPSET_CIDR = [
    {
        "digest": "dce088809f001ca83c39c8dcfc2a5e4892bf3d1b",
        "cidr": "192.168.1.10",
        "nomatch": True
    }
]


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise SystemExit(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise SystemExit(kwargs)


def get_module_args_group_conf(group, level="cluster", state="present"):
    return {
        "api_host": "host",
        "api_user": "user",
        "api_password": "password",
        "level": level,
        "group": group,
        "group_conf": True,
        "state": state
    }


def get_module_args_rules(state, pos=1, level='cluster', source_ip='1.1.1.1'):
    return {
        "api_host": "host",
        "api_user": "user",
        "api_password": "password",
        "level": level,
        "state": state,
        'rules': [
            {
                'type': 'out',
                'action': 'ACCEPT',
                'source': source_ip,
                'pos': pos,
                'enable': True
            }
        ]
    }


def get_module_args_ipset(state, name, cidr=False, nomatch=False):
    if cidr:
        return {
            "api_host": "host",
            "api_user": "user",
            "api_password": "password",
            "level": "cluster",
            "state": state,
            "ip_sets": [{
                "name": name,
                "cidrs": [{
                    "cidr": "192.168.1.10",
                    "nomatch": nomatch
                }]
            }]

        }
    return {
        "api_host": "host",
        "api_user": "user",
        "api_password": "password",
        "level": "cluster",
        "state": state,
        "ip_sets": [{
            "name": name,
        }]

    }


def get_module_args_fw_delete(pos, level='cluster', state='absent'):
    return {
        "api_host": "host",
        "api_user": "user",
        "api_password": "password",
        "level": level,
        "state": state,
        "pos": pos
    }


class TestProxmoxFirewallModule(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxFirewallModule, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_firewall
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()

        mock_cluster_fw = self.connect_mock.return_value.cluster.return_value.firewall.return_value
        mock_cluster_fw.rules.return_value.get.return_value = RAW_FIREWALL_RULES
        mock_cluster_fw.groups.return_value.get.return_value = RAW_GROUPS
        mock_cluster_fw.ipset.return_value.test_ipset.get.return_value = RAW_IPSET_CIDR
        mock_cluster_fw.ipset.return_value.get.return_value = RAW_IPSET

    def tearDown(self):
        self.connect_mock.stop()
        self.mock_module_helper.stop()
        super(TestProxmoxFirewallModule, self).tearDown()

    def test_create_group(self):
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_group_conf(group='test')):
                self.module.main()
        result = exc_info.value.args[0]
        assert result['changed'] is True
        assert result["msg"] == 'successfully created security group test'
        assert result['group'] == 'test'

    def test_delete_group(self):
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_group_conf(group='test1', state="absent")):
                self.module.main()
        result = exc_info.value.args[0]
        assert result['changed'] is True
        assert result["msg"] == 'successfully deleted security group test1'
        assert result['group'] == 'test1'

    def test_create_fw_rules(self):
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_rules(state='present', pos=2)):
                self.module.main()
        result = exc_info.value.args[0]
        assert result['changed'] is True
        assert result["msg"] == 'successfully created/updated firewall rules'

    def test_delete_fw_rule(self):
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_fw_delete(state='absent', pos=0)):
                self.module.main()
        result = exc_info.value.args[0]
        assert result['changed'] is True
        assert result["msg"] == 'successfully deleted firewall rules'

    def test_ipset_present(self):
        # New Ipset name
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_ipset(state='present', name='new_ipset', cidr=True)):
                self.module.main()
        result = exc_info.value.args[0]
        assert result['changed'] is True
        assert result["msg"] == 'All ipsets present.'

        # Same as existing ipset (no change)
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_ipset(state='present', name='test_ipset', cidr=True, nomatch=True)):
                self.module.main()
        result = exc_info.value.args[0]
        assert result['changed'] is False
        assert result["msg"] == 'All ipsets present.'

    def test_ipset_absent(self):
        # Delete full ipset
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_ipset(state='absent', name='test_ipset', cidr=False)):
                self.module.main()
        result = exc_info.value.args[0]
        assert result['changed'] is True
        assert result["msg"] == 'Ipsets are absent.'

        # Delete only 1 CIDR
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_ipset(state='absent', name='test_ipset', cidr=True)):
                self.module.main()
        result = exc_info.value.args[0]
        assert result['changed'] is True
        assert result["msg"] == 'Ipsets are absent.'

        # try to delete non existent ipset (changed=False)
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_ipset(state='absent', name='ipset_doesnt_exist')):
                self.module.main()
        result = exc_info.value.args[0]
        assert result['changed'] is False
        assert result["msg"] == 'Ipsets are absent.'
