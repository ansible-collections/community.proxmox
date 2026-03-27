#!/usr/bin/python
#
# Copyright (c) 2023, Sergei Antipov (UnderGreen) <greendayonfire@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import sys
from typing import Any

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


class ProxmoxPool:
    def __init__(self, pool: dict[str, Any]):
        self.poolid: str = pool.get("poolid", "")
        self.comment: str = pool.get("comment", "")
        self.members: list = pool.get("members", [])

        self.vmids: list[str] = []
        self.storage_ids: list[str] = []
        for member in self.members:
            if "vmid" in member:
                self.vmids.append(member["vmid"])
            if "storage" in member:
                self.storage_ids.append(member["storage"])

    def __bool__(self) -> bool:
        return self.poolid != ""

    def has_members(self) -> bool:
        return self.members != []

    def get_member_ids(self) -> tuple[list[str], list[str]]:
        return (self.vmids, self.storage_ids)


class ProxmoxPoolAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.pool = ProxmoxPool({})
        self.pool_not_found = False

    def cache_pool(self, poolid: str, refresh: bool = False):
        """Cache it to memory to avoid more API calls

        :param poolid: str - name of the pool
        :param refresh: bool - whether to force a cache refresh from API
        :return: None
        """
        if refresh or (not self.pool and not self.pool_not_found):
            try:
                pool = self.proxmox_api.pools.get(poolid=poolid)
            except Exception as e:
                if "does not exist" in str(e).lower():
                    self.pool = ProxmoxPool({})
                    self.pool_not_found = True
                else:
                    self.module.fail_json(msg=f"Unable to retrieve pool {poolid}: {e}")
                    sys.exit(1)
            else:
                if pool:
                    self.pool = ProxmoxPool(pool)
                    self.pool_not_found = False

    def is_pool_existing(self, poolid: str) -> bool:
        """Check whether pool already exists, using caching to avoid more API calls

        :param poolid: str - name of the pool
        :return: bool - does pool exist?
        """
        self.cache_pool(poolid)
        return bool(self.pool and not self.pool_not_found)

    def get_pool_members(self, poolid: str) -> list:
        """Retrieve pool members

        :param poolid: str - name of the pool
        :return: list[str] - list of members
        """
        self.cache_pool(poolid)
        return self.pool.members

    def flush_pool_members(self, poolid: str):
        """Delete all members of the Proxmox VE pool (vms and storage)

        :param poolid: str - name of the pool
        :return: None
        """
        if self.module.check_mode:
            return
        try:
            self.proxmox_api.pools.put(poolid=poolid, vms=self.pool.vmids, storage=self.pool.storage_ids, delete=1)
            self.cache_pool(poolid, refresh=True)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to delete all members from the pool {poolid}: {e}")

    def create_pool(self, poolid: str, comment: str = ""):
        """Create Proxmox VE pool

        :param poolid: str - name of the pool
        :param comment: str, optional - Description of a pool
        :return: None
        """
        if self.module.check_mode:
            return
        if not self.is_pool_existing(poolid):
            payload = {"poolid": poolid}
            if comment != "":
                payload["comment"] = comment
            try:
                self.proxmox_api.pools.post(poolid=poolid, comment=comment)
                self.cache_pool(poolid, refresh=True)
            except Exception as e:
                self.module.fail_json(msg=f"Failed to create pool with ID {poolid}: {e}")

    def delete_pool(self, poolid):
        """Delete Proxmox VE pool

        :param poolid: str - name of the pool
        :return: None
        """
        if not self.is_pool_existing(poolid):
            self.module.exit_json(changed=False, poolid=poolid, msg=f"Unable to delete inexistent pool {poolid}")
        if self.module.check_mode:
            return
        if self.pool.has_members():
            self.flush_pool_members(poolid)
            try:
                self.proxmox_api.pools.delete(poolid=poolid)
                self.cache_pool(poolid, refresh=True)
            except Exception as e:
                self.module.fail_json(msg=f"Failed to delete pool with ID {poolid}: {e}")

    def pool_needs_update(
        self, poolid: str, comment: str, vms: list[str], storage: list[str], members_state: str
    ) -> bool:
        self.cache_pool(poolid)

        comment = comment or ""
        if comment != self.pool.comment:
            return True

        vms = vms or []
        storage = storage or []
        intersect_vms = set(self.pool.vmids) & set(vms)
        intersect_storage = set(self.pool.storage_ids) & set(storage)
        union_vms = set(self.pool.vmids).union(set(vms))
        union_storage = set(self.pool.storage_ids).union(set(storage))

        if members_state == "present" and (
            union_vms != set(self.pool.vmids) or union_storage != set(self.pool.storage_ids)
        ):  # Something to add
            return True

        return members_state == "absent" and (
            intersect_vms != set() or intersect_storage != set()
        )  # Something to remove, or not

    def update_pool(self, poolid: str, comment: str, vms: list[str], storage: list[str], members_state: str):
        if not self.is_pool_existing(poolid):
            self.module.fail_json(msg=f"Unable to get members for inexistent pool {poolid}")
        payload = {}
        verb = "add"
        vms = vms or []
        storage = storage or []

        if members_state == "present":
            payload = {
                "poolid": poolid,
                "comment": comment,
                "vms": set(vms) - set(self.pool.vmids),
                "storage": set(storage) - set(self.pool.storage_ids),
            }
        else:
            payload = {
                "poolid": poolid,
                "comment": comment,
                "delete": 1,
                "vms": set(vms) & set(self.pool.vmids),
                "storage": set(storage) & set(self.pool.storage_ids),
            }
            verb = "remove"

        try:
            self.proxmox_api.pools.put(payload)
            self.cache_pool(poolid, refresh=True)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to {verb} members to pool with ID {poolid}: {e}")


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
            if members_state == "present":
                proxmox.update_pool(poolid, comment, vms, storage, members_state)

            module.exit_json(
                changed=True,
                poolid=poolid,
                members=proxmox.get_pool_members(poolid),
                msg=f"Pool {poolid} successfully created",
            )
        elif proxmox.pool_needs_update(poolid, comment, vms, storage, members_state):
            proxmox.update_pool(poolid, comment, vms, storage, members_state)

            module.exit_json(
                changed=True,
                poolid=poolid,
                members=proxmox.get_pool_members(poolid),
                msg=f"Pool {poolid} successfully updated",
            )
        else:
            module.exit_json(
                changed=False,
                poolid=poolid,
                members=proxmox.get_pool_members(poolid),
                msg=f"Pool {poolid} already up to date",
            )
    else:
        proxmox.delete_pool(poolid)
        module.exit_json(changed=True, poolid=poolid, msg=f"Pool {poolid} successfully deleted")


if __name__ == "__main__":
    main()
