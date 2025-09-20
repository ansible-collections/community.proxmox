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
from ansible_collections.community.proxmox.plugins.modules import proxmox_ipam_info
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)
import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils

RAW_IPAM_STATUS = [
    {
        "subnet": "10.10.1.0/24",
        "vnet": "test2",
        "zone": "test1",
        "ip": "10.10.1.0",
        "gateway": 1
    },
    {
        "ip": "10.10.0.1",
        "gateway": 1,
        "vnet": "test2",
        "subnet": "10.10.0.0/24",
        "zone": "test1"
    },
    {
        "zone": "test1",
        "vnet": "test2",
        "subnet": "10.10.0.0/24",
        "mac": "BC:24:11:F3:B1:81",
        "vmid": 102,
        "hostname": "ns3.proxmox.pc",
        "ip": "10.10.0.8"
    },
    {
        "subnet": "10.10.0.0/24",
        "vnet": "test2",
        "zone": "test1",
        "ip": "10.10.0.7",
        "hostname": "ns4.proxmox.pc",
        "vmid": 103,
        "mac": "BC:24:11:D5:CD:82"
    },
    {
        "ip": "10.10.0.5",
        "hostname": "ns2.proxmox.pc.test3",
        "mac": "BC:24:11:86:77:56",
        "vmid": 101,
        "subnet": "10.10.0.0/24",
        "vnet": "test2",
        "zone": "test1"
    }
]

RAW_IPAM = [
    {
        "ipam": "pve",
        "type": "pve",
        "digest": "da39a3ee5e6b4b0d3255bfef95601890afd80709"
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


def get_module_args(ipam=None, vmid=None):
    return {
        'api_host': 'host',
        'api_user': 'user',
        'api_password': 'password',
        'ipam': ipam,
        'vmid': vmid
    }


class TestProxmoxIpamInfoModule(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxIpamInfoModule, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_ipam_info
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()
        self.mock_ipam = self.connect_mock.return_value.cluster.return_value.sdn.return_value.ipams.return_value
        self.mock_ipam.get.return_value = RAW_IPAM
        self.mock_ipam.pve.return_value.status.return_value.get.return_value = RAW_IPAM_STATUS
        self.mock_ipam.status.return_value.get.return_value = RAW_IPAM_STATUS

    def tearDown(self):
        self.connect_mock.stop()
        self.mock_module_helper.stop()
        super(TestProxmoxIpamInfoModule, self).tearDown()

    def test_get_all_ipam_status(self):
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args(ipam=None)):
                self.module.main()

        result = exc_info.value.args[0]
        assert result["changed"] is False
        assert result["ipams"] == {'pve': RAW_IPAM_STATUS}

    def test_get_all_ipam_pve_status(self):
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args(ipam='pve')):
                self.module.main()

        result = exc_info.value.args[0]
        assert result["changed"] is False
        assert result["ipams"] == RAW_IPAM_STATUS

    def test_get_ip_by_vmid(self):
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args(vmid=102)):
                self.module.main()

        result = exc_info.value.args[0]
        assert result["changed"] is False
        assert result["ips"] == [x for x in RAW_IPAM_STATUS if x.get('vmid') == 102]
