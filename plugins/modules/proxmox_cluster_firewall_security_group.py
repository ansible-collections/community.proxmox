#!/usr/bin/python

# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

DOCUMENTATION = r"""
module: proxmox_cluster_firewall_security_group
short_description: Cluster firewall security group management for Proxmox VE
version_added: "2.0.0"
author:
  - Clément Cruau (@PendaGTP)
description:
  - Manage cluster-level firewall security groups in Proxmox VE.
  - Security groups hold ordered firewall rules that can be attached to guest rules.
  - If O(rules) is omitted when O(state=present), the module only creates the group and/or
    updates its comment; existing rules are not read or modified.
  - If O(rules) is set (including an empty list), the module synchronizes the full ordered
    ruleset, mapping list index 0 to position 0, etc.
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  state:
    description:
      - The desired state of the security group.
    type: str
    choices:
      - present
      - absent
    default: present
  name:
    description:
      - Security group name.
    type: str
    required: true
  comment:
    description:
      - Security group comment.
    type: str
  rules:
    description:
      - Full ordered list of firewall rules for the group, with index C(0) as position C(0), etc.
      - Omitted to manage only the group and comment, leaving current rules unchanged.
      - V([]) to remove all rules.
      - Optional rule fields (O(rules[].comment), O(rules[].dest), etc.) that are omitted in a rule
        entry are preserved from the existing rule on updates.
    type: list
    elements: dict
    suboptions:
      action:
        description:
          - Rule action (V(ACCEPT), V(DROP), V(REJECT), or a security group name if
            O(rules[].type) is V(group).
        type: str
        required: true
      type:
        description:
          - Rule direction or special type.
        type: str
        required: true
        choices:
          - in
          - out
          - forward
          - group
      comment:
        description:
          - Rule comment.
        type: str
      dest:
        description:
          - Match packet destination address.
            This can refer to a single IP address, an IP set ('+ipsetname') or an IP alias definition.
            You can also specify an address range like C(20.34.101.207-201.3.9.99),
            or a list of IP addresses and networks (entries are separated by comma).
            Please do not mix IPv4 and IPv6 addresses inside such lists.
        type: str
      dport:
        description:
          - Match TCP/UDP destination port.
            You can use service names or simple numbers V(0-65535), as defined in C(/etc/services).
            Port ranges can be specified with '\d+:\d+', for example V(80:85), and you can use comma separated list to match several ports or ranges.
        type: str
      enabled:
        description:
          - Whether the rule is active.
        type: bool
        default: true
      iface:
        description:
          - Network interface name.
        type: str
      log:
        description:
          - Log level for matching packets.
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
      macro:
        description:
          - Built-in firewall macro name.
          - Use predefined standard macro from https://pve.proxmox.com/pve-docs/pve-admin-guide.html#_firewall_macro_definitions
        type: str
      proto:
        description:
          - Match IP protocol (name or number per C(/etc/protocols)).
        type: str
      source:
        description:
          - Match packet source address.
            This can refer to a single IP address, an IP set ('+ipsetname') or an IP alias definition.
            You can also specify an address range like C(20.34.101.207-201.3.9.99),
            or a list of IP addresses and networks (entries are separated by comma).
            Please do not mix IPv4 and IPv6 addresses inside such lists.
        type: str
      sport:
        description:
          - Match TCP/UDP source port.
            You can use service names or simple numbers V(0-65535), as defined in C(/etc/services).
            Port ranges can be specified with '\d+:\d+', for example V(80:85), and you can use comma separated list to match several ports or ranges.
        type: str
      icmp_type:
        description:
          - ICMP type (when O(rules[].proto) is C(icmp) or C(icmpv6)/C(ipv6-icmp)).
        type: str

seealso:
  - name: Proxmox VE security group reference
    description: Security group reference for Proxmox VE Firewall
    link: https://pve.proxmox.com/pve-docs/chapter-pve-firewall.html#pve_firewall_security_groups
  - module: community.proxmox.proxmox_cluster_firewall
  - module: community.proxmox.proxmox_node_firewall
  - module: community.proxmox.proxmox_firewall

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.proxmox.attributes
"""

