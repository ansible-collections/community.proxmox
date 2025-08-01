# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, aleskxyz <aleskxyz@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import patch
import pytest

proxmoxer = pytest.importorskip("proxmoxer")

from ansible_collections.community.proxmox.plugins.modules import proxmox_node_network
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    ModuleTestCase,
    set_module_args,
)
import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils

# Mock API response for existing network interfaces
EXISTING_NETWORK_OUTPUT = [
    {
        "iface": "eth0",
        "type": "eth",
        "active": 1,
        "autostart": 1,
        "mtu": 1500,
        "method": "manual",
        "families": ["inet"],
    },
    {
        "iface": "vmbr0",
        "type": "bridge",
        "active": 1,
        "autostart": 1,
        "mtu": 1500,
        "method": "static",
        "families": ["inet"],
        "bridge_ports": "eth0",
        "address": "192.168.1.1",
        "netmask": "255.255.255.0",
    },
]

# Mock API response for specific interface
EXISTING_BRIDGE_CONFIG = {
    "iface": "vmbr0",
    "type": "bridge",
    "active": 1,
    "autostart": 1,
    "mtu": 1500,
    "method": "static",
    "families": ["inet"],
    "bridge_ports": "eth0",
    "address": "192.168.1.1",
    "netmask": "255.255.255.0",
}

# Mock pending changes response
MOCK_PENDING_CHANGES = """--- /etc/network/interfaces
+++ /etc/network/interfaces
@@ -10,6 +10,12 @@
 # The primary network interface
 auto eth0
 iface eth0 inet dhcp
+
+# Bridge interface
+auto vmbr1
+iface vmbr1 inet static
+        address 192.168.2.1/24
+        bridge_ports eth1"""


