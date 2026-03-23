#!/usr/bin/python
#
# Copyright (c) 2023, Sergei Antipov (UnderGreen) <greendayonfire@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_pool
short_description: Pool management for Proxmox VE cluster
description:
  - Create or delete a pool for Proxmox VE clusters.
  - For pool members management please consult M(community.proxmox.proxmox_pool_member) module.
author: "Sergei Antipov (@UnderGreen) <greendayonfire@gmail.com>"
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  poolid:
    description:
      - The pool ID.
    type: str
    aliases: ["name"]
    required: true
  state:
    description:
      - Indicate desired state of the pool.
      - The pool must be empty prior deleting it with O(state=absent).
    choices: ['present', 'absent']
    default: present
    type: str
  comment:
    description:
      - Specify the description for the pool.
      - Parameter is ignored when pool already exists or O(state=absent).
    type: str
  vms:
    description:
      - List of VM IDs or names to add or remove from the pool.
    type: list
    elements: str
  storage:
    description:
      - List of storage IDs to add or remove from the pool.
    type: list
    elements: str
  members_state:
    description:
      - Indicate desired state of the members provided.
    choices: ['present', 'absent']
    default: present
    type: str

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Create new Proxmox VE pool
  community.proxmox.proxmox_pool:
    api_host: node1
    api_user: root@pam
    api_password: password
    poolid: test
    comment: 'New pool'

- name: Delete the Proxmox VE pool
  community.proxmox.proxmox_pool:
    api_host: node1
    api_user: root@pam
    api_password: password
    poolid: test
    state: absent

- name: Create new Proxmox VE pool with members of both 'vm' and 'storage' types
  community.proxmox.proxmox_pool:
    api_host: node1
    api_user: root@pam
    api_password: password
    poolid: test
    comment: 'A pool'
    vms:
      - pxe.home.arpa
      - 101
    storage:
      - zfs-storage

- name: Ensure Proxmox VE pool is present, but members of both 'vm' and 'storage' types are absent
  community.proxmox.proxmox_pool:
    api_host: node1
    api_user: root@pam
    api_password: password
    poolid: test
    comment: 'My pool'
    vms:
      - pxe.home.arpa
    storage:
      - zfs-storage
    members_state : absent
"""

RETURN = r"""
poolid:
  description: The pool ID.
  returned: success
  type: str
  sample: test
members:
  description: Members of the pool.
  returned: success
  type: list
  elements: dict
  sample: [
    {
      "name": "template-ubuntu-24-04-cloud",
      "disk": 0,
      "node": "node1",
      "maxdisk": 3758096384,
      "id": "qemu/101",
      "template": 1,
      "netout": 0,
      "status": "stopped",
      "uptime": 0,
      "type": "qemu",
      "mem": 0,
      "diskwrite": 0,
      "netin": 0,
      "diskread": 0,
      "vmid": 101,
      "maxcpu": 1,
      "cpu": 0,
      "maxmem": 4294967296
    },
    {
      "content": "rootdir,images",
      "status": "available",
      "type": "storage",
      "disk": 29903578936,
      "node": "node1",
      "storage": "local-lvm",
      "plugintype": "lvmthin",
      "maxdisk": 151640866816,
      "id": "storage/node1/local-lvm",
      "shared": 0
    }
  ]
msg:
  description: A short message on what the module did.
  returned: always
  type: str
  sample: "Pool test successfully created"
