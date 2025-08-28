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


class ProxmoxZoneAnsible(ProxmoxAnsible):  
   def get_zones(self, type):
        try:
            if type == "all":
              zones = self.proxmox_api.cluster().sdn().zones().get()
            else:
              zones = self.proxmox_api.cluster().sdn().zones().get(type=type)
            return zones
                
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve zone information from cluster: {e}'
            )


def main():
    
    module_args = proxmox_auth_argument_spec()
    zone_args = dict(
        type=dict(type="str", 
                  choices=["evpn", "faucet", "qinq", "simple", "vlan", "vxlan", "all"], 
                  default="all", required=False)
    )
    module_args.update(zone_args)

    module = AnsibleModule(
        argument_spec=module_args,
        required_together=[("api_token_id", "api_token_secret")],
        required_one_of=[("api_password", "api_token_id")],
        supports_check_mode=True,
    )

    proxmox = ProxmoxZoneAnsible(module)
    type = module.params['type']
    results = {}
    zones = proxmox.get_zones(type)

    results['zones'] = zones
    module.exit_json(**results)

if __name__ == "__main__":
    main()