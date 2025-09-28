# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Jana Hoch <janahoch91@proton.me>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import patch, Mock

import pytest

proxmoxer = pytest.importorskip("proxmoxer")

from ansible_collections.community.proxmox.plugins.modules import proxmox_subnet
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)
import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils

RAW_SUBNETS = [
    {
        "type": "subnet",
        "subnet": "ans1-10.10.2.0-24",
        "zone": "ans1",
        "snat": 0,
        "cidr": "10.10.2.0/24",
        "id": "ans1-10.10.2.0-24",
        "mask": "24",
        "dhcp-range": [
            {
                "start-address": "10.10.2.5",
                "end-address": "10.10.2.25"
            },
            {
                "start-address": "10.10.2.50",
                "end-address": "10.10.2.100"
            }
        ],
        "digest": "c870dc42a3b5356b6037590e9552cbd5d2334963",
        "vnet": "test",
        "network": "10.10.2.0"
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


def get_module_args(vnet, subnet, zone, state='present', dhcp_range=None, snat=0, dhcp_range_update_mode='append'):
    return {
        'api_host': 'host',
        'api_user': 'user',
        'api_password': 'password',
        'vnet': vnet,
        'subnet': subnet,
        'zone': zone,
        'state': state,
        'dhcp_range': dhcp_range,
        'snat': snat,
        'dhcp_range_update_mode': dhcp_range_update_mode
    }


class TestProxmoxSubnetModule(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxSubnetModule, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_subnet
        self.fail_json_patcher = patch('ansible.module_utils.basic.AnsibleModule.fail_json',
                                       new=Mock(side_effect=fail_json))
        self.exit_json_patcher = patch('ansible.module_utils.basic.AnsibleModule.exit_json', new=exit_json)

        self.fail_json_mock = self.fail_json_patcher.start()
        self.exit_json_patcher.start()
        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()
        self.connect_mock.return_value.cluster.return_value.sdn.return_value.vnets.return_value.subnets.return_value.get.return_value = RAW_SUBNETS

    def tearDown(self):
        self.connect_mock.stop()
        self.exit_json_patcher.stop()
        self.fail_json_patcher.stop()
        super(TestProxmoxSubnetModule, self).tearDown()

    def test_subnet_create(self):
        # Create new Zone
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args(vnet='new_vnet',
                                                 subnet='10.10.10.0/24',
                                                 zone='test_zone')):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Created new subnet 10.10.10.0/24"
        assert result['subnet'] == 'test_zone-10.10.10.0-24'

    def test_subnet_update(self):
        # Normal subnet param (snat) differ
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args(vnet='test',
                                                 subnet='10.10.2.0/24',
                                                 zone='ans1',
                                                 snat=1)):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Updated subnet ans1-10.10.2.0-24"
        assert result['subnet'] == 'ans1-10.10.2.0-24'

        # No update needed
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args(vnet='test',
                                                 subnet='10.10.2.0/24',
                                                 zone='ans1')):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is False
        assert result["msg"] == "subnet ans1-10.10.2.0-24 is already present with correct parameters."
        assert result['subnet'] == 'ans1-10.10.2.0-24'

        # New dhcp_range
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args(vnet='test',
                                                 subnet='10.10.2.0/24',
                                                 zone='ans1',
                                                 dhcp_range=[{'start': '10.10.2.150', 'end': '10.10.2.200'}])):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Updated subnet ans1-10.10.2.0-24"
        assert result['subnet'] == 'ans1-10.10.2.0-24'

        # dhcp_range is partially overlapping and mode is append
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args(vnet='test',
                                                 subnet='10.10.2.0/24',
                                                 zone='ans1',
                                                 dhcp_range=[{'start': '10.10.2.10', 'end': '10.10.2.20'}])):
                self.module.main()
        result = exc_info.value.args[0]
        assert self.fail_json_mock.called
        assert result["failed"] is True
        assert result["msg"] == "There are partially overlapping DHCP ranges. this is not allowed."

    def test_subnet_absent(self):
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args(vnet='test',
                                                 subnet='10.10.2.0/24',
                                                 zone='ans1', state='absent')):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Deleted subnet ans1-10.10.2.0-24"
        assert result['subnet'] == 'ans1-10.10.2.0-24'
