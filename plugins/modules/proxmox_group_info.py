#!/usr/bin/python
#
# Copyright Tristan Le Guern <tleguern at bouledef.eu>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_group_info
short_description: Retrieve information about one or more Proxmox VE groups
description:
  - Retrieve information about one or more Proxmox VE groups.
options:
  group:
    description:
      - Restrict results to a specific group.
    aliases: ['groupid', 'name']
    type: str
author: Tristan Le Guern (@tleguern)
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module
"""


EXAMPLES = r"""
- name: List existing groups
  community.proxmox.proxmox_group_info:
    api_host: helldorado
    api_user: root@pam
    api_password: "{{ password | default(omit) }}"
    api_token_id: "{{ token_id | default(omit) }}"
    api_token_secret: "{{ token_secret | default(omit) }}"
  register: proxmox_groups

- name: Retrieve information about the admin group
  community.proxmox.proxmox_group_info:
    api_host: helldorado
    api_user: root@pam
    api_password: "{{ password | default(omit) }}"
    api_token_id: "{{ token_id | default(omit) }}"
    api_token_secret: "{{ token_secret | default(omit) }}"
    group: admin
  register: proxmox_group_admin
"""


RETURN = r"""
proxmox_groups:
  description: List of groups.
  returned: always, but can be empty
  type: list
  elements: dict
  contains:
    comment:
      description: Short description of the group.
      returned: on success, can be absent
      type: str
    groupid:
      description: Group name.
      returned: on success
      type: str
    users:
      description: List of users in the group.
      returned: on success
      type: list
      elements: str
"""


from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
)


def module_args():
    return dict(
        group=dict(type="str", aliases=["groupid", "name"]),
    )


def module_options():
    return {}


class ProxmoxGroupInfoAnsible(ProxmoxAnsible):
    def get_group(self, groupid):
        try:
            group = self.proxmox_api.access.groups.get(groupid)
        except Exception:
            self.module.fail_json(msg=f"Group '{groupid}' does not exist")
        group["groupid"] = groupid
        return ProxmoxGroup(group)

    def get_groups(self):
        groups = self.proxmox_api.access.groups.get()
        return [ProxmoxGroup(group) for group in groups]


class ProxmoxGroup:
    def __init__(self, group):
        self.group = dict()
        # Data representation is not the same depending on API calls
        for k, v in group.items():
            if k == "users" and isinstance(v, str):
                self.group["users"] = v.split(",")
            elif k == "members":
                self.group["users"] = group["members"]
            else:
                self.group[k] = v


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxGroupInfoAnsible(module)

    result = dict(changed=False)

    group = module.params["group"]

    if group:
        groups = [proxmox.get_group(groupid=group)]
    else:
        groups = proxmox.get_groups()
    result["proxmox_groups"] = [group.group for group in groups]

    module.exit_json(**result)


if __name__ == "__main__":
    main()
