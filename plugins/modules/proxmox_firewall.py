#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Jana Hoch <janahoch91@proton.me>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: proxmox_firewall
short_description: Manage firewall rules in Proxmox
description:
    - create/update/delete FW rules at cluster/group/vnet/node/vm level
    - Create/delete firewall security groups
    - get firewall rules at cluster/group/vnet/node/vm level
author: 'Jana Hoch <janahoch91@proton.me> (!UNKNOWN)'
attributes:
  check_mode:
    support: none
  diff_mode:
    support: none
options:
  state:
    description:
      - create/update/delete firewall rules or security group
      - if state is not provided then it will just list firewall rules at level
    type: str
    choices:
      - present
      - update
      - absent
  level:
    description:
      - Level at which the firewall rule applies.
    type: str
    choices:
      - cluster
      - group
      - vnet
      - node
      - vm
    default: cluster
  node:
    description:
      - Name of the node.
      - only needed when level is node.
    type: str
  vmid:
    description:
      - ID of the VM to which the rule applies.
      - only needed when level is vm.
    type: int
  vnet:
    description:
      - Name of the virtual network for the rule.
      - only needed when level is vnet.
    type: str
  pos:
    description:
      - Position of the rule in the list.
      - only needed if deleting rule or trying to list it
    type: int
  group_conf:
    description:
      - Whether security group should be created or deleted.
    type: bool
    default: false
  group:
    description:
      - Name of the group to which the rule belongs.
      - only needed when level is group or group_conf is True.
    type: str
  comment:
    description:
      - Comment for security group.
      - Only needed when creating group.
    type: str
  rules:
    description:
      - List of individual rules to be applied.
    type: list
    elements: dict
    suboptions:
      action:
        description:
          - Rule action ('ACCEPT', 'DROP', 'REJECT') or security group name.
        type: str
        required: true
      type:
        description:
          - Rule type.
        choices:
          - in
          - out
          - forward
          - group
        type: str
        required: true
      comment:
        description:
          - Optional comment for the specific rule.
        type: str
      dest:
        description:
          - Restrict packet destination address.
          - This can refer to a single IP address, an IP set ('+ipsetname') or an IP alias definition.
          - You can also specify an address range like '20.34.101.207-201.3.9.99', or a list of IP addresses and networks (entries are separated by comma).
          - Please do not mix IPv4 and IPv6 addresses inside such lists.
        type: str
      digest:
        description:
          - Prevent changes if current configuration file has a different digest.
          - This can be used to prevent concurrent modifications.
          - If not provided we will calculate at runtime.
        type: str
      dport:
        description:
          - Restrict TCP/UDP destination port.
          - You can use service names or simple numbers (0-65535), as defined in '/etc/services'.
          - Port ranges can be specified with '\d+:\d+', for example '80:85', and you can use comma separated list to match several ports or ranges.
        type: str
      enable:
        description:
          - Enable or disable the rule.
        type: bool
      icmp_type:
        description:
          - Specify icmp-type. Only valid if proto equals 'icmp' or 'icmpv6'/'ipv6-icmp'.
        type: str
      iface:
        description:
          - Network interface name. You have to use network configuration key names for VMs and containers ('net\d+').
          - Host related rules can use arbitrary strings.
        type: str
      log:
        description:
          - Logging level for the rule.
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
        type: str
      macro:
        description:
          - Use predefined standard macro.
        type: str
      pos:
        description:
          - Position of the rule in the list.
        type: int
      proto:
        description:
          - IP protocol. You can use protocol names ('tcp'/'udp') or simple numbers, as defined in '/etc/protocols'.
        type: str
      source:
        description:
          - Restrict packet source address.
          - This can refer to a single IP address, an IP set ('+ipsetname') or an IP alias definition.
          - You can also specify an address range like '20.34.101.207-201.3.9.99', or a list of IP addresses and networks (entries are separated by comma).
          - Please do not mix IPv4 and IPv6 addresses inside such lists.
        type: str
      sport:
        description:
          - Restrict TCP/UDP source port.
          - You can use service names or simple numbers (0-65535), as defined in '/etc/services'.
          - Port ranges can be specified with '\d+:\d+', for example '80:85', and you can use comma separated list to match several ports or ranges.
        type: str
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Get Cluster level firewall rules
  community.proxmox.proxmox_firewall:
    api_user: "{{ pc.proxmox.api_user }}"
    api_token_id: "{{ pc.proxmox.api_token_id }}"
    api_token_secret: "{{ vault.proxmox.api_token_secret }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no
    level: cluster

