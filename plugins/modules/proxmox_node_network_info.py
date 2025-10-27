#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, aleskxyz <aleskxyz@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: proxmox_node_network_info
short_description: Retrieve information about Proxmox VE node network interfaces
version_added: "1.4.0"
description:
  - Retrieve information about network interfaces on Proxmox VE nodes.
  - This module does not make any changes to the system.
author: "aleskxyz (@aleskxyz)"
options:
  node:
    description:
      - The Proxmox node to retrieve network interface information from.
    type: str
    required: true
  iface:
    description:
      - Name of a specific network interface to retrieve information for.
      - If not specified, information for all interfaces will be returned.
    type: str
    required: false
  iface_type:
    description:
      - Filter results by interface type.
    type: str
    choices: ['bridge', 'bond', 'eth', 'vlan', 'OVSBridge', 'OVSBond', 'OVSPort', 'OVSIntPort']
    required: false
  check_changes:
    description:
      - Whether to check for pending network configuration changes.
      - When enabled, the module will return only information about any staged changes that are waiting to be applied.
      - When disabled (default), the module will return network interface information.
      - This parameter cannot be used together with C(iface) or C(iface_type) parameters, as checking for pending changes is a node-level operation.
    type: bool
    default: false
    required: false
seealso:
  - module: community.proxmox.proxmox_node_network
    description: Manage network interfaces on Proxmox nodes.
  - name: Proxmox Network Configuration
    description: Proxmox VE network configuration documentation.
    link: "https://pve.proxmox.com/wiki/Network_Configuration"
  - name: Proxmox API Documentation
    description: Proxmox VE API documentation.
    link: "https://pve.proxmox.com/pve-docs/api-viewer/index.html#/nodes/{node}/network"
attributes:
  check_mode:
    support: full
    details: Check mode is fully supported.
  diff_mode:
    support: none
    details: This is an info module and does not make changes.
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module
"""

EXAMPLES = r"""
- name: Get all network interfaces on a node
  community.proxmox.proxmox_node_network_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve01

- name: Get information about a specific network interface
  community.proxmox.proxmox_node_network_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve01
    iface: vmbr0

- name: Get all bridge interfaces on a node
  community.proxmox.proxmox_node_network_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve01
    iface_type: bridge

- name: Check only for pending changes
  community.proxmox.proxmox_node_network_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve01
    check_changes: true
"""

RETURN = r"""
proxmox_node_networks:
  description: List of network interfaces on the node
  returned: success, when check_changes is false or not specified
  type: list
  elements: dict
  sample: [
    {
      "iface": "vmbr0",
      "type": "bridge",
      "active": true,
      "autostart": true,
      "bridge_ports": "eth0",
      "cidr": "192.168.1.1/24",
      "address": "192.168.1.1",
      "netmask": "255.255.255.0",
      "gateway": "192.168.1.254",
      "mtu": 1500,
      "method": "static",
      "families": ["inet"],
      "exists": true
    },
    {
      "iface": "bond0",
      "type": "bond",
      "active": true,
      "autostart": true,
      "slaves": "eth1 eth2",
      "bond_mode": "active-backup",
      "bond-primary": "eth1",
      "mtu": 1500,
      "method": "manual",
      "families": ["inet"],
      "exists": true
    }
  ]
pending_changes:
  description: Pending network configuration changes
  returned: success, when check_changes is true
  type: str
  sample: |
    --- /etc/network/interfaces
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
    +        bridge_ports eth1
has_pending_changes:
  description: Whether there are any pending network configuration changes
  returned: success, when check_changes is true
  type: bool
  sample: true
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    proxmox_auth_argument_spec,
    ProxmoxAnsible,
    proxmox_to_ansible_bool,
)


def main():
    module_args = proxmox_auth_argument_spec()
    module_args.update(
        node=dict(type="str", required=True),
        iface=dict(type="str", required=False),
        iface_type=dict(
            type="str",
            required=False,
            choices=[
                "bridge",
                "bond",
                "eth",
                "vlan",
                "OVSBridge",
                "OVSBond",
                "OVSPort",
                "OVSIntPort",
            ],
        ),
        check_changes=dict(type="bool", default=False, required=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    proxmox = ProxmoxNodeNetworkInfoAnsible(module)
    result = proxmox.run()
    module.exit_json(**result)


class ProxmoxNodeNetworkInfoAnsible(ProxmoxAnsible):
    def check_network_changes(self, node):
        """Check if there are pending network configuration changes.

        This is a workaround for the proxmoxer module which doesn't provide
        access to the 'changes' field in the API response. We use a direct
        HTTP request to access this field for idempotency checks.
        """
        try:
            resp = self.proxmox_api._store["session"].request(
                "GET", f"{self.proxmox_api._store['base_url']}/nodes/{node}/network"
            )
            resp.raise_for_status()
            changes = resp.json().get("changes", None)
            return changes
        except Exception as e:
            self.module.fail_json(
                msg=f"Failed to check network changes for node {node}: {to_native(e)}",
                exception=traceback.format_exc(),
            )

    def convert_boolean_values(self, network_data):
        """Convert boolean values from Proxmox format (0/1) to Ansible format (True/False)."""
        # List of known boolean fields in network interface data
        boolean_fields = ["active", "autostart", "bridge_vlan_aware", "exists"]

        converted_data = {}
        for key, value in network_data.items():
            if key in boolean_fields and isinstance(value, int) and value in [0, 1]:
                converted_data[key] = proxmox_to_ansible_bool(value)
            else:
                converted_data[key] = value

        return converted_data

    def run(self):
        node = self.module.params["node"]
        iface = self.module.params.get("iface")
        iface_type = self.module.params.get("iface_type")
        check_changes = self.module.params.get("check_changes")
        result = dict(changed=False)

        # Validate parameter combinations
        if check_changes and (iface or iface_type):
            self.module.fail_json(
                msg="check_changes cannot be used with iface or iface_type parameters. "
                "Checking for pending changes is a node-level operation that applies to all network interfaces."
            )

        # Validate node exists
        try:
            node_info = self.get_node(node)
            if not node_info:
                self.module.fail_json(
                    msg=f"Node '{node}' not found in the Proxmox cluster"
                )
        except Exception as e:
            self.module.fail_json(
                msg=f"Failed to validate node '{node}': {to_native(e)}",
                exception=traceback.format_exc(),
            )

        try:
            # Check for pending changes if requested
            if check_changes:
                pending_changes = self.check_network_changes(node)
                result["pending_changes"] = pending_changes
                result["has_pending_changes"] = (
                    pending_changes is not None and len(pending_changes.strip()) > 0
                )
                return result

            # Get all interfaces or filter by type using API parameter
            if iface_type:
                networks = self.proxmox_api.nodes(node).network.get(type=iface_type)
            else:
                networks = self.proxmox_api.nodes(node).network.get()

            # Convert boolean values for each network interface
            converted_networks = []
            for network in networks:
                converted_network = self.convert_boolean_values(network)
                converted_networks.append(converted_network)

            if iface:
                # Search for interface by name
                converted_networks = [
                    network
                    for network in converted_networks
                    if network["iface"] == iface
                ]

            result["proxmox_node_networks"] = converted_networks

        except Exception as e:
            if iface:
                self.module.fail_json(
                    msg=f"Failed to retrieve information for interface '{iface}' on node '{node}': {to_native(e)}",
                    exception=traceback.format_exc(),
                )
            else:
                self.module.fail_json(
                    msg=f"Failed to retrieve network interfaces from node '{node}': {to_native(e)}",
                    exception=traceback.format_exc(),
                )

        return result


if __name__ == "__main__":
    main()
