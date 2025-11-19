#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, aleskxyz <aleskxyz@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: proxmox_node_network
version_added: "1.4.0"
short_description: Manage network interfaces on Proxmox nodes
requirements:
  - ipaddress
description:
  - This module allows you to manage network interfaces on Proxmox nodes.
  - Supports various interface types including bridge, bond, eth, vlan, and OVS interfaces.
  - Network configuration changes are staged and must be explicitly applied using C(state=apply) to take effect.
  - Changes made with C(state=present) or C(state=absent) are only staged and will not affect the running network configuration until applied.
author: "aleskxyz (@aleskxyz)"
notes:
  - Network configuration changes are staged and must be explicitly applied using C(state=apply) to take effect.
  - Changes made with C(state=present) or C(state=absent) are only staged and will not affect the running network configuration until applied.
  - Interface type cannot be changed after creation. Delete and recreate the interface to change its type.
  - "Ethernet interfaces (C(eth) type) represent physical hardware and cannot be created via API. Only existing physical interfaces can be configured."
  - "Bond and OVS bond interfaces must follow naming format C(bondX) where X is a number between 0 and 9999 (e.g., C(bond0), C(bond1), C(bond9999))."
  - "VLAN interfaces support two naming formats: C(vlanXY) (e.g., C(vlan100)) and C(iface_name.vlan_id) (e.g., C(eth0.100))."
  - For C(vlanXY) format, C(vlan_raw_device) parameter is required.
  - For C(iface_name.vlan_id) format, C(vlan_raw_device) should not be specified.
  - "Parameter deletion is supported for specific parameters. Set string parameters to empty string C('') or integer parameters to C(-1) to delete them."
  - "Deletable parameters: C(cidr), C(gateway), C(cidr6), C(gateway6), C(comments), C(mtu),
    C(bridge_ports), C(bridge_vids), C(ovs_ports), C(ovs_options), C(ovs_tag)."
  - "When C(state=apply) or C(state=revert), only the C(node) parameter is accepted. All other parameters are not allowed."
seealso:
  - module: community.proxmox.proxmox_node_network_info
    description: Retrieve information about network interfaces on Proxmox nodes.
  - name: Proxmox Network Configuration
    description: Proxmox VE network configuration documentation.
    link: https://pve.proxmox.com/wiki/Network_Configuration
attributes:
  check_mode:
    support: full
    details: Check mode is fully supported for all states.
  diff_mode:
    support: full
    details: Check mode is fully supported for all states.
options:
  node:
    description:
      - The Proxmox node to manage network interfaces on.
    type: str
    required: true
  state:
    description:
      - The desired state of the network interface.
      - C(present) and C(absent) stage changes but do not apply them to the running configuration.
      - C(apply) applies all staged network configuration changes to the running configuration.
      - C(revert) discards all staged network configuration changes.
    type: str
    choices:
      - present
      - absent
      - apply
      - revert
    default: present
  iface:
    description:
      - Network interface name.
      - Required when C(state=present) or C(state=absent).
      - For C(vlan) interface type, should be in format C(vlanXY) (e.g., C(vlan100)) or C(iface_name.vlan_id) (e.g., C(eth0.100)).
    type: str
    required: false
  iface_type:
    description:
      - Type of network interface.
      - Required when C(state=present).
      - Cannot be changed after interface creation.
    type: str
    choices:
      - bridge
      - bond
      - eth
      - vlan
      - OVSBridge
      - OVSBond
      - OVSIntPort
    required: false
  cidr:
    description:
      - IPv4 host address with prefix length (e.g., '192.168.1.10/24').
      - Supported for C(eth), C(bridge), C(bond), C(vlan), C(OVSBridge), and C(OVSIntPort) interface types.
      - Can be deleted by setting to empty string C('').
    type: str
    required: false
  gateway:
    description:
      - Default IPv4 gateway address.
      - Supported for C(eth), C(bridge), C(bond), C(vlan), C(OVSBridge), and C(OVSIntPort) interface types.
      - Can be deleted by setting to empty string C('').
    type: str
    required: false
  cidr6:
    description:
      - IPv6 host address with prefix length (e.g., '2001:db8::10/64').
      - Supported for C(eth), C(bridge), C(bond), C(vlan), C(OVSBridge), and C(OVSIntPort) interface types.
      - Can be deleted by setting to empty string C('').
    type: str
    required: false
  gateway6:
    description:
      - Default IPv6 gateway address.
      - Supported for C(eth), C(bridge), C(bond), C(vlan), C(OVSBridge), and C(OVSIntPort) interface types.
      - Can be deleted by setting to empty string C('').
    type: str
    required: false
  autostart:
    description:
      - Automatically start interface on boot.
      - Supported for C(eth), C(bridge), C(bond), C(vlan), and C(OVSBridge) interface types.
    type: bool
    required: false
  comments:
    description:
      - Comments for the interface configuration.
      - Supported for C(eth), C(bridge), C(bond), C(vlan), C(OVSBridge), C(OVSBond), and C(OVSIntPort) interface types.
      - Can be deleted by setting to empty string C('').
    type: str
    required: false
  mtu:
    description:
      - Maximum Transmission Unit (1280 - 65520).
      - Supported for C(eth), C(bridge), C(bond), C(vlan), C(OVSBridge), C(OVSBond), and C(OVSIntPort) interface types.
      - Can be deleted by setting to C(-1).
    type: int
    required: false
  # Bridge specific options
  bridge_ports:
    description:
      - Specify the interfaces you want to add to your bridge.
      - Supported for C(bridge) interface type only.
      - Can be deleted by setting to empty string C('').
    type: str
    required: false
  bridge_vids:
    description:
      - Specify the allowed VLANs (e.g., '2 4 100-200').
      - Only used if C(bridge_vlan_aware) is enabled.
      - Supported for C(bridge) interface type only.
      - Can be deleted by setting to empty string C('').
    type: str
    required: false
  bridge_vlan_aware:
    description:
      - Enable bridge VLAN support.
      - Supported for C(bridge) interface type only.
    type: bool
    required: false
  # Bond specific options
  bond_primary:
    description:
      - Primary interface for active-backup bond.
      - Required for C(active-backup) bonding mode.
      - Supported for C(bond) interface type only.
      - Primary interface should be specified in C(slaves) parameter as well.
    type: str
    required: false
  bond_mode:
    description:
      - Bonding mode for C(bond) or C(OVSBond) interface types.
      - "Valid values for C(bond) interface type: C(balance-rr), C(active-backup), C(balance-xor), C(broadcast), C(802.3ad), C(balance-tlb), C(balance-alb)"
      - "Valid values for C(OVSBond) interface type: C(active-backup), C(balance-slb), C(lacp-balance-slb), C(lacp-balance-tcp)"
    type: str
    choices:
      - balance-rr
      - active-backup
      - balance-xor
      - broadcast
      - 802.3ad
      - balance-tlb
      - balance-alb
      - balance-slb
      - lacp-balance-slb
      - lacp-balance-tcp
    required: false
  bond_xmit_hash_policy:
    description:
      - Transmit hash policy for bond type.
      - Required for C(balance-xor) and C(802.3ad) bonding modes.
    type: str
    choices:
      - layer2
      - layer2+3
      - layer3+4
    required: false
  slaves:
    description:
      - Interfaces used by the bonding device (space separated).
      - Required for C(bond) interface type.
    type: str
    required: false
  # VLAN specific options
  vlan_raw_device:
    description:
      - Raw device for VLAN interface.
      - Required if iface is in format 'vlanXY'.
      - Supported for C(vlan) interface type only.
    type: str
    required: false
  # OVS specific options
  ovs_ports:
    description:
      - Interfaces to add to OVS bridge.
      - Supported for C(OVSBridge) interface type only.
      - Can be deleted by setting to empty string C('').
    type: str
    required: false
  ovs_options:
    description:
      - OVS interface options.
      - Supported for C(OVSBridge), C(OVSBond), and C(OVSIntPort) interface types.
      - Can be deleted by setting to empty string C('').
    type: str
    required: false
  ovs_bonds:
    description:
      - Interfaces used by OVS bonding device. (space separated)
      - Required for C(OVSBond) interface type.
    type: str
    required: false
  ovs_bridge:
    description:
      - OVS bridge name.
      - Required for C(OVSBond) and C(OVSIntPort) interface types.
    type: str
    required: false
  ovs_tag:
    description:
      - VLAN tag (1 - 4094).
      - Supported for C(OVSBond) and C(OVSIntPort) interface types.
      - Can be deleted by setting to C(-1).
    type: int
    required: false
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
# Configure a network interface
- name: Configure network interface
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: eth0
    iface_type: eth
    cidr: 192.168.1.10/24
    gateway: 192.168.1.1
    cidr6: 2001:db8::10/64
    gateway6: 2001:db8::1
    autostart: true
    mtu: 1500
    comments: "Management network"