- name: Create firewall rules at cluster level
  community.proxmox.proxmox_firewall:
    api_user: "{{ pc.proxmox.api_user }}"
    api_token_id: "{{ pc.proxmox.api_token_id }}"
    api_token_secret: "{{ vault.proxmox.api_token_secret }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no
    level: cluster
    state: present
    rules:
      - type: out
        action: ACCEPT
        source: 1.1.1.1
        log: nolog
        pos: 9
        enable: True
      - type: out
        action: ACCEPT
        source: 1.0.0.1
        pos: 10
        enable: True

- name: Update Cluster level firewall rules
  community.proxmox.proxmox_firewall:
    api_user: "{{ pc.proxmox.api_user }}"
    api_token_id: "{{ pc.proxmox.api_token_id }}"
    api_token_secret: "{{ vault.proxmox.api_token_secret }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no
    level: cluster
    state: update
    rules:
      - type: out
        action: ACCEPT
        source: 8.8.8.8
        log: nolog
        pos: 9
        enable: False
      - type: out
        action: ACCEPT
        source: 8.8.4.4
        pos: 10
        enable: False

- name: Delete cluster level firewall rule at pos 10
  community.proxmox.proxmox_firewall:
    api_user: "{{ pc.proxmox.api_user }}"
    api_token_id: "{{ pc.proxmox.api_token_id }}"
    api_token_secret: "{{ vault.proxmox.api_token_secret }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no
    level: cluster
    state: absent
    pos: 10

- name: Create security group
  community.proxmox.proxmox_firewall:
    api_user: "{{ pc.proxmox.api_user }}"
    api_token_id: "{{ pc.proxmox.api_token_id }}"
    api_token_secret: "{{ vault.proxmox.api_token_secret }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no
    group_conf: True
    state: present
    group: test

- name: Delete security group
  community.proxmox.proxmox_firewall:
    api_user: "{{ pc.proxmox.api_user }}"
    api_token_id: "{{ pc.proxmox.api_token_id }}"
    api_token_secret: "{{ vault.proxmox.api_token_secret }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no
    group_conf: True
    state: absent
    group: test
"""

RETURN = r"""
group:
    description: group name which was created/deleted
    returned: on success
    type: str
    sample:
      test

firewall_rules:
    description: List of firewall rules.
    returned: on success
    type: list
    elements: dict
    sample:
      [
        {
            "action": "ACCEPT",
            "digest": "b5ddaed23b415b9368706fc9edc83d037526aae9",
            "dport": "53",
            "enable": 1,
            "ipversion": 4,
            "log": "nolog",
            "pos": 0,
            "proto": "udp",
            "source": "192.168.1.0/24",
            "type": "in"
        },
        {
            "action": "ACCEPT",
            "digest": "b5ddaed23b415b9368706fc9edc83d037526aae9",
            "dport": "53",
            "enable": 1,
            "ipversion": 4,
            "log": "nolog",
            "pos": 1,
            "proto": "tcp",
            "source": "192.168.1.0/24",
            "type": "in"
        },
        {
            "action": "ACCEPT",
            "dest": "192.168.1.0/24",
            "digest": "b5ddaed23b415b9368706fc9edc83d037526aae9",
            "enable": 1,
            "ipversion": 4,
            "log": "nolog",
            "pos": 2,
            "type": "out"
        },
        {
            "action": "ACCEPT",
            "digest": "b5ddaed23b415b9368706fc9edc83d037526aae9",
            "enable": 1,
            "ipversion": 4,
            "log": "nolog",
            "pos": 3,
            "source": "192.168.1.0/24",
            "type": "in"
        },
        {
            "action": "ACCEPT",
            "dest": "+sdn/test2-gateway",
            "digest": "b5ddaed23b415b9368706fc9edc83d037526aae9",
            "enable": 1,
            "iface": "test2",
            "log": "nolog",
            "macro": "DNS",
            "pos": 4,
            "type": "in"
        },
        {
            "action": "ACCEPT",
            "digest": "b5ddaed23b415b9368706fc9edc83d037526aae9",
            "enable": 1,
            "iface": "test2",
            "log": "nolog",
            "macro": "DHCPfwd",
            "pos": 5,
            "type": "in"
        },
        {
            "action": "ACCEPT",
            "dest": "+sdn/test2-all",
            "digest": "b5ddaed23b415b9368706fc9edc83d037526aae9",
            "dport": "68",
            "enable": 1,
            "log": "nolog",
            "pos": 6,
            "proto": "udp",
            "source": "+sdn/test2-gateway",
            "sport": "67",
            "type": "out"
        },
        {
            "action": "DROP",
            "digest": "b5ddaed23b415b9368706fc9edc83d037526aae9",
            "enable": 1,
            "log": "nolog",
            "pos": 7,
            "type": "in"
        },
        {
            "action": "DROP",
            "digest": "b5ddaed23b415b9368706fc9edc83d037526aae9",
            "enable": 1,
            "log": "nolog",
            "pos": 8,
            "type": "out"
        }
      ]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    proxmox_auth_argument_spec,
    ansible_to_proxmox_bool,
    ProxmoxAnsible
)


