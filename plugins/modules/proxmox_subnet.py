#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Jana Hoch <janahoch91@proton.me>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: proxmox_subnet
short_description: Create/Update/Delete subnets from SDN
description:
  - Create, update, or delete subnets in Proxmox SDN.
author: 'Jana Hoch <janahoch91@proton.me> (!UNKNOWN)'
attributes:
  check_mode:
    support: none
  diff_mode:
    support: none
options:
  state:
    description:
      - Desired state of the network configuration.
      - Choices include present (create), absent (delete), or update (modify).
    type: str
    choices: ['present', 'absent']
    default: present
  update:
    description:
      - If O(state=present) then it will update the subnet if needed.
    type: bool
    default: True
  subnet:
    description:
      - subnet CIDR.
    type: str
    required: true
  vnet:
    description:
      - The virtual network to which the subnet belongs.
    type: str
    required: true
  zone:
    description:
      - Vnet Zone
    type: str
  dhcp_dns_server:
    description:
      - IP address for the DNS server.
    type: str
  dhcp_range:
    description:
      - Range of IP addresses for DHCP.
    type: list
    elements: dict
    suboptions:
      start:
        description:
          - Starting IP address of the DHCP range.
        type: str
        required: true
      end:
        description:
          - Ending IP address of the DHCP range.
        type: str
        required: true
  dnszoneprefix:
    description:
      - Prefix for the DNS zone.
    type: str
  gateway:
    description:
      - Subnet Gateway. Will be assign on vnet for layer3 zones.
    type: str
  lock_token:
    description:
      - the token for unlocking the global SDN configuration.
    type: str
  snat:
    description:
      - Enable Source NAT for the subnet.
    type: bool
    default: False
  delete:
    description:
      - A list of settings you want to delete.
    type: str
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Create a subnet
  community.proxmox.proxmox_subnet:
    api_user: "{{ pc.proxmox.api_user }}"
    api_token_id: "{{ pc.proxmox.api_token_id }}"
    api_token_secret: "{{ vault.proxmox.api_token_secret }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no
    vnet: test
    subnet: 10.10.2.0/24
    zone: ans1
    state: present
    dhcp_range:
      - start: 10.10.2.5
        end: 10.10.2.50
      - start: 10.10.2.100
        end: 10.10.2.150
    snat: True

- name: Delete a subnet
  community.proxmox.proxmox_subnet:
    api_user: "{{ pc.proxmox.api_user }}"
    api_token_id: "{{ pc.proxmox.api_token_id }}"
    api_token_secret: "{{ vault.proxmox.api_token_secret }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no
    vnet: test
    subnet: 10.10.2.0/24
    zone: ans1
    state: absent
"""

RETURN = r"""
subnet:
  description:
    - Subnet ID which was created/updated/deleted
  returned: on success
  type: str
  sample:
    ans1-10.10.2.0-24
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.proxmox.plugins.module_utils.proxmox_sdn import ProxmoxSdnAnsible
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    proxmox_auth_argument_spec,
    ansible_to_proxmox_bool
)


def get_proxmox_args():
    return dict(
        state=dict(type="str", choices=["present", "absent"], default='present', required=False),
        update=dict(type="bool", default=True),
        subnet=dict(type="str", required=True),
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
        lock_token=dict(type="str", required=False, no_log=False),
        snat=dict(type='bool', default=False, required=False),
        delete=dict(type="str", required=False)
    )


def get_ansible_module():
    module_args = proxmox_auth_argument_spec()
    module_args.update(get_proxmox_args())

    return AnsibleModule(
        argument_spec=module_args,
        required_if=[
            ('state', 'present', ['subnet', 'vnet', 'zone']),
            ('state', 'absent', ['zone', 'vnet', 'subnet']),
        ]
    )