EXAMPLES = r"""
- name: Webserver security group
  community.proxmox.proxmox_cluster_firewall_security_group:
    name: webserver
    comment: Managed by Ansible
    rules:
      - type: in
        action: ACCEPT
        comment: Allow HTTP
        dest: 192.168.1.100
        dport: "80"
        proto: tcp
        log: info
      - type: in
        action: ACCEPT
        comment: Allow HTTPS
        dest: 192.168.1.100
        dport: "443"
        proto: tcp
        log: info
"""

RETURN = r"""
name:
  description: The security group name.
  returned: on success
  type: str
  sample: webserver
comment:
  description: The security group comment.
  returned: on success
  type: str
  sample: Managed by Ansible
rules:
  description: The security group rules.
  returned: on success, only if O(state=present) and O(rules) is set
  type: list
  elements: dict
  sample: []
msg:
  description: A short message on what the module did.
  returned: always
  type: str
  sample: "Security group web updated"
"""

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    ansible_to_proxmox_bool,
    create_proxmox_module,
    is_not_found_error,
    proxmox_to_ansible_bool,
)

_COMPARABLE_RULE_KEYS = {
    "action",
    "type",
    "comment",
    "dest",
    "dport",
    "enable",
    "iface",
    "log",
    "macro",
    "proto",
    "source",
    "sport",
    "icmp-type",
}

_COMPARE_OPTIONAL_KEYS = tuple(k for k in _COMPARABLE_RULE_KEYS if k not in ("action", "type", "enable"))


def _api_rule_to_ansible(r):
    """Map one API rule dict to Ansible-style keys (for return)."""
    if not r:
        return r
    out = {}
    for k, v in r.items():
        if k == "enable":
            out["enabled"] = proxmox_to_ansible_bool(v)
        elif k == "icmp-type":
            out["icmp_type"] = v
        else:
            out[k] = v
    return out


def _normalize_for_return(r):
    """Normalize a user-supplied Ansible rule dict for consistent return in check mode."""
    out = dict(r)
    out.setdefault("enabled", True)
    return out


_OPTIONAL_RULE_TO_API = {
    "comment": "comment",
    "dest": "dest",
    "dport": "dport",
    "iface": "iface",
    "log": "log",
    "macro": "macro",
    "proto": "proto",
    "source": "source",
    "sport": "sport",
    "icmp_type": "icmp-type",
}


def _build_create_rule_payload(desired_rule, position, group_name):
    payload = {
        "action": desired_rule["action"],
        "type": desired_rule["type"],
        "enable": ansible_to_proxmox_bool(desired_rule.get("enabled", True)),
    }
    for ansible_key, api_key in _OPTIONAL_RULE_TO_API.items():
        if desired_rule.get(ansible_key):
            payload[api_key] = desired_rule[ansible_key]
    if group_name:
        payload["group"] = group_name
    if position:
        payload["pos"] = position
    return {k: v for k, v in payload.items() if v or k == "enable"}


def _build_update_rule_payload(desired_rule, current_rule):
    """Build API body for updating an existing rule, seeding from current state."""
    payload = {}
    if current_rule:
        for k in _COMPARABLE_RULE_KEYS:
            if current_rule.get(k) is not None:
                payload[k] = current_rule[k]
    payload["action"] = desired_rule["action"]
    payload["type"] = desired_rule["type"]
    payload["enable"] = ansible_to_proxmox_bool(desired_rule.get("enabled", True))
    for ansible_key, api_key in _OPTIONAL_RULE_TO_API.items():
        if desired_rule.get(ansible_key) is not None:
            payload[api_key] = desired_rule[ansible_key]
    return {k: v for k, v in payload.items() if v is not None or k == "enable"}


