#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r"""
module: proxmox_role
short_description: Role management for Proxmox VE cluster
version_added: "1.6.0"
author:
  - Clément Cruau (@PendaGTP)
description:
  - Create, update or delete roles in Proxmox VE cluster.
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  roleid:
    description:
      - The role ID.
    type: str
    aliases: ["name"]
    required: true
  state:
    description:
      - Indicate desired state of the role.
      - Custom roles are not allowed to use PVE reserved prefix.
    type: str
    choices:
      - present
      - absent
    default: present
  privs:
    description:
      - List of privileges the role has.
    type: list
    aliases: ["privileges"]
    elements: str
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Create new Proxmox VE role
  community.proxmox.proxmox_role:
    api_host: node1
    api_user: root@pam
    api_password: password
    roleid: test
    privs:
      - VM.PowerMgmt
      - VM.Console

- name: Delete Proxmox VE role
  community.proxmox.proxmox_role:
    api_host: node1
    api_user: root@pam
    api_password: password
    roleid: test
    state: absent
"""

RETURN = r"""
roleid:
  description: The role ID which was created/updated/deleted.
  returned: on success
  type: str
  sample:
    test
msg:
  description: A short message on what the module did.
  returned: always
  type: str
  sample: "Role test successfully created"
"""

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    proxmox_auth_argument_spec, ProxmoxAnsible)
from ansible.module_utils.basic import AnsibleModule


def get_proxmox_args():
    return dict(
        state=dict(choices=["present", "absent"], default="present"),
        roleid=dict(aliases=["name"], required=True),
        privs=dict(type="list", aliases=["privileges"], elements="str"),
    )


def get_ansible_module():
    module_args = proxmox_auth_argument_spec()
    module_args.update(get_proxmox_args())

    return AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )


class ProxmoxRoleAnsible(ProxmoxAnsible):

    def __init__(self, module):
        super(ProxmoxRoleAnsible, self).__init__(module)
        self.params = module.params

    def run(self):
        state = self.params.get("state")

        role_params = {
            "roleid": self.params.get("roleid"),
            "privs": self.params.get("privs"),
        }

        if state == "present":
            self.role_present(role_params=role_params)
        elif state == "absent":
            self.role_absent(role_params["roleid"])

    def _get_role(self, roleid):
        try:
            return self.proxmox_api.access.roles.get(roleid)
        except Exception as e:
            error_str = str(e).lower()
            if "does not exist" in error_str:
                return None
            self.module.fail_json(msg=f"Failed to retrieve role {roleid}: {e}")

    def _privs_to_string(self, privs_list):
        if not privs_list:
            return ""
        return ",".join(sorted(privs_list))

    def _role_privs_to_list(self, role_data):
        if not role_data:
            return []
        return sorted([priv for priv, enabled in role_data.items() if enabled])

    def _privs_need_update(self, existing_privs, desired_privs):
        return sorted(existing_privs) != sorted(desired_privs)

    def role_present(self, role_params):
        roleid = role_params["roleid"]
        desired_privs = role_params["privs"] or []

        existing_role = self._get_role(roleid)

        if existing_role is None:
            if self.module.check_mode:
                self.module.exit_json(
                    changed=True,
                    roleid=roleid,
                    msg=f"Role {roleid} would be created"
                )

            try:
                privs_string = self._privs_to_string(desired_privs)
                self.proxmox_api.access.roles.post(
                    roleid=roleid, privs=privs_string)
                self.module.exit_json(
                    changed=True,
                    roleid=roleid,
                    msg=f"Role {roleid} successfully created"
                )
            except Exception as e:
                self.module.fail_json(
                    changed=False,
                    roleid=roleid,
                    msg=f"Failed to create role {roleid}: {e}"
                )
        else:
            existing_privs = self._role_privs_to_list(existing_role)
            needs_update = self._privs_need_update(
                existing_privs, desired_privs)

            if not needs_update:
                self.module.exit_json(
                    changed=False,
                    roleid=roleid,
                    msg=f"Role {roleid} already exists with desired configuration"
                )

            if self.module.check_mode:
                self.module.exit_json(
                    changed=True,
                    roleid=roleid,
                    msg=f"Role {roleid} would be updated"
                )

            try:
                privs_string = self._privs_to_string(desired_privs)
                self.proxmox_api.access.roles(roleid).put(privs=privs_string)
                self.module.exit_json(
                    changed=True,
                    roleid=roleid,
                    msg=f"Role {roleid} successfully updated"
                )
            except Exception as e:
                self.module.fail_json(
                    changed=False,
                    roleid=roleid,
                    msg=f"Failed to update role {roleid}: {e}"
                )

    def role_absent(self, roleid):
        existing_role = self._get_role(roleid)

        if existing_role is None:
            self.module.exit_json(
                changed=False,
                roleid=roleid,
                msg=f"Role {roleid} does not exist"
            )

        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                roleid=roleid,
                msg=f"Role {roleid} would be deleted"
            )

        try:
            self.proxmox_api.access.roles(roleid).delete()
            self.module.exit_json(
                changed=True,
                roleid=roleid,
                msg=f"Role {roleid} successfully deleted",
            )
        except Exception as e:
            self.module.fail_json(
                changed=False,
                roleid=roleid,
                msg=f"Failed to delete role {roleid}: {e}"
            )


def main():
    module = get_ansible_module()
    proxmox = ProxmoxRoleAnsible(module)

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f"An error occurred: {e}")


if __name__ == "__main__":
    main()