class ProxmoxSubnetAnsible(ProxmoxSdnAnsible):
    def __init__(self, module):
        super(ProxmoxSubnetAnsible, self).__init__(module)
        self.params = module.params

    def run(self):
        state = self.params.get("state")
        update = self.params.get("update")

        subnet_params = {
            'subnet': self.params.get('subnet'),
            'type': 'subnet',
            'vnet': self.params.get('vnet'),
            'dhcp-dns-server': self.params.get('dhcp_dns_server'),
            'dhcp-range': self.get_dhcp_range(),
            'dnszoneprefix': self.params.get('dnszoneprefix'),
            'gateway': self.params.get('gateway'),
            'lock-token': self.params.get('lock_token') or self.get_global_sdn_lock(),
            'snat': ansible_to_proxmox_bool(self.params.get('snat'))
        }

        if state == 'present':
            self.subnet_present(update=update, **subnet_params)
        elif state == 'absent':
            self.subnet_absent(**subnet_params)

    def get_dhcp_range(self):
        if self.params.get('dhcp_range') is None:
            return None
        dhcp_range = [f"start-address={x['start']},end-address={x['end']}" for x in self.params.get('dhcp_range')]
        return dhcp_range

    def subnet_present(self, update, **subnet_params):
        vnet_name = subnet_params['vnet']
        lock = subnet_params['lock-token']
        subnet_cidr = subnet_params['subnet']
        subnet_id = f"{self.params['zone']}-{subnet_params['subnet'].replace('/', '-')}"

        try:
            vnet = getattr(self.proxmox_api.cluster().sdn().vnets(), vnet_name)

            # Check if subnet already present
            if subnet_id in [x['subnet'] for x in vnet().subnets().get()]:
                if update:
                    subnet = getattr(vnet().subnets(), subnet_id)
                    subnet_params['digest'] = subnet.get()['digest']
                    subnet_params['delete'] = self.params.get('delete')
                    del subnet_params['type']
                    del subnet_params['subnet']

                    subnet.put(**subnet_params)
                    self.apply_sdn_changes_and_release_lock(lock=lock)
                    self.module.exit_json(
                        changed=True, subnet=subnet_id, msg=f'Updated subnet {subnet_id}'
                    )
                else:
                    self.release_lock(lock=lock)
                    self.module.exit_json(
                        changed=False, subnet=subnet_id, msg=f'subnet {subnet_id} already present and update is false.'
                    )
            else:
                vnet.subnets().post(**subnet_params)
                self.apply_sdn_changes_and_release_lock(lock=lock)
                self.module.exit_json(
                    changed=True, subnet=subnet_id, msg=f'Created new subnet {subnet_cidr}'
                )
        except Exception as e:
            self.rollback_sdn_changes_and_release_lock(lock=lock)
            self.module.fail_json(
                msg=f'Failed to create subnet. Rolling back all changes : {e}'
            )

    def subnet_absent(self, **subnet_params):
        vnet_id = subnet_params['vnet']
        lock = subnet_params['lock-token']
        subnet_id = f"{self.params['zone']}-{subnet_params['subnet'].replace('/', '-')}"

        params = {
            'subnet': subnet_id,
            'vnet': vnet_id,
            'lock-token': lock
        }

        try:
            vnet = getattr(self.proxmox_api.cluster().sdn().vnets(), vnet_id)

            # Check if subnet already present
            if subnet_id in [x['subnet'] for x in vnet().subnets().get()]:
                subnet = getattr(vnet().subnets(), subnet_id)
                subnet.delete(**params)
                self.apply_sdn_changes_and_release_lock(lock=lock)
                self.module.exit_json(
                    changed=True, subnet=subnet_id, msg=f'Deleted subnet {subnet_id}'
                )
            else:
                self.release_lock(lock=lock)
                self.module.exit_json(
                    changed=False, subnet=subnet_id, msg=f'subnet {subnet_id} already not present.'
                )
        except Exception as e:
            self.rollback_sdn_changes_and_release_lock(lock=lock)
            self.module.fail_json(
                msg=f'Failed to delete subnet. Rolling back all changes. : {e}'
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
