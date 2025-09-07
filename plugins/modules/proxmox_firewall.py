#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Jana Hoch <janahoch91@proton.me>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r""""""

EXAMPLES = r""""""

RETURN = r""""""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    proxmox_auth_argument_spec,
    ansible_to_proxmox_bool,
    ProxmoxAnsible
)


def get_proxmox_args():
    return dict(
        state=dict(type="str", choices=["present", "absent", "update"], required=False),
        force=dict(type="bool", default=False, required=False),
        level=dict(type="str", choices=["cluster", "node", "vm", "vnet", "group"], default="cluster", required=False),
        node=dict(type="str", required=False),
        vmid=dict(type="int", required=False),
        vnet=dict(type="str", required=False),
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
        ]
    )


class ProxmoxFirewallAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super(ProxmoxFirewallAnsible, self).__init__(module)
        self.params = module.params

    def run(self):
        state = self.params.get("state")
        force = self.params.get("force")
        level = self.params.get("level")
        rules =self.params.get("rules")

        # if rules is not None:
        #     rules = [rules.get('icmp_type')

        if state == "present":
            if level == "vm":
                pass
            elif level == "node":
                pass
            elif level == "vnet":
                pass
            elif level == "group":
                pass
            else:
                if rules is not None:
                    self.create_cluster_fw_rules(rules=rules)
        else:
            if level == "vm":
                rules = self.get_vmid_fw_rules(vmid=self.params['vmid'])
            elif level == "node":
                rules = self.get_node_fw_rules(node=self.params['node'])
            elif level == "vnet":
                rules = self.get_vnet_fw_rules(vnet=self.params['vnet'])
            elif level == "group":
                rules = self.get_group_fw_rules(group=self.params['group'])
            else:
                rules = self.get_cluster_fw_rules()
            self.module.exit_json(
                changed=False, firewall_rules=rules, msg=f'successfully retrieved firewall rules'
            )

    def get_group_fw_rules(self, group, pos=None):
        try:
            group = getattr(self.proxmox_api.cluster().firewall().groups(), group)
            return group().get(pos=pos)
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve security group level firewall rules: {e}'
            )

    def get_vnet_fw_rules(self, vnet, pos=None):
        try:
            vnet = getattr(self.proxmox_api.cluster().sdn().vnets(), vnet)
            return vnet().firewall().rules().get(pos=pos)
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve vnet level firewall rules: {e}'
            )

    def get_cluster_fw_rules(self, pos=None):
        try:
            return self.proxmox_api.cluster().firewall().rules().get(pos=pos)
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve cluster level firewall rules: {e}'
            )

    def get_node_fw_rules(self, node, pos=None):
        try:
            node = getattr(self.proxmox_api.nodes(), node)
            return node().firewall().rules().get(pos=pos)
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve cluster level firewall rules: {e}'
            )

    def get_vmid_fw_rules(self, vmid, pos=None):
        try:
            vm = self.get_vm(vmid=vmid)

            node = getattr(self.proxmox_api.nodes(), vm['node'])
            virt = getattr(node(), vm['type'])
            vm = getattr(virt(), vmid)

            return vm().firewall().rules().get(pos=pos)
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve firewall rules for vmid - {vmid}: {e}'
            )

    def create_cluster_fw_rules(self, rules):
        for rule in rules:
            rule['icmp-type'] = rule.get('icmp_type')
            rule['enable'] = ansible_to_proxmox_bool(rule.get('enable'))
            del rule['icmp_type']
            try:
                firewall_obj =  self.proxmox_api.cluster().firewall
                firewall_obj().rules().post(**rule)
                self.move_rule_to_correct_pos(firewall_obj, rule)

            except Exception as e:
                self.module.fail_json(
                    msg=f'Failed to create firewall rule {rule}: {e}'
                )
        else:
            self.module.exit_json(
                changed=True, msg=f'successfully created firewall rules'
            )

    def move_rule_to_correct_pos(self, firewall_obj, rule):
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
                fw_rule_at0 = getattr(firewall_obj().rules(), str(0))
                for param, value, in fw_rule_at0.get().items():
                    if param in rule.keys() and param != 'pos' and value != rule.get(param):
                        self.module.warn(
                            msg=f'Skipping workaround for rule placement. '
                                f'Verify rule is at correct pos '
                                f'provided - {rule} rule_at0 - {fw_rule_at0.get()}')
                        break  # No need to move this. Potentially the issue is resolved.
                else:
                    fw_rule_at0.put(moveto=pos+1)  # `moveto` moves rule to one position before the value
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
