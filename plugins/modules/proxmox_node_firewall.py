#!/usr/bin/python

# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

DOCUMENTATION = r"""
module: proxmox_node_firewall
short_description: Node-level firewall options management for Proxmox VE cluster
version_added: "2.0.0"
author:
  - Clément Cruau (@PendaGTP)
description:
  - Manage firewall options at the node level in Proxmox VE.
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  state:
    description:
      - Enable or disable the firewall node-wide.
    choices:
      - enabled
      - disabled
    type: str
    default: enabled
  node_name:
    description:
      - Name of the node to configure the firewall on.
    type: str
    aliases: ["node"]
    required: true
  log_level_in:
    description:
      - Log level for incoming traffic.
    type: str
    choices:
      - emerg
      - alert
      - crit
      - err
      - warning
      - notice
      - info
      - debug
      - nolog
    default: nolog
  log_level_out:
    description:
      - Log level for outgoing traffic.
    type: str
    choices:
      - emerg
      - alert
      - crit
      - err
      - warning
      - notice
      - info
      - debug
      - nolog
    default: nolog
  log_level_forward:
    description:
      - Log level for fowarded traffic.
    type: str
    choices:
      - emerg
      - alert
      - crit
      - err
      - warning
      - notice
      - info
      - debug
      - nolog
    default: nolog
  ndp:
    description:
      - Enable NDP (Neighbor Discovery Protocol).
    type: bool
    default: true
  nftables:
    description:
      - Enable nftables based firewall.
    type: bool
    default: false
  nosmurfs:
    description:
      - Enable SMURFS filter.
    type: bool
    default: true
  smurf_log_level:
    description:
      - Log level for SMURFS filter.
    type: str
    choices:
      - emerg
      - alert
      - crit
      - err
      - warning
      - notice
      - info
      - debug
      - nolog
    default: nolog
  tcp_flags_log_level:
    description:
      - Log level for illegal TCP flags filter.
    type: str
    choices:
      - emerg
      - alert
      - crit
      - err
      - warning
      - notice
      - info
      - debug
      - nolog
    default: nolog
  tcpflags:
    description:
      - Filter illegal combinations of TCP flags.
    type: bool
    default: false
  nf_conntrack_allow_invalid:
    description: Allow invalid packets on connection tracking.
    type: bool
    default: false
  nf_conntrack_helpers:
    description:
      - Enable conntrack helpers for specific protocols.
    type: str
  nf_conntrack_max:
    description:
      - Maximum number of tracked connections.
      - Minimum value is 32768.
    type: int
    default: 262144
  nf_conntrack_tcp_timeout_established:
    description:
      - Conntrack established timeout in seconds.
      - Minimum value is 7875.
    type: int
    default: 432000
  nf_conntrack_tcp_timeout_syn_recv:
    description:
      - Conntrack syn recv timeout.
      - Values between 30 - 60.
    type: int
    default: 60
  protection_synflood:
    description:
      - Enable synflood protection.
    type: bool
    default: false
  protection_synflood_burst:
    description:
      - Synflood protection rate burst by IP source address.
    type: int
    default: 1000
  protection_synflood_rate:
    description:
      - Synflood protection rate syn/sec by IP source address.
    type: int
    default: 200


seealso:
  - name: Proxmox VE Firewall configuration
    description: Complete reference of Proxmox VE Firewall
    link: https://pve.proxmox.com/pve-docs/chapter-pve-firewall.html
  - name: Proxmox VE node-wide configuration
    description: Complete reference of Proxmox VE Firewall host configuration
    link: https://pve.proxmox.com/pve-docs/chapter-pve-firewall.html#pve_firewall_host_specific_configuration
  - module: community.proxmox.proxmox_node_firewall_info
  - module: community.proxmox.proxmox_cluster_firewall

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Configure traffic log level
  community.proxmox.proxmox_node_firewall:
    state: enabled
    node_name: pve-001
    log_level_in: alert
    log_level_out: alert
    log_level_forward: alert

- name: Disable node-wide firewall
  community.proxmox.proxmox_node_firewall:
    state: disabled
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

msg:
  description: A short message on what the module did.
  returned: always
  type: str
  sample: "Node firewall options updated"
"""

from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.errors import AnsibleValidationError

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
)
from ansible_collections.community.proxmox.plugins.module_utils.proxmox_node_firewall import (
    SCHEMA,
    node_firewall_options_to_ansible_result,
)


def _validate_nf_conntrack_max(value):
    MIN_VALUE = 32768
    if value is not None and value < MIN_VALUE:
        raise AnsibleValidationError(f"nf_conntrack_max must be greater than {MIN_VALUE}")


