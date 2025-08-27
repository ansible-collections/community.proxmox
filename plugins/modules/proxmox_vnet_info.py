#!/usr/bin/python
# -*- coding: utf-8 -*-

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
    ProxmoxAnsible
)


class ProxmoxVnetInfoAnsible(ProxmoxAnsible):  
    def get_subnets(self, vnet):
        try:
            vnet = getattr(self.proxmox_api.cluster().sdn().vnets(), vnet)
            return vnet().subnets.get()
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve subnet information from vnet {vnet}: {e}'
            )

    def get_firewall(self, vnet_name):
        try:
            vnet = getattr(self.proxmox_api.cluster().sdn().vnets(), vnet_name)
            return vnet().firewall.rules().get()
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve subnet information from vnet {vnet_name}: {e}'
            )

    def get_vnet_detail(self):
        try:
            vnets = self.proxmox_api.cluster().sdn().vnets().get()
            for vnet in vnets:
                vnet['subnets'] = self.get_subnets(vnet['vnet'])
                vnet['firewall_rules'] = self.get_firewall(vnet['vnet'])
            return vnets
                
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve vnet information from cluster: {e}'
            )


def main():
    
    module_args = proxmox_auth_argument_spec()
    vnet_info_args = dict(
        vnet=dict(type="str", required=False)
    )
    module_args.update(vnet_info_args)

    module = AnsibleModule(
        argument_spec=module_args,
        required_together=[("api_token_id", "api_token_secret")],
        required_one_of=[("api_password", "api_token_id")],
        supports_check_mode=True,
    )

    proxmox = ProxmoxVnetInfoAnsible(module)
    vnet = module.params['vnet']
    results = {}
    vnets = proxmox.get_vnet_detail()

    if vnet:
        vnets = [vnet_details for vnet_details in vnets if vnet_details['vnet'] == vnet]
    
    results['vnets'] = vnets
    module.exit_json(**results)

if __name__ == "__main__":
    main()