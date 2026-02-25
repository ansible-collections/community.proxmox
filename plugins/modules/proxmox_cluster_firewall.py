#!/usr/bin/python

# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_cluster_firewall
short_description: Cluster-level firewall options management for Proxmox VE cluster
version_added: "1.6.0"
author:
  - Clément Cruau (@PendaGTP)
description:
  - Manage firewall options at the cluster level in Proxmox VE.
  - Enable or disable the firewall cluster-wide, set default policies, ebtables, and log ratelimiting.
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  state:
    description:
      - Enable or disable the firewall cluster-wide.
    choices:
      - enabled
      - disabled
    type: str
    default: disabled
  ebtables:
    description:
      - Enable ebtables rules cluster-wide.
    type: bool
    default: true
  input_policy:
    description:
      - Default policy for incoming traffic.
    choices:
      - ACCEPT
      - REJECT
      - DROP
    type: str
    default: DROP
  output_policy:
    description:
      - Default policy for outgoing traffic.
    choices:
      - ACCEPT
      - REJECT
      - DROP
    type: str
    default: ACCEPT
  forward_policy:
    description:
      - Default policy for forwarded traffic.
    choices:
      - ACCEPT
      - DROP
    type: str
    default: ACCEPT
  log_ratelimit:
    description:
      - Log ratelimiting settings.
    type: dict
    suboptions:
      enabled:
        description:
          - Enable or disable log ratelimiting.
        type: bool
        default: true
      burst:
        description:
          - Initial burst of packages which will always get logged before the rate is applied.
        type: int
        default: 5
      rate:
        description:
          - Frequency with which the burst bucket gets refilled.
          - Must match the pattern C([1-9][0-9]*/(second|minute|hour|day)), e.g. C(1/second).
        type: str
        default: 1/second

seealso:
  - name: Proxmox VE Firewall configuration
    description: Complete reference of Proxmox VE Firewall
    link: https://pve.proxmox.com/pve-docs/chapter-pve-firewall.html

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Set cluster-wide firewall options
  community.proxmox.proxmox_cluster_firewall:
    state: enabled
    ebtables: true
    input_policy: DROP
    output_policy: ACCEPT
    forward_policy: ACCEPT
    log_ratelimit:
      enabled: false
      burst: 10
      rate: 5/second

- name: Block ingress and allow egress traffic
  community.proxmox.proxmox_cluster_firewall:
    state: enabled
    ebtables: true
    input_policy: DROP
    output_policy: ACCEPT
    forward_policy: ACCEPT

- name: Set cluster-wide firewall ratelimiting options
  community.proxmox.proxmox_cluster_firewall:
    state: enabled
    ebtables: true
    log_ratelimit:
      enabled: false
      burst: 10
      rate: 5/second

- name: Disable cluster-wide firewall
  community.proxmox.proxmox_cluster_firewall:
    state: disabled
"""

RETURN = r"""
enabled:
  description: Whether the firewall is enabled cluster-wide.
  returned: on success
  type: bool
  sample: true
ebtables:
  description: Whether ebtables is enabled cluster-wide.
  returned: on success
  type: bool
  sample: false
input_policy:
  description: Default policy for incoming traffic.
  returned: on success
  type: str
  sample: DROP
output_policy:
  description: Default policy for outgoing traffic.
  returned: on success
  type: str
  sample: ACCEPT
forward_policy:
  description: Default policy for forwarded traffic.
  returned: on success
  type: str
  sample: ACCEPT
log_ratelimit:
  description: Log ratelimiting settings (when present in cluster options).
  returned: on success
  type: dict
  sample: {"enabled": true, "burst": 5, "rate": "1/second"}
msg:
  description: A short message on what the module did.
  returned: always
  type: str
  sample: "Cluster firewall options updated"
