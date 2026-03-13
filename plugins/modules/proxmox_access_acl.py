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
        - Type of access control.
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

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    ansible_to_proxmox_bool,
    create_proxmox_module,
    proxmox_to_ansible_bool,
)


def _ace_matches(ace, desired):
    if ace["path"] != desired["path"]:
        return False
    roleid = desired.get("roleid")
    if roleid and ace["roleid"] != roleid:
        return False
    ace_type = desired.get("type")
    if ace_type and ace["type"] != ace_type:
        return False
    ugid = desired.get("ugid")
    if ugid and ace["ugid"] != ugid:
        return False
    propagate = desired.get("propagate")
    if propagate:
        ace_propagate = proxmox_to_ansible_bool(ace.get("propagate", 1))
        if ace_propagate != propagate:
            return False
    return True


def _build_put_payload(ace_data, delete=False):
    payload = {
        "path": ace_data["path"],
        "roles": ace_data["roleid"],
        "propagate": ace_data["propagate"],
        f"{ace_data['type']}s": ace_data["ugid"],
    }
    if delete:
        payload["delete"] = 1
    return payload


def module_args():
    return dict(
        state=dict(choices=["present", "absent"], default="present"),
        path=dict(type="str", required=False),
        roleid=dict(type="str", required=False),
        type=dict(type="str", choices=["user", "group", "token"]),
        ugid=dict(type="str"),
        propagate=dict(type="bool", default=True),
    )


def module_options():
    return dict(
        supports_check_mode=False,
        required_if=[
            ["state", "present", ["path", "roleid", "type", "ugid"]],
            ["state", "absent", ["path"]],
        ],
    )


class ProxmoxAccessACLAnsible(ProxmoxAnsible):
    def _get_acls(self):
        return self.proxmox_api.access.acl.get()

    def _put_acl(self, **data):
        return self.proxmox_api.access.acl.put(**data)

    def _filter_matching_aces(self, existing_acls, desired):
        return [ace for ace in existing_acls if _ace_matches(ace, desired)]

    def create(self, existing_acls, desired):
        if self._filter_matching_aces(existing_acls, desired):
            return False

        payload = _build_put_payload(
            {
                "path": desired["path"],
                "roleid": desired["roleid"],
                "type": desired["type"],
                "ugid": desired["ugid"],
                "propagate": ansible_to_proxmox_bool(desired["propagate"]),
            },
            delete=False,
        )
        self._put_acl(**payload)
        return True

    def delete(self, existing_acls, desired):
        to_remove = self._filter_matching_aces(existing_acls, desired)

        if not to_remove:
            return False

        for ace in to_remove:
            payload = _build_put_payload(
                {
                    "path": ace["path"],
                    "roleid": ace["roleid"],
                    "type": ace["type"],
                    "ugid": ace["ugid"],
                    "propagate": ace.get("propagate", 1),
                },
                delete=True,
            )
            self._put_acl(**payload)
        return True


def run_module():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxAccessACLAnsible(module)

    state = module.params.get("state")
    path = module.params["path"]
    roleid = module.params["roleid"]
    ace_type = module.params["type"]
    ugid = module.params["ugid"]
    propagate = module.params["propagate"]

    result = dict(
        changed=False,
        old_acls=[],
    )

    try:
        result["old_acls"] = existing_acls = proxmox._get_acls()
        desired_ace = dict(path=path, roleid=roleid, type=ace_type, ugid=ugid, propagate=propagate)

        if state == "present":
            r = proxmox.create(existing_acls, desired_ace)
        elif state == "absent":
            r = proxmox.delete(existing_acls, desired_ace)

        result["changed"] = r
        if r:
            result["new_acls"] = proxmox._get_acls()
    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
