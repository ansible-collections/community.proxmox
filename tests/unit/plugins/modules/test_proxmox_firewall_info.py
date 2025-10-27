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
from ansible_collections.community.proxmox.plugins.modules import proxmox_firewall_info
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

RAW_ALIASES = [
    {
        "name": "test1",
        "cidr": "10.10.1.0/24",
        "digest": "978391f460484e8d4fb3ca785cfe5a9d16fe8b1f",
        "ipversion": 4
    },
    {
        "name": "test2",
        "cidr": "10.10.2.0/24",
        "digest": "978391f460484e8d4fb3ca785cfe5a9d16fe8b1f",
        "ipversion": 4
    },
    {
        "name": "test3",
        "cidr": "10.10.3.0/24",
        "digest": "978391f460484e8d4fb3ca785cfe5a9d16fe8b1f",
        "ipversion": 4
    }
]

RAW_CLUSTER_RESOURCES = [
    {
        "vmid": 100,
        "maxcpu": 8,
        "memhost": 860138496,
        "type": "qemu",
        "id": "qemu/100",
        "diskread": 127452302,
        "netin": 42,
        "netout": 0,
        "cpu": 0.0046731498237984,
        "uptime": 119787,
        "template": 0,
        "disk": 0,
        "name": "nextcloud",
        "maxdisk": 644245094400,
        "mem": 445415424,
        "status": "running",
        "diskwrite": 1024,
        "maxmem": 8589934592,
        "node": "pve"
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
        "comment": "Proxmox pve-01"
    }
]

EXPECTED_IPSET = [
    {
        "digest": "48671c29c6503157990fc99354b78f32e8654c78",
        "name": "test_ipset",
        "cidrs": [
            {
                "digest": "dce088809f001ca83c39c8dcfc2a5e4892bf3d1b",
                "cidr": "192.168.1.10",
                "comment": "Proxmox pve-01",
                "nomatch": False
            }
        ]

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


def get_module_args(level="cluster", vmid=None, node=None, vnet=None, group=None):
    return {
        "api_host": "host",
        "api_user": "user",
        "api_password": "password",
        "level": level,
        "vmid": vmid,
        "node": node,
        "vnet": vnet,
        "group": group
    }


class TestProxmoxFirewallModule(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxFirewallModule, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_firewall_info
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()

        self.connect_mock.return_value.cluster.resources.get.return_value = (
            RAW_CLUSTER_RESOURCES
        )

        mock_cluster_fw = self.connect_mock.return_value.cluster.return_value.firewall.return_value
        mock_vm100_fw = self.connect_mock.return_value.nodes.return_value.return_value.return_value.firewall.return_value

        mock_cluster_fw.rules.return_value.get.return_value = RAW_FIREWALL_RULES
        mock_cluster_fw.groups.return_value.get.return_value = RAW_GROUPS
        mock_cluster_fw.aliases.return_value.get.return_value = RAW_ALIASES
        mock_cluster_fw.ipset.return_value.test_ipset.get.return_value = RAW_IPSET_CIDR
        mock_cluster_fw.ipset.return_value.get.return_value = RAW_IPSET

        mock_vm100_fw.rules.return_value.get.return_value = RAW_FIREWALL_RULES
        mock_vm100_fw.aliases.return_value.get.return_value = RAW_ALIASES

    def tearDown(self):
        self.connect_mock.stop()
        self.mock_module_helper.stop()
        super(TestProxmoxFirewallModule, self).tearDown()

    def test_cluster_level_info(self):
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args()):
                self.module.main()
        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert result["msg"] == "successfully retrieved firewall rules and groups"
        assert result["firewall_rules"] == RAW_FIREWALL_RULES
        assert result["groups"] == ['test1', 'test2']
        assert result["aliases"] == RAW_ALIASES
        assert result["ip_sets"] == EXPECTED_IPSET

    def test_vm_level_info(self):
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args(level='vm', vmid=100)):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is False
        assert result["msg"] == "successfully retrieved firewall rules and groups"
        assert result["firewall_rules"] == RAW_FIREWALL_RULES
        assert result["groups"] == ['test1', 'test2']
        assert result["aliases"] == RAW_ALIASES
