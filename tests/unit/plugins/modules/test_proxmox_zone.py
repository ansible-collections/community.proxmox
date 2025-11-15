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

from ansible_collections.community.proxmox.plugins.modules import proxmox_zone
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
    },
    {
        "zone": "vxlan-fabric-zone",
        "digest": "abc123def456",
        "type": "vxlan",
        "fabric": "my-fabric",
        "mtu": 1450
    },
    {
        "zone": "vxlan-peers-zone",
        "digest": "def456abc123",
        "type": "vxlan",
        "peers": "192.168.1.10,192.168.1.11,192.168.1.12",
        "vxlan-port": 4789
    },
    {
        "zone": "simple-zone",
        "digest": "xyz789",
        "type": "simple"
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


def get_module_args_vxlan_fabric(zone, fabric, state='present', update=True, **kwargs):
    """Helper to build module args for VXLAN zones with fabric"""
    args = {
        'api_host': 'host',
        'api_user': 'user',
        'api_password': 'password',
        'type': 'vxlan',
        'zone': zone,
        'fabric': fabric,
        'state': state,
        'update': update,
    }
    args.update(kwargs)
    return args


def get_module_args_vxlan_peers(zone, peers, state='present', update=True, **kwargs):
    """Helper to build module args for VXLAN zones with peers"""
    args = {
        'api_host': 'host',
        'api_user': 'user',
        'api_password': 'password',
        'type': 'vxlan',
        'zone': zone,
        'peers': peers,
        'state': state,
        'update': update,
    }
    args.update(kwargs)
    return args


class TestProxmoxZoneModule(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxZoneModule, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_zone
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
        super(TestProxmoxZoneModule, self).tearDown()

    def test_zone_present(self):
        # Create new Zone
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_zone(zone_type='simple', zone='test')):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Created new Zone - test"
        assert result['zone'] == 'test'

        # Update the zone
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_zone(zone_type='simple', zone='test1', state='present')):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Updated zone - test1"
        assert result['zone'] == 'test1'

        # Zone Already exists update=False
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_zone(zone_type='simple', zone='test1', update=False)):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is False
        assert result["msg"] == 'Zone test1 already exists and update is false!'
        assert result['zone'] == 'test1'

        # Zone Already exists with update=True
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_zone(zone_type='vlan', zone='test1', update=True, bridge='test')):
                self.module.main()
        result = exc_info.value.args[0]
        assert self.fail_json_mock.called
        assert result['failed'] is True
        assert result['msg'] == 'zone test1 exists with different type and we cannot change type post fact.'

    def test_zone_absent(self):
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(get_module_args_zone(zone_type='simple', zone='test1', state='absent')):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Successfully deleted zone test1"
        assert result['zone'] == 'test1'

    def test_vxlan_zone_create_with_fabric(self):
        """Test creating a new VXLAN zone with fabric"""
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(
                get_module_args_vxlan_fabric(
                    zone='new-vxlan-fabric',
                    fabric='test-fabric'
                )
            ):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Created new Zone - new-vxlan-fabric"
        assert result['zone'] == 'new-vxlan-fabric'

    def test_vxlan_zone_create_with_peers(self):
        """Test creating a new VXLAN zone with peers"""
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(
                get_module_args_vxlan_peers(
                    zone='new-vxlan-peers',
                    peers='10.0.0.1,10.0.0.2,10.0.0.3'
                )
            ):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Created new Zone - new-vxlan-peers"
        assert result['zone'] == 'new-vxlan-peers'

    def test_vxlan_zone_create_without_fabric_or_peers(self):
        """Test that creating VXLAN zone without fabric or peers fails"""
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args({
                'api_host': 'host',
                'api_user': 'user',
                'api_password': 'password',
                'type': 'vxlan',
                'zone': 'invalid-vxlan',
                'state': 'present',
                'update': True,
            }):
                self.module.main()
        result = exc_info.value.args[0]
        assert self.fail_json_mock.called
        assert result['failed'] is True
        assert 'fabric or peers' in result['msg']

    def test_vxlan_zone_update_peers_zone(self):
        """Test updating an existing VXLAN zone with peers"""
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(
                get_module_args_vxlan_peers(
                    zone='vxlan-peers-zone',
                    peers='192.168.1.10,192.168.1.11,192.168.1.12,192.168.1.13',  # Added peer
                    update=True
                )
            ):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Updated zone - vxlan-peers-zone"
        assert result['zone'] == 'vxlan-peers-zone'

    def test_vxlan_zone_delete_fabric_zone(self):
        """Test deleting a VXLAN zone with fabric"""
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(
                get_module_args_vxlan_fabric(
                    zone='vxlan-fabric-zone',
                    fabric='my-fabric',
                    state='absent'
                )
            ):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Successfully deleted zone vxlan-fabric-zone"
        assert result['zone'] == 'vxlan-fabric-zone'

    def test_vxlan_zone_delete_peers_zone(self):
        """Test deleting a VXLAN zone with peers"""
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(
                get_module_args_vxlan_peers(
                    zone='vxlan-peers-zone',
                    peers='192.168.1.10,192.168.1.11',
                    state='absent'
                )
            ):
                self.module.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Successfully deleted zone vxlan-peers-zone"
        assert result['zone'] == 'vxlan-peers-zone'

    def test_vxlan_zone_empty_peers_list(self):
        """Test VXLAN zone with empty peers string"""
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(
                get_module_args_vxlan_peers(
                    zone='vxlan-empty-peers',
                    peers=''
                )
            ):
                self.module.main()
        result = exc_info.value.args[0]
        # Should fail validation since neither fabric nor valid peers provided
        assert self.fail_json_mock.called or result["changed"] is False

    def test_vxlan_zone_empty_fabric(self):
        """Test VXLAN zone with empty fabric string"""
        with pytest.raises(SystemExit) as exc_info:
            with set_module_args(
                get_module_args_vxlan_fabric(
                    zone='vxlan-empty-fabric',
                    fabric=''
                )
            ):
                self.module.main()
        result = exc_info.value.args[0]
        # Should fail validation
        assert self.fail_json_mock.called or result["changed"] is False
