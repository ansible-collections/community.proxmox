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
  force:
    description:
      - If state is present and if 1 or more rule already exists at given pos force will update them
      - If state is update and if 1 or more rule doesn't exist force will create
    type: bool
    default: false
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
  aliases:
    description:
      - List of aliases
      - Alias can only be created/updated/deleted at cluster or VM level
    type: list
    elements: dict
    suboptions:
      name:
        description: Alias name
        type: str
        required: true
      cidr:
        description:
          - CIDR for alias
          - only needed when O(state=present) or O(state=update)
        type: str
        required: false
      comment:
        description: Comment for Alias
        type: str
        required: false
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
        required: true
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

- name: Create FW aliases
  community.proxmox.proxmox_firewall:
    api_user: "{{ pc.proxmox.api_user }}"
    api_token_id: "{{ pc.proxmox.api_token_id }}"
    api_token_secret: "{{ vault.proxmox.api_token_secret }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no
    state: present
    aliases:
      - name: test1
        cidr: '10.10.1.0/24'
      - name: test2
        cidr: '10.10.2.0/24'

- name: Update FW aliases
  community.proxmox.proxmox_firewall:
    api_user: "{{ pc.proxmox.api_user }}"
    api_token_id: "{{ pc.proxmox.api_token_id }}"
    api_token_secret: "{{ vault.proxmox.api_token_secret }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no
    state: update
    aliases:
      - name: test1
        cidr: '10.10.1.0/28'
      - name: test2
        cidr: '10.10.2.0/28'

- name: Delete FW aliases
  community.proxmox.proxmox_firewall:
    api_user: "{{ pc.proxmox.api_user }}"
    api_token_id: "{{ pc.proxmox.api_token_id }}"
    api_token_secret: "{{ vault.proxmox.api_token_secret }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no
    state: absent
    aliases:
      - name: test1
      - name: test2
"""

RETURN = r"""
group:
    description: group name which was created/deleted
    returned: on success
    type: str
    sample:
      test

groups:
    description: list of firewall security groups
    returned: on success
    type: list
    elements: str
    sample:
      [ "test" ]

aliases:
    description:
      - list of alias present at given level
      - aliases are only available for cluster and VM level so if any other level it'll be empty list
    returned: on success
    type: list
    elements: dict
    sample:
        [
            {
                "cidr": "10.10.1.0/24",
                "digest": "978391f460484e8d4fb3ca785cfe5a9d16fe8b1f",
                "ipversion": 4,
                "name": "test1"
            },
            {
                "cidr": "10.10.2.0/24",
                "digest": "978391f460484e8d4fb3ca785cfe5a9d16fe8b1f",
                "ipversion": 4,
                "name": "test2"
            },
            {
                "cidr": "10.10.3.0/24",
                "digest": "978391f460484e8d4fb3ca785cfe5a9d16fe8b1f",
                "ipversion": 4,
                "name": "test3"
            }
        ]

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
    compare_list_of_dicts,
    ProxmoxAnsible
)


def get_proxmox_args():
    return dict(
        state=dict(type="str", choices=["present", "absent", "update"], required=False),
        force=dict(type="bool", default=False),
        level=dict(type="str", choices=["cluster", "node", "vm", "vnet", "group"], default="cluster", required=False),
        node=dict(type="str", required=False),
        vmid=dict(type="int", required=False),
        vnet=dict(type="str", required=False),
        pos=dict(type="int", required=False),
        group_conf=dict(type="bool", default=False),
        group=dict(type="str", required=False),
        comment=dict(type="str", required=False),
        aliases=dict(
            type="list",
            elements="dict",
            required=False,
            options=dict(
                name=dict(type="str", required=True),
                cidr=dict(type="str", required=False),
                comment=dict(type="str", required=False)
            )
        ),
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
                pos=dict(type="int", required=True),
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
        ],
        mutually_exclusive=[
            ('aliases', 'rules'),
        ]
    )


class ProxmoxFirewallAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super(ProxmoxFirewallAnsible, self).__init__(module)
        self.params = module.params

    def validate_params(self):
        if self.params.get('state') in ['present', 'update']:
            if self.params.get('group_conf') != bool(self.params.get('rules') or self.params.get('aliases')):
                return True
            else:
                self.module.fail_json(
                    msg="When state is present either group_conf should be true or rules/aliases must be present but not both"
                )
        elif self.params.get('state') == 'absent':
            if self.params.get('group_conf') != bool(self.params.get('pos') or self.params.get('aliases')):
                return True
            else:
                self.module.fail_json(
                    msg="When State is absent either group_conf should be true or pos/aliases must be present but not both"
                )
        else:
            return True

    def run(self):
        self.validate_params()

        state = self.params.get("state")
        force = self.params.get("force")
        level = self.params.get("level")
        aliases = self.params.get("aliases")
        rules = self.params.get("rules")
        group = self.params.get("group")
        group_conf = self.params.get("group_conf")

        if rules is not None:
            for rule in rules:
                rule['icmp-type'] = rule.get('icmp_type')
                rule['enable'] = ansible_to_proxmox_bool(rule.get('enable'))
                del rule['icmp_type']

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
            firewall_obj = None
            rules_obj = getattr(self.proxmox_api.cluster().firewall().groups(), group)

        else:
            firewall_obj = self.proxmox_api.cluster().firewall
            rules_obj = firewall_obj().rules

        if state == "present":
            if group_conf:
                self.create_group(group=group, comment=self.params.get('comment'))
            if rules is not None:
                self.create_fw_rules(rules_obj=rules_obj, rules=rules, force=force)
            if aliases is not None:
                self.create_aliases(firewall_obj=firewall_obj, level=level, aliases=aliases, force=force)
        elif state == "update":
            if group_conf:
                self.create_group(group=group, comment=self.params.get('comment'))
            if rules is not None:
                self.update_fw_rules(rules_obj=rules_obj, rules=rules, force=force)
            if aliases is not None:
                self.update_aliases(firewall_obj=firewall_obj, level=level, aliases=aliases, force=force)
        elif state == "absent":
            if self.params.get('pos'):
                self.delete_fw_rule(rules_obj=rules_obj, pos=self.params.get('pos'))
            if group_conf:
                self.delete_group(group_name=group)
            if aliases is not None:
                self.delete_aliases(firewall_obj=firewall_obj, level=level, aliases=aliases)
        else:
            rules = self.get_fw_rules(rules_obj, pos=self.params.get('pos'))
            groups = self.get_groups()
            aliases = self.get_aliases(firewall_obj=firewall_obj, level=level)
            self.module.exit_json(
                changed=False,
                firewall_rules=rules,
                groups=groups,
                aliases=aliases,
                msg='successfully retrieved firewall rules and groups'
            )

    def get_aliases(self, firewall_obj, level):
        if firewall_obj is None or level not in ['cluster', 'vm']:
            return list()
        try:
            return firewall_obj().aliases().get()
        except Exception as e:
            self.module.fail_json(
                msg='Failed to retrieve aliases'
            )

    def create_aliases(self, firewall_obj, level, aliases, force=False):
        if firewall_obj is None or level not in ['cluster', 'vm']:
            self.module.fail_json(
                msg='Aliases can only be created at cluster or VM level'
            )

        aliases_to_create, aliases_to_update = compare_list_of_dicts(
            existing_list=self.get_aliases(firewall_obj=firewall_obj, level=level),
            new_list=aliases,
            uid='name',
            params_to_ignore=['digest', 'ipversion']
        )

        if len(aliases_to_create) == 0 and len(aliases_to_update) == 0:
            self.module.exit_json(
                changed=False,
                msg='No need to create/update any aliases'
            )
        elif len(aliases_to_update) > 0 and not force:
            self.module.fail_json(
                msg=f"Need to update aliases - {[x['name'] for x in aliases_to_update]} but force is false"
            )

        for alias in aliases_to_create:
            try:
                firewall_obj().aliases().post(**alias)
            except Exception as e:
                self.module.fail_json(
                    msg=f"Failed to create Alias {alias['name']} - {e}"
                )
        if len(aliases_to_update) > 0 and force:
            self.update_aliases(firewall_obj=firewall_obj, level=level, aliases=aliases_to_update, force=False)
        else:
            self.module.exit_json(
                changed=True,
                msg="Aliases created"
            )

    def update_aliases(self, firewall_obj, level, aliases, force=False):
        aliases_to_create, aliases_to_update = compare_list_of_dicts(
            existing_list=self.get_aliases(firewall_obj=firewall_obj, level=level),
            new_list=aliases,
            uid='name',
            params_to_ignore=['digest', 'ipversion']
        )

        if len(aliases_to_update) == 0 and len(aliases_to_create) == 0:
            self.module.exit_json(
                changed=False,
                msg='No need to create/update any alias.'

            )
        elif len(aliases_to_create) > 0 and not force:
            self.module.fail_json(
                msg=f"Need to create new alias - {[x['name'] for x in aliases_to_create]} But force is false"
            )

        for alias in aliases_to_update:
            try:
                alias_obj = getattr(firewall_obj().aliases(), alias['name'])
                alias_obj().put(**alias)
            except Exception as e:
                self.module.fail_json(
                    msg=f"Failed to update Alias {alias['name']} - {e}"
                )
        if len(aliases_to_update) > 0 and force:
            self.update_aliases(firewall_obj=firewall_obj, level=level, aliases=aliases_to_update, force=False)
        else:
            self.module.exit_json(
                changed=True,
                msg="Aliases updated"
            )

    def delete_aliases(self, firewall_obj, level, aliases):
        existing_aliases = set([x.get('name') for x in self.get_aliases(firewall_obj=firewall_obj, level=level)])
        aliases = set([x.get('name') for x in aliases])
        aliases_to_delete = list(existing_aliases.intersection(aliases))

        if len(aliases_to_delete) == 0:
            self.module.exit_json(
                changed=False,
                msg="No need to delete any alias"
            )
        for alias_name in aliases_to_delete:
            try:
                alias_obj = getattr(firewall_obj().aliases(), alias_name)
                alias_obj().delete()
            except Exception as e:
                self.module.fail_json(
                    msg=f"Failed to delete alias {alias_name} - {e}"
                )
        self.module.exit_json(
            changed=True,
            msg="Successfully deleted aliases"
        )

    def create_group(self, group, comment=None):
        if group in self.get_groups():
            self.module.exit_json(
                changed=False, group=group, msg=f"security group {group} already exists"
            )
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
        if group_name not in self.get_groups():
            self.module.exit_json(
                changed=False, group=group_name, msg=f"security group {group_name} already doesn't exists"
            )
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

    def get_groups(self):
        try:
            return [x['group'] for x in self.proxmox_api.cluster().firewall().groups().get()]
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve firewall security groups: {e}'
            )

    def delete_fw_rule(self, rules_obj, pos):
        try:
            for item in self.get_fw_rules(rules_obj):
                if item.get('pos') == pos:
                    break
            else:
                self.module.exit_json(
                    changed=False, msg="Firewall rule already doesn't exist"
                )
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

    def update_fw_rules(self, rules_obj, rules, force):
        existing_rules = self.get_fw_rules(rules_obj)
        rules_to_create, rules_to_update = compare_list_of_dicts(
            existing_list=existing_rules,
            new_list=rules,
            uid='pos',
            params_to_ignore=['digest', 'ipversion']
        )

        if len(rules_to_update) == 0 and len(rules_to_create) == 0:
            self.module.exit_json(
                changed=False,
                msg='No need to update any FW rules.'

            )
        elif len(rules_to_create) > 0 and not force:
            self.module.fail_json(
                msg=f"Need to create new rules for pos - {[x['pos'] for x in rules_to_create]} But force is false"
            )

        for rule in rules_to_update:
            try:
                rule_obj = getattr(rules_obj(), str(rule['pos']))
                rule['digest'] = rule_obj.get().get('digest')  # Avoids concurrent changes
                rule_obj.put(**rule)

            except Exception as e:
                self.module.fail_json(
                    msg=f'Failed to update firewall rule at pos {rule["pos"]}: {e}'
                )

        if len(rules_to_create) > 0:
            self.create_fw_rules(rules_obj=rules_obj, rules=rules_to_create, force=False)
        self.module.exit_json(
            changed=True, msg='successfully updated firewall rules'
        )

    def create_fw_rules(self, rules_obj, rules, force):
        existing_rules = self.get_fw_rules(rules_obj=rules_obj)
        rules_to_create, rules_to_update = compare_list_of_dicts(
            existing_list=existing_rules,
            new_list=rules,
            uid='pos',
            params_to_ignore=['digest', 'ipversion']
        )

        if len(rules_to_create) == 0 and len(rules_to_update) == 0:
            self.module.exit_json(
                changed=False,
                msg='No need to create/update any rule'
            )
        elif len(rules_to_update) > 0 and not force:
            self.module.fail_json(
                msg=f"Need to update rules at pos - {[x['pos'] for x in rules_to_update]} but force is false"
            )

        for rule in rules_to_create:
            try:
                rules_obj().post(**rule)
                self.move_rule_to_correct_pos(rules_obj, rule)

            except Exception as e:
                self.module.fail_json(
                    msg=f'Failed to create firewall rule {rule}: {e}'
                )
        if len(rules_to_update) > 0 and force:
            self.update_fw_rules(rules_obj=rules_obj, rules=rules_to_update, force=False)
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
