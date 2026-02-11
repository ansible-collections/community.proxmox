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

from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    ModuleTestCase,
    set_module_args,
)

import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
from ansible_collections.community.proxmox.plugins.modules import (
    proxmox_node_network_info,
)

# Mock API response from Proxmox node network endpoint
RAW_NETWORK_OUTPUT = [
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
    {
        "iface": "bond0",
        "type": "bond",
        "active": 0,
        "autostart": 1,
        "mtu": 1500,
        "method": "manual",
        "families": ["inet"],
        "slaves": "eth1 eth2",
        "bond_mode": "active-backup",
    },
]

# Expected output after boolean conversion (0/1 -> True/False)
EXPECTED_NETWORK_OUTPUT = [
    {
        "iface": "eth0",
        "type": "eth",
        "active": True,
        "autostart": True,
        "mtu": 1500,
        "method": "manual",
        "families": ["inet"],
    },
    {
        "iface": "vmbr0",
        "type": "bridge",
        "active": True,
        "autostart": True,
        "mtu": 1500,
        "method": "static",
        "families": ["inet"],
        "bridge_ports": "eth0",
        "address": "192.168.1.1",
        "netmask": "255.255.255.0",
    },
    {
        "iface": "bond0",
        "type": "bond",
        "active": False,
        "autostart": True,
        "mtu": 1500,
        "method": "manual",
        "families": ["inet"],
        "slaves": "eth1 eth2",
        "bond_mode": "active-backup",
    },
]

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


class TestProxmoxNodeNetworkInfo(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxNodeNetworkInfo, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_node_network_info

        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()

        mock_nodes = self.connect_mock.return_value.nodes
        mock_node_obj = mock_nodes.return_value
        mock_nodes.side_effect = lambda node=None: mock_node_obj

        mock_network_obj = mock_node_obj.network.return_value
        mock_node_obj.network = mock_network_obj
        mock_node_obj.network.return_value = mock_network_obj
        mock_network_obj.get.return_value = RAW_NETWORK_OUTPUT

        mock_nodes.get.return_value = [{"node": "pve"}]

        mock_network_obj.get.side_effect = lambda type=None: [
            interface for interface in RAW_NETWORK_OUTPUT if type is None or interface["type"] == type
        ]

    def tearDown(self):
        self.connect_mock.stop()
        super(TestProxmoxNodeNetworkInfo, self).tearDown()

    def test_basic_network_info(self):
        """Test basic network interface retrieval."""
        with pytest.raises(AnsibleExitJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert not result["changed"]
        assert result["proxmox_node_networks"] == EXPECTED_NETWORK_OUTPUT

    def test_filter_by_iface(self):
        """Test filtering by specific interface name."""
        with pytest.raises(AnsibleExitJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vmbr0",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert not result["changed"]
        assert len(result["proxmox_node_networks"]) == 1
        assert result["proxmox_node_networks"][0]["iface"] == "vmbr0"

    def test_filter_by_iface_type(self):
        """Test filtering by interface type."""
        mock_network_obj = self.connect_mock.return_value.nodes.return_value.network.return_value
        mock_network_obj.get.side_effect = lambda type=None: [
            interface for interface in RAW_NETWORK_OUTPUT if type is None or interface["type"] == type
        ]

        with pytest.raises(AnsibleExitJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface_type": "bridge",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert not result["changed"]
        for network in result["proxmox_node_networks"]:
            assert network["type"] == "bridge"

    def test_check_changes_with_pending_changes(self):
        """Test check_changes functionality with pending changes."""

        class MockResponse:
            def json(self):
                return {
                    "data": RAW_NETWORK_OUTPUT,
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
            with pytest.raises(AnsibleExitJson) as exc_info:
                with set_module_args(
                    {
                        "api_host": "host",
                        "api_user": "user",
                        "api_password": "password",
                        "node": "pve",
                        "check_changes": True,
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert not result["changed"]
            assert result["pending_changes"] == MOCK_PENDING_CHANGES
            assert result["has_pending_changes"] is True

    def test_check_changes_without_pending_changes(self):
        """Test check_changes functionality without pending changes."""

        class MockResponse:
            def json(self):
                return {"data": RAW_NETWORK_OUTPUT, "changes": None, "success": 1}

            def raise_for_status(self, *args, **kwargs):
                pass

        mock_response = MockResponse()

        with patch.object(
            self.connect_mock.return_value._store["session"],
            "request",
            return_value=mock_response,
        ):
            with pytest.raises(AnsibleExitJson) as exc_info:
                with set_module_args(
                    {
                        "api_host": "host",
                        "api_user": "user",
                        "api_password": "password",
                        "node": "pve",
                        "check_changes": True,
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert not result["changed"]
            assert result["pending_changes"] is None
            assert result["has_pending_changes"] is False

    def test_invalid_parameter_combination(self):
        """Test that check_changes cannot be used with iface or iface_type."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "check_changes": True,
                    "iface": "eth0",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "check_changes cannot be used with iface or iface_type parameters" in result["msg"]

    def test_node_not_found(self):
        """Test error handling when node doesn't exist."""
        with patch.object(self.module.ProxmoxNodeNetworkInfoAnsible, "get_node", return_value=None):
            with pytest.raises(AnsibleFailJson) as exc_info:
                with set_module_args(
                    {
                        "api_host": "host",
                        "api_user": "user",
                        "api_password": "password",
                        "node": "nonexistent",
                    }
                ):
                    self.module.main()

            result = exc_info.value.args[0]
            assert "Node 'nonexistent' not found in the Proxmox cluster" in result["msg"]

    def test_boolean_conversion(self):
        """Test that boolean values are properly converted."""
        with pytest.raises(AnsibleExitJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "bond0",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert not result["changed"]
        bond0_interface = result["proxmox_node_networks"][0]
        assert bond0_interface["iface"] == "bond0"
        assert bond0_interface["active"] is False
        assert bond0_interface["autostart"] is True

    def test_node_not_specified(self):
        """Test error handling when node parameter is not specified."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args({"api_host": "host", "api_user": "user", "api_password": "password"}):
                self.module.main()

        result = exc_info.value.args[0]
        assert "missing required arguments: node" in result["msg"]

    def test_iface_specified_but_not_found(self):
        """Test when iface is specified but the interface doesn't exist."""
        with pytest.raises(AnsibleExitJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "nonexistent_interface",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert not result["changed"]
        assert result["proxmox_node_networks"] == []

    def test_iface_type_specified_but_not_found(self):
        """Test when iface_type is specified but no interfaces of that type exist."""
        with pytest.raises(AnsibleExitJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface_type": "OVSPort",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert not result["changed"]
        assert result["proxmox_node_networks"] == []

    def test_iface_type_invalid(self):
        """Test when iface_type is specified with an invalid value."""
        with pytest.raises(AnsibleFailJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface_type": "invalid_type",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert "value of iface_type must be one of:" in result["msg"]

    def test_combination_iface_and_iface_type_not_found(self):
        """Test when both iface and iface_type are specified but combination doesn't exist."""
        with pytest.raises(AnsibleExitJson) as exc_info:
            with set_module_args(
                {
                    "api_host": "host",
                    "api_user": "user",
                    "api_password": "password",
                    "node": "pve",
                    "iface": "vmbr0",
                    "iface_type": "eth",
                }
            ):
                self.module.main()

        result = exc_info.value.args[0]
        assert not result["changed"]
        assert result["proxmox_node_networks"] == []