"""

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
)


def module_args():
    return dict(
        poolid=dict(type="str", aliases=["name"], required=True),
        comment=dict(type="str"),
        state=dict(default="present", choices=["present", "absent"]),
        vms=dict(type="list", elements="str"),
        storage=dict(type="list", elements="str"),
        members_state=dict(default="present", choices=["present", "absent"]),
    )


def module_options():
    return {}


class ProxmoxPoolAnsible(ProxmoxAnsible):
    def is_pool_existing(self, poolid):
        """Check whether pool already exist

        :param poolid: str - name of the pool
        :return: bool - is pool exists?
        """
        try:
            self.proxmox_api.pools.get(poolid=poolid)
            return True
        except Exception as e:
            error_str = str(e).lower()
            if "does not exist" in error_str:
                return False
            self.module.fail_json(msg=f"Unable to retrieve pool {poolid}: {e}")

    def is_pool_empty(self, poolid: str) -> bool:
        """Check whether pool has members

        :param poolid: str - name of the pool
        :return: bool - is pool empty?
        """
        return bool(not (self.get_pool(poolid)["members"]))

    def pool_members(self, poolid: str) -> tuple[list, list]:
        vms = []
        storage = []
        for member in self.get_pool(poolid)["members"]:
            if member["type"] == "storage":
                storage.append(member["storage"])
            else:
                vms.append(member["vmid"])

        return (vms, storage)

    def flush_pool_members(self, poolid: str):
        if self.module.check_mode:
            return

        try:
            vms, storage = self.pool_members(poolid)
            self.proxmox_api.pools(poolid).put(vms=vms, storage=storage, delete=1)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to delete all members from the pool {poolid}: {e}")

    def create_pool(self, poolid, comment=None):
        """Create Proxmox VE pool

        :param poolid: str - name of the pool
        :param comment: str, optional - Description of a pool
        :return: None
        """

        if self.module.check_mode:
            return

        existing_pool = self.is_pool_existing(poolid)
        if not existing_pool:
            try:
                self.proxmox_api.pools.post(poolid=poolid, comment=comment)
            except Exception as e:
                self.module.fail_json(msg=f"Failed to create pool with ID {poolid}: {e}")

    def delete_pool(self, poolid):
        """Delete Proxmox VE pool

        :param poolid: str - name of the pool
        :return: None
        """
        if not self.is_pool_existing(poolid):
            self.module.exit_json(changed=False, poolid=poolid, msg=f"Pool {poolid} doesn't exist")

        if self.module.check_mode:
            return

        if not self.is_pool_empty(poolid):
            self.flush_pool_members(poolid)

            try:
                self.proxmox_api.pools.delete(poolid=poolid)
            except Exception as e:
                self.module.fail_json(msg=f"Failed to delete pool with ID {poolid}: {e}")

    def pool_needs_update(self, poolid: str, vms: str, storage: str, members_state: str) -> bool:
        existing_vms, existing_storage = self.pool_members(poolid)
        intersect_vms = set(existing_vms) & set(vms)
        intersect_storage = set(existing_storage) & set(storage)
        return not (
            (  # Nothing to add
                members_state == "present" and intersect_vms == set(vms) and intersect_storage == set(storage)
            )
            or (  # Nothing to remove
                members_state == "absent" and intersect_vms == set() and intersect_storage == set()
            )
        )

    def update_pool(self, poolid: str, vms: str, storage: str, members_state: str) -> tuple[list, list]:
        existing_vms, existing_storage = self.pool_members(poolid)
        payload = {}
        verb = "add"

        if members_state == "present":
            payload = {
                "poolid": poolid,
                "vms": set(vms) - set(existing_vms),
                "storage": set(storage) - set(existing_storage)
            }
        else:
            payload = {
                "poolid": poolid,
                "delete": 1,
                "vms": set(vms) & set(existing_vms),
                "storage": set(storage) & set(existing_storage)
            }
            verb = "remove"

        try:
            self.proxmox_api.pools.put(payload)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to {verb} members to pool with ID {poolid}: {e}")
        finally:
            return self.pool_members(poolid)


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxPoolAnsible(module)

    poolid = module.params["poolid"]
    comment = module.params["comment"]
    state = module.params["state"]
    vms = module.params["vms"]
    storage = module.params["storage"]
    members_state = module.params["members_state"]

    if state == "present":
        if not proxmox.is_pool_existing:
            proxmox.create_pool(poolid, comment)
            current_members = []
            if members_state == "present":
                vms_members, storage_members = proxmox.update_pool(poolid, vms, storage, members_state)
                current_members = vms_members + storage_members

            module.exit_json(
                changed=True,
                poolid=poolid,
                members=current_members,
                msg=f"Pool {poolid} successfully created",
            )
        elif proxmox.pool_needs_update(poolid, vms, storage, members_state):
            vms_members, storage_members = proxmox.update_pool(poolid, vms, storage, members_state)

            module.exit_json(
                changed=True,
                poolid=poolid,
                members=vms_members + storage_members,
                msg=f"Pool {poolid} successfully updated",
            )
        else:
            module.exit_json(
                changed=False, poolid=poolid, members=vms + storage, msg=f"Pool {poolid} already up to date"
            )
    else:
        if not proxmox.is_pool_empty(poolid):
            proxmox.flush_pool_members(poolid)

        proxmox.delete_pool(poolid)
        module.exit_json(changed=True, poolid=poolid, msg=f"Pool {poolid} successfully deleted")


if __name__ == "__main__":
    main()
