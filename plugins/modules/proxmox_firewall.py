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
        level=dict(type="str", choices=["cluster", "node", "vm", "vnet"], default="cluster", required=False),
        node=dict(type="str", required=False),
        vmid=dict(type="int", required=False),
        vnet=dict(type="str", required=False)
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

        if level == "vm":
            rules = self.get_vmid_fw_rules(vmid=self.params['vmid'])
        elif level == "node":
            rules = self.get_node_fw_rules(node=self.params['node'])
        elif level == "vnet":
            rules = self.get_vnet_fw_rules(vnet=self.params['vnet'])
        else:
            rules = self.get_cluster_fw_rules()
        self.module.exit_json(
            changed=False, firewall_rules=rules, msg=f'successfully retrieved firewall rules'
        )

    def get_vnet_fw_rules(self, vnet, pos=None):
        try:
            vnet = getattr(self.proxmox_api.cluster().sdn().vnets(), vnet)
            return vnet().firewall().rules().get()
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

            return vm().firewall().rules().get()
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve firewall rules for vmid - {vmid}: {e}'
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
