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


class TestProxmoxNodeNetwork(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxNodeNetwork, self).setUp()
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
        super(TestProxmoxNodeNetwork, self).tearDown()

    def test_invalid_node(self):
        """Test invalid node."""
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

    def test_invalid_state(self):
        """Test invalid state."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "state": "invalid_state",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "value of state must be one of: present, absent, apply, revert"
            in result["msg"]
        )

    def test_create_interface_all_types_minimum_params(self):
        """Test creating interface for all if_types with minimum params."""
        interface_types = [
            "bridge",
            "bond",
            "vlan",
            "OVSBridge",
            "OVSBond",
            "OVSIntPort",
        ]

        for iface_type in interface_types:
            # Use proper interface names based on type
            if iface_type == "bond":
                iface_name = "bond0"
            elif iface_type == "OVSBond":
                iface_name = "bond1"
            elif iface_type == "OVSIntPort":
                iface_name = "ovsint0"
            elif iface_type == "OVSBridge":
                iface_name = "ovsbr0"
            elif iface_type == "vlan":
                iface_name = "vlan100"
            else:
                iface_name = f"test_{iface_type}"

            created_config = {"iface": iface_name, "iface_type": iface_type}

            # Add required parameters based on interface type
            module_args = {
                "api_host": "host",
                "api_user": "user",
                "api_password": "password",
                "node": "pve",
                "iface": iface_name,
                "iface_type": iface_type,
            }

            if iface_type == "bond":
                module_args.update(
                    {
                        "bond_mode": "balance-rr",
                        "slaves": "eth0 eth1",
                    }
                )
            elif iface_type == "vlan":
                module_args.update(
                    {
                        "vlan_raw_device": "eth0",
                    }
                )
            elif iface_type == "OVSBond":
                module_args.update(
                    {
                        "bond_mode": "active-backup",
                        "ovs_bonds": "eth0 eth1",
                        "ovs_bridge": "ovsbr0",
                    }
                )
            elif iface_type == "OVSIntPort":
                module_args.update(
                    {
                        "ovs_bridge": "ovsbr0",
                    }
                )

            with patch.object(
                self.module.ProxmoxNetworkManager,
                "get_interface_config",
                side_effect=[None, created_config],
            ):
                with patch.object(
                    self.module.ProxmoxNetworkManager,
                    "create_interface",
                    return_value=True,
                ):
                    with pytest.raises(AnsibleExitJson) as exc_info:
                        with set_module_args(module_args):
                            self.module.main()

                    result = exc_info.value.args[0]
                    assert result["changed"] is True
                    assert result["interface"]["iface"] == iface_name
                    assert "created" in result["msg"].lower()

    def test_create_interface_wrong_if_type(self):
        """Test creating interface with wrong if_type."""
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

    def test_create_eth_interface_non_existing(self):
        """Test creating eth interface with non existing interface name."""
        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            return_value=None,  # Interface doesn't exist
        ):
            with pytest.raises(AnsibleFailJson) as exc_info:
                with set_module_args(
                    {
                        "api_host": "host",
                        "api_user": "user",
                        "api_password": "password",
                        "node": "pve",
                        "iface": "nonexistent_eth",
                        "iface_type": "eth",
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert (
                "Cannot create interface 'nonexistent_eth' of type 'eth'"
                in result["msg"]
            )

    def test_create_eth_interface_existing(self):
        """Test creating eth interface with existing interface name."""
        existing_config = {
            "iface": "eth0",
            "type": "eth",
            "active": 1,
            "autostart": 1,
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            return_value=existing_config,
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
                            "iface": "eth0",
                            "iface_type": "eth",
                            "cidr": "192.168.1.0/24",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "eth0"
                assert "updated" in result["msg"].lower()

    def test_delete_eth_interface(self):
        """Test deleting a eth interface."""
        existing_config = {
            "iface": "eth0",
            "type": "eth",
            "active": 1,
            "autostart": 1,
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            return_value=existing_config,
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
                            "iface": "eth0",
                            "state": "absent",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert "deleted" in result["msg"].lower()

    def test_create_bridge_all_params_and_delete_one_by_one(self):
        """Test creating bridge interface with all possible params and deleting them one by one."""
        # First create with all parameters
        all_params_config = {
            "iface": "vmbr0",
            "iface_type": "bridge",
            "bridge_ports": "eth0 eth1",
            "cidr": "192.168.1.0/24",
            "gateway": "192.168.1.1",
            "cidr6": "2001:db8::/64",
            "gateway6": "2001:db8::1",
            "comments": "Test bridge",
            "mtu": 9000,
            "bridge_vids": "100 200",
            "bridge_vlan_aware": True,
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            side_effect=[None, all_params_config],
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
                            "bridge_ports": "eth0 eth1",
                            "cidr": "192.168.1.0/24",
                            "gateway": "192.168.1.1",
                            "cidr6": "2001:db8::/64",
                            "gateway6": "2001:db8::1",
                            "comments": "Test bridge",
                            "mtu": 9000,
                            "bridge_vids": "100 200",
                            "bridge_vlan_aware": True,
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "vmbr0"

        # Now test deleting parameters one by one
        params_to_delete = [
            ("cidr", ""),
            ("gateway", ""),
            ("cidr6", ""),
            ("gateway6", ""),
            ("comments", ""),
            ("mtu", -1),
            ("bridge_ports", ""),
            ("bridge_vids", ""),
        ]

        for param_name, delete_value in params_to_delete:
            # Create config without the parameter being deleted
            updated_config = all_params_config.copy()
            if param_name in ["cidr", "gateway", "cidr6", "gateway6", "comments"]:
                updated_config.pop(param_name, None)
            elif param_name == "mtu":
                updated_config.pop(param_name, None)
            elif param_name == "bridge_ports":
                updated_config[param_name] = ""
            elif param_name == "bridge_vids":
                updated_config[param_name] = "2-4094"  # Default when deleted

            with patch.object(
                self.module.ProxmoxNetworkManager,
                "get_interface_config",
                side_effect=[all_params_config, updated_config],
            ):
                with patch.object(
                    self.module.ProxmoxNetworkManager,
                    "update_interface",
                    return_value=True,
                ):
                    with pytest.raises(AnsibleExitJson) as exc_info:
                        module_args = {
                            "api_host": "host",
                            "api_user": "user",
                            "api_password": "password",
                            "node": "pve",
                            "iface": "vmbr0",
                            "iface_type": "bridge",
                            "bridge_ports": "eth0 eth1",
                            "bridge_vlan_aware": True,
                        }
                        module_args[param_name] = delete_value

                        with set_module_args(module_args):
                            self.module.main()

                    result = exc_info.value.args[0]
                    assert result["changed"] is True
                    assert result["interface"]["iface"] == "vmbr0"
                    assert "updated" in result["msg"].lower()

    def test_create_bridge_all_params_and_update_one_by_one(self):
        """Test creating bridge interface with all possible params and updating them one by one."""
        # First create with all parameters
        all_params_config = {
            "iface": "vmbr0",
            "iface_type": "bridge",
            "bridge_ports": "eth0 eth1",
            "cidr": "192.168.1.0/24",
            "gateway": "192.168.1.1",
            "cidr6": "2001:db8::/64",
            "gateway6": "2001:db8::1",
            "comments": "Test bridge",
            "mtu": 9000,
            "bridge_vids": "100 200",
            "bridge_vlan_aware": True,
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            side_effect=[None, all_params_config],
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
                            "bridge_ports": "eth0 eth1",
                            "cidr": "192.168.1.0/24",
                            "gateway": "192.168.1.1",
                            "cidr6": "2001:db8::/64",
                            "gateway6": "2001:db8::1",
                            "comments": "Test bridge",
                            "mtu": 9000,
                            "bridge_vids": "100 200",
                            "bridge_vlan_aware": True,
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "vmbr0"

        # Now test updating parameters one by one
        params_to_update = [
            ("cidr", "192.168.2.0/24"),
            ("gateway", "192.168.2.1"),
            ("cidr6", "2001:db9::/64"),
            ("gateway6", "2001:db9::1"),
            ("comments", "Updated bridge"),
            ("mtu", 1500),
            ("bridge_ports", "eth2 eth3"),
            ("bridge_vids", "300 400"),
        ]

        for param_name, new_value in params_to_update:
            # Create config with the updated parameter
            updated_config = all_params_config.copy()
            updated_config[param_name] = new_value

            with patch.object(
                self.module.ProxmoxNetworkManager,
                "get_interface_config",
                side_effect=[all_params_config, updated_config],
            ):
                with patch.object(
                    self.module.ProxmoxNetworkManager,
                    "update_interface",
                    return_value=True,
                ):
                    with pytest.raises(AnsibleExitJson) as exc_info:
                        module_args = {
                            "api_host": "host",
                            "api_user": "user",
                            "api_password": "password",
                            "node": "pve",
                            "iface": "vmbr0",
                            "iface_type": "bridge",
                            "bridge_ports": "eth0 eth1",
                            "bridge_vlan_aware": True,
                        }

                        # For gateway updates, we need to include cidr
                        if param_name == "gateway":
                            module_args["cidr"] = "192.168.1.0/24"
                        elif param_name == "gateway6":
                            module_args["cidr6"] = "2001:db8::/64"

                        module_args[param_name] = new_value

                        with set_module_args(module_args):
                            self.module.main()

                    result = exc_info.value.args[0]
                    assert result["changed"] is True
                    assert result["interface"]["iface"] == "vmbr0"
                    assert "updated" in result["msg"].lower()

    def test_gateway_without_cidr_should_fail(self):
        """gateway requires cidr to be set."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vmbr0",
                    "iface_type": "bridge",
                    # Intentionally omit cidr
                    "gateway": "192.168.1.1",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "gateway cannot be set when cidr is not defined" in result["msg"]

    def test_gateway6_without_cidr6_should_fail(self):
        """gateway6 requires cidr6 to be set."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vmbr0",
                    "iface_type": "bridge",
                    # Intentionally omit cidr6
                    "gateway6": "2001:db8::1",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "gateway6 cannot be set when cidr6 is not defined" in result["msg"]

    def test_invalid_gateway_format_should_fail(self):
        """gateway must be a valid IPv4 address when provided."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vmbr0",
                    "iface_type": "bridge",
                    "cidr": "192.168.1.10/24",
                    "gateway": "999.999.999.999",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "gateway must be a valid IPv4 address" in result["msg"]

        # Also fail if IPv6 is passed to IPv4 gateway
        with pytest.raises(AnsibleFailJson) as exc_info2:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vmbr0",
                    "iface_type": "bridge",
                    "cidr": "192.168.1.10/24",
                    "gateway": "2001:db8::1",
                }
            ):
                self.module.main()

        result2 = exc_info2.value.args[0]
        assert "gateway must be a valid IPv4 address" in result2["msg"]

    def test_invalid_gateway6_format_should_fail(self):
        """gateway6 must be a valid IPv6 address when provided."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vmbr0",
                    "iface_type": "bridge",
                    "cidr6": "2001:db8::10/64",
                    "gateway6": "not_an_ip",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "gateway6 must be a valid IPv6 address" in result["msg"]

        # Also fail if IPv4 is passed to IPv6 gateway6
        with pytest.raises(AnsibleFailJson) as exc_info2:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vmbr0",
                    "iface_type": "bridge",
                    "cidr6": "2001:db8::10/64",
                    "gateway6": "192.168.1.1",
                }
            ):
                self.module.main()

        result2 = exc_info2.value.args[0]
        assert "gateway6 must be a valid IPv6 address" in result2["msg"]

    def test_create_bond_invalid_name(self):
        """Test creating bond with invalid name."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "invalid_bond",
                    "iface_type": "bond",
                    "bond_mode": "balance-rr",
                    "slaves": "eth0 eth1",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "Interface name 'invalid_bond' for type 'bond' must follow format 'bondX'"
            in result["msg"]
        )

    def test_create_bond_lacp_balance_slb_mode(self):
        """Test creating bond with 'lacp-balance-slb' mode which is only valid for ovsbond."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "bond0",
                    "iface_type": "bond",
                    "bond_mode": "lacp-balance-slb",
                    "slaves": "eth0 eth1",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "Invalid bond_mode for bond type. Must be one of: balance-rr, active-backup, balance-xor, broadcast, 802.3ad, balance-tlb, balance-alb"
            in result["msg"]
        )

    def test_create_bond_active_backup_without_primary(self):
        """Test creating bond with 'active-backup' mode and don't mention bond_primary."""
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
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "bond_primary is required for active-backup mode" in result["msg"]

    def test_create_bond_active_backup_primary_not_in_slaves(self):
        """Test creating bond with 'active-backup' mode and mention bond_primary but don't include it in slaves."""
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

    def test_create_bond_active_backup_primary_in_slaves(self):
        """Test creating bond with 'active-backup' mode and mention bond_primary and include it in slaves."""
        created_config = {
            "iface": "bond0",
            "iface_type": "bond",
            "bond_mode": "active-backup",
            "bond_primary": "eth0",
            "slaves": "eth0 eth1",
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
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "bond0"
                assert "created" in result["msg"].lower()

    def test_create_bond_balance_xor_without_hash_policy(self):
        """Test creating bond with 'balance-xor' mode and don't mention bond_xmit_hash_policy."""
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
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "bond_xmit_hash_policy is required for balance-xor and 802.3ad modes"
            in result["msg"]
        )

    def test_create_bond_balance_xor_invalid_hash_policy(self):
        """Test creating bond with 'balance-xor' mode and mention invalid bond_xmit_hash_policy."""
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
                    "bond_xmit_hash_policy": "invalid_policy",
                    "slaves": "eth0 eth1",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "value of bond_xmit_hash_policy must be one of: layer2, layer2+3, layer3+4"
            in result["msg"]
        )

    def test_create_bond_balance_xor_valid_hash_policy(self):
        """Test creating bond with 'balance-xor' mode and mention valid bond_xmit_hash_policy."""
        created_config = {
            "iface": "bond0",
            "iface_type": "bond",
            "bond_mode": "balance-xor",
            "bond_xmit_hash_policy": "layer2",
            "slaves": "eth0 eth1",
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
                            "bond_mode": "balance-xor",
                            "bond_xmit_hash_policy": "layer2",
                            "slaves": "eth0 eth1",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "bond0"
                assert "created" in result["msg"].lower()

    def test_create_bond_balance_rr_with_primary(self):
        """Test creating bond with 'balance-rr' mode and mention bond_primary."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "bond0",
                    "iface_type": "bond",
                    "bond_mode": "balance-rr",
                    "bond_primary": "eth0",
                    "slaves": "eth0 eth1",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "bond_primary should not be defined if bond_mode is not active-backup"
            in result["msg"]
        )

    def test_create_bond_balance_rr_mode(self):
        """Test creating bond with 'balance-rr' mode."""
        created_config = {
            "iface": "bond0",
            "iface_type": "bond",
            "bond_mode": "balance-rr",
            "slaves": "eth0 eth1",
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
                            "bond_mode": "balance-rr",
                            "slaves": "eth0 eth1",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "bond0"
                assert "created" in result["msg"].lower()

    def test_create_bond_balance_rr_without_slaves(self):
        """Test creating bond with 'balance-rr' mode without slaves."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "bond0",
                    "iface_type": "bond",
                    "bond_mode": "balance-rr",
                    # Missing slaves
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "slaves is required for bond type" in result["msg"]

    def test_create_vlan_interface_vlan10_name(self):
        """Test creating vlan interface with vlan.10 name."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vlan.10",
                    "iface_type": "vlan",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "VLAN interface name 'vlan.10' must follow format 'vlanXY'" in result["msg"]
        )

    def test_create_vlan_interface_eth10_name(self):
        """Test creating vlan interface with eth10 name."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "eth10",
                    "iface_type": "vlan",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "VLAN interface name 'eth10' must follow format 'vlanXY'" in result["msg"]
        )

    def test_create_vlan_interface_vlan10_name_no_raw_device(self):
        """Test creating vlan interface with vlan10 name and don't mention vlan_raw_device."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vlan10",
                    "iface_type": "vlan",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "vlan_raw_device is required for VLAN interface 'vlan10' in vlanXY format"
            in result["msg"]
        )

    def test_create_vlan_interface_vlan10_name_with_raw_device(self):
        """Test creating vlan interface with vlan10 name and mention vlan_raw_device."""
        created_config = {
            "iface": "vlan10",
            "iface_type": "vlan",
            "vlan_raw_device": "eth0",
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
                            "iface": "vlan10",
                            "iface_type": "vlan",
                            "vlan_raw_device": "eth0",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "vlan10"
                assert "created" in result["msg"].lower()

    def test_create_vlan_interface_eth0_10_name_no_raw_device(self):
        """Test creating vlan interface with eth0.10 name and don't mention vlan_raw_device."""
        created_config = {
            "iface": "eth0.10",
            "iface_type": "vlan",
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
                            "iface": "eth0.10",
                            "iface_type": "vlan",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "eth0.10"
                assert "created" in result["msg"].lower()

    def test_create_vlan_interface_eth0_10_name_with_raw_device(self):
        """Test creating vlan interface with eth0.10 name and mention vlan_raw_device."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "eth0.10",
                    "iface_type": "vlan",
                    "vlan_raw_device": "eth0",  # Should not be specified for dot format
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "vlan_raw_device should not be specified for VLAN interface 'eth0.10' in iface_name.vlan_id format"
            in result["msg"]
        )

    def test_create_ovsbond_without_bridge(self):
        """Test creating ovsbond without bridge."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "bond0",
                    "iface_type": "OVSBond",
                    "bond_mode": "active-backup",
                    "ovs_bonds": "eth0 eth1",
                    # Missing ovs_bridge
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "ovs_bridge is required for OVSBond type" in result["msg"]

    def test_create_ovsbond_without_slave(self):
        """Test creating ovsbond without slave."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "bond0",
                    "iface_type": "OVSBond",
                    "bond_mode": "active-backup",
                    "ovs_bridge": "ovsbr0",
                    # Missing ovs_bonds
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "ovs_bonds is required for OVSBond type" in result["msg"]

    def test_create_ovsbond_with_balance_rr_type(self):
        """Test creating ovsbond with balance-rr type."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "bond0",
                    "iface_type": "OVSBond",
                    "bond_mode": "balance-rr",  # Invalid for OVSBond
                    "ovs_bonds": "eth0 eth1",
                    "ovs_bridge": "ovsbr0",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "Invalid bond_mode for OVSBond. Must be one of: active-backup, balance-slb, lacp-balance-slb, lacp-balance-tcp"
            in result["msg"]
        )

    def test_create_ovsbond_with_invalid_name(self):
        """Test creating ovsbond with invalid name."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "invalid_ovsbond",
                    "iface_type": "OVSBond",
                    "bond_mode": "active-backup",
                    "ovs_bonds": "eth0 eth1",
                    "ovs_bridge": "ovsbr0",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "Interface name 'invalid_ovsbond' for type 'OVSBond' must follow format 'bondX'"
            in result["msg"]
        )

    def test_create_ovsbond_with_autostart(self):
        """Test creating ovsbond with AutoStart."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "bond0",
                    "iface_type": "OVSBond",
                    "bond_mode": "active-backup",
                    "ovs_bonds": "eth0 eth1",
                    "ovs_bridge": "ovsbr0",
                    "autostart": True,  # This should fail - autostart not supported for OVSBond
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert (
            "Parameters autostart are not valid for interface type 'OVSBond'"
            in result["msg"]
        )

    def test_create_valid_ovsbond(self):
        """Test creating a valid ovsbond."""
        created_config = {
            "iface": "bond0",
            "iface_type": "OVSBond",
            "bond_mode": "active-backup",
            "ovs_bonds": "eth0 eth1",
            "ovs_bridge": "ovsbr0",
            "ovs_tag": 100,
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
                            "iface": "bond0",
                            "iface_type": "OVSBond",
                            "bond_mode": "active-backup",
                            "ovs_bonds": "eth0 eth1",
                            "ovs_bridge": "ovsbr0",
                            "ovs_tag": 100,
                            "ovs_options": "updelay=5000",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "bond0"
                assert "created" in result["msg"].lower()

    def test_update_valid_ovsbond_modes_and_slaves(self):
        """Test updating a valid ovsbond modes and slaves."""
        existing_config = {
            "iface": "bond0",
            "iface_type": "OVSBond",
            "bond_mode": "active-backup",
            "ovs_bonds": "eth0 eth1",
            "ovs_bridge": "ovsbr0",
        }

        updated_config = {
            "iface": "bond0",
            "iface_type": "OVSBond",
            "bond_mode": "balance-slb",
            "ovs_bonds": "eth2 eth3",
            "ovs_bridge": "ovsbr0",
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            side_effect=[existing_config, updated_config],
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
                            "iface": "bond0",
                            "iface_type": "OVSBond",
                            "bond_mode": "balance-slb",
                            "ovs_bonds": "eth2 eth3",
                            "ovs_bridge": "ovsbr0",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert result["interface"]["iface"] == "bond0"
                assert "updated" in result["msg"].lower()

    def test_delete_valid_ovsbond_and_options_and_comments(self):
        """Test deleting a valid ovsbond and options and comments."""
        existing_config = {
            "iface": "bond0",
            "iface_type": "OVSBond",
            "bond_mode": "active-backup",
            "ovs_bonds": "eth0 eth1",
            "ovs_bridge": "ovsbr0",
            "ovs_tag": 100,
            "ovs_options": "updelay=5000",
            "comments": "Test OVS bond",
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            return_value=existing_config,
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
                            "iface": "bond0",
                            "state": "absent",
                        }
                    ):
                        self.module.main()

                result = exc_info.value.args[0]
                assert result["changed"] is True
                assert "deleted" in result["msg"].lower()

    def test_apply_network_changes(self):
        """Test applying staged network changes."""
        mock_pending_changes = """--- /etc/network/interfaces
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

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_network_changes",
            return_value=mock_pending_changes,
        ):
            with patch.object(
                self.module.ProxmoxNetworkManager, "apply_network", return_value=True
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

    def test_apply_network_no_pending_changes(self):
        """Test applying when there are no pending changes."""
        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_network_changes",
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

    def test_revert_network_no_pending_changes(self):
        """Test reverting when there are no pending changes."""
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
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert result["changed"] is True
            assert "reverted" in result["msg"].lower()

    def test_apply_network_check_mode(self):
        """Test applying network changes in check mode."""
        mock_pending_changes = """--- /etc/network/interfaces
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

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_network_changes",
            return_value=mock_pending_changes,
        ):
            with pytest.raises(AnsibleExitJson) as exc_info:
                with set_module_args(
                    {
                        "api_host": "host",
                        "api_user": "user",
                        "api_password": "password",
                        "node": "pve",
                        "state": "apply",
                        "_ansible_check_mode": True,
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert result["changed"] is True
            assert "may be applied" in result["msg"].lower()

    def test_revert_network_check_mode(self):
        """Test reverting network changes in check mode."""
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
        assert "may be reverted" in result["msg"].lower()

    def test_create_bridge_check_mode(self):
        """Test creating a bridge interface in check mode."""
        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            return_value=None,  # Interface doesn't exist
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

    def test_update_bridge_check_mode(self):
        """Test updating a bridge interface in check mode."""
        existing_config = {
            "iface": "vmbr0",
            "iface_type": "bridge",
            "bridge_ports": "eth0",
            "cidr": "192.168.1.1/24",
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            return_value=existing_config,
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

    def test_delete_interface_check_mode(self):
        """Test deleting an interface in check mode."""
        existing_config = {
            "iface": "vmbr0",
            "iface_type": "bridge",
            "bridge_ports": "eth0",
        }

        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            return_value=existing_config,
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
                        "_ansible_check_mode": True,
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert result["changed"] is True
            assert "would be deleted" in result["msg"].lower()

    def test_create_bond_check_mode(self):
        """Test creating a bond interface in check mode."""
        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            return_value=None,  # Interface doesn't exist
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
                        "_ansible_check_mode": True,
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert result["changed"] is True
            assert result["interface"]["iface"] == "bond0"
            assert "would be created" in result["msg"].lower()

    def test_create_vlan_check_mode(self):
        """Test creating a VLAN interface in check mode."""
        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            return_value=None,  # Interface doesn't exist
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
                        "_ansible_check_mode": True,
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert result["changed"] is True
            assert result["interface"]["iface"] == "vlan100"
            assert "would be created" in result["msg"].lower()

    def test_create_ovsbond_check_mode(self):
        """Test creating an OVS bond interface in check mode."""
        with patch.object(
            self.module.ProxmoxNetworkManager,
            "get_interface_config",
            return_value=None,  # Interface doesn't exist
        ):
            with pytest.raises(AnsibleExitJson) as exc_info:
                with set_module_args(
                    {
                        "api_host": "host",
                        "api_user": "user",
                        "api_password": "password",
                        "node": "pve",
                        "iface": "bond0",
                        "iface_type": "OVSBond",
                        "bond_mode": "active-backup",
                        "ovs_bonds": "eth0 eth1",
                        "ovs_bridge": "ovsbr0",
                        "_ansible_check_mode": True,
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert result["changed"] is True
            assert result["interface"]["iface"] == "bond0"
            assert "would be created" in result["msg"].lower()

    def test_get_all_interfaces_direct_call(self):
        """Test the get_all_interfaces method directly."""
        # Create a mock module for the manager
        mock_module = type(
            "MockModule",
            (),
            {
                "fail_json": lambda self, **kwargs: None,
                "params": {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                },
            },
        )()

        manager = self.module.ProxmoxNetworkManager(mock_module)

        with patch.object(
            manager.proxmox_api.nodes,
            "return_value.network.return_value.get",
            return_value=EXISTING_NETWORK_OUTPUT,
        ):
            result = manager.get_all_interfaces()
            assert result is not None
            assert len(result) > 0
            # Verify conversion from API format to Ansible format
            for interface in result:
                assert "iface" in interface
                assert (
                    "iface_type" in interface
                )  # API 'type' becomes 'iface_type' in Ansible format

    def test_validate_params_direct_call(self):
        """Test the validate_params method directly."""
        # Create a mock module for the manager
        mock_module = type(
            "MockModule",
            (),
            {
                "fail_json": lambda self, **kwargs: None,
                "params": {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vmbr1",
                    "iface_type": "bridge",
                    "bridge_ports": "eth1",
                },
            },
        )()

        manager = self.module.ProxmoxNetworkManager(mock_module)
        result = manager.validate_params()
        assert isinstance(result, list)

    def test_validate_interface_name_direct_call(self):
        """Test the validate_interface_name method directly."""
        # Create a mock module for the manager
        mock_module = type(
            "MockModule",
            (),
            {
                "fail_json": lambda self, **kwargs: None,
                "params": {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vmbr1",
                    "iface_type": "bridge",
                },
            },
        )()

        manager = self.module.ProxmoxNetworkManager(mock_module)
        result = manager.validate_interface_name()
        assert isinstance(result, list)

    def test_validate_parameter_combinations_direct_call(self):
        """Test the validate_parameter_combinations method directly."""
        # Create a mock module for the manager
        mock_module = type(
            "MockModule",
            (),
            {
                "fail_json": lambda self, **kwargs: None,
                "params": {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vmbr1",
                    "iface_type": "bridge",
                    "bridge_ports": "eth1",
                },
            },
        )()

        manager = self.module.ProxmoxNetworkManager(mock_module)
        result = manager.validate_parameter_combinations()
        assert isinstance(result, list)

    def test_build_interface_data_direct_call(self):
        """Test the _build_interface_data method directly."""
        # Create a mock module for the manager
        mock_module = type(
            "MockModule",
            (),
            {
                "fail_json": lambda self, **kwargs: None,
                "params": {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vmbr1",
                    "iface_type": "bridge",
                    "bridge_ports": "eth1",
                    "cidr": "192.168.1.0/24",
                },
            },
        )()

        manager = self.module.ProxmoxNetworkManager(mock_module)
        result = manager._build_interface_data()
        assert isinstance(result, dict)

    def test_has_differences_direct_call(self):
        """Test the _has_differences method directly."""
        # Create a mock module for the manager
        mock_module = type(
            "MockModule",
            (),
            {
                "fail_json": lambda self, **kwargs: None,
                "params": {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vmbr0",
                    "iface_type": "bridge",
                    "bridge_ports": "eth0 eth1",
                },
            },
        )()

        manager = self.module.ProxmoxNetworkManager(mock_module)
        current_config = {
            "iface": "vmbr0",
            "iface_type": "bridge",
            "bridge_ports": "eth0",
        }
        result = manager._has_differences(current_config)
        assert isinstance(result, bool)

    def test_get_network_changes_direct_call(self):
        """Test the get_network_changes method directly."""
        # Create a mock module for the manager
        mock_module = type(
            "MockModule",
            (),
            {
                "fail_json": lambda self, **kwargs: None,
                "params": {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                },
            },
        )()

        manager = self.module.ProxmoxNetworkManager(mock_module)

        with patch.object(
            manager.proxmox_api.nodes,
            "return_value.network.return_value.get",
            return_value="mock diff output",
        ):
            result = manager.get_network_changes()
            assert result is not None

    def test_validate_bridge_params_direct_call(self):
        """Test the validate_bridge_params method directly."""
        # Create a mock module for the manager
        mock_module = type(
            "MockModule",
            (),
            {
                "fail_json": lambda self, **kwargs: None,
                "params": {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vmbr1",
                    "iface_type": "bridge",
                    "bridge_ports": "eth1",
                    "bridge_vlan_aware": True,
                },
            },
        )()

        manager = self.module.ProxmoxNetworkManager(mock_module)
        result = manager.validate_bridge_params()
        assert isinstance(result, list)

    def test_validate_bond_params_direct_call(self):
        """Test the validate_bond_params method directly."""
        # Create a mock module for the manager
        mock_module = type(
            "MockModule",
            (),
            {
                "fail_json": lambda self, **kwargs: None,
                "params": {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "bond0",
                    "iface_type": "bond",
                    "bond_mode": "active-backup",
                    "bond_primary": "eth0",
                    "slaves": "eth0 eth1",
                },
            },
        )()

        manager = self.module.ProxmoxNetworkManager(mock_module)
        result = manager.validate_bond_params()
        assert isinstance(result, list)

    def test_validate_vlan_params_direct_call(self):
        """Test the validate_vlan_params method directly."""
        # Create a mock module for the manager
        mock_module = type(
            "MockModule",
            (),
            {
                "fail_json": lambda self, **kwargs: None,
                "params": {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vlan100",
                    "iface_type": "vlan",
                    "vlan_raw_device": "eth0",
                },
            },
        )()

        manager = self.module.ProxmoxNetworkManager(mock_module)
        result = manager.validate_vlan_params()
        assert isinstance(result, list)

    def test_validate_ovs_bond_params_direct_call(self):
        """Test the validate_ovs_bond_params method directly."""
        # Create a mock module for the manager
        mock_module = type(
            "MockModule",
            (),
            {
                "fail_json": lambda self, **kwargs: None,
                "params": {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "bond0",
                    "iface_type": "OVSBond",
                    "bond_mode": "active-backup",
                    "ovs_bonds": "eth0 eth1",
                    "ovs_bridge": "ovsbr0",
                },
            },
        )()

        manager = self.module.ProxmoxNetworkManager(mock_module)
        result = manager.validate_ovs_bond_params()
        assert isinstance(result, list)