# Create a simple bridge interface
- name: Create bridge interface
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: vmbr0
    iface_type: bridge
    cidr: 192.168.1.10/24
    gateway: 192.168.1.1
    autostart: true

# Create a bond interface
- name: Create bond interface
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: bond0
    iface_type: bond
    bond_mode: active-backup
    bond_primary: eth0
    slaves: eth0 eth1
    cidr: 192.168.1.0/24
    gateway: 192.168.1.1

# Create a VLAN interface
- name: Create VLAN interface
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: eth0.100
    iface_type: vlan
    cidr: 192.168.100.10/24

# Create a VLAN interface with vlanXY format
- name: Create VLAN interface
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: vlan100
    iface_type: vlan
    vlan_raw_device: eth0
    cidr: 192.168.100.0/24

# Create a complex bridge with VLAN awareness
- name: Create VLAN-aware bridge
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: vmbr1
    iface_type: bridge
    bridge_ports: eth1 eth2
    bridge_vlan_aware: true
    bridge_vids: "2 4 100-200"
    cidr: 192.168.2.0/24
    gateway: 192.168.2.1
    mtu: 9000
    comments: "VLAN-aware bridge for trunking"

# Create an OVS bridge
- name: Create OVS bridge
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: ovsbr0
    iface_type: OVSBridge
    ovs_ports: eth3 eth4
    ovs_options: "updelay=5000"
    cidr: 192.168.3.10/24
    gateway: 192.168.3.1

# Create an OVS bond
- name: Create OVS bond
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: bond1  # Must follow bondX format where X is 0-9999
    iface_type: OVSBond
    bond_mode: active-backup
    ovs_bonds: eth5 eth6
    ovs_bridge: ovsbr0
    ovs_tag: 10
    ovs_options: "updelay=5000"

# Create an OVS internal port
- name: Create OVS internal port
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: ovsint0
    iface_type: OVSIntPort
    ovs_bridge: ovsbr0
    ovs_tag: 20
    ovs_options: "tag=20"
    cidr: 192.168.20.10/24
    gateway: 192.168.20.1

# Create interface with IPv6
- name: Create dual-stack interface
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: vmbr2
    iface_type: bridge
    bridge_ports: eth7
    cidr: 192.168.4.0/24
    gateway: 192.168.4.1
    cidr6: 2001:db8::/64
    gateway6: 2001:db8::1
    autostart: true

# Remove an interface
- name: Remove interface
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: absent
    iface: vmbr0

# Apply network configuration
- name: Apply network
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: apply

# Complete workflow example
- name: Create interface and apply changes
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: vmbr1
    iface_type: bridge
    cidr: 192.168.2.10/24
    gateway: 192.168.2.1

- name: Apply staged network changes
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: apply

# Revert network configuration changes
- name: Revert network changes
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: revert

# Using API token authentication
- name: Create interface with API token
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_token_id: my-token
    api_token_secret: my-token-secret
    node: pve01
    state: present
    iface: vmbr3
    iface_type: bridge
    cidr: 192.168.5.10/24
    gateway: 192.168.5.1

