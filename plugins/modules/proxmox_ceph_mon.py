#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, (@teslamania) <nicolas.vial@protonmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
module: proxmox_ceph_mon
version_added: 1.5.0
short_description: Add or delete Ceph Monitor.
description:
  - Add or delete monitors of a ceph cluster.
author: Vial Nicolas (@teslamania)
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none

options:
    state:
        description: Indicate whether the Ceph monitor should be present (created if missing) or absent (deleted if it exists).
        required: true
        choices: ['present', 'absent']
        type: str
    node:
        description: The cluster node name.
        required: true
        type: str

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module
"""


EXAMPLES = r"""
- name: Add a ceph monitor
  community.proxmox.proxmox_ceph_mon:
    api_host: proxmox-01.example.com
    api_user: root@pam
    api_password: secret
    node: proxmox-02
    state: present

- name: Delete a ceph monitor
  community.proxmox.proxmox_ceph_mon:
    api_host: proxmox-01.example.com
    api_user: root@pam
    api_password: secret
    node: proxmox-02
    state: absent
"""

RETURN = r"""
monitor:
    description: The node name.
    type: str
    returned: always
msg:
    description: The output message that the module generates.
    type: str
    returned: always
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    proxmox_auth_argument_spec,
    ProxmoxAnsible,
)


class ProxmoxCephMonAnsible(ProxmoxAnsible):
    def check_node(self, node):
        nodes = self.proxmox_api.cluster.resources.get(type="node")
        nodes = [item["node"] for item in nodes]
        if node not in nodes:
            self.module.fail_json(
                msg="Node %s does not exist in the cluster" % node
            )

    def check_monitors(self, node):
        monitors = self.proxmox_api.nodes(node).ceph.mon.get()
        for mon in monitors:
            if mon["name"] == node:
                return True
        return False

    def add_mon(self, monitor):
        self.check_node(monitor)
        if self.check_monitors(monitor):
            self.module.exit_json(
                changed=False,
                msg="Monitor already exists",
                monitor=monitor
            )
        else:
            if not self.module.check_mode:
                self.proxmox_api.nodes(monitor).ceph.mon(monitor).create()
                msg = f"Monitor {monitor} added"
            else:
                msg = f"Monitor {monitor} would be added"

            self.module.exit_json(
                changed=True,
                msg=msg,
                monitor=monitor
            )

    def del_mon(self, monitor):
        self.check_node(monitor)
        if self.check_monitors(monitor):
            if not self.module.check_mode:
                self.proxmox_api.nodes(monitor).ceph.mon(monitor).delete()
                msg = f"Monitor {monitor} deleted"
            else:
                msg = f"Monitor {monitor} would be deleted"

            self.module.exit_json(
                changed=True,
                msg=msg,
                monitor=monitor
            )
        else:
            self.module.exit_json(
                changed=False,
                msg="Monitor not present",
                monitor=monitor
            )


def main():
    module_args = proxmox_auth_argument_spec()
    monitor_args = dict(
        node=dict(type='str', required=True),
        state=dict(choices=['present', 'absent'], required=True),
    )

    module_args.update(monitor_args)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[("api_password", "api_token_id")],
        required_together=[("api_token_id", "api_token_secret")],
    )

    proxmox = ProxmoxCephMonAnsible(module)
    state = module.params['state']

    if state == 'present':
        try:
            proxmox.add_mon(module.params['node'])
        except Exception as e:
            module.fail_json(
                msg="Adding monitor failed with exception: %s" % to_native(e)
            )

    elif state == 'absent':
        try:
            proxmox.del_mon(module.params['node'])
        except Exception as e:
            module.fail_json(
                msg="Deleting monitor failed with exception: %s" % to_native(e)
            )


if __name__ == "__main__":
    main()
