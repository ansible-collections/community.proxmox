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

from ansible_collections.community.proxmox.plugins.modules import proxmox_vnet_info
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)
import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils

RAW_VNETS = [
    {
        "digest": "1c0fb7bcd93d4c8cc9c444a91b9064ee34e5c786",
        "type": "vnet",
        "vnet": "lab",
        "zone": "lab",
        "tag": 100
    },
    {
        "zone": "ans1",
        "type": "vnet",
        "vnet": "test",
        "isolate-ports": 1,
        "digest": "1c0fb7bcd93d4c8cc9c444a91b9064ee34e5c786",
        "alias": "test1"
    },
    {
        "zone": "test1",
        "vnet": "test2",
        "type": "vnet",
        "digest": "1c0fb7bcd93d4c8cc9c444a91b9064ee34e5c786"
    }
]

LAB_SUBNETS = [
    {
        "network": "10.10.100.0",
        "snat": 1,
        "zone": "lab",
        "mask": "24",
        "vnet": "lab",
        "cidr": "10.10.100.0/24",
        "dhcp-range": [],
        "digest": "3ad95a6415851300419c14a62fcc0890b9095b88",
        "subnet": "lab-10.10.100.0-24",
        "type": "subnet",
        "id": "lab-10.10.100.0-24"
    }
]

TEST_SUBNETS = [
    {
        "network": "10.10.2.0",
        "cidr": "10.10.2.0/24",
        "snat": 1,
        "dhcp-range": [
            {
                "end-address": "10.10.2.15",
                "start-address": "10.10.2.5"
            },
            {
                "start-address": "10.10.2.20",
                "end-address": "10.10.2.40"
            }
        ],
        "zone": "ans1",
        "mask": "24",
        "digest": "3ad95a6415851300419c14a62fcc0890b9095b88",
        "subnet": "ans1-10.10.2.0-24",
        "vnet": "test",
        "type": "subnet",
        "id": "ans1-10.10.2.0-24"
    }
]

TEST2_SUBNETS = [
    {
        "network": "10.10.0.0",
        "cidr": "10.10.0.0/24",
        "dhcp-range": [
            {
                "end-address": "10.10.0.50",
                "start-address": "10.10.0.5"
            }
        ],
        "zone": "test1",
        "mask": "24",
        "digest": "3ad95a6415851300419c14a62fcc0890b9095b88",
        "subnet": "test1-10.10.0.0-24",
        "type": "subnet",
        "vnet": "test2",
        "id": "test1-10.10.0.0-24",
        "gateway": "10.10.0.1"
    },
    {
        "zone": "test1",
        "dhcp-range": [
            {
                "end-address": "10.10.1.50",
                "start-address": "10.10.1.5"
            }
        ],
        "cidr": "10.10.1.0/24",
        "network": "10.10.1.0",
        "digest": "3ad95a6415851300419c14a62fcc0890b9095b88",
        "mask": "24",
        "id": "test1-10.10.1.0-24",
        "type": "subnet",
        "vnet": "test2",
        "subnet": "test1-10.10.1.0-24",
        "gateway": "10.10.1.0"
    }
]

LAB_FIREWALL = []
TEST2_FIREWALL = []

TEST_FIREWALL = [
    {
        "digest": "36016a02a5387d4c1171d29be966d550216bc500",
        "enable": 1,
        "macro": "DNS",
        "action": "ACCEPT",
        "type": "forward",
        "dest": "+sdn/test2-gateway",
        "log": "nolog",
        "pos": 0
    },
    {
        "action": "ACCEPT",
        "macro": "DHCPfwd",
        "digest": "36016a02a5387d4c1171d29be966d550216bc500",
        "enable": 1,
        "pos": 1,
        "log": "nolog",
        "type": "forward"
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


def get_module_args(vnet=None):
    return {
        'api_host': 'host',
        'api_user': 'user',
        'api_password': 'password',
        'vnet': vnet
    }


class TestProxmoxVnetInfoModule(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxVnetInfoModule, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_vnet_info
        self.fail_json_patcher = patch('ansible.module_utils.basic.AnsibleModule.fail_json',
                                       new=Mock(side_effect=fail_json))
        self.exit_json_patcher = patch('ansible.module_utils.basic.AnsibleModule.exit_json', new=exit_json)

        self.fail_json_mock = self.fail_json_patcher.start()
        self.exit_json_patcher.start()
        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()
        self.mock_vnets = self.connect_mock.return_value.cluster.return_value.sdn.return_value.vnets.return_value
        self.mock_vnets.get.return_value = RAW_VNETS

        self.mock_vnets.lab.return_value.subnets.return_value.get.return_value = LAB_SUBNETS
        self.mock_vnets.test.return_value.subnets.return_value.get.return_value = TEST_SUBNETS
        self.mock_vnets.test2.return_value.subnets.return_value.get.return_value = TEST2_SUBNETS

        self.mock_vnets.lab.return_value.firewall.return_value.rules.return_value.get.return_value = []
        self.mock_vnets.test.return_value.firewall.return_value.rules.return_value.get.return_value = TEST_FIREWALL
        self.mock_vnets.test2.return_value.firewall.return_value.rules.return_value.get.return_value = []

    def tearDown(self):
        self.connect_mock.stop()
        self.exit_json_patcher.stop()
        self.fail_json_patcher.stop()
        super(TestProxmoxVnetInfoModule, self).tearDown()

    def test_get_vnets(self):
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args()):
                self.module.main()

        # Aggregate all vnet information into a single variable
        full_vnet_information = RAW_VNETS.copy()
        for idx, vnet in enumerate(RAW_VNETS):
            subnet_var = f"{vnet['vnet'].upper()}_SUBNETS"
            firewall_var = f"{vnet['vnet'].upper()}_FIREWALL"
            full_vnet_information[idx]['subnets'] = globals()[subnet_var]
            full_vnet_information[idx]['firewall_rules'] = globals()[firewall_var]

        result = exc_info.value.args[0]
        assert result["changed"] is False
        assert result["msg"] == 'Successfully retrieved vnet info'
        assert result["vnets"] == RAW_VNETS