"""

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    ansible_to_proxmox_bool,
    proxmox_auth_argument_spec,
    proxmox_to_ansible_bool,
)

LOG_RATELIMIT_RATE_PATTERN = re.compile(r"^[1-9][0-9]*/(second|minute|hour|day)$")


def _validate_log_ratelimit_rate(rate):
    if rate is None:
        return True
    return bool(LOG_RATELIMIT_RATE_PATTERN.match(rate))


def _parse_log_ratelimit_string(value):
    """Parse Proxmox log_ratelimit string (e.g. enable=1,burst=5,rate=1/second) into a dict."""
    if not value or not isinstance(value, str):
        return None
    result = {}
    for raw_part in value.strip().split(","):
        part = raw_part.strip()
        if "=" not in part:
            continue
        key, val = part.split("=", 1)
        key = key.strip().lower()
        val = val.strip()
        if key == "enable":
            result["enabled"] = proxmox_to_ansible_bool(1 if val == "1" else 0)
        elif key == "burst":
            try:
                result["burst"] = int(val)
            except ValueError:
                pass
        elif key == "rate":
            result["rate"] = val
    return result


def _build_log_ratelimit_string(enabled, burst, rate):
    """Build a Proxmox log_ratelimit string (e.g. enable=1,burst=5,rate=1/second) from parts."""
    parts = []
    if enabled is not None:
        parts.append(f"enable={ansible_to_proxmox_bool(enabled)}")
    if burst is not None:
        parts.append(f"burst={int(burst)}")
    if rate is not None:
        parts.append(f"rate={rate}")
    return ",".join(parts) if parts else None


def _validate_args(module):
    lr = module.params.get("log_ratelimit")
    if not lr or lr.get("rate") is None:
        return
    lr_rate = lr["rate"]
    if not _validate_log_ratelimit_rate(lr_rate):
        module.fail_json(
            msg="log_ratelimit.rate must be a valid rate expression, e.g. '1/second'",
            rate=lr_rate,
        )


def _module_args():
    return dict(
        state=dict(choices=["enabled", "disabled"], default="disabled"),
        ebtables=dict(type="bool", default=True),
        input_policy=dict(type="str", choices=["ACCEPT", "REJECT", "DROP"], default="DROP"),
        output_policy=dict(type="str", choices=["ACCEPT", "REJECT", "DROP"], default="ACCEPT"),
        forward_policy=dict(type="str", choices=["ACCEPT", "DROP"], default="ACCEPT"),
        log_ratelimit=dict(
            type="dict",
            options=dict(
                enabled=dict(type="bool", default=True),
                burst=dict(type="int", default=5),
                rate=dict(type="str", default="1/second"),
            ),
        ),
    )


def _module_options():
    return dict(supports_check_mode=True)


def ansible_module():
    args = proxmox_auth_argument_spec()
    args.update(_module_args())
    module = AnsibleModule(argument_spec=args, **_module_options())
    _validate_args(module)
    return module


class ProxmoxClusterFirewallAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def run(self):
        self._apply()

    def _get_fw_options(self):
        try:
            return self.proxmox_api.cluster().firewall().options.get()
        except Exception as e:
            self.module.fail_json(msg=f"Failed to retrieve cluster firewall options: {to_native(e)}")

    def _current_to_ansible(self, current):
        """Translate a raw Proxmox API options dict into Ansible-format keys and types."""
        if not current:
            return {}

        out = {}
        if "enable" in current:
            out["enabled"] = proxmox_to_ansible_bool(current["enable"])
        if "ebtables" in current:
            out["ebtables"] = proxmox_to_ansible_bool(current["ebtables"])
        if "policy_in" in current:
            out["input_policy"] = current["policy_in"]
        if "policy_out" in current:
            out["output_policy"] = current["policy_out"]
        if "policy_forward" in current:
            out["forward_policy"] = current["policy_forward"]
        if "log_ratelimit" in current and current["log_ratelimit"]:
            out["log_ratelimit"] = _parse_log_ratelimit_string(current["log_ratelimit"])

        return out

    def _desired_ansible(self):
        """Build the desired state as an Ansible-format dict."""
        out = {
            "enabled": self.params["state"] == "enabled",
            "ebtables": self.params["ebtables"],
            "input_policy": self.params["input_policy"],
            "output_policy": self.params["output_policy"],
            "forward_policy": self.params["forward_policy"],
        }
        lr = self.params.get("log_ratelimit")
        if lr:
            out["log_ratelimit"] = {
                "enabled": lr["enabled"],
                "burst": lr["burst"],
                "rate": lr["rate"],
            }
        return out

    def _ansible_to_api_payload(self, desired):
        """Convert an Ansible-format desired dict to the API payload for PUT."""
        payload = {
            "enable": ansible_to_proxmox_bool(desired["enabled"]),
            "ebtables": ansible_to_proxmox_bool(desired["ebtables"]),
            "policy_in": desired["input_policy"],
            "policy_out": desired["output_policy"],
            "policy_forward": desired["forward_policy"],
        }
        lr = desired.get("log_ratelimit")
        if lr:
            log_ratelimit_str = _build_log_ratelimit_string(
                lr.get("enabled"),
                lr.get("burst"),
                lr.get("rate"),
            )
            if log_ratelimit_str:
                payload["log_ratelimit"] = log_ratelimit_str
        return payload

    def _fw_options_differ(self, current_ansible, desired_ansible):
        return any(current_ansible.get(key) != desired_value for key, desired_value in desired_ansible.items())

    def _apply(self):
        current = self._get_fw_options()
        current_ansible = self._current_to_ansible(current)
        desired = self._desired_ansible()

        if not self._fw_options_differ(current_ansible, desired):
            self.module.exit_json(
                changed=False,
                msg="Cluster firewall options already match desired state",
                **current_ansible,
            )

        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                msg="Cluster firewall options would be updated",
                **{**current_ansible, **desired},
            )

        payload = self._ansible_to_api_payload(desired)
        try:
            self.proxmox_api.cluster().firewall().options.put(**payload)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to set cluster firewall options: {to_native(e)}")

        updated = self._get_fw_options()
        result = self._current_to_ansible(updated)
        msg = "Cluster firewall options updated"
        self.module.exit_json(changed=True, msg=msg, **result)


def main():
    module = ansible_module()
    proxmox = ProxmoxClusterFirewallAnsible(module)

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f"An error occurred: {to_native(e)}")


if __name__ == "__main__":
    main()