class TestProxmoxNodeNetworkSimple(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxNodeNetworkSimple, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_node_network

        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()

        mock_nodes = self.connect_mock.return_value.nodes
        mock_node_obj = mock_nodes.return_value
        mock_nodes.side_effect = lambda node=None: mock_node_obj

        mock_network_obj = mock_node_obj.network.return_value
        mock_node_obj.network = mock_network_obj
        mock_node_obj.network.return_value = mock_network_obj
        mock_network_obj.get.return_value = EXISTING_NETWORK_OUTPUT

        mock_nodes.get.return_value = [{"node": "pve"}]

        mock_network_obj.get.side_effect = lambda type=None: [
            interface
            for interface in EXISTING_NETWORK_OUTPUT
            if type is None or interface["type"] == type
        ]

    def tearDown(self):
        self.connect_mock.stop()
        super(TestProxmoxNodeNetworkSimple, self).tearDown()

    def test_create_bridge_interface(self):
        """Test creating a new bridge interface."""
        # Mock the interface config to return None initially (interface doesn't exist)
        # Then return the created config after creation
        created_config = {
            "iface": "vmbr1",
            "type": "bridge",
            "bridge_ports": "eth1",
            "cidr": "192.168.2.1/24",
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            side_effect=[None, created_config],
        ):
            with patch.object(
                self.module.ProxmoxNetworkManager, "create_interface", return_value=True
            ):
                with pytest.raises(AnsibleExitJson) as exc_info:
                    with set_module_args(
                        {
                            "api_host": "host",
                            "api_user": "user",
                            "api_password": "password",
                            "node": "pve",
                            "iface": "vmbr1",
                            "iface_type": "bridge",
                            "bridge_ports": "eth1",
                            "cidr": "192.168.2.1/24",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "vmbr1"
                assert "created" in result["msg"].lower()

    def test_update_existing_interface(self):
        """Test updating an existing interface."""
        updated_config = {
            "iface": "vmbr0",
            "type": "bridge",
            "bridge_ports": "eth0 eth1",
            "mtu": 9000,
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            side_effect=[EXISTING_BRIDGE_CONFIG, updated_config],
        ):
            with patch.object(
                self.module.ProxmoxNetworkManager, "update_interface", return_value=True
            ):
                with pytest.raises(AnsibleExitJson) as exc_info:
                    with set_module_args(
                        {
                            "api_host": "host",
                            "api_user": "user",
                            "api_password": "password",
                            "node": "pve",
                            "iface": "vmbr0",
                            "iface_type": "bridge",
                            "bridge_ports": "eth0 eth1",
                            "mtu": 9000,
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "vmbr0"
                assert "updated" in result["msg"].lower()

    def test_no_changes_needed(self):
        """Test when no changes are needed."""
        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            return_value=EXISTING_BRIDGE_CONFIG,
        ):
            with patch.object(
                self.module.ProxmoxNetworkManager,
                "update_interface",
                return_value=False,
            ):
                with pytest.raises(AnsibleExitJson) as exc_info:
                    with set_module_args(
                        {
                            "api_host": "host",
                            "api_user": "user",
                            "api_password": "password",
                            "node": "pve",
                            "iface": "vmbr0",
                            "iface_type": "bridge",
                            "bridge_ports": "eth0",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is False
                assert result["interface"]["iface"] == "vmbr0"
                assert "already exists with correct configuration" in result["msg"]

    def test_delete_interface(self):
        """Test deleting an interface."""
        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            return_value=EXISTING_BRIDGE_CONFIG,
        ):
            with patch.object(
                self.module.ProxmoxNetworkManager, "delete_interface", return_value=True
            ):
                with pytest.raises(AnsibleExitJson) as exc_info:
                    with set_module_args(
                        {
                            "api_host": "host",
                            "api_user": "user",
                            "api_password": "password",
                            "node": "pve",
                            "iface": "vmbr0",
                            "state": "absent",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert "deleted" in result["msg"].lower()

    def test_apply_network_changes(self):
        """Test applying staged network changes."""

        class MockResponse:
            def json(self):
                return {
                    "data": EXISTING_NETWORK_OUTPUT,
                    "changes": MOCK_PENDING_CHANGES,
                    "success": 1,
                }

            def raise_for_status(self, *args, **kwargs):
                pass

        mock_response = MockResponse()

        with patch.object(
            self.connect_mock.return_value._store["session"],
            "request",
            return_value=mock_response,
        ):
            with patch.object(
                self.module.ProxmoxNetworkManager, "apply_network", return_value=True
            ):
                with patch.object(
                    self.module.ProxmoxNetworkManager,
                    "check_network_changes",
                    return_value=MOCK_PENDING_CHANGES,
                ):
                    with pytest.raises(AnsibleExitJson) as exc_info:
                        with set_module_args(
                            {
                                "api_host": "host",
                                "api_user": "user",
                                "api_password": "password",
                                "node": "pve",
                                "state": "apply",
                            }
                        ):
                            self.module.main()

                    result = exc_info.value.args[0]
                    assert result["changed"] is True
                    assert "applied" in result["msg"].lower()

    def test_revert_network_changes(self):
        """Test reverting staged network changes."""
        with patch.object(
            self.module.ProxmoxNetworkManager, "revert_network", return_value=True
        ):
            with pytest.raises(AnsibleExitJson) as exc_info:
                with set_module_args(
                    {
                        "api_host": "host",
                        "api_user": "user",
                        "api_password": "password",
                        "node": "pve",
                        "state": "revert",
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert result["changed"] is True
            assert "reverted" in result["msg"].lower()

    def test_missing_required_parameters(self):
        """Test error when required parameters are missing."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "state": "present",
                    # Missing iface and iface_type
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "state is present but all of the following are missing: iface, iface_type"
            in result["msg"]
        )

    def test_invalid_interface_type(self):
        """Test error with invalid interface type."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "test0",
                    "iface_type": "invalid_type",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "value of iface_type must be one of: bridge, bond, eth, vlan, OVSBridge, OVSBond, OVSIntPort, got: invalid_type"
            in result["msg"]
        )

    def test_invalid_mtu_value(self):
        """Test error with invalid MTU value."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "eth0",
                    "iface_type": "eth",
                    "mtu": 1000,  # Too low
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "MTU must be between 1280 and 65520" in result["msg"]

    def test_invalid_cidr_format(self):
        """Test error with invalid CIDR format."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "eth0",
                    "iface_type": "eth",
                    "cidr": "invalid_cidr",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "Invalid IPv4 CIDR format" in result["msg"]

    def test_bridge_without_required_parameters(self):
        """Test bridge interface with missing required parameters."""
        # Bridge interfaces don't actually require bridge_ports, so this should work
        created_config = {"iface": "vmbr0", "type": "bridge"}

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            side_effect=[None, created_config],
        ):
            with patch.object(
                self.module.ProxmoxNetworkManager, "create_interface", return_value=True
            ):
                with pytest.raises(AnsibleExitJson) as exc_info:
                    with set_module_args(
                        {
                            "api_host": "host",
                            "api_user": "user",
                            "api_password": "password",
                            "node": "pve",
                            "iface": "vmbr0",
                            "iface_type": "bridge",
                            # bridge_ports is optional
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "vmbr0"

    def test_vlan_without_raw_device(self):
        """Test VLAN interface without vlan_raw_device."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vlan100",
                    "iface_type": "vlan",
                    # Missing vlan_raw_device
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "vlan_raw_device is required when iface starts with 'vlan'" in result["msg"]
        )

    def test_node_not_found(self):
        """Test error handling when node doesn't exist."""
        with patch.object(
            self.module.ProxmoxNetworkManager, "get_node", return_value=None
        ):
            with pytest.raises(AnsibleFailJson) as exc_info:
                with set_module_args(
                    {
                        "api_host": "host",
                        "api_user": "user",
                        "api_password": "password",
                        "node": "nonexistent",
                        "iface": "eth0",
                        "iface_type": "eth",
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert "Node 'nonexistent' not found" in result["msg"]

    def test_check_mode_create(self):
        """Test creating interface in check mode."""
        with patch.object(
            self.module.ProxmoxNetworkManager, "get_interface_config", return_value=None
        ):
            with pytest.raises(AnsibleExitJson) as exc_info:
                with set_module_args(
                    {
                        "api_host": "host",
                        "api_user": "user",
                        "api_password": "password",
                        "node": "pve",
                        "iface": "vmbr1",
                        "iface_type": "bridge",
                        "bridge_ports": "eth1",
                        "cidr": "192.168.2.1/24",
                        "_ansible_check_mode": True,
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert result["changed"] is True
            assert result["interface"]["iface"] == "vmbr1"
            assert "would be created" in result["msg"].lower()

    def test_check_mode_update(self):
        """Test updating interface in check mode."""
        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            return_value=EXISTING_BRIDGE_CONFIG,
        ):
            with pytest.raises(AnsibleExitJson) as exc_info:
                with set_module_args(
                    {
                        "api_host": "host",
                        "api_user": "user",
                        "api_password": "password",
                        "node": "pve",
                        "iface": "vmbr0",
                        "iface_type": "bridge",
                        "bridge_ports": "eth0 eth1",
                        "mtu": 9000,
                        "_ansible_check_mode": True,
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert result["changed"] is True
            assert result["interface"]["iface"] == "vmbr0"
            assert "would be updated" in result["msg"].lower()

    def test_bridge_vids_without_vlan_aware(self):
        """Test bridge with bridge_vids but without bridge_vlan_aware."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vmbr0",
                    "iface_type": "bridge",
                    "bridge_ports": "eth0",
                    "bridge_vids": "100 200",
                    # Missing bridge_vlan_aware: true
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "bridge_vids should not be defined if bridge_vlan_aware is not set or false"
            in result["msg"]
        )

    def test_bond_missing_required_parameters(self):
        """Test bond interface with missing required parameters."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "bond0",
                    "iface_type": "bond",
                    # Missing bond_mode and slaves
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "bond_mode is required for bond type" in result["msg"]
        assert "slaves is required for bond type" in result["msg"]

    def test_bond_active_backup_without_primary(self):
        """Test active-backup bond without bond_primary."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "bond0",
                    "iface_type": "bond",
                    "bond_mode": "active-backup",
                    "slaves": "eth0 eth1",
                    # Missing bond_primary
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "bond_primary is required for active-backup mode" in result["msg"]

    def test_bond_primary_not_in_slaves(self):
        """Test bond with bond_primary not in slaves list."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "bond0",
                    "iface_type": "bond",
                    "bond_mode": "active-backup",
                    "bond_primary": "eth0",
                    "slaves": "eth1 eth2",  # eth0 not in slaves
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "bond_primary must be included in slaves for active-backup mode"
            in result["msg"]
        )

    def test_bond_balance_xor_without_hash_policy(self):
        """Test balance-xor bond without bond_xmit_hash_policy."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "bond0",
                    "iface_type": "bond",
                    "bond_mode": "balance-xor",
                    "slaves": "eth0 eth1",
                    # Missing bond_xmit_hash_policy
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "bond_xmit_hash_policy is required for balance-xor and 802.3ad modes"
            in result["msg"]
        )

    def test_vlan_invalid_format(self):
        """Test VLAN interface with invalid naming format."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "invalid_vlan",
                    "iface_type": "vlan",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "VLAN iface must be in format" in result["msg"]

    def test_vlan_id_out_of_range(self):
        """Test VLAN interface with VLAN ID out of range."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "eth0.5000",  # VLAN ID > 4094
                    "iface_type": "vlan",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "VLAN ID must be between 1 and 4094" in result["msg"]

    def test_vlan_dot_format_with_raw_device(self):
        """Test VLAN interface with dot format but with vlan_raw_device."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "eth0.100",
                    "iface_type": "vlan",
                    "vlan_raw_device": "eth0",  # Should not be defined for dot format
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "vlan_raw_device should not be defined when iface does not start with 'vlan'"
            in result["msg"]
        )

    def test_ovsbond_missing_required_parameters(self):
        """Test OVSBond interface with missing required parameters."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "ovsbond0",
                    "iface_type": "OVSBond",
                    # Missing bond_mode, ovs_bonds, ovs_bridge
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "bond_mode is required for OVSBond type" in result["msg"]
        assert "ovs_bonds is required for OVSBond type" in result["msg"]
        assert "ovs_bridge is required for OVSBond type" in result["msg"]

    def test_ovsintport_missing_bridge(self):
        """Test OVSIntPort interface without ovs_bridge."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "ovsint0",
                    "iface_type": "OVSIntPort",
                    # Missing ovs_bridge
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "ovs_bridge is required for OVSIntPort type" in result["msg"]

    def test_invalid_ipv6_cidr_format(self):
        """Test error with invalid IPv6 CIDR format."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "eth0",
                    "iface_type": "eth",
                    "cidr6": "invalid_ipv6_cidr",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "Invalid IPv6 CIDR format" in result["msg"]

    def test_create_complex_bridge(self):
        """Test creating a complex bridge with VLAN awareness."""
        created_config = {
            "iface": "vmbr1",
            "type": "bridge",
            "bridge_ports": "eth1 eth2",
            "bridge_vlan_aware": True,
            "bridge_vids": "2 4 100-200",
            "cidr": "192.168.2.0/24",
            "gateway": "192.168.2.1",
            "mtu": 9000,
            "comments": "VLAN-aware bridge for trunking",
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            side_effect=[None, created_config],
        ):
            with patch.object(
                self.module.ProxmoxNetworkManager, "create_interface", return_value=True
            ):
                with pytest.raises(AnsibleExitJson) as exc_info:
                    with set_module_args(
                        {
                            "api_host": "host",
                            "api_user": "user",
                            "api_password": "password",
                            "node": "pve",
                            "iface": "vmbr1",
                            "iface_type": "bridge",
                            "bridge_ports": "eth1 eth2",
                            "bridge_vlan_aware": True,
                            "bridge_vids": "2 4 100-200",
                            "cidr": "192.168.2.0/24",
                            "gateway": "192.168.2.1",
                            "mtu": 9000,
                            "comments": "VLAN-aware bridge for trunking",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "vmbr1"
                assert "created" in result["msg"].lower()

    def test_create_bond_interface(self):
        """Test creating a bond interface."""
        created_config = {
            "iface": "bond0",
            "type": "bond",
            "bond_mode": "active-backup",
            "bond_primary": "eth0",
            "slaves": "eth0 eth1",
            "cidr": "192.168.1.0/24",
            "gateway": "192.168.1.1",
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            side_effect=[None, created_config],
        ):
            with patch.object(
                self.module.ProxmoxNetworkManager, "create_interface", return_value=True
            ):
                with pytest.raises(AnsibleExitJson) as exc_info:
                    with set_module_args(
                        {
                            "api_host": "host",
                            "api_user": "user",
                            "api_password": "password",
                            "node": "pve",
                            "iface": "bond0",
                            "iface_type": "bond",
                            "bond_mode": "active-backup",
                            "bond_primary": "eth0",
                            "slaves": "eth0 eth1",
                            "cidr": "192.168.1.0/24",
                            "gateway": "192.168.1.1",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "bond0"
                assert "created" in result["msg"].lower()

    def test_create_vlan_interface(self):
        """Test creating a VLAN interface."""
        created_config = {
            "iface": "eth0.100",
            "type": "vlan",
            "cidr": "192.168.100.0/24",
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            side_effect=[None, created_config],
        ):
            with patch.object(
                self.module.ProxmoxNetworkManager, "create_interface", return_value=True
            ):
                with pytest.raises(AnsibleExitJson) as exc_info:
                    with set_module_args(
                        {
                            "api_host": "host",
                            "api_user": "user",
                            "api_password": "password",
                            "node": "pve",
                            "iface": "eth0.100",
                            "iface_type": "vlan",
                            "cidr": "192.168.100.0/24",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "eth0.100"
                assert "created" in result["msg"].lower()

    def test_interface_type_change_restriction(self):
        """Test that interface type cannot be changed after creation."""
        existing_config = {
            "iface": "eth0",
            "type": "eth",
            "cidr": "192.168.1.0/24",
            "gateway": "192.168.1.1",
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            return_value=existing_config,
        ):
            with pytest.raises(AnsibleFailJson) as exc_info:
                with set_module_args(
                    {
                        "api_host": "host",
                        "api_user": "user",
                        "api_password": "password",
                        "node": "pve",
                        "iface": "eth0",
                        "iface_type": "bridge",  # Trying to change from eth to bridge
                        "cidr": "192.168.1.0/24",
                        "gateway": "192.168.1.1",
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert (
                "Cannot change interface type from 'eth' to 'bridge'" in result["msg"]
            )
            assert "Interface type cannot be modified after creation" in result["msg"]

    def test_create_ovs_bridge(self):
        """Test creating an OVS bridge interface."""
        created_config = {
            "iface": "ovsbr0",
            "type": "OVSBridge",
            "ovs_ports": "eth3 eth4",
            "ovs_options": "updelay=5000",
            "cidr": "192.168.3.0/24",
            "gateway": "192.168.3.1",
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            side_effect=[None, created_config],
        ):
            with patch.object(
                self.module.ProxmoxNetworkManager, "create_interface", return_value=True
            ):
                with pytest.raises(AnsibleExitJson) as exc_info:
                    with set_module_args(
                        {
                            "api_host": "host",
                            "api_user": "user",
                            "api_password": "password",
                            "node": "pve",
                            "iface": "ovsbr0",
                            "iface_type": "OVSBridge",
                            "ovs_ports": "eth3 eth4",
                            "ovs_options": "updelay=5000",
                            "cidr": "192.168.3.0/24",
                            "gateway": "192.168.3.1",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "ovsbr0"
                assert "created" in result["msg"].lower()

    def test_create_ovs_bond(self):
        """Test creating an OVS bond interface."""
        created_config = {
            "iface": "ovsbond0",
            "type": "OVSBond",
            "bond_mode": "active-backup",
            "ovs_bonds": "eth5 eth6",
            "ovs_bridge": "ovsbr0",
            "ovs_tag": 10,
            "ovs_options": "updelay=5000",
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            side_effect=[None, created_config],
        ):
            with patch.object(
                self.module.ProxmoxNetworkManager, "create_interface", return_value=True
            ):
                with pytest.raises(AnsibleExitJson) as exc_info:
                    with set_module_args(
                        {
                            "api_host": "host",
                            "api_user": "user",
                            "api_password": "password",
                            "node": "pve",
                            "iface": "ovsbond0",
                            "iface_type": "OVSBond",
                            "bond_mode": "active-backup",
                            "ovs_bonds": "eth5 eth6",
                            "ovs_bridge": "ovsbr0",
                            "ovs_tag": 10,
                            "ovs_options": "updelay=5000",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "ovsbond0"
                assert "created" in result["msg"].lower()

    def test_create_ovs_int_port(self):
        """Test creating an OVS internal port."""
        created_config = {
            "iface": "ovsint0",
            "type": "OVSIntPort",
            "ovs_bridge": "ovsbr0",
            "ovs_tag": 20,
            "ovs_options": "tag=20",
            "cidr": "192.168.20.0/24",
            "gateway": "192.168.20.1",
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            side_effect=[None, created_config],
        ):
            with patch.object(
                self.module.ProxmoxNetworkManager, "create_interface", return_value=True
            ):
                with pytest.raises(AnsibleExitJson) as exc_info:
                    with set_module_args(
                        {
                            "api_host": "host",
                            "api_user": "user",
                            "api_password": "password",
                            "node": "pve",
                            "iface": "ovsint0",
                            "iface_type": "OVSIntPort",
                            "ovs_bridge": "ovsbr0",
                            "ovs_tag": 20,
                            "ovs_options": "tag=20",
                            "cidr": "192.168.20.0/24",
                            "gateway": "192.168.20.1",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "ovsint0"
                assert "created" in result["msg"].lower()

    def test_create_dual_stack_interface(self):
        """Test creating a dual-stack IPv4/IPv6 interface."""
        created_config = {
            "iface": "vmbr2",
            "type": "bridge",
            "bridge_ports": "eth7",
            "cidr": "192.168.4.0/24",
            "gateway": "192.168.4.1",
            "cidr6": "2001:db8::/64",
            "gateway6": "2001:db8::1",
            "autostart": True,
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            side_effect=[None, created_config],
        ):
            with patch.object(
                self.module.ProxmoxNetworkManager, "create_interface", return_value=True
            ):
                with pytest.raises(AnsibleExitJson) as exc_info:
                    with set_module_args(
                        {
                            "api_host": "host",
                            "api_user": "user",
                            "api_password": "password",
                            "node": "pve",
                            "iface": "vmbr2",
                            "iface_type": "bridge",
                            "bridge_ports": "eth7",
                            "cidr": "192.168.4.0/24",
                            "gateway": "192.168.4.1",
                            "cidr6": "2001:db8::/64",
                            "gateway6": "2001:db8::1",
                            "autostart": True,
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "vmbr2"
                assert "created" in result["msg"].lower()

    def test_create_interface_with_comments(self):
        """Test creating an interface with comments."""
        created_config = {
            "iface": "eth0",
            "type": "eth",
            "cidr": "192.168.1.0/24",
            "gateway": "192.168.1.1",
            "comments": "Management network",
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            side_effect=[None, created_config],
        ):
            with patch.object(
                self.module.ProxmoxNetworkManager, "create_interface", return_value=True
            ):
                with pytest.raises(AnsibleExitJson) as exc_info:
                    with set_module_args(
                        {
                            "api_host": "host",
                            "api_user": "user",
                            "api_password": "password",
                            "node": "pve",
                            "iface": "eth0",
                            "iface_type": "eth",
                            "cidr": "192.168.1.0/24",
                            "gateway": "192.168.1.1",
                            "comments": "Management network",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "eth0"
                assert result["interface"]["comments"] == "Management network"
                assert "created" in result["msg"].lower()

    def test_ovs_tag_out_of_range(self):
        """Test OVS tag with value out of range (1-4094)."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "ovsint0",
                    "iface_type": "OVSIntPort",
                    "ovs_bridge": "ovsbr0",
                    "ovs_tag": 5000,  # Out of range
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "ovs_tag must be between 1 and 4094" in result["msg"]

    def test_ovs_tag_invalid_type(self):
        """Test OVS tag with invalid type."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "ovsint0",
                    "iface_type": "OVSIntPort",
                    "ovs_bridge": "ovsbr0",
                    "ovs_tag": "invalid",  # Should be integer
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        # The actual error message from Ansible's type conversion
        assert "cannot be converted to an int" in result["msg"]

    def test_vlan_interface_vlanxy_format(self):
        """Test creating VLAN interface with vlanXY format."""
        created_config = {
            "iface": "vlan100",
            "type": "vlan",
            "vlan_raw_device": "eth0",
            "cidr": "192.168.100.0/24",
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            side_effect=[None, created_config],
        ):
            with patch.object(
                self.module.ProxmoxNetworkManager, "create_interface", return_value=True
            ):
                with pytest.raises(AnsibleExitJson) as exc_info:
                    with set_module_args(
                        {
                            "api_host": "host",
                            "api_user": "user",
                            "api_password": "password",
                            "node": "pve",
                            "iface": "vlan100",
                            "iface_type": "vlan",
                            "vlan_raw_device": "eth0",
                            "cidr": "192.168.100.0/24",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "vlan100"
                assert "created" in result["msg"].lower()

    def test_apply_with_no_pending_changes(self):
        """Test applying when there are no pending changes."""
        with patch.object(
            self.module.ProxmoxNetworkManager,
            "check_network_changes",
            return_value=None,
        ):
            with pytest.raises(AnsibleExitJson) as exc_info:
                with set_module_args(
                    {
                        "api_host": "host",
                        "api_user": "user",
                        "api_password": "password",
                        "node": "pve",
                        "state": "apply",
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert result["changed"] is False
            assert "No staged network configuration changes to apply" in result["msg"]

    def test_revert_with_no_pending_changes(self):
        """Test reverting when there are no pending changes."""
        # The module always returns changed=True in check mode for revert
        with patch.object(
            self.module.ProxmoxNetworkManager, "revert_network", return_value=False
        ):
            with pytest.raises(AnsibleExitJson) as exc_info:
                with set_module_args(
                    {
                        "api_host": "host",
                        "api_user": "user",
                        "api_password": "password",
                        "node": "pve",
                        "state": "revert",
                        "_ansible_check_mode": True,
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert result["changed"] is True
            assert "may be reverted" in result["msg"]

    def test_eth_with_bridge_parameters(self):
        """Test eth interface with bridge-specific parameters."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "eth0",
                    "iface_type": "eth",
                    "cidr": "192.168.1.0/24",
                    "bridge_ports": "eth1",  # Invalid for eth type
                    "bridge_vlan_aware": True,  # Invalid for eth type
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "Parameters bridge_ports, bridge_vlan_aware are not valid for interface type 'eth'"
            in result["msg"]
        )

    def test_bridge_with_bond_parameters(self):
        """Test bridge interface with bond-specific parameters."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vmbr0",
                    "iface_type": "bridge",
                    "cidr": "192.168.1.0/24",
                    "bond_mode": "active-backup",  # Invalid for bridge type
                    "slaves": "eth0 eth1",  # Invalid for bridge type
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "Parameters bond_mode, slaves are not valid for interface type 'bridge'"
            in result["msg"]
        )

    def test_bond_with_vlan_parameters(self):
        """Test bond interface with VLAN-specific parameters."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "bond0",
                    "iface_type": "bond",
                    "bond_mode": "active-backup",
                    "slaves": "eth0 eth1",
                    "vlan_raw_device": "eth0",  # Invalid for bond type
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "Parameters vlan_raw_device are not valid for interface type 'bond'"
            in result["msg"]
        )

    def test_vlan_with_bridge_parameters(self):
        """Test VLAN interface with bridge-specific parameters."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "eth0.100",
                    "iface_type": "vlan",
                    "cidr": "192.168.100.0/24",
                    "bridge_ports": "eth1",  # Invalid for vlan type
                    "bridge_vlan_aware": True,  # Invalid for vlan type
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "Parameters bridge_ports, bridge_vlan_aware are not valid for interface type 'vlan'"
            in result["msg"]
        )

    def test_ovsbridge_with_bond_parameters(self):
        """Test OVS bridge with bond-specific parameters."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "ovsbr0",
                    "iface_type": "OVSBridge",
                    "ovs_ports": "eth3 eth4",
                    "bond_mode": "active-backup",  # Invalid for OVS bridge type
                    "slaves": "eth0 eth1",  # Invalid for OVS bridge type
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "Parameters bond_mode, slaves are not valid for interface type 'OVSBridge'"
            in result["msg"]
        )

    def test_ovsbond_with_bridge_parameters(self):
        """Test OVS bond with bridge-specific parameters."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "ovsbond0",
                    "iface_type": "OVSBond",
                    "bond_mode": "active-backup",
                    "ovs_bonds": "eth5 eth6",
                    "ovs_bridge": "ovsbr0",
                    "bridge_ports": "eth1",  # Invalid for OVS bond type
                    "bridge_vlan_aware": True,  # Invalid for OVS bond type
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "Parameters bridge_ports, bridge_vlan_aware are not valid for interface type 'OVSBond'"
            in result["msg"]
        )

    def test_ovsintport_with_bond_parameters(self):
        """Test OVS internal port with bond-specific parameters."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "ovsint0",
                    "iface_type": "OVSIntPort",
                    "ovs_bridge": "ovsbr0",
                    "bond_mode": "active-backup",  # Invalid for OVS int port type
                    "slaves": "eth0 eth1",  # Invalid for OVS int port type
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "Parameters bond_mode, slaves are not valid for interface type 'OVSIntPort'"
            in result["msg"]
        )

    def test_multiple_incompatible_parameters(self):
        """Test multiple incompatible parameters for an interface type."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "eth0",
                    "iface_type": "eth",
                    "cidr": "192.168.1.0/24",
                    "bridge_ports": "eth1",  # Invalid for eth
                    "bond_mode": "active-backup",  # Invalid for eth
                    "vlan_raw_device": "eth0",  # Invalid for eth
                    "ovs_bridge": "ovsbr0",  # Invalid for eth
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "Parameters bridge_ports, bond_mode, vlan_raw_device, ovs_bridge are not valid for interface type 'eth'"
            in result["msg"]
        )
