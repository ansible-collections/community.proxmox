#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2025, Jana Hoch <janahoch91@proton.me>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from pygments.lexer import default

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
        vnet=dict(type="str", required=False),
        zone=dict(type="str", required=False),
        alias=dict(type="str", required=False),
        isolate_ports=dict(type="bool", default=False, required=False),
        lock_token=dict(type="str", required=False),
        tag=dict(type="int", required=False),
        type=dict(type="str", choices=['vnet'], required=False),
        vlanaware=dict(type="str", required=False),
        delete=dict(type="str", required=False)
    )

def get_ansible_module():
    module_args = proxmox_auth_argument_spec()
    module_args.update(get_proxmox_args())

    return AnsibleModule(
        argument_spec=module_args,
        required_if=[
        ]
    )

class ProxmoxVnetAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super(ProxmoxVnetAnsible, self).__init__(module)
        self.params = module.params

    def run(self):
        state = self.params.get("state")
        force = self.params.get("force")

        vnet_params = {
            'vnet': self.params.get('vnet'),
            'zone': self.params.get('zone'),
            'alias': self.params.get('alias'),
            'isolate-ports': ansible_to_proxmox_bool(self.params.get('isolate_ports')),
            'lock-token': self.params.get('lock_token') or self.get_global_sdn_lock(),
            'tag': self.params.get('tag'),
            'type': self.params.get('type'),
            'vlanaware': self.params.get('vlanaware')
        }

        if state == 'present':
            self.vnet_present(force=force, **vnet_params)
        elif state == 'update':
            self.vnet_update(**vnet_params)
        elif state == 'absent':
            self.vnet_absent(

            )

    def get_vnet_detail(self):
        try:
            return self.proxmox_api.cluster().sdn().vnets().get()
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve vnet information from cluster: {e}'
            )

    def vnet_present(self, force, **vnet_args):
        vnet = vnet_args['vnet']
        lock = vnet_args['lock-token']
        available_vnets = [vnet['vnet'] for vnet in self.get_vnet_detail()]

        # Check if vnet already exists
        if vnet in available_vnets:
            if force:
                self.vnet_update(force=force, **vnet_args)
            else:
                self.release_lock(lock)
                self.module.fail_json(
                    msg=f'vnet {vnet} already exists and force is false.'
                )
        else:
            try:
                self.proxmox_api.cluster().sdn().vnets().post(**vnet_args)
                self.apply_sdn_changes_and_release_lock(lock)
                self.module.exit_json(
                    changed=True, vnet=vnet, msg=f'Create new vnet {vnet}'
                )
            except Exception as e:
                self.module.warn(f'Failed to create vnet - {e}')
                self.rollback_sdn_changes_and_release_lock(lock)
                self.module.fail_json(
                    msg=f'Failed to create vnet - {e}. Rolling back all changes.'
                )

    def vnet_update(self, **vnet_params):
        available_vnets = {vnet['vnet']: vnet['digest'] for vnet in self.get_vnet_detail()}
        lock = vnet_params['lock-token']
        vnet_name = vnet_params['vnet']

        if vnet_name not in available_vnets.keys():
            self.vnet_present(force=False, **vnet_params)
        else:
            vnet_params['digest'] = available_vnets[vnet_name]
            vnet_params['delete'] = self.params.get('delete')
            del vnet_params['type']

            try:
                vnet = getattr(self.proxmox_api.cluster().sdn().vnets(), vnet_name)
                vnet.put(**vnet_params)
                self.apply_sdn_changes_and_release_lock(lock)
                self.module.exit_json(
                    changed=True, vnet=vnet_name, msg=f'updated vnet {vnet_name}'
                )
            except Exception as e:
                self.module.warn(f'Failed to update vnet - {e}')
                self.rollback_sdn_changes_and_release_lock(lock)
                self.module.fail_json(
                    msg=f'Failed to update vnet - {e}. Rolling back all changes.'
                )

    def vnet_absent(self):
        pass


def main():
    module = get_ansible_module()
    proxmox = ProxmoxVnetAnsible(module)

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f'An error occurred: {e}')

if __name__ == "__main__":
    main()