# Delete specific parameters from an interface
- name: Remove IP configuration from bridge
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: vmbr0
    iface_type: bridge
    cidr: ""          # Delete IPv4 CIDR
    gateway: ""       # Delete IPv4 gateway
    cidr6: ""         # Delete IPv6 CIDR
    gateway6: ""      # Delete IPv6 gateway
    comments: ""      # Delete comments
    mtu: -1           # Delete MTU (use -1 for integer parameters)

# Remove bridge ports and VLAN configuration
- name: Remove bridge ports and VLAN settings
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: vmbr1
    iface_type: bridge
    bridge_ports: ""  # Remove all bridge ports
    bridge_vlan_aware: true
    bridge_vids: ""   # Remove VLAN IDs (requires bridge_vlan_aware: true)

# Remove OVS-specific parameters
- name: Remove OVS options and ports
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: ovsbr0
    iface_type: OVSBridge
    ovs_ports: ""     # Remove OVS ports
    ovs_options: ""   # Remove OVS options
    ovs_tag: -1       # Remove VLAN tag (use -1 for integer parameters)

# Configure existing physical Ethernet interface
- name: Configure physical Ethernet interface
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: eth0
    iface_type: eth
    cidr: 192.168.1.10/24
    gateway: 192.168.1.1
    mtu: 9000
    comments: "Management interface"
  # Note: eth interfaces represent physical hardware and cannot be created via API
  # Only existing physical interfaces can be configured

# Create bond interface with proper naming format
- name: Create bond interface
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: bond0  # Must follow bondX format where X is 0-9999
    iface_type: bond
    bond_mode: active-backup
    bond_primary: eth0
    slaves: eth0 eth1
    cidr: 192.168.10.0/24
    gateway: 192.168.10.1


"""

RETURN = r"""
changed:
  description: Whether the module made changes.
  returned: always
  type: bool
  sample: true
msg:
  description: A message describing what happened.
  returned: always
  type: str
  sample: "Interface vmbr0 created successfully"
interface:
  description: The interface configuration that was applied.
  returned: when state is present
  type: dict
  sample:
    iface: vmbr0
    iface_type: bridge
    cidr: 192.168.1.0/24
    gateway: 192.168.1.1
    autostart: true
    mtu: 1500
    comments: "Management network"
diff:
  description: Differences between configurations in YAML format with before/after states.
  returned: when changes were made (create, update, delete)
  type: list
