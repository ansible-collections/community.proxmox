#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Jeffrey van Pelt (@Thulium-Drake) <jeff@vanpelt.one>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
module: proxmox_snap_info
short_description: Snapshot management of instances in Proxmox VE cluster
description:
  - Allows you to list snapshots from instances in Proxmox VE cluster.
  - Supports both KVM and LXC, OpenVZ has not been tested, as it is no longer supported on Proxmox VE.
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  hostname:
    description:
      - The instance name.
    type: str
  vmid:
    description:
      - The instance ID.
      - If not set, will be fetched from PromoxAPI based on the hostname.
    type: str
  snapname:
    description:
      - Name of the snapshot that has to be listed.
    type: str
    required: false

notes:
  - Requires proxmoxer and requests modules on host. These modules can be installed with pip.
author: Jeffrey van Pelt (@Thulium-Drake)
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: List all snapshots for container or VM
  community.proxmox.proxmox_snap_info:
    api_user: root@pam
    api_password: 1q2w3e
    api_host: node1
    vmid: 100

- name: List specific snapshot for container or VM
  community.proxmox.proxmox_snap_info:
    api_user: root@pam
    api_password: 1q2w3e
    api_host: node1
    vmid: 100
    snapname: my-snapshot
"""

RETURN = r"""
snapshot:
  description: Snapshot information when snapname is provided and found.
  returned: when snapname is provided and the snapshot exists
  type: dict
snapshots:
  description: List of snapshots when snapname is not provided.
  returned: when snapname is not provided
  type: list
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (proxmox_auth_argument_spec, ProxmoxAnsible)


class ProxmoxSnapAnsible(ProxmoxAnsible):
    def snapshot(self, vm, vmid):
        return getattr(self.proxmox_api.nodes(vm['node']), vm['type'])(vmid).snapshot


def main():
    module_args = proxmox_auth_argument_spec()
    snap_args = dict(
        vmid=dict(required=False),
        hostname=dict(),
        snapname=dict(type='str', required=False),
    )
    module_args.update(snap_args)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    proxmox = ProxmoxSnapAnsible(module)

    vmid = module.params['vmid']
    hostname = module.params['hostname']
    snapname = module.params['snapname']

    # If hostname is set get the VM id from ProxmoxAPI
    if not vmid and hostname:
        vmid = proxmox.get_vmid(hostname)
    elif not vmid:
        module.exit_json(changed=False, msg="Vmid could not be fetched (vmid or hostname required)")

    vm = proxmox.get_vm(vmid)

    try:
        snapshots = proxmox.snapshot(vm, vmid).get()
        if snapname:
            snapshot = next(
                (s for s in snapshots if s.get('name') == snapname),
                None
            )

            if not snapshot:
                module.exit_json(
                    changed=False,
                    snapshots=[],
                    msg=f"Snapshot '{snapname}' not found"
                )

            module.exit_json(
                changed=False,
                snapshot=snapshot
            )

        # No snapname → return all snapshots
        module.exit_json(
            changed=False,
            snapshots=snapshots
        )

    except Exception as e:
        module.fail_json(msg="Failed to list snapshots: %s" % to_native(e))


if __name__ == '__main__':
    main()
