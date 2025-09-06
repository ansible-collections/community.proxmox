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
        state=dict(type="str", choices=["present", "absent", "update"], default='present', required=False),
        force=dict(type="bool", default=False, required=False),
        subnet=dict(type="str", required=True),
        type=dict(type="str", choices=['subnet'], default='subnet', required=False),
        vnet=dict(type="str", required=True),
        zone=dict(type="str", required=False),
        dhcp_dns_server=dict(type="str", required=False),
        dhcp_range=dict(
            type='list',
            elements='dict',
            required=False,
            options=dict(
                start=dict(type='str', required=True),
                end=dict(type='str', required=True)
            )
        ),
        dnszoneprefix=dict(type='str', required=False),
        gateway=dict(type='str', required=False),
        lock_token=dict(type="str", required=False),
        snat=dict(type='bool', default=False, required=False),
        delete=dict(type="str", required=False)
    )

def get_ansible_module():
    module_args = proxmox_auth_argument_spec()
    module_args.update(get_proxmox_args())

    return AnsibleModule(
        argument_spec=module_args,
        required_if=[
            ('state', 'present', ['subnet', 'type', 'vnet']),
            ('state', 'update', ['zone', 'vnet', 'subnet']),
        ]
    )

class ProxmoxSubnetAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super(ProxmoxSubnetAnsible, self).__init__(module)
        self.params = module.params

    def run(self):
        state = self.params.get("state")
        force = self.params.get("force")

        subnet_params = {
            'subnet': self.params.get('subnet'),
            'type': self.params.get('type'),
            'vnet': self.params.get('vnet'),
            'dhcp-dns-server': self.params.get('dhcp_dns_server'),
            'dhcp-range': self.get_dhcp_range(),
            'dnszoneprefix': self.params.get('dnszoneprefix'),
            'gateway': self.params.get('gateway'),
            'lock-token': self.params.get('lock_token') or self.get_global_sdn_lock(),
            'snat': ansible_to_proxmox_bool(self.params.get('snat'))
        }

        if state == 'present':
            self.subnet_present(**subnet_params)
        elif state == 'update':
            self.subnet_update(**subnet_params)

    def get_dhcp_range(self):
        if self.params.get('dhcp_range') is None:
            return None
        dhcp_range = [f"start-address={x['start']},end-address={x['end']}" for x in self.params.get('dhcp_range')]
        return dhcp_range

    def subnet_present(self, **subnet_params):
        vnet_name = subnet_params['vnet']
        lock = subnet_params['lock-token']
        subnet = subnet_params['subnet']

        try:
            vnet = getattr(self.proxmox_api.cluster().sdn().vnets(), vnet_name)
            vnet.subnets().post(**subnet_params)
            self.apply_sdn_changes_and_release_lock(lock=lock)
            self.module.exit_json(
                changed=True, subnet=subnet, msg=f'Created new subnet {subnet}'
            )
        except Exception as e:
            self.rollback_sdn_changes_and_release_lock(lock=lock)
            self.module.fail_json(
                msg=f'Failed to create subnet. Rolling back all changes. : {e}'
            )

    def subnet_update(self, **subnet_params):
        lock = subnet_params['lock-token']
        vnet_id = subnet_params['vnet']
        subnet_id = f"{self.params['zone']}-{subnet_params['subnet'].replace('/', '-')}"

        subnet_params['delete'] = self.params.get('delete')
        del subnet_params['type']
        del subnet_params['subnet']

        try:
            vnet = getattr(self.proxmox_api.cluster().sdn().vnets(), vnet_id)
            subnet = getattr(vnet().subnets(), subnet_id)

            subnet_params['digest'] = subnet.get()['digest']

            subnet.put(**subnet_params)
            self.apply_sdn_changes_and_release_lock(lock=lock)
            self.module.exit_json(
                changed=True, subnet=subnet_id, msg=f'Updated subnet {subnet_id}'
            )
        except Exception as e:
            self.rollback_sdn_changes_and_release_lock(lock=lock)
            self.module.fail_json(
                msg=f'Failed to update subnet. Rolling back all changes. : {e}'
            )


def main():
    module = get_ansible_module()
    proxmox = ProxmoxSubnetAnsible(module)

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f'An error occurred: {e}')


if __name__ == "__main__":
    main()