"""


import re
from ipaddress import ip_address, ip_interface
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.common.yaml import yaml_dump
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    ansible_to_proxmox_bool,
    proxmox_to_ansible_bool,
    proxmox_auth_argument_spec,
)


# Single source of truth for all parameter definitions
PARAMETER_DEFINITIONS = {
    "node": {
        "type": "str",
        "required": True,
    },
    "state": {
        "type": "str",
        "choices": ["present", "absent", "apply", "revert"],
        "default": "present",
    },
    "iface": {
        "type": "str",
    },
    "iface_type": {
        "type": "str",
        "choices": [
            "bridge",
            "bond",
            "eth",
            "vlan",
            "OVSBridge",
            "OVSBond",
            "OVSIntPort",
        ],
        "api_name": "type",
    },
    "cidr": {
        "type": "str",
        "deletable": True,
        "iface_types": ["eth", "bridge", "bond", "vlan", "OVSBridge", "OVSIntPort"],
    },
    "gateway": {
        "type": "str",
        "deletable": True,
        "iface_types": ["eth", "bridge", "bond", "vlan", "OVSBridge", "OVSIntPort"],
    },
    "cidr6": {
        "type": "str",
        "deletable": True,
        "iface_types": ["eth", "bridge", "bond", "vlan", "OVSBridge", "OVSIntPort"],
    },
    "gateway6": {
        "type": "str",
        "deletable": True,
        "iface_types": ["eth", "bridge", "bond", "vlan", "OVSBridge", "OVSIntPort"],
    },
    "autostart": {
        "type": "bool",
        "iface_types": ["eth", "bridge", "bond", "vlan", "OVSBridge"],
    },
    "comments": {
        "type": "str",
        "deletable": True,
        "iface_types": [
            "eth",
            "bridge",
            "bond",
            "vlan",
            "OVSBridge",
            "OVSBond",
            "OVSIntPort",
        ],
    },
    "mtu": {
        "type": "int",
        "deletable": True,
        "iface_types": [
            "eth",
            "bridge",
            "bond",
            "vlan",
            "OVSBridge",
            "OVSBond",
            "OVSIntPort",
        ],
    },
    "bridge_ports": {
        "type": "str",
        "deletable": True,
        "default_response": "",
        "iface_types": ["bridge"],
    },
    "bridge_vids": {
        "type": "str",
        "deletable": True,
        "default_response": "2-4094",
        "iface_types": ["bridge"],
    },
    "bridge_vlan_aware": {
        "type": "bool",
        "iface_types": ["bridge"],
    },
    "bond_primary": {
        "type": "str",
        "api_name": "bond-primary",
        "iface_types": ["bond"],
    },
    "bond_mode": {
        "type": "str",
        "choices": [
            "balance-rr",
            "active-backup",
            "balance-xor",
            "broadcast",
            "802.3ad",
            "balance-tlb",
            "balance-alb",
            "balance-slb",
            "lacp-balance-slb",
            "lacp-balance-tcp",
        ],
        "iface_types": ["bond", "OVSBond"],
    },
    "bond_xmit_hash_policy": {
        "type": "str",
        "choices": ["layer2", "layer2+3", "layer3+4"],
        "iface_types": ["bond"],
    },
    "slaves": {
        "type": "str",
        "iface_types": ["bond"],
    },
    "vlan_raw_device": {
        "type": "str",
        "api_name": "vlan-raw-device",
        "iface_types": ["vlan"],
    },
    "ovs_ports": {
        "type": "str",
        "deletable": True,
        "default_response": "",
        "iface_types": ["OVSBridge"],
    },
    "ovs_options": {
        "type": "str",
        "deletable": True,
        "default_response": "",
        "iface_types": ["OVSBridge", "OVSBond", "OVSIntPort"],
    },
    "ovs_bonds": {
        "type": "str",
        "iface_types": ["OVSBond"],
    },
    "ovs_bridge": {
        "type": "str",
        "iface_types": ["OVSBond", "OVSIntPort"],
    },
    "ovs_tag": {
        "type": "int",
        "deletable": True,
        "iface_types": ["OVSBond", "OVSIntPort"],
    },
    # Read-only parameters returned by API
    "active": {
        "type": "bool",
        "read_only": True,
    },
    "vlan_id": {
        "type": "int",
        "read_only": True,
        "api_name": "vlan-id",
    },
    "exists": {
        "type": "bool",
        "read_only": True,
    },
    "priority": {
        "type": "int",
        "read_only": True,
    },
}


def _is_valid_cidr(cidr):
    """Validate IPv4 host address with prefix using ipaddress."""
    if not cidr:
        return False
    try:
        iface = ip_interface(cidr)
        return iface.version == 4
    except Exception:
        return False


def _is_valid_cidr6(cidr):
    """Validate IPv6 host address with prefix using ipaddress."""
    if not cidr:
        return False
    try:
        iface = ip_interface(cidr)
        return iface.version == 6
    except Exception:
        return False


def _is_valid_ipv4(addr):
    """Validate IPv4 address using ipaddress."""
    if not addr:
        return False
    try:
        return ip_address(addr).version == 4
    except Exception:
        return False


def _is_valid_ipv6(addr):
    """Validate IPv6 address using ipaddress."""
    if not addr:
        return False
    try:
        return ip_address(addr).version == 6
    except Exception:
        return False


def get_network_args():
    """Get network-specific arguments for AnsibleModule."""
    args = {}
    for param_name, param_def in PARAMETER_DEFINITIONS.items():
        if param_def.get("read_only"):
            continue

        arg_def = {"type": param_def["type"]}

        if "choices" in param_def:
            arg_def["choices"] = param_def["choices"]
        if "default" in param_def:
            arg_def["default"] = param_def["default"]
        if "required" in param_def:
            arg_def["required"] = param_def["required"]

        args[param_name] = arg_def

    return args


class ProxmoxNetworkManager(ProxmoxAnsible):
    """Manages Proxmox network interfaces."""

    def __init__(self, module):
        super(ProxmoxNetworkManager, self).__init__(module)
        self.params = module.params
        self.node = self.params["node"]

    def get_params_for_interface_type(self, iface_type):
        """Get parameters applicable to a specific interface type."""
        params = []
        for param_name, param_def in PARAMETER_DEFINITIONS.items():
            if param_def.get("read_only"):
                continue

            if "iface_types" in param_def and iface_type in param_def["iface_types"]:
                params.append(param_name)

        return params

    def get_all_valid_params(self):
        """Get all valid parameter names."""
        return list(PARAMETER_DEFINITIONS.keys())

    def get_core_params(self):
        """Get core parameters (not read-only and not interface-specific)."""
        return {
            param_name
            for param_name, param_def in PARAMETER_DEFINITIONS.items()
            if not param_def.get("read_only") and "iface_types" not in param_def
        }

    def normalize_comment(self, comment):
        """Normalize comment string."""
        if comment is None:
            return None
        return str(comment).strip()

    def get_api_name(self, param_name):
        """Get API parameter name for a given Ansible parameter name."""
        if param_name in PARAMETER_DEFINITIONS:
            return PARAMETER_DEFINITIONS[param_name].get("api_name", param_name)
        return param_name

    def get_ansible_name(self, api_param_name):
        """Get Ansible parameter name for a given API parameter name."""
        for param_name, param_def in PARAMETER_DEFINITIONS.items():
            if param_def.get("api_name") == api_param_name:
                return param_name
        return api_param_name

    def is_delete_intention(self, value, param_name):
        """Check if a value represents delete intention for a parameter."""
        if param_name not in PARAMETER_DEFINITIONS:
            return False

        param_def = PARAMETER_DEFINITIONS[param_name]
        if not param_def.get("deletable"):
            return False

        param_type = param_def["type"]

        if param_type == "str":
            return value == ""
        elif param_type == "int":
            return value == -1
        else:
            return False

    def get_effective_value(self, value, param_name):
        """Get the effective value for validation (treat delete intentions as null)."""
        if param_name not in PARAMETER_DEFINITIONS:
            return value

        param_def = PARAMETER_DEFINITIONS[param_name]
        if not param_def.get("deletable"):
            return value

        param_type = param_def["type"]

        if param_type == "str" and value == "":
            return None
        elif param_type == "int" and value == -1:
            return None
        else:
            return value

    def is_effectively_deleted(self, current_value, param_name):
        """Check if a parameter is effectively deleted based on current value."""
        if param_name not in PARAMETER_DEFINITIONS:
            return False

        param_def = PARAMETER_DEFINITIONS[param_name]
        if not param_def.get("deletable"):
            return False

        default_response = param_def.get("default_response")

        if default_response is None:
            return current_value is None
        else:
            # If current_value is None (not present), it's effectively deleted
            # because the API will return the default_response when we try to delete it
            if current_value is None:
                return True
            return current_value == default_response

    def validate_common_params(self):
        """Validate common parameters."""
        errors = []

        mtu_value = self.get_effective_value(self.params.get("mtu"), "mtu")
        if mtu_value is not None:
            try:
                mtu = int(mtu_value)
                if not (1280 <= mtu <= 65520):
                    errors.append("mtu must be between 1280 and 65520")
            except (ValueError, TypeError):
                errors.append("mtu must be an integer")

        cidr_value = self.get_effective_value(self.params.get("cidr"), "cidr")
        if cidr_value:
            if not _is_valid_cidr(cidr_value):
                errors.append("Invalid IPv4 cidr format")

        cidr6_value = self.get_effective_value(self.params.get("cidr6"), "cidr6")
        if cidr6_value:
            if not _is_valid_cidr6(cidr6_value):
                errors.append("Invalid IPv6 cidr format")

        # Gateway requires corresponding CIDR to be defined
        gateway_value = self.get_effective_value(self.params.get("gateway"), "gateway")
        if gateway_value and not cidr_value:
            errors.append("gateway cannot be set when cidr is not defined")
        elif gateway_value:
            if not _is_valid_ipv4(gateway_value):
                errors.append("gateway must be a valid IPv4 address")

        gateway6_value = self.get_effective_value(
            self.params.get("gateway6"), "gateway6"
        )
        if gateway6_value and not cidr6_value:
            errors.append("gateway6 cannot be set when cidr6 is not defined")
        elif gateway6_value:
            if not _is_valid_ipv6(gateway6_value):
                errors.append("gateway6 must be a valid IPv6 address")

        return errors

    def validate_eth_params(self):
        """Validate eth interface parameters."""
        errors = []
        return errors

    def validate_bridge_params(self):
        """Validate bridge-specific parameters."""
        errors = []

        # bridge_vids requires bridge_vlan_aware to be enabled
        bridge_vids_value = self.get_effective_value(
            self.params.get("bridge_vids"), "bridge_vids"
        )
        if bridge_vids_value is not None:
            if not self.params.get("bridge_vlan_aware"):
                errors.append(
                    "bridge_vids should not be defined if bridge_vlan_aware is not set or false"
                )

        return errors

    def validate_bond_params(self):
        """Validate bond-specific parameters."""
        errors = []

        if not self.params.get("bond_mode"):
            errors.append("bond_mode is required for bond type")
        else:
            bond_mode = self.params.get("bond_mode")
            valid_modes = [
                "balance-rr",
                "active-backup",
                "balance-xor",
                "broadcast",
                "802.3ad",
                "balance-tlb",
                "balance-alb",
            ]
            if bond_mode not in valid_modes:
                errors.append(
                    f"Invalid bond_mode for bond type. Must be one of: {', '.join(valid_modes)}"
                )

        if not self.params.get("slaves"):
            errors.append("slaves is required for bond type")

        # Mode-specific validation
        bond_mode = self.params.get("bond_mode")
        if bond_mode == "active-backup":
            if not self.params.get("bond_primary"):
                errors.append("bond_primary is required for active-backup mode")
            else:
                bond_primary = self.params.get("bond_primary")
                slaves = self.params.get("slaves", "").split()
                if bond_primary not in slaves:
                    errors.append(
                        "bond_primary must be included in slaves for active-backup mode"
                    )
        elif bond_mode in ["balance-xor", "802.3ad"]:
            if not self.params.get("bond_xmit_hash_policy"):
                errors.append(
                    "bond_xmit_hash_policy is required for balance-xor and 802.3ad modes"
                )

        # Validate parameter combinations based on bond mode
        if self.params.get("bond_primary") is not None and bond_mode != "active-backup":
            errors.append(
                "bond_primary should not be defined if bond_mode is not active-backup"
            )

        if self.params.get("bond_xmit_hash_policy") is not None and bond_mode not in [
            "balance-xor",
            "802.3ad",
        ]:
            errors.append(
                "bond_xmit_hash_policy should not be defined if bond_mode is not balance-xor or 802.3ad"
            )

        return errors

    def validate_vlan_params(self):
        """Validate VLAN-specific parameters."""
        errors = []

        iface = self.params.get("iface", "")

        # Validate vlan_raw_device based on interface naming format
        if iface.startswith("vlan"):
            if not self.params.get("vlan_raw_device"):
                errors.append(
                    f"vlan_raw_device is required for VLAN interface '{iface}' in vlanXY format"
                )
        else:
            if self.params.get("vlan_raw_device") is not None:
                errors.append(
                    f"vlan_raw_device should not be specified for VLAN interface '{iface}' in iface_name.vlan_id format"
                )

        return errors

    def validate_ovs_bridge_params(self):
        """Validate OVS bridge parameters."""
        errors = []
        return errors

    def validate_ovs_bond_params(self):
        """Validate OVS bond parameters."""
        errors = []

        if not self.params.get("bond_mode"):
            errors.append("bond_mode is required for OVSBond type")
        else:
            bond_mode = self.params.get("bond_mode")
            valid_modes = [
                "active-backup",
                "balance-slb",
                "lacp-balance-slb",
                "lacp-balance-tcp",
            ]
            if bond_mode not in valid_modes:
                errors.append(
                    f"Invalid bond_mode for OVSBond. Must be one of: {', '.join(valid_modes)}"
                )

        if not self.params.get("ovs_bonds"):
            errors.append("ovs_bonds is required for OVSBond type")

        if not self.params.get("ovs_bridge"):
            errors.append("ovs_bridge is required for OVSBond type")

        # Validate VLAN tag range (1-4094)
        ovs_tag_value = self.get_effective_value(self.params.get("ovs_tag"), "ovs_tag")
        if ovs_tag_value is not None:
            try:
                ovs_tag = int(ovs_tag_value)
                if not (1 <= ovs_tag <= 4094):
                    errors.append("ovs_tag must be between 1 and 4094")
            except (ValueError, TypeError):
                errors.append("ovs_tag must be an integer")

        return errors

    def validate_ovs_int_port_params(self):
        """Validate OVS internal port parameters."""
        errors = []

        if not self.params.get("ovs_bridge"):
            errors.append("ovs_bridge is required for OVSIntPort type")

        # Validate VLAN tag range (1-4094)
        ovs_tag_value = self.get_effective_value(self.params.get("ovs_tag"), "ovs_tag")
        if ovs_tag_value is not None:
            try:
                ovs_tag = int(ovs_tag_value)
                if not (1 <= ovs_tag <= 4094):
                    errors.append("ovs_tag must be between 1 and 4094")
            except (ValueError, TypeError):
                errors.append("ovs_tag must be an integer")

        return errors

    def validate_params(self):
        """Validate all parameters based on interface type."""
        errors = []

        # Basic state requirements
        state = self.params.get("state", "present")
        if state == "present":
            if not self.params.get("iface"):
                errors.append("iface is required when state is present")
            if not self.params.get("iface_type"):
                errors.append("iface_type is required when state is present")
        elif state == "absent":
            if not self.params.get("iface"):
                errors.append("iface is required when state is absent")
        elif state in ["apply", "revert"]:
            # For apply/revert states, only node parameter is allowed
            allowed_params = ["node", "state"]
            auth_params = list(proxmox_auth_argument_spec().keys())
            all_allowed_params = allowed_params + auth_params

            # Check for any parameters other than node, state, and auth params
            for param_name, value in self.params.items():
                if value is not None and param_name not in all_allowed_params:
                    errors.append(
                        f"Parameter '{param_name}' is not allowed when state is '{state}'. Only 'node' parameter is accepted."
                    )

            # Return early for apply/revert states - no further validation needed
            return errors

        # Interface name format validation
        errors.extend(self.validate_interface_name())

        # Parameter combination validation
        errors.extend(self.validate_parameter_combinations())

        if errors:
            return errors

        # Parameter value validation
        errors.extend(self.validate_common_params())

        # Type-specific validation
        iface_type = self.params.get("iface_type")
        if iface_type:
            if iface_type == "eth":
                errors.extend(self.validate_eth_params())
            elif iface_type == "bridge":
                errors.extend(self.validate_bridge_params())
            elif iface_type == "bond":
                errors.extend(self.validate_bond_params())
            elif iface_type == "vlan":
                errors.extend(self.validate_vlan_params())
            elif iface_type == "OVSBridge":
                errors.extend(self.validate_ovs_bridge_params())
            elif iface_type == "OVSBond":
                errors.extend(self.validate_ovs_bond_params())
            elif iface_type == "OVSIntPort":
                errors.extend(self.validate_ovs_int_port_params())

        return errors

    def validate_interface_name(self):
        """Validate interface name format based on interface type."""
        errors = []
        iface = self.params.get("iface")
        iface_type = self.params.get("iface_type")

        if not iface or not iface_type:
            return errors

        # Bond interfaces must follow bondX format (X = 0-9999)
        if iface_type in ["bond", "OVSBond"]:
            if not re.match(r"^bond\d{1,5}$", iface):
                errors.append(
                    f"Interface name '{iface}' for type '{iface_type}' must follow format 'bondX' where X is a number between 0 and 9999"
                )
            else:
                bond_number = int(iface[4:])
                if bond_number > 9999:
                    errors.append(
                        f"bond interface number must be between 0 and 9999, got {bond_number}"
                    )

        # VLAN interfaces support two formats: eth0.100 and vlan100
        elif iface_type == "vlan":
            if not (
                re.match(r"^(?!vlan\.)[a-zA-Z0-9_-]+\.\d+$", iface)
                or re.match(r"^vlan\d+$", iface)
            ):
                errors.append(
                    f"VLAN interface name '{iface}' must follow format 'vlanXY' (e.g., vlan100) or 'iface_name.vlan_id' (e.g., eth0.100)"
                )
            else:
                try:
                    if iface.startswith("vlan"):
                        vlan_id = int(iface[4:])
                    else:
                        vlan_id = int(iface.split(".")[-1])
                    if not (1 <= vlan_id <= 4094):
                        errors.append(
                            f"vlan_id must be between 1 and 4094, got {vlan_id}"
                        )
                except (ValueError, TypeError):
                    errors.append("vlan_id must be a valid integer")

        return errors

    def validate_parameter_combinations(self):
        """Validate parameter combinations based on interface type."""
        errors = []
        iface_type = self.params.get("iface_type")

        if not iface_type:
            return errors

        # Get parameters that are set and validate against allowed parameters
        set_params = [key for key, value in self.params.items() if value is not None]
        allowed_params = self.get_params_for_interface_type(iface_type)
        core_params = self.get_core_params()
        auth_params = list(proxmox_auth_argument_spec().keys())
        all_allowed_params = allowed_params + list(core_params) + auth_params

        invalid_params = [
            param for param in set_params if param not in all_allowed_params
        ]

        if invalid_params:
            errors.append(
                f"Parameters {', '.join(invalid_params)} are not valid for interface type '{iface_type}'"
            )

        return errors

    def _is_eth_interface_deleted(self, interface):
        """Check if an eth interface is considered deleted (inactive)."""
        has_priority = "priority" in interface
        autostart = interface.get("autostart", False)
        active = interface.get("active", False)

        # Interface is deleted if it has no priority, autostart is false, and active is false
        return not has_priority and not autostart and not active

    def get_network_changes(self):
        """Check if there are pending network configuration changes.

        Workaround for proxmoxer module which doesn't provide access to the 'changes' field.
        """
        try:
            resp = self.proxmox_api._store["session"].request(
                "GET",
                f"{self.proxmox_api._store['base_url']}/nodes/{self.node}/network",
            )
            resp.raise_for_status()
            changes = resp.json().get("changes", None)
            return changes
        except Exception as e:
            self.module.fail_json(
                msg=f"Failed to check network changes for node {self.node}: {e}"
            )

    def get_all_interfaces(self):
        """Get all network interfaces."""
        try:
            interfaces = self.proxmox_api.nodes(self.node).network.get()
            # Convert API parameter names to Ansible format and normalize values
            converted_interfaces = []
            for interface in interfaces:
                converted_interface = {}
                for key, value in interface.items():
                    converted_key = self.get_ansible_name(key)
                    if converted_key == "comments":
                        value = self.normalize_comment(value)
                    elif isinstance(value, int) and value in [0, 1]:
                        if (
                            converted_key in PARAMETER_DEFINITIONS
                            and PARAMETER_DEFINITIONS[converted_key]["type"] == "bool"
                        ):
                            value = proxmox_to_ansible_bool(value)
                    converted_interface[converted_key] = value
                converted_interfaces.append(converted_interface)
            return converted_interfaces
        except Exception as e:
            self.module.fail_json(
                msg="Failed to get network interfaces: %s" % to_native(e),
                exception=traceback.format_exc(),
            )

    def get_interface_config(self):
        """Get current interface configuration."""
        try:
            interfaces = self.get_all_interfaces()
            iface = self.params.get("iface")

            # Find the specific interface
            for interface in interfaces:
                if interface.get("iface") == iface:
                    return interface

            return None  # Interface not found
        except Exception as e:
            self.module.fail_json(
                msg="Failed to get interface configuration: %s" % to_native(e),
                exception=traceback.format_exc(),
            )

    def create_interface(self):
        """Create network interface."""
        try:
            data = self._build_interface_data()
            # Remove 'delete' property for creation (only valid for updates)
            if "delete" in data:
                del data["delete"]
            self.proxmox_api.nodes(self.node).network.post(**data)
            return True
        except Exception as e:
            self.module.fail_json(
                msg="Failed to create interface: %s" % to_native(e),
                exception=traceback.format_exc(),
            )

    def update_interface(self):
        """Update network interface."""
        try:
            data = self._build_interface_data()
            iface = self.params.get("iface")
            self.proxmox_api.nodes(self.node).network(iface).put(**data)
            return True
        except Exception as e:
            self.module.fail_json(
                msg="Failed to update interface: %s" % to_native(e),
                exception=traceback.format_exc(),
            )

    def delete_interface(self):
        """Delete network interface."""
        try:
            iface = self.params.get("iface")
            self.proxmox_api.nodes(self.node).network(iface).delete()
            return True
        except Exception as e:
            self.module.fail_json(
                msg="Failed to delete interface: %s" % to_native(e),
                exception=traceback.format_exc(),
            )

    def apply_network(self):
        """Apply network configuration."""
        try:
            self.proxmox_api.nodes(self.node).network.put()
            return True
        except Exception as e:
            self.module.fail_json(
                msg="Failed to apply network: %s" % to_native(e),
                exception=traceback.format_exc(),
            )

    def revert_network(self):
        """Revert network configuration."""
        try:
            self.proxmox_api.nodes(self.node).network.delete()
            return True
        except Exception as e:
            self.module.fail_json(
                msg="Failed to revert network: %s" % to_native(e),
                exception=traceback.format_exc(),
            )

    def execute(self):
        """Execute the network management operation."""
        state = self.params.get("state", "present")

        # Validate node exists before any API calls
        try:
            node_info = self.get_node(self.node)
            if not node_info:
                self.module.fail_json(
                    msg=f"Node '{self.node}' not found in the Proxmox cluster"
                )
        except Exception as e:
            self.module.fail_json(msg=f"Failed to validate node '{self.node}': {e}")

        try:
            if state == "present":
                return self._handle_present_state()
            elif state == "absent":
                return self._handle_absent_state()
            elif state == "apply":
                return self._handle_apply_state()
            elif state == "revert":
                return self._handle_revert_state()
        except Exception as e:
            self.module.fail_json(
                msg="Failed to manage network interface: %s" % to_native(e),
                exception=traceback.format_exc(),
            )

    def _handle_present_state(self):
        """Handle present state (create or update)."""
        iface = self.params.get("iface")
        current_config = self.get_interface_config()

        if current_config:
            # Check if interface type is being changed (not allowed)
            current_type = current_config.get("iface_type")
            desired_type = self.params.get("iface_type")
            if current_type and desired_type and current_type != desired_type:
                self.module.fail_json(
                    msg=f"Cannot change interface type from '{current_type}' to '{desired_type}'. "
                    f"Interface type cannot be modified after creation. "
                    f"Delete the interface and recreate it with the desired type."
                )

            if self._has_differences(current_config):
                if not self.module.check_mode:
                    self.update_interface()
                    updated_config = self.get_interface_config()
                    msg = f"Interface {iface} updated successfully"
                    after_config = updated_config
                    before_config = current_config
                else:
                    after_config = self._build_interface_config()
                    before_config = self._filter_config_to_user_params(current_config)
                    msg = f"Interface {iface} would be updated"

                return {
                    "changed": True,
                    "msg": msg,
                    "interface": after_config,
                    "diff": self._format_diff(before_config, after_config, iface),
                }
            else:
                return {
                    "changed": False,
                    "msg": f"Interface {iface} already exists with correct configuration",
                    "interface": current_config,
                }
        else:
            # Prevent creation of eth interfaces (physical hardware)
            iface_type = self.params.get("iface_type")
            if iface_type == "eth":
                self.module.fail_json(
                    msg=f"Cannot create interface '{iface}' of type 'eth'. "
                    f"Ethernet interfaces represent physical hardware and cannot be created via API. "
                    f"Only existing physical interfaces can be configured."
                )

            if not self.module.check_mode:
                self.create_interface()
                created_config = self.get_interface_config()
                msg = f"Interface {iface} created successfully"
            else:
                created_config = self._build_interface_config()
                msg = f"Interface {iface} would be created"

            return {
                "changed": True,
                "msg": msg,
                "interface": created_config,
                "diff": self._format_diff(None, created_config, iface),
            }

    def _handle_absent_state(self):
        """Handle absent state (delete)."""
        iface = self.params.get("iface")
        iface_type = self.params.get("iface_type")
        current_config = self.get_interface_config()

        # Special handling for eth interfaces (check if actually deleted/inactive)
        if iface_type == "eth" and current_config:
            if self._is_eth_interface_deleted(current_config):
                return {"changed": False, "msg": f"Interface {iface} does not exist"}

        if current_config:
            if not self.module.check_mode:
                self.delete_interface()
                msg = f"Interface {iface} deleted successfully"
            else:
                msg = f"Interface {iface} would be deleted"
            return {
                "changed": True,
                "msg": msg,
                "diff": self._format_diff(current_config, None, iface),
            }
        else:
            return {"changed": False, "msg": f"Interface {iface} does not exist"}

    def _handle_apply_state(self):
        """Handle apply state."""
        if self.module.check_mode:
            return {
                "changed": True,
                "msg": "Staged network configuration changes may be applied",
            }

        changes = self.get_network_changes()

        if changes:
            self.apply_network()
            return {
                "changed": True,
                "msg": "Staged network configuration changes applied successfully",
                "diff": {"prepared": changes},
            }
        else:
            return {
                "changed": False,
                "msg": "No staged network configuration changes to apply",
            }

    def _handle_revert_state(self):
        """Handle revert state."""
        if self.module.check_mode:
            return {
                "changed": True,
                "msg": "Staged network configuration changes may be reverted",
            }

        changes = self.get_network_changes()

        if changes:
            self.revert_network()
            return {
                "changed": True,
                "msg": "Staged network configuration changes reverted successfully",
            }
        else:
            return {
                "changed": False,
                "msg": "No staged network configuration changes to revert",
            }

    def _build_interface_data(self):
        """Build interface data for API calls."""
        data = {}
        delete_list = []

        if self.params.get("iface"):
            data["iface"] = self.params.get("iface")

        if self.params.get("iface_type"):
            data["type"] = self.params.get("iface_type")

        # Process all parameters for the interface type
        for param_name in self.get_params_for_interface_type(
            self.params.get("iface_type")
        ):
            if self.params.get(param_name) is not None:
                value = self.params.get(param_name)

                # Handle delete intentions (empty string for str, -1 for int)
                if self.is_delete_intention(value, param_name):
                    api_param_name = self.get_api_name(param_name)
                    delete_list.append(api_param_name)
                else:
                    # Handle boolean values: False = delete, True = set to 1
                    if isinstance(value, bool):
                        if value is False:
                            api_param_name = self.get_api_name(param_name)
                            delete_list.append(api_param_name)
                            continue
                        else:
                            value = ansible_to_proxmox_bool(value)

                    api_param_name = self.get_api_name(param_name)
                    data[api_param_name] = value

        if delete_list:
            data["delete"] = delete_list

        return data

    def _has_differences(self, current_config):
        """Check if there are differences between current and desired configuration."""
        core_params = self.get_core_params()
        network_params = get_network_args()
        for param_name in self.params:
            if (
                param_name in network_params
                and param_name not in core_params
                and self.params.get(param_name) is not None
            ):
                current_value = current_config.get(param_name)
                desired_value = self.params.get(param_name)

                # Check if parameter should be deleted
                if self.is_delete_intention(desired_value, param_name):
                    if not self.is_effectively_deleted(current_value, param_name):
                        return True
                    continue

                # Handle boolean comparison with Proxmox format conversion
                if isinstance(desired_value, bool):
                    if current_value is None:
                        # Assume False if not present in config
                        if desired_value is not False:
                            return True
                        continue
                    if current_value in [0, 1]:
                        current_value = proxmox_to_ansible_bool(current_value)
                    desired_value_proxmox = ansible_to_proxmox_bool(desired_value)
                    if current_value != desired_value_proxmox:
                        return True
                elif param_name == "comments":
                    # Normalize comments for comparison
                    current_value_normalized = self.normalize_comment(current_value)
                    if current_value_normalized != desired_value:
                        return True
                else:
                    if str(current_value) != str(desired_value):
                        return True

        return False

    def _format_diff(self, before_config, after_config, iface):
        """Format configuration differences in YAML format for Ansible diff."""
        # Determine operation type for diff formatting
        is_create = before_config is None and after_config is not None
        is_delete = before_config is not None and after_config is None

        if is_create:
            diff_entry = {
                "after": yaml_dump(after_config, default_flow_style=False, indent=2),
                "after_header": iface,
                "before": None,
            }
        elif is_delete:
            diff_entry = {
                "before": yaml_dump(before_config, default_flow_style=False, indent=2),
                "before_header": iface,
                "after": None,
            }
        else:
            diff_entry = {
                "before": yaml_dump(before_config, default_flow_style=False, indent=2),
                "after": yaml_dump(after_config, default_flow_style=False, indent=2),
                "before_header": iface,
                "after_header": iface,
            }

        return [diff_entry]

    def _filter_config_to_user_params(self, config):
        """Filter configuration to only include parameters that the user has defined."""
        if config is None:
            return None

        filtered_config = {}

        # Always include interface identification
        if "iface" in config:
            filtered_config["iface"] = config["iface"]
        if "iface_type" in config:
            filtered_config["iface_type"] = config["iface_type"]

        # Include only parameters that the user has set
        for param_name in self.get_all_valid_params():
            if self.params.get(param_name) is not None:
                if param_name in config:
                    filtered_config[param_name] = config[param_name]

        return filtered_config

    def _build_interface_config(self):
        """Build interface configuration dictionary."""
        config = {
            "iface": self.params.get("iface"),
            "iface_type": self.params.get("iface_type"),
        }

        # Add all parameters that are set, with proper value conversion
        for param_name in self.get_all_valid_params():
            if self.params.get(param_name) is not None:
                value = self.params.get(param_name)

                # Skip delete intentions in config output
                if self.is_delete_intention(value, param_name):
                    continue

                # Convert boolean values to Proxmox format for consistency
                if isinstance(value, bool):
                    value = ansible_to_proxmox_bool(value)

                # Normalize comments for return data
                if param_name == "comments" and isinstance(value, str):
                    value = self.normalize_comment(value)

                config[param_name] = value

        return config


def main():
    """Main function."""
    module_args = proxmox_auth_argument_spec()
    network_args = get_network_args()
    module_args.update(network_args)

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[
            ("state", "present", ["iface", "iface_type"]),
        ],
        required_one_of=[("api_password", "api_token_id")],
        required_together=[("api_token_id", "api_token_secret")],
        supports_check_mode=True,
    )

    # Create network manager instance
    network_manager = ProxmoxNetworkManager(module)

    # Validate parameters
    validation_errors = network_manager.validate_params()
    if validation_errors:
        module.fail_json(
            msg="Parameter validation failed: " + "; ".join(validation_errors)
        )

    # Execute the operation
    result = network_manager.execute()

    module.exit_json(**result)


if __name__ == "__main__":
    main()