def _normalize_compare_optional(key, value):
    if value is None or value == "":
        return None
    if key in ("dport", "sport") and isinstance(value, int):
        return str(value)
    return value


def _normalize_for_compare(api_rule):
    if not api_rule:
        return None
    action = api_rule.get("action")
    rtype = api_rule.get("type")
    out = {
        "action": action,
        "type": rtype,
        "enabled": proxmox_to_ansible_bool(api_rule.get("enable")),
    }
    for key in _COMPARE_OPTIONAL_KEYS:
        value = api_rule.get(key)
        normalized = _normalize_compare_optional(key, value)
        if normalized is None:
            continue
        out_key = "icmp_type" if key == "icmp-type" else key
        out[out_key] = normalized
    return out


def _rules_content_equal(a_api, b_api):
    return _normalize_for_compare(a_api) == _normalize_for_compare(b_api)


def _put_rule_payload(merged):
    return {k: v for k, v in merged.items() if k not in ("pos", "ipversion", "group")}


def _is_digest_conflict_error(exc):
    text = to_native(exc).lower()
    return "detected modified configuration" in text and "file changed by other user" in text


def _sort_rules(rules):
    return sorted(rules, key=lambda x: x["pos"])


def module_args():
    return dict(
        state=dict(choices=["present", "absent"], default="present"),
        name=dict(type="str", required=True),
        comment=dict(type="str", default=None),
        rules=dict(
            type="list",
            elements="dict",
            default=None,
            options=dict(
                action=dict(type="str", required=True),
                type=dict(type="str", required=True, choices=["in", "out", "forward", "group"]),
                comment=dict(type="str"),
                dest=dict(type="str"),
                dport=dict(type="str"),
                enabled=dict(type="bool", default=True),
                iface=dict(type="str"),
                log=dict(
                    type="str",
                    choices=["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug", "nolog"],
                ),
                macro=dict(type="str"),
                proto=dict(type="str"),
                source=dict(type="str"),
                sport=dict(type="str"),
                icmp_type=dict(type="str"),
            ),
        ),
    )


def module_options():
    return dict()


class ProxmoxClusterFirewallSecurityGroupAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def run(self):
        state = self.params["state"]
        name = self.params["name"]

        if state == "present":
            self._ensure_present(name)
        else:
            self._ensure_absent(name)

    def _ensure_present(self, name):
        existing = self._fetch_group(name)

        if existing is None:
            if self.module.check_mode:
                rules_param = self.params.get("rules")
                self.module.exit_json(
                    changed=True,
                    name=name,
                    msg=f"Security group {name} would be created",
                    comment=self.params.get("comment"),
                    rules=[_normalize_for_return(r) for r in rules_param] if rules_param is not None else None,
                )

            result = self._create(name, self.params.get("rules") or [])
            self.module.exit_json(**result)

        result = self._reconcile(name, existing)
        self.module.exit_json(**result)

    def _ensure_absent(self, name):
        existing = self._fetch_group(name)

        if existing is None:
            self.module.exit_json(
                changed=False,
                name=name,
                msg=f"Firewall security group {name} does not exist",
            )

        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                name=name,
                msg=f"Firewall security group {name} would be deleted",
            )

        result = self._delete(name)
        self.module.exit_json(**result)

    def _create(self, name, rules):
        self._create_group(name)
        self._create_rules(name, rules)
        rules_param = self.params.get("rules")
        fetched_rules = self._fetch_rules(name) if rules_param is not None else None
        result = self._build_present_result(name, self.params.get("comment"), fetched_rules)
        return {
            "changed": True,
            "msg": f"Firewall security group {name} successfully created",
            **result,
        }

    def _delete(self, name):
        self._delete_rules(name)
        self._delete_group(name)
        return {
            "changed": True,
            "name": name,
            "msg": f"Firewall security group {name} successfully deleted",
        }

    def _reconcile(self, name, existing):
        comment = self.params.get("comment")
        rules_param = self.params.get("rules")

        existing_comment = existing.get("comment") or ""
        need_comment = comment is not None and (existing_comment != (comment or ""))
        need_rules = rules_param is not None and self._rules_would_change(rules_param, name)
        will_change = need_comment or need_rules

        if self.module.check_mode:
            if not will_change:
                res = {
                    "changed": False,
                    "name": name,
                    "msg": f"Firewall security group {name} is already in desired state",
                }
                res["comment"] = existing.get("comment")
                if rules_param is not None:
                    res["rules"] = [_api_rule_to_ansible(x) for x in self._fetch_rules(name)]
                return res
            res = {
                "changed": True,
                "name": name,
                "msg": f"Firewall security group {name} would be updated",
                "comment": comment if comment is not None else existing.get("comment"),
            }
            if rules_param is not None:
                res["rules"] = [_normalize_for_return(r) for r in rules_param]
            return res

        changed = False
        if need_comment:
            self._update_group_comment(name, comment, existing)
            changed = True
        if need_rules:
            self._reconcile_rules(name, rules_param)
            changed = True

        actual_comment = comment if need_comment else existing.get("comment")
        fetched_rules = self._fetch_rules(name) if rules_param is not None else None
        result = self._build_present_result(name, actual_comment, fetched_rules)
        msg = (
            f"Firewall security group {name} successfully updated"
            if changed
            else f"Firewall security group {name} is already in desired state"
        )
        return {
            "changed": changed,
            "name": name,
            "msg": msg,
            **result,
        }

    def _build_present_result(self, name, comment, rules):
        out = {"name": name, "comment": comment}
        if rules is not None:
            out["rules"] = [_api_rule_to_ansible(x) for x in rules]
        return out

    def _create_group(self, name):
        try:
            self.proxmox_api.cluster().firewall().groups().post(**self._build_create_group_params())
        except Exception as e:
            self.module.fail_json(msg=f"Failed to create firewall security group {name}: {to_native(e)}")

    def _build_create_group_params(self):
        p = self.params
        payload = {"group": p["name"]}
        if p.get("comment"):
            payload["comment"] = p["comment"]
        return payload

    def _delete_group(self, name):
        try:
            self.proxmox_api.cluster().firewall().groups(name).delete()
        except Exception as e:
            self.module.fail_json(msg=f"Failed to delete firewall security group {name}: {to_native(e)}")

    def _update_group_comment(self, name, comment, existing):
        try:
            self.proxmox_api.cluster().firewall().groups().post(
                **self._build_update_group_comment_params(name, comment, existing)
            )
        except Exception as e:
            self.module.fail_json(msg=f"Failed to update firewall security group {name}: {to_native(e)}")

    def _build_update_group_comment_params(self, name, comment, existing):
        payload = {"group": name, "rename": name, "comment": comment}
        if existing.get("digest"):
            payload["digest"] = existing["digest"]
        return payload

    def _fetch_group(self, name):
        try:
            groups = self.proxmox_api.cluster().firewall().groups().get()
            return next((group for group in groups if group["group"] == name), None)
        except Exception as e:
            if is_not_found_error(e):
                return None
            self.module.fail_json(msg=f"Failed to read firewall security groups: {to_native(e)}")

    def _rules_would_change(self, desired, group_name):
        current = self._fetch_rules(group_name)
        if len(desired) != len(current):
            return True
        for i, d in enumerate(desired):
            want = _build_update_rule_payload(d, current[i])
            if not _rules_content_equal(want, current[i]):
                return True
        return False

    def _create_rules(self, name, desired):
        for i, rule in enumerate(desired):
            payload = _build_create_rule_payload(rule, i, name)
            try:
                self.proxmox_api.cluster().firewall().groups(name).post(**payload)
            except Exception as e:
                self.module.fail_json(msg=f"Failed to create firewall rule in security group {name}: {to_native(e)}")

    def _delete_rules(self, name):
        rules = self._fetch_rules(name)
        while rules:
            rule = max(rules, key=lambda r: r["pos"])
            digest = rule.get("digest")
            try:
                del_kw = {}
                if digest:
                    del_kw["digest"] = digest
                self.proxmox_api.cluster().firewall().groups(name)(rule["pos"]).delete(**del_kw)
            except Exception as e:
                self.module.fail_json(
                    msg=f"Failed to delete firewall rule in security group {name} at position {rule['pos']}: {to_native(e)}"
                )
            rules = self._fetch_rules(name)

    def _fetch_rules(self, name):
        try:
            rules = self.proxmox_api.cluster().firewall().groups(name).get()
            return _sort_rules(rules)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to read firewall rules for security group {name}: {to_native(e)}")

    def _reconcile_rules(self, name, desired):
        rules = self._prune_excess_rules(name, desired)
        self._update_rules_in_prefix(name, desired, rules)
        self._create_missing_trailing_rules(name, desired, rules)

    def _prune_excess_rules(self, name, desired):
        rules = self._fetch_rules(name)

        while len(rules) > len(desired):
            position = max(rule["pos"] for rule in rules)
            rule_at_pos = next(r for r in rules if r["pos"] == position)
            digest = rule_at_pos.get("digest")
            try:
                del_kw = {"pos": position}
                if digest:
                    del_kw["digest"] = digest
                self.proxmox_api.cluster().firewall().groups(name)(position).delete(**del_kw)
            except Exception as e:
                self.module.fail_json(
                    msg=f"Failed to delete firewall rule in security group {name} at position {position}: {to_native(e)}"
                )
            rules = self._fetch_rules(name)

        return rules

    def _update_rules_in_prefix(self, name, desired, rules):
        for i in range(min(len(desired), len(rules))):
            retries_left = 1
            while True:
                try:
                    current_rule = self.proxmox_api.cluster().firewall().groups(name)(i).get()
                    want = _build_update_rule_payload(desired[i], current_rule)
                    if current_rule.get("digest"):
                        want["digest"] = current_rule["digest"]
                    if _rules_content_equal(want, current_rule):
                        break
                    self.proxmox_api.cluster().firewall().groups(name)(i).put(**_put_rule_payload(want))
                    break
                except Exception as e:
                    if retries_left > 0 and _is_digest_conflict_error(e):
                        retries_left -= 1
                        continue
                    self.module.fail_json(
                        msg=f"Failed to update firewall rule in security group {name} at position {i}: {to_native(e)}"
                    )

    def _create_missing_trailing_rules(self, name, desired, rules):
        while len(rules) < len(desired):
            i = len(rules)
            body = _build_create_rule_payload(desired[i], i, name)
            try:
                self.proxmox_api.cluster().firewall().groups(name).post(**body)
            except Exception as e:
                self.module.fail_json(
                    msg=f"Failed to create firewall rule in security group {name} at position {i}: {to_native(e)}"
                )
            self._move_rule_to_correct_pos(name, body)
            rules = self._fetch_rules(name)

    def _move_rule_to_correct_pos(self, name, rule):
        """If Proxmox inserts new rules at pos 0, move them to the intended position."""
        position = rule.get("pos")
        if position is None or position == 0:
            return
        try:
            rule_at0 = self.proxmox_api.cluster().firewall().groups(name)(0).get()
            for param, value in rule_at0.items():
                if param in rule and param != "pos" and value != rule.get(param):
                    self.module.warn(
                        f"Skipping rule position workaround for security group {name}: "
                        f"rule at pos 0 does not match the rule just created. "
                        f"Verify rule is at correct position."
                    )
                    return
            self.proxmox_api.cluster().firewall().groups(name)(0).put(moveto=(position + 1))
        except Exception as e:
            self.module.fail_json(
                msg=f"Failed to move firewall rule in security group {name} at position {position}: {to_native(e)}"
            )


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxClusterFirewallSecurityGroupAnsible(module)
    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f"An error occurred: {to_native(e)}")


if __name__ == "__main__":
    main()
