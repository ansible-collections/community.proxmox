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

from ansible_collections.community.proxmox.plugins.modules import proxmox_vnet
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)
import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise SystemExit(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise SystemExit(kwargs)


def get_module_args_zone(zone, vnet, state='present', update=True, alias=None):
    return {
        'api_host': 'host',
        'api_user': 'user',
        'api_password': 'password',
        'zone': zone,
        'state': state,
        'update': update,
        'vnet': vnet,
        'alias': alias
    }


RAW_VNETS = [
    {
        "type": "vnet",
        "vnet": "test",
        "zone": "ans1",
        "alias": "test1",
        "digest": "79ee852ce6fd2cc12c047363e7059a761fe68a8c",
        "isolate-ports": 1
    },
    {
        "type": "vnet",
        "zone": "test1",
        "digest": "79ee852ce6fd2cc12c047363e7059a761fe68a8c",
        "vnet": "test2"
    }
]


class TestProxmoxVnetModule(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxVnetModule, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_vnet
        self.fail_json_patcher = patch('ansible.module_utils.basic.AnsibleModule.fail_json',
                                       new=Mock(side_effect=fail_json))
        self.exit_json_patcher = patch('ansible.module_utils.basic.AnsibleModule.exit_json', new=exit_json)

        self.fail_json_mock = self.fail_json_patcher.start()
        self.exit_json_patcher.start()
        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()
        self.connect_mock.return_value.cluster.return_value.sdn.return_value.vnets.return_value.get.return_value = RAW_VNETS.copy()

    def tearDown(self):
        self.connect_mock.stop()
        self.exit_json_patcher.stop()
        self.fail_json_patcher.stop()
        super(TestProxmoxVnetModule, self).tearDown()

    def test_vnet_present(self):
        # Create new Vnet
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_zone(zone='ztest', vnet='vtest')):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Create new vnet vtest"
        assert result['vnet'] == 'vtest'

        # Update the vnet
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_zone(zone='test1', vnet='test2', alias='test', update=True)):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "updated vnet test2"
        assert result['vnet'] == 'test2'

        # Vnet needs to be updated but update=False
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_zone(zone='test1', vnet='test2', alias='test', update=False)):
                self.module.main()
        result = exc_info.value.args[0]
        assert self.fail_json_mock.called
        assert result["failed"] is True
        assert result["msg"] == 'vnet test2 needs to be updated but update is false.'

    def test_zone_absent(self):
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_zone(zone='test1', vnet='test2', state='absent')):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Deleted vnet test2"
        assert result['vnet'] == 'test2'
