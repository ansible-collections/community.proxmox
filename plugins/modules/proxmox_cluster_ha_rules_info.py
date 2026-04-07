#!/usr/bin/python

# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
---
module: proxmox_cluster_ha_rules_info
short_description: Retrieve Proxmox VE HA rules
description:
  - Retreive Proxmox VE High Availability managed resources rules
version_added: 2.0.0
author: Clément Cruau (@PendaGTP)
options:
  rule:
    description:
      - Target by rule name.
    aliases: ["name"]
    type: str
  type:
    description:
      - Target rules by type.
    choices: ["node-affinity", "resource-affinity"]
    type: str
  resource:
    description:
      - Target rules affecting the specified resource.
    type: str
seealso:
  - module: community.proxmox.proxmox_cluster_ha_rules
    description: Management of HA rules
  - name: Proxmox HA rules configuration
    description:  Complete reference of Proxmox VE HA rules
    link: https://pve.proxmox.com/pve-docs/chapter-ha-manager.html#ha_manager_rules
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module
"""

EXAMPLES = r"""
- name: Get prefer-pve-001 HA rule
  community.proxmox.proxmox_cluster_ha_rules_info:
    rule: prefer-pve-001

- name: List HA rules
  community.proxmox.proxmox_cluster_ha_rules_info:

- name: List HA node-affinity rules
  community.proxmox.proxmox_cluster_ha_rules_info:
    type: node-affinity

- name: List HA resource-affinity rules
  community.proxmox.proxmox_cluster_ha_rules_info:
    type: resource-affinity

- name: List HA rules affected by a resource
  community.proxmox.proxmox_cluster_ha_rules_info:
    resource: vm:100

- name: List HA node-affinity rules affected by a resource
  community.proxmox.proxmox_cluster_ha_rules_info:
    type: node-affinity
    resource: vm:100
"""

RETURN = r"""
rules:
  description: HA rules
  returned: on success
  type: list
  elements: dict
  contains:
    rule:
      description: The name of the HA rule.
      returned: on success
      sample: prefer-pve-001
      type: str
    type:
      description: The HA rule type
      returned: on success
      sample: node-affinity
      type: str
    comment:
      description: A comment associated with the rule.
      returned: on success
      sample: Prefer pve-001 for these VMs
      type: str
    resources:
      description: A list of HA resource IDs that this rule applies to.
      returned: on success
      sample: [
        "vm:100",
        "ct:101"
      ]
      type: list
      elements: str
    nodes:
      description: A list of cluster node names and their priorities (if configured, otherwise only the node name is returned)
      returned: on success, when rule type is node-affinity
      sample: [
          "pve-001:1",
          "pve-002:2",
          "pve-003"
        ]
      type: list
      elements: str
    affinity:
      description: The affinity type
      returned: on success, when rule type is resource-affinity
      sample: positive
      type: str
    disable:
      description: Whether the HA rule is disabled.
      returned: on success
      sample: false
      type: bool
    strict:
      description: Whether the node affinity rule is strict.
      returned: on success, when rule type is node-affinity
      sample: false
      type: bool
    order:
      description: The rule position.
      returned: on success
      sample: 1
      type: int
"""


from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
    proxmox_to_ansible_bool,
)


def _normalize_rules(rules):
    rules = sorted(rules, key=lambda x: x["order"])
    for rule in rules:
        rule.pop("digest", None)
        rule["resources"] = rule.get("resources", "").split(",")
        rule["disable"] = proxmox_to_ansible_bool(rule.get("disable", 0))
        if rule["type"] == "node-affinity":
            rule["nodes"] = rule.get("nodes", "").split(",")
            rule["strict"] = proxmox_to_ansible_bool(rule.get("strict", 0))

    return rules


def module_args():
    return dict(
        rule=dict(type="str", aliases=["name"]),
        type=dict(type="str", choices=["node-affinity", "resource-affinity"]),
        resource=dict(type="str"),
    )


def module_options():
    return dict(
        mutually_exclusive=[("rule", "type"), ("rule", "resource")],
    )


class ProxmoxClusterHARuleInfoAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def _list(self, rule_type=None, resource=None):
        params = {}
        if rule_type:
            params["type"] = rule_type
        if resource:
            params["resource"] = resource
        try:
            rules = self.proxmox_api.cluster.ha.rules.get(**params)
            return _normalize_rules(rules)
        except Exception as e:
            self.module.fail_json(msg=f"An error occurred: {e}")

    def _get(self, rule):
        try:
            rule = self.proxmox_api.cluster.ha.rules(rule).get()
            return _normalize_rules([rule])
        except Exception as e:
            self.module.fail_json(msg=f"An error occurred: {e}")

    def run(self):
        rule = self.params.get("rule")
        rule_type = self.params.get("type")
        resource = self.params.get("resource")

        if rule:
            rules = self._get(rule)
        else:
            rules = self._list(rule_type, resource)

        return rules


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxClusterHARuleInfoAnsible(module)

    result = dict(changed=False)

    result["rules"] = proxmox.run()
    module.exit_json(**result)


if __name__ == "__main__":
    main()
