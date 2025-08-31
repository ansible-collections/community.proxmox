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


def get_proxmox_args():
    return dict(
        ipam=dict(type="str", required=False),
        vmid=dict(type='int', required=False)
    )


def get_ansible_module():
    module_args = proxmox_auth_argument_spec()
    module_args.update(get_proxmox_args())
    return AnsibleModule(argument_spec=module_args)


class ProxmoxIpamInfoAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super(ProxmoxIpamInfoAnsible, self).__init__(module)
        self.params = module.params

    def run(self):
        vmid = self.params.get('vmid')
        ipam = self.params.get('ipam')
        if vmid:
            self.module.exit_json(
                changed=False, ip=self.get_ip_by_vmid(vmid)
            )

        elif self.params.get('ipam'):
            if ipam not in self.get_ipams():
                self.module.fail_json(
                    msg=f'Ipam {ipam} is not present'
                )
            else:
                self.module.exit_json(
                    changed=False,
                    ipams=self.get_ipam_status()[ipam]
                )
        else:
            self.module.exit_json(
                changed=False,
                ipams=self.get_ipam_status()
            )

    def get_ipams(self):
        try:
            ipams = self.proxmox_api.cluster().sdn().ipams().get()
            return [ipam['ipam'] for ipam in ipams]
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve ipam information {e}'
            )

    def get_ipam_status(self):
        try:
            ipam_status = dict()
            ipams = self.get_ipams()
            for ipam_id in ipams:
                ipam = getattr(self.proxmox_api.cluster().sdn().ipams(), ipam_id)
                ipam_status[ipam_id] = ipam().status().get()
            return ipam_status
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve ipam status {e}'
            )

    def get_ip_by_vmid(self, vmid):
        ipam_status = self.get_ipam_status()
        for ipam in ipam_status.values():
            for item in ipam:
                if item.get('vmid') == vmid:
                    return item.get('ip')

def main():
    module = get_ansible_module()
    proxmox = ProxmoxIpamInfoAnsible(module)

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f'An error occurred: {e}')

if __name__ == "__main__":
    main()