def get_proxmox_args():
    return dict(
        state=dict(type="str", choices=["present", "absent", "update"], required=False),
        level=dict(type="str", choices=["cluster", "node", "vm", "vnet", "group"], default="cluster", required=False),
        node=dict(type="str", required=False),
        vmid=dict(type="int", required=False),
        vnet=dict(type="str", required=False),
        pos=dict(type="int", required=False),
        group_conf=dict(type="bool", default=False),
        group=dict(type="str", required=False),
        comment=dict(type="str", required=False),
        rules=dict(
            type="list",
            elements="dict",
            required=False,
            options=dict(
                action=dict(type="str", required=True),
                type=dict(type="str", choices=["in", "out", "forward", "group"], required=True),
                comment=dict(type="str", required=False),
                dest=dict(type="str", required=False),
                digest=dict(type="str", required=False),
                dport=dict(type="str", required=False),
                enable=dict(type="bool", required=False),
                icmp_type=dict(type="str", required=False),
                iface=dict(type="str", required=False),
                log=dict(type="str",
                         choices=["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug", "nolog"],
                         required=False),
                macro=dict(type="str", required=False),
                pos=dict(type="int", required=False),
                proto=dict(type="str", required=False),
                source=dict(type="str", required=False),
                sport=dict(type="str", required=False)
            )
        )
    )


def get_ansible_module():
    module_args = proxmox_auth_argument_spec()
    module_args.update(get_proxmox_args())

    return AnsibleModule(
        argument_spec=module_args,
        required_if=[
            ('group_conf', True, ['group']),
            ('level', 'vm', ['vmid']),
            ('level', 'node', ['node']),
            ('level', 'vnet', ['vnet']),
            ('level', 'group', ['group']),
        ]
    )


class ProxmoxFirewallAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super(ProxmoxFirewallAnsible, self).__init__(module)
        self.params = module.params

    def validate_params(self):
        if self.params.get('state') in ['present', 'update']:
            return self.params.get('group_conf') or self.params.get('rules')
        elif self.params.get('state') == 'absent':
            return self.params.get('group_conf') or self.params.get('pos')
        else:
            return True

    def run(self):
        if not self.validate_params():
            self.module.fail_json(
                msg='parameter validation failed. '
                    'If state is present/update we need either group_conf to be True or rules to be present. '
                    'If state is absent we need group_conf to be True or pos to be present. '
            )

        state = self.params.get("state")
        level = self.params.get("level")
        rules = self.params.get("rules")

        if level == "vm":
            vm = self.get_vm(vmid=self.params.get('vmid'))
            node = getattr(self.proxmox_api.nodes(), vm['node'])
            virt = getattr(node(), vm['type'])
            vm = getattr(virt(), vm['vmid'])
            firewall_obj = vm().firewall
            rules_obj = firewall_obj().rules

        elif level == "node":
            node = getattr(self.proxmox_api.nodes(), self.params.get('node'))
            firewall_obj = node().firewall
            rules_obj = firewall_obj().rules

        elif level == "vnet":
            vnet = getattr(self.proxmox_api.cluster().sdn().vnets(), self.params.get('vnet'))
            firewall_obj = vnet().firewall
            rules_obj = firewall_obj().rules

        elif level == "group":
            rules_obj = getattr(self.proxmox_api.cluster().firewall().groups(), self.params.get('group'))

        else:
            firewall_obj = self.proxmox_api.cluster().firewall
            rules_obj = firewall_obj().rules

        if state == "present":
            if self.params.get('group_conf'):
                self.create_group(group=self.params.get('group'), comment=self.params.get('comment'))
            if rules is not None:
                self.create_fw_rules(rules_obj=rules_obj, rules=rules)
        elif state == "update":
            if self.params.get('group_conf'):
                self.create_group(group=self.params.get('group'), comment=self.params.get('comment'))
            if rules is not None:
                self.update_fw_rules(rules_obj=rules_obj, rules=rules)
        elif state == "absent":
            if self.params.get('pos'):
                self.delete_fw_rule(rules_obj=rules_obj, pos=self.params.get('pos'))
            if self.params.get('group_conf'):
                self.delete_group(group_name=self.params.get('group'))
        else:
            rules = self.get_fw_rules(rules_obj, pos=self.params.get('pos'))
            self.module.exit_json(
                changed=False, firewall_rules=rules, msg='successfully retrieved firewall rules'
            )

    def create_group(self, group, comment=None):
        try:
            self.proxmox_api.cluster().firewall().groups.post(group=group, comment=comment)
            self.module.exit_json(
                changed=True, group=group, msg=f'successfully created security group {group}'
            )
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to create security group: {e}'
            )

    def delete_group(self, group_name):
        try:
            group = getattr(self.proxmox_api.cluster().firewall().groups(), group_name)
            group.delete()
            self.module.exit_json(
                changed=True, group=group_name, msg=f'successfully deleted security group {group_name}'
            )
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to delete security group {group_name}: {e}'
            )

    def get_fw_rules(self, rules_obj, pos=None):
        if pos is not None:
            rules_obj = getattr(rules_obj(), str(pos))
        try:
            return rules_obj.get()
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve firewall rules: {e}'
            )

    def delete_fw_rule(self, rules_obj, pos):
        try:
            rule_obj = getattr(rules_obj(), str(pos))
            digest = rule_obj.get().get('digest')
            rule_obj.delete(pos=pos, digest=digest)

            self.module.exit_json(
                changed=True, msg='successfully deleted firewall rules'
            )
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to delete firewall rule at pos {pos}: {e}'
            )

    def update_fw_rules(self, rules_obj, rules):
        for rule in rules:
            rule['icmp-type'] = rule.get('icmp_type')
            rule['enable'] = ansible_to_proxmox_bool(rule.get('enable'))
            del rule['icmp_type']
            try:
                rule_obj = getattr(rules_obj(), str(rule['pos']))
                rule['digest'] = rule_obj.get().get('digest')  # Avoids concurrent changes
                rule_obj.put(**rule)

            except Exception as e:
                self.module.fail_json(
                    msg=f'Failed to update firewall rule at pos {rule["pos"]}: {e}'
                )
        self.module.exit_json(
            changed=True, msg='successfully created firewall rules'
        )

    def create_fw_rules(self, rules_obj, rules):
        for rule in rules:
            rule['icmp-type'] = rule.get('icmp_type')
            rule['enable'] = ansible_to_proxmox_bool(rule.get('enable'))
            del rule['icmp_type']
            try:
                rules_obj().post(**rule)
                self.move_rule_to_correct_pos(rules_obj, rule)

            except Exception as e:
                self.module.fail_json(
                    msg=f'Failed to create firewall rule {rule}: {e}'
                )
        self.module.exit_json(
            changed=True, msg='successfully created firewall rules'
        )

    def move_rule_to_correct_pos(self, rules_obj, rule):
        ##################################################################################################
        # TODO: Once below mentioned issue is fixed. Remove this workaround.                             #
        # Currently Proxmox API doesn't honor pos. All new rules are created at pos 0                    #
        # https://forum.proxmox.com/threads/issue-when-creating-a-firewall-rule.135878/                  #
        # Not able to find it in BUGZILLA. So maybe this is expected behaviour.                          #
        # To workaround this issue we will check rule at pos 0 and if needed move it to correct position #
        ##################################################################################################

        pos = rule.get('pos')
        rule = {k: v for k, v in rule.items() if v is not None}
        if pos is not None and pos != 0:
            try:
                fw_rule_at0 = getattr(rules_obj(), str(0))
                for param, value, in fw_rule_at0.get().items():
                    if param in rule.keys() and param != 'pos' and value != rule.get(param):
                        self.module.warn(
                            msg=f'Skipping workaround for rule placement. '
                                f'Verify rule is at correct pos '
                                f'provided - {rule} rule_at0 - {fw_rule_at0.get()}')
                        break  # No need to move this. Potentially the issue is resolved.
                else:
                    fw_rule_at0.put(moveto=(pos + 1))  # moveto moves rule to one position before the value
            except Exception as e:
                self.module.fail_json(
                    msg=f'Rule created but failed to move it to correct pos. {e}'
                )


def main():
    module = get_ansible_module()
    proxmox = ProxmoxFirewallAnsible(module)

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f'An error occurred: {e}')


if __name__ == "__main__":
    main()
