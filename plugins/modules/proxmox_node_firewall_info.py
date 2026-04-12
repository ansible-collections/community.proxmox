#!/usr/bin/python

# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

DOCUMENTATION = r"""
module: proxmox_node_firewall_info
short_description: Get node-level firewall options for Proxmox VE cluster
version_added: "2.0.0"
author:
  - Clément Cruau (@PendaGTP)
description:
  - Get firewall options at the node level in Proxmox VE.
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  node_name:
    description:
      - Name of the node.
    type: str
    aliases: ["node"]
    required: true

seealso:
  - name: Proxmox VE Firewall configuration
    description: Complete reference of Proxmox VE Firewall
    link: https://pve.proxmox.com/pve-docs/chapter-pve-firewall.html
  - name: Proxmox VE node-wide configuration
    description: Complete reference of Proxmox VE Firewall host configuration
    link: https://pve.proxmox.com/pve-docs/chapter-pve-firewall.html#pve_firewall_host_specific_configuration
  - module: community.proxmox.proxmox_node_firewall
  - module: community.proxmox.proxmox_cluster_firewall

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Get node-wide firewall options
  community.proxmox.proxmox_node_firewall_info:
    node_name: pve-001
"""

RETURN = r"""
enabled:
  description: Whether the firewall is enabled node-wide.
  returned: on success
  type: bool
  sample: true
node_name:
  description: The name of the node.
  returned: on success
  type: str
  sample: pve-001
log_level_in:
  description: Log level setting for incoming traffic.
  returned: on success
  type: str
  sample: no_log
log_level_out:
  description: Log level setting for outgoing traffic.
  returned: on success
  type: str
  sample: no_log
log_level_forward:
  description: Log level setting for fowarded traffic.
  returned: on success
  type: str
  sample: no_log
ndp:
  description: Whether NDP (Neighbor Discovery Protocol) is enabled.
  returned: on success
  type: bool
  sample: true
nftables:
  description: Whether nftables based firewall is enabled.
  returned: on success
  type: bool
  sample: false
nosmurfs:
  description: Whether SMURFS filter is enabled.
  returned: on success
  type: bool
  sample: true
smurf_log_level:
  description: Log level setting for SMURFS filter.
  returned: on success
  type: str
tcp_flags_log_level:
  description: Log level setting for illegal TCP flags filter.
  returned: on success
  type: str
tcpflags:
  description: Whether illegal combinations of TCP flags are filtered.
  returned: on success
  type: bool
  sample: false
nf_conntrack_allow_invalid:
  description: Whether invalid packets are allowed on connection tracking.
  returned: on success
  type: bool
  sample: false
nf_conntrack_helpers:
  description: Conntrack helpers for specific protocols.
  returned: on success
  type: str
nf_conntrack_max:
  description: Maximum number of tracked connections.
  returned: on success
  type: int
  sample: 262144
nf_conntrack_tcp_timeout_established:
  description: Conntrack established timeout in seconds.
  returned: on success
  type: int
  sample: 432000
nf_conntrack_tcp_timeout_syn_recv:
  description: Conntrack syn recv timeout in seconds.
  returned: on success
  type: int
  sample: 60
protection_synflood:
  description: Whether synflood protection is enabled.
  returned: on success
  type: bool
  sample: false
protection_synflood_burst:
  description: Synflood protection rate burst by IP source address.
  returned: on success
  type: int
  sample: 1000
protection_synflood_rate:
  description: Synflood protection rate syn/sec by IP source address.
  returned: on success
  type: int
  sample: 200
"""

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
)
from ansible_collections.community.proxmox.plugins.module_utils.proxmox_node_firewall import (
    get_node_firewall_options_result,
)


def module_args():
    return dict(
        node_name=dict(aliases=["node"], type="str", required=True),
    )


def module_options():
    return {}


class ProxmoxNodeFirewallAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def run(self):
        current_raw = self._fetch_firewall_options()
        current = self._format_options(current_raw)
        self.module.exit_json(
            changed=False,
            **current,
        )

    def _fetch_firewall_options(self):
        try:
            return self.proxmox_api.nodes(self.params["node_name"]).firewall().options.get()
        except Exception as e:
            self.module.fail_json(msg=f"Failed to retrieve node firewall options: {to_native(e)}")

    def _format_options(self, raw):
        return get_node_firewall_options_result(self.params["node_name"], raw)


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxNodeFirewallAnsible(module)

    proxmox.run()


if __name__ == "__main__":
    main()
