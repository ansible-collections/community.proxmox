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
version_added: "1.3.0"
short_description: Manage network interfaces on Proxmox nodes
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
  - "VLAN interfaces support two naming formats: C(vlanXY) (e.g., C(vlan100)) and C(iface_name.vlan_id) (e.g., C(eth0.100))."
  - For C(vlanXY) format, C(vlan_raw_device) parameter is required.
  - For C(iface_name.vlan_id) format, C(vlan_raw_device) should not be specified.
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
      - IPv4 CIDR notation (e.g., '192.168.1.0/24').
      - Supported for C(eth), C(bridge), C(bond), C(vlan), C(OVSBridge), and C(OVSIntPort) interface types.
    type: str
    required: false
  gateway:
    description:
      - Default IPv4 gateway address.
      - Supported for C(eth), C(bridge), C(bond), C(vlan), C(OVSBridge), and C(OVSIntPort) interface types.
    type: str
    required: false
  cidr6:
    description:
      - IPv6 CIDR notation (e.g., '2001:db8::/64').
      - Supported for C(eth), C(bridge), C(bond), C(vlan), C(OVSBridge), and C(OVSIntPort) interface types.
    type: str
    required: false
  gateway6:
    description:
      - Default IPv6 gateway address.
      - Supported for C(eth), C(bridge), C(bond), C(vlan), C(OVSBridge), and C(OVSIntPort) interface types.
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
    type: str
    required: false
  mtu:
    description:
      - Maximum Transmission Unit (1280 - 65520).
      - Supported for all interface types.
    type: int
    required: false
  # Bridge specific options
  bridge_ports:
    description:
      - Specify the interfaces you want to add to your bridge.
      - Supported for C(bridge) interface type only.
    type: str
    required: false
  bridge_vids:
    description:
      - Specify the allowed VLANs (e.g., '2 4 100-200').
      - Only used if C(bridge_vlan_aware) is enabled.
      - Supported for C(bridge) interface type only.
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
    type: str
    required: false
  ovs_options:
    description:
      - OVS interface options.
      - Supported for C(OVSBridge), C(OVSBond), and C(OVSIntPort) interface types.
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
    cidr: 192.168.1.0/24
    gateway: 192.168.1.1
    cidr6: 2001:db8::/64
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
    cidr: 192.168.1.0/24
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
    cidr: 192.168.100.0/24

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
    cidr: 192.168.3.0/24
    gateway: 192.168.3.1

# Create an OVS bond
- name: Create OVS bond
  community.proxmox.proxmox_node_network:
    api_host: proxmox.example.com:8006
    api_user: root@pam
    api_password: secret
    node: pve01
    state: present
    iface: ovsbond0
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
    cidr: 192.168.20.0/24
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
    cidr: 192.168.2.0/24
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
    cidr: 192.168.5.0/24
    gateway: 192.168.5.1
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


def get_params_for_interface_type(iface_type):
    """Get valid parameters for a specific interface type from argument spec."""
    interface_type_mapping = get_interface_type_mapping()
    valid_params = []

    for param_name, supported_types in interface_type_mapping.items():
        if iface_type in supported_types:
            valid_params.append(param_name)

    return valid_params


def get_all_valid_params():
    """Get all valid parameters across all interface types from argument spec."""
    interface_type_mapping = get_interface_type_mapping()
    all_params = set()

    for param_name in interface_type_mapping.keys():
        all_params.add(param_name)

    return list(all_params)


def normalize_comment(comment):
    """Normalize comment by removing trailing newline character.

    Proxmox stores comments with a trailing newline character (\n).
    This function removes it for consistent comparison.
    """
    if comment is None:
        return None
    if isinstance(comment, str):
        return comment.rstrip("\n")
    return comment


def get_api_name(param_name):
    """Get the API parameter name for a given Ansible parameter name."""
    api_name_mapping = get_api_name_mapping()
    if param_name in api_name_mapping:
        return api_name_mapping[param_name]
    return param_name


