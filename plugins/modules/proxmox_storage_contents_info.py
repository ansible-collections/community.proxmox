#!/usr/bin/python
#
# Copyright Julian Vanden Broeck (@l00ptr) <julian.vandenbroeck at dalibo.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_storage_contents_info
short_description: List content from a Proxmox VE storage
description:
  - Retrieves information about stored objects on a specific storage attached to a node.
options:
  storage:
    description:
      - Only return content stored on that specific storage.
    aliases: ['name']
    type: str
    required: true
  node:
    description:
      - Proxmox node to which the storage is attached.
    type: str
    required: true
  content:
    description:
      - Filter on a specific content type.
    type: str
    choices: ["all", "backup", "rootdir", "images", "iso", "import"]
    default: "all"
  vmid:
    description:
      - Filter on a specific VMID.
    type: int
author: Julian Vanden Broeck (@l00ptr)
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module
"""


EXAMPLES = r"""
- name: List existing storages
  community.proxmox.proxmox_storage_contents_info:
    api_host: helldorado
    api_user: root@pam
    api_password: "{{ password | default(omit) }}"
    api_token_id: "{{ token_id | default(omit) }}"
    api_token_secret: "{{ token_secret | default(omit) }}"
    storage: lvm2
    content: backup
    vmid: 130
"""


RETURN = r"""
proxmox_storage_content:
  description: Content of of storage attached to a node.
  type: list
  returned: success
  elements: dict
  contains:
    content:
      description: Proxmox content of listed objects on this storage.
      type: str
      returned: success
    ctime:
      description: Creation time of the listed objects.
      type: str
      returned: success
    format:
      description: Format of the listed objects (can be V(raw), V(pbs-vm), V(iso),...).
      type: str
      returned: success
    size:
      description: Size of the listed objects.
      type: int
      returned: success
    subtype:
      description: Subtype of the listed objects (can be V(qemu) or V(lxc)).
      type: str
      returned: When storage is dedicated to backup, typically on PBS storage.
    verification:
      description: Backup verification status of the listed objects.
      type: dict
      returned: When storage is dedicated to backup, typically on PBS storage.
      sample: {
        "state": "ok",
        "upid": "UPID:backup-srv:00130F49:1A12D8375:00001CD7:657A2258:verificationjob:daily\\x3av\\x2dd0cc18c5\\x2d8707:root@pam:"
        }
    volid:
      description: Volume identifier of the listed objects.
      type: str
      returned: success
"""


from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
)


def module_args():
    return dict(
        storage=dict(type="str", required=True, aliases=["name"]),
        content=dict(
            type="str", required=False, default="all", choices=["all", "backup", "rootdir", "images", "iso", "import"]
        ),
        vmid=dict(type="int"),
        node=dict(required=True, type="str"),
    )


def module_options():
    return {}


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxAnsible(module)

    result = dict(changed=False)
    res = proxmox.get_storage_content(
        node=module.params["node"],
        storage=module.params["storage"],
        content=None if module.params["content"] == "all" else module.params["content"],
        vmid=module.params["vmid"],
    )
    result["proxmox_storage_content"] = res
    module.exit_json(**result)


if __name__ == "__main__":
    main()
