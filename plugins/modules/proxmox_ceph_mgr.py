#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, (@teslamania) <nicolas.vial@protonmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
module: proxmox_ceph_mgr
version_added: 1.5.0
short_description: Add or delete Ceph Manager.
description:
  - Add or delete managers of a ceph cluster.
author: Vial Nicolas (@teslamania)
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none

options:
    state:
        description: Indicate whether the Ceph manager should be present (created if missing) or absent (deleted if it exists).
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
- name: Add a ceph manager
  community.proxmox.proxmox_ceph_mgr:
    api_host: proxmox-01.example.com
    api_user: root@pam
    api_password: secret
    node: proxmox-02
    state: present

- name: Delete a ceph manager
  community.proxmox.proxmox_ceph_mgr:
    api_host: proxmox-01.example.com
    api_user: root@pam
    api_password: secret
    node: proxmox-02
    state: absent
"""

RETURN = r"""
manager:
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


class ProxmoxCephMgrAnsible(ProxmoxAnsible):
    def check_node(self, node):
        nodes = self.proxmox_api.cluster.resources.get(type="node")
        nodes = [item["node"] for item in nodes]
        if node not in nodes:
            self.module.fail_json(
                msg="Node %s does not exist in the cluster" % node
            )

    def check_managers(self, node):
        managers = self.proxmox_api.nodes(node).ceph.mgr.get()
        for mgr in managers:
            if mgr["name"] == node:
                return True
        return False

    def add_mgr(self, manager):
        self.check_node(manager)
        if self.check_managers(manager):
            self.module.exit_json(
                changed=False,
                msg="Manager already exists",
                manager=manager
            )
        else:
            if not self.module.check_mode:
                self.proxmox_api.nodes(manager).ceph.mgr(manager).create()
                msg = f"Manager {manager} added"
            else:
                msg = f"Manager {manager} would be added"

            self.module.exit_json(
                changed=True,
                msg=msg,
                manager=manager
            )

    def del_mgr(self, manager):
        self.check_node(manager)
        if self.check_managers(manager):
            if not self.module.check_mode:
                self.proxmox_api.nodes(manager).ceph.mgr(manager).delete()
                msg = f"Manager {manager} deleted"
            else:
                msg = f"Manager {manager} would be deleted"

            self.module.exit_json(
                changed=True,
                msg=msg,
                manager=manager
            )
        else:
            self.module.exit_json(
                changed=False,
                msg="Manager not present",
                manager=manager
            )


def main():
    module_args = proxmox_auth_argument_spec()
    manager_args = dict(
        node=dict(type='str', required=True),
        state=dict(choices=['present', 'absent'], required=True),
    )

    module_args.update(manager_args)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[("api_password", "api_token_id")],
        required_together=[("api_token_id", "api_token_secret")],
    )

    proxmox = ProxmoxCephMgrAnsible(module)
    state = module.params['state']

    if state == 'present':
        try:
            proxmox.add_mgr(module.params['node'])
        except Exception as e:
            module.fail_json(
                msg="Adding manager failed with exception: %s" % to_native(e)
            )

    elif state == 'absent':
        try:
            proxmox.del_mgr(module.params['node'])
        except Exception as e:
            module.fail_json(
                msg="Deleting manager failed with exception: %s" % to_native(e)
            )


if __name__ == "__main__":
    main()