def get_ansible_name(api_param_name):
    """Get the Ansible parameter name for a given API parameter name."""
    api_name_mapping = get_api_name_mapping()
    read_only_params = get_read_only_params()

    # Check regular API name mappings first
    for param_name, api_name in api_name_mapping.items():
        if api_name == api_param_name:
            return param_name

    # Check read-only parameters
    for param_name, param_info in read_only_params.items():
        if param_info["api_name"] == api_param_name:
            return param_name

    return api_param_name


def get_ansible_argument_spec():
    """Get network arguments for AnsibleModule."""
    return get_network_args()


def get_network_args():
    """Get network-specific arguments."""
    return dict(
        node=dict(type="str", required=True),
        state=dict(
            type="str",
            choices=["present", "absent", "apply", "revert"],
            default="present",
        ),
        iface=dict(type="str"),
        iface_type=dict(
            type="str",
            choices=[
                "bridge",
                "bond",
                "eth",
                "vlan",
                "OVSBridge",
                "OVSBond",
                "OVSIntPort",
            ],
        ),
        # Common parameters (all interface types)
        cidr=dict(type="str"),
        gateway=dict(type="str"),
        cidr6=dict(type="str"),
        gateway6=dict(type="str"),
        autostart=dict(type="bool"),
        comments=dict(type="str"),
        mtu=dict(type="int"),
        # Bridge specific parameters
        bridge_ports=dict(type="str"),
        bridge_vids=dict(type="str"),
        bridge_vlan_aware=dict(type="bool"),
        # Bond specific parameters
        bond_primary=dict(type="str"),
        bond_mode=dict(
            type="str",
            choices=[
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
        ),
        bond_xmit_hash_policy=dict(
            type="str",
            choices=["layer2", "layer2+3", "layer3+4"],
        ),
        slaves=dict(type="str"),
        # VLAN specific parameters
        vlan_raw_device=dict(type="str"),
        # OVS specific parameters
        ovs_ports=dict(type="str"),
        ovs_options=dict(type="str"),
        ovs_bonds=dict(type="str"),
        ovs_bridge=dict(type="str"),
        ovs_tag=dict(type="int"),
    )


def get_interface_type_mapping():
    """Get mapping of parameters to interface types for validation."""
    return {
        "cidr": ["eth", "bridge", "bond", "vlan", "OVSBridge", "OVSIntPort"],
        "gateway": ["eth", "bridge", "bond", "vlan", "OVSBridge", "OVSIntPort"],
        "cidr6": ["eth", "bridge", "bond", "vlan", "OVSBridge", "OVSIntPort"],
        "gateway6": ["eth", "bridge", "bond", "vlan", "OVSBridge", "OVSIntPort"],
        "autostart": ["eth", "bridge", "bond", "vlan", "OVSBridge"],
        "comments": [
            "eth",
            "bridge",
            "bond",
            "vlan",
            "OVSBridge",
            "OVSBond",
            "OVSIntPort",
        ],
        "mtu": ["eth", "bridge", "bond", "vlan", "OVSBridge", "OVSBond", "OVSIntPort"],
        "bridge_ports": ["bridge"],
        "bridge_vids": ["bridge"],
        "bridge_vlan_aware": ["bridge"],
        "bond_primary": ["bond"],
        "bond_mode": ["bond", "OVSBond"],
        "bond_xmit_hash_policy": ["bond"],
        "slaves": ["bond"],
        "vlan_raw_device": ["vlan"],
        "ovs_ports": ["OVSBridge"],
        "ovs_options": ["OVSBridge", "OVSBond", "OVSIntPort"],
        "ovs_bonds": ["OVSBond"],
        "ovs_bridge": ["OVSBond", "OVSIntPort"],
        "ovs_tag": ["OVSBond", "OVSIntPort"],
    }


def get_api_name_mapping():
    """Get mapping of Ansible parameter names to API parameter names."""
    return {
        "iface_type": "type",
        "bond_primary": "bond-primary",
        "vlan_raw_device": "vlan-raw-device",
    }


def get_read_only_params():
    """Get list of read-only parameters that are only present in API responses."""
    return {
        "active": {"api_name": "active", "type": "bool"},
        "vlan_id": {"api_name": "vlan-id", "type": "int"},
        "exists": {"api_name": "exists", "type": "bool"},
    }


def get_param_type(param_name):
    """Get the type of a parameter (regular or read-only)."""
    network_args = get_network_args()
    read_only_params = get_read_only_params()

    # Check regular parameters first
    if param_name in network_args:
        return network_args[param_name].get("type")

    # Check read-only parameters
    if param_name in read_only_params:
        return read_only_params[param_name]["type"]

    return None


class ProxmoxNetworkManager(ProxmoxAnsible):
    """Manages Proxmox network interfaces."""

    def __init__(self, module):
        super(ProxmoxNetworkManager, self).__init__(module)
        self.params = module.params
        self.node = self.params["node"]

    def validate_common_params(self):
        """Validate common parameters."""
        errors = []

        # Validate MTU if provided
        if self.params.get("mtu") is not None:
            try:
                mtu = int(self.params["mtu"])
                if not (1280 <= mtu <= 65520):
                    errors.append("MTU must be between 1280 and 65520")
            except (ValueError, TypeError):
                errors.append("MTU must be an integer")

        # Validate CIDR format if provided
        if self.params.get("cidr"):
            if not self._is_valid_cidr(self.params["cidr"]):
                errors.append("Invalid IPv4 CIDR format")

        if self.params.get("cidr6"):
            if not self._is_valid_cidr6(self.params["cidr6"]):
                errors.append("Invalid IPv6 CIDR format")

        return errors

    def validate_bridge_params(self):
        """Validate bridge-specific parameters."""
        errors = []

        # bridge_ports is optional
        # bridge_vlan_aware is optional boolean

        # bridge_vids should not be defined if bridge_vlan_aware is not set or false
        if self.params.get("bridge_vids") is not None:
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
            # Validate bond_mode is one of the valid modes for regular bonds
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

        # Validate bond_mode specific requirements
        bond_mode = self.params.get("bond_mode")
        if bond_mode == "active-backup":
            if not self.params.get("bond_primary"):
                errors.append("bond_primary is required for active-backup mode")
            else:
                # bond_primary should be included in slaves for active-backup mode
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

        # bond_primary should not be defined if bond_mode is not active-backup
        if self.params.get("bond_primary") is not None and bond_mode != "active-backup":
            errors.append(
                "bond_primary should not be defined if bond_mode is not active-backup"
            )

        # bond_xmit_hash_policy should not be defined if bond_mode is not balance-xor or 802.3ad
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
        # Check for both VLAN formats: eth0.100 and vlan100 (but not vlan.100)
        if not (
            re.match(r"^(?!vlan\.)[a-zA-Z0-9_-]+\.\d+$", iface)
            or re.match(r"^vlan\d+$", iface)
        ):
            errors.append(
                "VLAN iface must be in format 'string.digit' (e.g., 'eth0.100') or 'vlanXX' (e.g., 'vlan100')"
            )
        else:
            # Extract VLAN ID
            try:
                if iface.startswith("vlan"):
                    vlan_id = int(iface[4:])  # Remove 'vlan' prefix
                else:
                    vlan_id = int(iface.split(".")[-1])  # Get part after dot
                if not (1 <= vlan_id <= 4094):
                    errors.append("VLAN ID must be between 1 and 4094")
            except (ValueError, TypeError):
                errors.append("VLAN ID must be a valid integer")

            # vlan_raw_device should be defined if iface is like vlanxx, otherwise should not be defined
            if iface.startswith("vlan"):
                if not self.params.get("vlan_raw_device"):
                    errors.append(
                        "vlan_raw_device is required when iface starts with 'vlan'"
                    )
            else:
                if self.params.get("vlan_raw_device") is not None:
                    errors.append(
                        "vlan_raw_device should not be defined when iface does not start with 'vlan'"
                    )

        return errors

    def validate_ovs_bridge_params(self):
        """Validate OVS bridge parameters."""
        errors = []

        # ovs_ports and ovs_options are optional

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

        # Validate ovs_tag if provided
        if self.params.get("ovs_tag") is not None:
            try:
                ovs_tag = int(self.params["ovs_tag"])
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

        # Validate ovs_tag if provided
        if self.params.get("ovs_tag") is not None:
            try:
                ovs_tag = int(self.params["ovs_tag"])
                if not (1 <= ovs_tag <= 4094):
                    errors.append("ovs_tag must be between 1 and 4094")
            except (ValueError, TypeError):
                errors.append("ovs_tag must be an integer")

        return errors

    def validate_params(self):
        """Validate all parameters based on interface type."""
        errors = []

        # Step 1: State-specific validation (basic requirements)
        state = self.params.get("state", "present")
        if state == "present":
            if not self.params.get("iface"):
                errors.append("iface is required when state is present")
            if not self.params.get("iface_type"):
                errors.append("iface_type is required when state is present")
        elif state == "absent":
            if not self.params.get("iface"):
                errors.append("iface is required when state is absent")

        # Step 2: Validate parameter combinations (which parameters are allowed together)
        errors.extend(self.validate_parameter_combinations())

        # If there are combination errors, return early - don't validate values
        if errors:
            return errors

        # Step 3: Validate parameter values (only if combinations are valid)
        errors.extend(self.validate_common_params())

        # Type-specific value validation
        iface_type = self.params.get("iface_type")
        if iface_type:
            if iface_type == "bridge":
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

    def validate_parameter_combinations(self):
        """Validate parameter combinations based on interface type."""
        errors = []
        iface_type = self.params.get("iface_type")

        if not iface_type:
            return errors

        # Get all parameters that are set (not None)
        set_params = [key for key, value in self.params.items() if value is not None]

        # Get valid parameters for this interface type
        allowed_params = get_params_for_interface_type(iface_type)

        # Define parameters that should always be allowed (authentication, common, etc.)
        always_allowed_params = [
            "state",
            "iface",
            "iface_type",
            "node",
            "api_host",
            "api_user",
            "api_password",
            "api_token_id",
            "api_token_secret",
            "validate_certs",
        ]

        # Find invalid parameters
        invalid_params = [
            param
            for param in set_params
            if param not in allowed_params and param not in always_allowed_params
        ]

        if invalid_params:
            errors.append(
                f"Parameters {', '.join(invalid_params)} are not valid for interface type '{iface_type}'"
            )

        return errors

    def _is_valid_cidr(self, cidr):
        """Validate IPv4 CIDR format."""
        pattern = r"^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$"
        return bool(re.match(pattern, cidr))

    def _is_valid_cidr6(self, cidr):
        """Validate IPv6 CIDR format."""
        pattern = r"^[0-9a-fA-F:]+/\d{1,3}$"
        return bool(re.match(pattern, cidr))

    def _is_eth_interface_deleted(self, interface):
        """Check if an eth interface is considered deleted (inactive)."""
        # For eth interfaces, check if they are actually active/deleted
        has_priority = "priority" in interface
        autostart = interface.get("autostart", False)
        active = interface.get("active", False)

        # If no priority, autostart is false, and active is false, consider it deleted
        return not has_priority and not autostart and not active

    def check_network_changes(self):
        """Check if there are pending network configuration changes.

        This is a workaround for the proxmoxer module which doesn't provide
        access to the 'changes' field in the API response. We use a direct
        HTTP request to access this field for idempotency checks.
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
            # Convert parameter names from API format to Ansible format
            converted_interfaces = []
            for interface in interfaces:
                converted_interface = {}
                for key, value in interface.items():
                    converted_key = get_ansible_name(key)
                    # Normalize comments (remove trailing newline)
                    if converted_key == "comments" and isinstance(value, str):
                        value = normalize_comment(value)
                    # Convert boolean values from Proxmox format (0/1) to Ansible format (True/False)
                    elif isinstance(value, int) and value in [0, 1]:
                        # Check if this parameter is defined as boolean in our argument spec
                        param_type = get_param_type(converted_key)
                        if param_type == "bool":
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
            # Interface exists, check if update is needed
            differences = self._get_differences(current_config)
            if differences:
                # Changes needed
                if not self.module.check_mode:
                    self.update_interface()
                    # Get fresh data from server after update
                    updated_config = self.get_interface_config()
                    msg = f"Interface {iface} updated successfully"
                    after_config = updated_config
                    before_config = (
                        current_config  # Use full server response for non-check mode
                    )
                else:
                    # In check mode, use user-provided config for "after" state
                    after_config = self._build_interface_config()
                    # For check mode, filter current_config to only include user-defined parameters
                    before_config = self._filter_config_to_user_params(current_config)
                    msg = f"Interface {iface} would be updated"

                return {
                    "changed": True,
                    "msg": msg,
                    "interface": after_config,
                    "diff": self._format_diff(before_config, after_config, iface),
                }
            else:
                # No changes needed
                return {
                    "changed": False,
                    "msg": f"Interface {iface} already exists with correct configuration",
                    "interface": current_config,
                }
        else:
            # Interface doesn't exist, create it
            if not self.module.check_mode:
                self.create_interface()
                # Get fresh data from server after creation
                created_config = self.get_interface_config()
                msg = f"Interface {iface} created successfully"
            else:
                # In check mode, return what we would create
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

        # Special handling for eth interfaces
        if iface_type == "eth" and current_config:
            # For eth interfaces, check if they are actually deleted (inactive)
            if self._is_eth_interface_deleted(current_config):
                # Interface is already deleted (inactive)
                return {"changed": False, "msg": f"Interface {iface} does not exist"}

        if current_config:
            # Interface exists, delete it
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
            # Interface doesn't exist
            return {"changed": False, "msg": f"Interface {iface} does not exist"}

    def _handle_apply_state(self):
        """Handle apply state."""
        if self.module.check_mode:
            # In check mode, always report that apply would make changes
            return {
                "changed": True,
                "msg": "Staged network configuration changes may be applied",
            }

        # Check if there are pending changes to apply
        changes = self.check_network_changes()

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
            # In check mode, always report that revert would make changes
            return {
                "changed": True,
                "msg": "Staged network configuration changes may be reverted",
            }

        # Check if there are pending changes to revert
        changes = self.check_network_changes()

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

        # Add iface for creation
        if self.params.get("iface"):
            data["iface"] = self.params.get("iface")

        # Add type for creation and updates
        if self.params.get("iface_type"):
            data["type"] = self.params.get("iface_type")

        # Add all parameters that are set
        for param_name in get_all_valid_params():
            if self.params.get(param_name) is not None:
                value = self.params.get(param_name)

                # Convert boolean values to Proxmox format (0/1)
                if isinstance(value, bool):
                    value = ansible_to_proxmox_bool(value)

                # Convert parameter name to API format
                api_param_name = get_api_name(param_name)
                data[api_param_name] = value

        return data

    def _get_differences(self, current_config):
        """Get differences between current and desired configuration."""
        differences = []

        # Check if interface type is being changed (not allowed)
        current_type = current_config.get("type")
        desired_type = self.params.get("iface_type")
        if current_type and desired_type and current_type != desired_type:
            self.module.fail_json(
                msg=f"Cannot change interface type from '{current_type}' to '{desired_type}'. "
                f"Interface type cannot be modified after creation. "
                f"Delete the interface and recreate it with the desired type."
            )

        # Get all parameters that are set by the user
        for param_name in get_all_valid_params():
            if self.params.get(param_name) is not None:
                current_value = current_config.get(param_name)
                desired_value = self.params.get(param_name)

                # Handle boolean conversion for comparison
                if isinstance(desired_value, bool):
                    # Convert current value from Proxmox format (0/1) to Ansible format (True/False)
                    if current_value in [0, 1]:
                        current_value = proxmox_to_ansible_bool(current_value)
                    # Convert desired value to Proxmox format for comparison
                    desired_value_proxmox = ansible_to_proxmox_bool(desired_value)
                    if current_value != desired_value_proxmox:
                        differences.append(
                            {
                                "parameter": param_name,
                                "current": current_value,
                                "desired": desired_value,
                            }
                        )
                elif param_name == "comments":
                    # Handle comment normalization (remove trailing newline from Proxmox)
                    current_value_normalized = normalize_comment(current_value)
                    if current_value_normalized != desired_value:
                        differences.append(
                            {
                                "parameter": param_name,
                                "current": current_value_normalized,
                                "desired": desired_value,
                            }
                        )
                else:
                    # Handle order-independent parameters (interfaces in bridges/bonds, VLAN IDs)
                    if param_name in [
                        "bridge_ports",
                        "slaves",
                        "ovs_ports",
                        "ovs_bonds",
                        "bridge_vids",
                    ]:
                        # Split into sets and compare (order doesn't matter)
                        current_values = (
                            set(str(current_value).split()) if current_value else set()
                        )
                        desired_values = (
                            set(str(desired_value).split()) if desired_value else set()
                        )

                        if current_values != desired_values:
                            differences.append(
                                {
                                    "parameter": param_name,
                                    "current": current_value,
                                    "desired": desired_value,
                                }
                            )
                    else:
                        # Simple string comparison for other parameters
                        if str(current_value) != str(desired_value):
                            differences.append(
                                {
                                    "parameter": param_name,
                                    "current": current_value,
                                    "desired": desired_value,
                                }
                            )

        return differences

    def _format_diff(self, before_config, after_config, iface):
        """Format configuration differences in YAML format for Ansible diff.

        Args:
            before_config: Configuration before changes (dict or None)
            after_config: Configuration after changes (dict or None)
            iface: Interface name for headers
        """
        # Determine operation type
        is_create = before_config is None and after_config is not None
        is_delete = before_config is not None and after_config is None

        if is_create:
            # For create operations, just show the interface name
            diff_entry = {
                "after": yaml_dump(after_config, default_flow_style=False, indent=2),
                "after_header": iface,
                "before": None,
            }
        elif is_delete:
            # For delete operations, just show the interface name
            diff_entry = {
                "before": yaml_dump(before_config, default_flow_style=False, indent=2),
                "before_header": iface,
                "after": None,
            }
        else:
            # For update operations, show before/after states
            diff_entry = {
                "before": yaml_dump(before_config, default_flow_style=False, indent=2),
                "after": yaml_dump(after_config, default_flow_style=False, indent=2),
                "before_header": iface,
                "after_header": iface,
            }

        return [diff_entry]

    def _filter_config_to_user_params(self, config):
        """Filter configuration to only include parameters that the user has defined.

        Args:
            config: Full configuration from server response

        Returns:
            dict: Filtered configuration with only user-defined parameters
        """
        if config is None:
            return None

        filtered_config = {}

        # Always include iface and iface_type if they exist in the config
        if "iface" in config:
            filtered_config["iface"] = config["iface"]
        if "iface_type" in config:
            filtered_config["iface_type"] = config["iface_type"]

        # Get all parameters that the user has set
        for param_name in get_all_valid_params():
            if self.params.get(param_name) is not None:
                # Only include if the parameter exists in the current config
                if param_name in config:
                    filtered_config[param_name] = config[param_name]

        return filtered_config

    def _build_interface_config(self):
        """Build interface configuration dictionary."""
        config = {
            "iface": self.params.get("iface"),
            "iface_type": self.params.get("iface_type"),
        }

        # Add all parameters that are set, with proper boolean handling
        for param_name in get_all_valid_params():
            if self.params.get(param_name) is not None:
                value = self.params.get(param_name)

                # Convert boolean values to Proxmox format (0/1) for consistency
                if isinstance(value, bool):
                    value = ansible_to_proxmox_bool(value)

                # Normalize comments for return data (remove trailing newline)
                if param_name == "comments" and isinstance(value, str):
                    value = normalize_comment(value)

                config[param_name] = value

        return config


def main():
    """Main function."""
    module_args = proxmox_auth_argument_spec()
    network_args = get_ansible_argument_spec()
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