def _validate_nf_conntrack_tcp_timeout_syn_recv(value):
    MIN_VALUE = 30
    MAX_VALUE = 60
    if value is not None and (value < MIN_VALUE or value > MAX_VALUE):
        raise AnsibleValidationError(f"nf_conntrack_tcp_timeout_syn_recv must be between {MIN_VALUE} and {MAX_VALUE}")


def _validate_protection_synflood_burst(value):
    MIN_VALUE = 1000
    if value is not None and value < MIN_VALUE:
        raise AnsibleValidationError(f"protection_synflood_burst must be greater than {MIN_VALUE}")


def _validate_protection_synflood_rate(value):
    MIN_VALUE = 200
    if value is not None and value < MIN_VALUE:
        raise AnsibleValidationError(f"protection_synflood_rate must be greater than {MIN_VALUE}")


def module_args():
    return dict(
        state=dict(choices=["enabled", "disabled"], default="enabled"),
        node_name=dict(aliases=["node"], type="str", required=True),
        log_level_in=dict(
            type="str",
            choices=["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug", "nolog"],
            default="nolog",
        ),
        log_level_out=dict(
            type="str",
            choices=["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug", "nolog"],
            default="nolog",
        ),
        log_level_forward=dict(
            type="str",
            choices=["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug", "nolog"],
            default="nolog",
        ),
        ndp=dict(type="bool", default=True),
        nftables=dict(type="bool", default=False),
        nosmurfs=dict(type="bool", default=True),
        smurf_log_level=dict(
            type="str",
            choices=["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug", "nolog"],
            default="nolog",
        ),
        tcp_flags_log_level=dict(
            type="str",
            choices=["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug", "nolog"],
            default="nolog",
        ),
        tcpflags=dict(type="bool", default=False),
        nf_conntrack_allow_invalid=dict(type="bool", default=False),
        nf_conntrack_helpers=dict(type="str"),
        nf_conntrack_max=dict(type="int", default=262144),
        nf_conntrack_tcp_timeout_established=dict(type="int", default=432000),
        nf_conntrack_tcp_timeout_syn_recv=dict(type="int", default=60),
        protection_synflood=dict(type="bool", default=False),
        protection_synflood_burst=dict(type="int", default=1000),
        protection_synflood_rate=dict(type="int", default=200),
    )


def module_options():
    return {}


class ProxmoxNodeFirewallAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def run(self):
        self._ensure_state()

    def validate_params(self):
        try:
            _validate_nf_conntrack_max(self.params["nf_conntrack_max"])
            _validate_nf_conntrack_tcp_timeout_syn_recv(self.params["nf_conntrack_tcp_timeout_syn_recv"])
            _validate_protection_synflood_burst(self.params["protection_synflood_burst"])
            _validate_protection_synflood_rate(self.params["protection_synflood_rate"])
        except AnsibleValidationError as e:
            self.module.fail_json(msg=to_native(e))

    def _ensure_state(self):
        current_raw = self._fetch_firewall_options()
        current = self._format_options(current_raw)
        desired = self._build_desired()

        if not self._is_update_required(current, desired):
            self.module.exit_json(
                changed=False,
                msg="Node firewall options already match desired state",
                **current,
            )

        if self.module.check_mode:
            result = current.copy()
            result.update(desired)
            self.module.exit_json(
                changed=True,
                msg="Node firewall options would be updated",
                **result,
            )

        self._update_firewall(desired)

        updated_raw = self._fetch_firewall_options()
        updated = self._format_options(updated_raw)

        self.module.exit_json(
            changed=True,
            msg="Node firewall options updated",
            **updated,
        )

    def _is_update_required(self, current, desired):
        return any(current[k] != desired[k] for k in SCHEMA)

    def _update_firewall(self, desired):
        payload = self._build_params(desired)

        try:
            self.proxmox_api.nodes(self.params["node_name"]).firewall().options.put(**payload)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to set node firewall options: {to_native(e)}")

    def _fetch_firewall_options(self):
        try:
            return self.proxmox_api.nodes(self.params["node_name"]).firewall().options.get()
        except Exception as e:
            self.module.fail_json(msg=f"Failed to retrieve node firewall options: {to_native(e)}")

    def _build_desired(self):
        result = {
            "node_name": self.params["node_name"],
            "enabled": self.params["state"] == "enabled",
        }

        for field in SCHEMA:
            if field == "enabled":
                continue
            result[field] = self.params.get(field)

        return result

    def _build_params(self, desired):
        payload = {}

        for field, meta in SCHEMA.items():
            api_key = meta.get("api", field)
            value = desired.get(field)

            if value is None:
                continue

            if "to_api" in meta:
                value = meta["to_api"](value)

            payload[api_key] = value

        return payload

    def _format_options(self, raw):
        return node_firewall_options_to_ansible_result(self.params["node_name"], raw)


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxNodeFirewallAnsible(module)

    proxmox.validate_params()
    proxmox.run()


if __name__ == "__main__":
    main()
