#!/usr/bin/python

# Copyright (c) 2025, Markus Kötter <koetter@cispa.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-FileCopyrightText: (c) 2025, Markus Kötter <koetter@cispa.de>
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
---
module: proxmox_access_acl
short_description: Manages ACLs on the Proxmox PVE cluster
version_added: "1.1.0"
author:
  - Markus Kötter (@commonism)
description:
  - Setting ACLs via C(/access/acls) to grant permission to interact with objects.
attributes:
  check_mode:
    support: none
  diff_mode:
    support: none
options:
  state:
    description:
      - Indicate desired state of the ACL.
    type: str
    required: true
    choices: ["present", "absent"]
    default: present
  path:
    description:
      - Access Control Path.
    type: str
  roleid:
    description:
        - The name of the role.
    type: str
  type:
    description:
        - type of access control
    choices: ["user", "group", "token"]
    type: str
  ugid:
    description:
      - The ID of user or group.
    type: str
  propagate:
    description:
      - Allow to propagate (inherit) permissions.
    type: bool
    default: true
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Create ACE
  community.proxmox.proxmox_access_acl:
    api_host: "{{ ansible_host }}"
    api_password: "{{ proxmox_root_pw | default(lookup('ansible.builtin.env', 'PROXMOX_PASSWORD', default='')) }}"
    api_user: root@pam

    state: "present"
    path: /vms/100
    type: user
    ugid: "a01mako@pam"
    roleid: PVEVMUser
    propagate: 1

- name: Delete all ACEs for a given path
  community.proxmox.proxmox_access_acl:
    api_host: "{{ ansible_host }}"
    api_password: "{{ proxmox_root_pw | default(lookup('ansible.builtin.env', 'PROXMOX_PASSWORD', default='')) }}"
    api_user: root@pam

    state: "absent"
    path: /vms/100
"""

RETURN = r"""
# These are examples of possible return values, and in general should use other names for return values.
old_acls:
    description: The original name param that was passed in.
    type: list
    returned: always
new_acls:
    description: The output message that the test module generates.
    type: list
    returned: when changed
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    proxmox_auth_argument_spec,
)


class ProxmoxAccessACLAnsible(ProxmoxAnsible):
    def _get(self):
        acls = self.proxmox_api.access.acl.get()
        return acls

    def _put(self, **data):
        return self.proxmox_api.access.acl.put(**data)

    def create(self, acls, path, roleid, type, ugid, propagate):
        for ace in acls:
            if (ace["path"], ace["roleid"], ace["type"], ace["ugid"], bool(ace.get("propagate", 1))) == (
                path,
                roleid,
                type,
                ugid,
                propagate,
            ):
                return False

        data = {"path": path, "roles": roleid, "propagate": int(propagate), f"{type}s": ugid}

        self._put(**data)
        return True

    def delete(self, acls, path, roleid, type, ugid, propagate):
        changed = False
        for ace in acls:
            if path != ace["path"]:
                continue
            if roleid and roleid != ace["roleid"]:
                continue
            if type and type != ace["type"]:
                continue
            if ugid and ace["ugid"] != ugid:
                continue
            if propagate and bool(ace.get("propagate", 1)) != propagate:
                continue

            data = {
                "path": ace["path"],
                "roles": ace["roleid"],
                "propagate": ace["propagate"],
                f"{ace['type']}s": ace["ugid"],
            }

            self._put(**data, delete="1")
            changed = True
        return changed


def run_module():
    module_args = proxmox_auth_argument_spec()

    acl_args = dict(
        state=dict(choices=["present", "absent"], default="present"),
        path=dict(type="str", required=False),
        roleid=dict(type="str", required=False),
        type=dict(type="str", choices=["user", "group", "token"]),
        ugid=dict(type="str"),
        propagate=dict(type="bool", default=True),
    )

    module_args.update(acl_args)

    result = dict(
        changed=False,
        old_acls=[],
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    if module.params["state"] == "present":
        required = frozenset({"path", "roleid", "type", "ugid"})
        exists = frozenset(map(lambda x: x[0], filter(lambda x: x[1] is not None, module.params.items())))
        if len(required - exists) > 0:
            result["failed"] = True
            result["missing_parameters"] = required - exists
            module.fail_json(
                msg=f"The following required parameters are not provided {sorted(required - exists)}", **result
            )

    proxmox = ProxmoxAccessACLAnsible(module)

    state = module.params.get("state")
    path = module.params["path"]
    roleid = module.params["roleid"]
    type = module.params["type"]
    ugid = module.params["ugid"]
    propagate = module.params["propagate"]

    try:
        result["old_acls"] = acls = proxmox._get()

        if state == "present":
            r = proxmox.create(acls, path, roleid, type, ugid, propagate)
        elif state == "absent":
            r = proxmox.delete(acls, path, roleid, type, ugid, propagate)

        result["changed"] = r
        if r:
            result["new_acls"] = proxmox._get()
    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
