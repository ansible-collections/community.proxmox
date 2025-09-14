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

from ansible_collections.community.proxmox.plugins.modules import proxmox_zone_info
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)
import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils

RAW_ZONES = [
    {
        "zone": "ans1",
        "digest": "e3105246736ab2420104e34bca1dea68d152acc7",
        "ipam": "pve",
        "dhcp": "dnsmasq",
        "type": "simple"
    },
    {
        "type": "vlan",
        "zone": "lab",
        "digest": "e3105246736ab2420104e34bca1dea68d152acc7",
        "ipam": "pve",
        "bridge": "vmbr100"
    },
    {
        "digest": "e3105246736ab2420104e34bca1dea68d152acc7",
        "ipam": "pve",
        "zone": "test1",
        "type": "simple",
        "dhcp": "dnsmasq"
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


def get_module_args_state_none():
    return {
        'api_host': 'host',
        'api_user': 'user',
        'api_password': 'password',
    }


def get_module_args_zone(zone_type, zone, state='present', update=True, bridge=None):
    return {
        'api_host': 'host',
        'api_user': 'user',
        'api_password': 'password',
        'type': zone_type,
        'zone': zone,
        'state': state,
        'update': update,
        'bridge': bridge
    }


class TestProxmoxZoneInfoModule(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxZoneInfoModule, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_zone_info
        self.fail_json_patcher = patch('ansible.module_utils.basic.AnsibleModule.fail_json',
                                       new=Mock(side_effect=fail_json))
        self.exit_json_patcher = patch('ansible.module_utils.basic.AnsibleModule.exit_json', new=exit_json)

        self.fail_json_mock = self.fail_json_patcher.start()
        self.exit_json_patcher.start()
        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()
        self.connect_mock.return_value.cluster.return_value.sdn.return_value.zones.return_value.get.return_value = RAW_ZONES

    def tearDown(self):
        self.connect_mock.stop()
        self.exit_json_patcher.stop()
        self.fail_json_patcher.stop()
        super(TestProxmoxZoneInfoModule, self).tearDown()

    def test_get_zones(self):
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_state_none()):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is False
        assert result["msg"] == "Successfully retrieved zone info."
        assert result["zones"] == RAW_ZONES
