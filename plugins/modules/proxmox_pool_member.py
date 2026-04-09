#!/usr/bin/python
#
# Copyright (c) 2023, Sergei Antipov (UnderGreen) <greendayonfire@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

DOCUMENTATION = r"""
module: proxmox_pool_member
short_description: Add or delete members from Proxmox VE cluster pools
description:
  - Add or remove members from a pool in Proxmox VE clusters.
  - Each member is a dict with either a C(vm) key (vmid or VM name) or a C(storage) key.
  - When O(exclusive=true), the pool membership is reconciled to match exactly O(members),
    ignoring O(state).
author: "Sergei Antipov (@UnderGreen) <greendayonfire@gmail.com>"
attributes:
  check_mode:
    support: full
  diff_mode:
    support: full
options:
  poolid:
    description:
      - The pool ID.
    type: str
    aliases: ["name"]
    required: true
  members:
    description:
      - List of members to add or remove from the pool.
      - Each item is a dict with either a C(vm) key (vmid or VM name)
        or a C(storage) key (storage name as string).
    type: list
    elements: dict
    required: true
    suboptions:
      vm:
        description: VM id or VM name.
        type: str
      storage:
        description: Storage name.
        type: str
  state:
    description:
      - Desired state for each member listed in O(members).
      - Ignored when O(exclusive=true).
    choices: ['present', 'absent']
    default: present
    type: str
  exclusive:
    description:
      - When V(true), reconcile pool membership to match exactly O(members).
      - Members present in the pool but absent from O(members) will be removed.
      - Members in O(members) but absent from the pool will be added.
      - O(state) is ignored when this option is V(true).
      - This option is not loop aware, so if you use `with_' , it will be exclusive per iteration of the loop.
      - If you want multiple members in the pool you need to pass them all to `members' in a single batch.
    type: bool
    default: false

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Add VMs and a storage to a pool
  community.proxmox.proxmox_pool_member:
    api_host: node1
    api_user: root@pam
    api_password: password
    poolid: test
    members:
      - vm: 101
      - vm: pxe.home.arpa
      - storage: zfs-data

- name: Remove a VM and a storage from a pool
  community.proxmox.proxmox_pool_member:
    api_host: node1
    api_user: root@pam
    api_password: password
    poolid: test
    state: absent
    members:
      - vm: 101
      - storage: zfs-data

- name: Enforce exact pool membership (exclusive mode)
  community.proxmox.proxmox_pool_member:
    api_host: node1
    api_user: root@pam
    api_password: password
    poolid: test
    exclusive: true
    members:
      - vm: 101
      - storage: zfs-data
"""

RETURN = r"""
poolid:
  description: The pool ID.
  returned: success
  type: str
  sample: test
members:
  description: Final list of members in the pool after the operation.
  returned: success
  type: list
  elements: dict
  sample: [
    {"vm": "101"},
    {"storage": "zfs-data"}
  ]
msg:
  description: A short message on what the module did.
  returned: always
  type: str
  sample: "Member 101 deleted from the pool test"
"""

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
)


def module_args():
    return dict(
        poolid=dict(type="str", aliases=["name"], required=True),
        members=dict(
            type="list",
            elements="dict",
            required=True,
            options=dict(
                vm=dict(type="str"),
                storage=dict(type="str"),
            ),
        ),
        state=dict(default="present", choices=["present", "absent"]),
        exclusive=dict(type="bool", default=False),
    )


def module_options():
    return {}


class ProxmoxPoolMemberAnsible(ProxmoxAnsible):
    def pool_members(self, poolid: str) -> tuple[set[str]]:
        vms = set()
        storage = set()
        for member in self.get_pool(poolid)["members"]:
            if member["type"] == "storage":
                storage.add(member["storage"])
            else:
                vms.add(member["vmid"])
        return (vms, storage)

    def _resolve_member(self, member_spec: dict[str, str]) -> tuple[str, str]:
        """
        Parse one member dict from the task params.

        Returns (kind, key) where kind is 'vm' or 'storage' and key is
        str (vmid) for VMs or str (storage name) for storages.
        """

        if member_spec.get("storage"):
            return ("storage", member_spec["storage"])
        if member_spec.get("vm"):
            raw = member_spec["vm"]
            try:
                return ("vm", str(int(raw)))
            except (ValueError, TypeError):
                return ("vm", str(self.get_vmid(str(raw))))
        self.module.fail_json(msg=f"Each member must have either a 'vm' or a 'storage' key: {member_spec}")

    def _pool_members_as_dicts(self, vm_ids: set[str], storage_names: set[str]) -> list[dict[str, str]]:
        """Convert internal sets to the output list-of-dicts format."""
        result = [{"vm": str(vmid)} for vmid in sorted(vm_ids)]
        result += [{"storage": s} for s in sorted(storage_names)]
        return result

    def _fail_on_missing_storage(self, storages_to_add: set[str]) -> None:
        # Validate requested storages exist before touching the API.
        if storages_to_add:
            cluster_storages = {s["storage"] for s in self.get_storages(type=None)}
            missing = storages_to_add - cluster_storages
            if missing:
                self.module.fail_json(msg=f"Storage(s) not found in the cluster: {', '.join(sorted(missing))}")

    def reconcile_members(
        self, poolid: str, desired_members: list[dict[str, str]], exclusive: bool, state: str
    ) -> tuple[bool, list[dict[str, str]]]:
        """Compute and apply the delta between current and desired membership.

        - exclusive=True  → desired_members is the full target state (state ignored)
        - exclusive=False → add or remove each spec according to state

        :param poolid: str - name of the pool
        :param desired_members: list[dict[str, str]] - list of member specs to apply (member key must be one of [vm, storage])
        :param exclusive: bool - whether to the whole list or only the delta
        :param state: str - state must be one of [absent, present]
        :return: (bool, list[dict[str, str]]) - Whether state is changed and list of final members
        """
        current_vm_ids, current_storage_names = self.pool_members(poolid)

        resolved = []
        for member in desired_members:
            kind, key = self._resolve_member(member)
            resolved.append((kind, key))

        desired_vm_ids = {key for kind, key in resolved if kind == "vm"}
        desired_storage_names = {key for kind, key in resolved if kind == "storage"}

        if exclusive:
            vms_to_add = desired_vm_ids - current_vm_ids
            vms_to_remove = current_vm_ids - desired_vm_ids
            storages_to_add = desired_storage_names - current_storage_names
            storages_to_remove = current_storage_names - desired_storage_names
        elif state == "present":
            vms_to_add = desired_vm_ids - current_vm_ids
            storages_to_add = desired_storage_names - current_storage_names
            vms_to_remove = set()
            storages_to_remove = set()
        else:
            vms_to_remove = desired_vm_ids & current_vm_ids
            storages_to_remove = desired_storage_names & current_storage_names
            vms_to_add = set()
            storages_to_add = set()

        changed = bool(vms_to_add or vms_to_remove or storages_to_add or storages_to_remove)

        after_vms = (current_vm_ids | vms_to_add) - vms_to_remove
        after_storages = (current_storage_names | storages_to_add) - storages_to_remove

        if not changed:
            return False, self._pool_members_as_dicts(after_vms, after_storages)

        if self.module.check_mode:
            return True, self._pool_members_as_dicts(after_vms, after_storages)

        self._fail_on_missing_storage(storages_to_add)

        payload = {}
        if vms_to_add:
            payload["vms"] = sorted(vms_to_add)
        elif vms_to_remove:
            payload["vms"] = sorted(vms_to_remove)
            payload["delete"] = 1

        if storages_to_add:
            payload["storage"] = sorted(storages_to_add)
        elif storages_to_remove:
            payload["storage"] = sorted(storages_to_remove)
            payload["delete"] = 1

        try:
            self.proxmox_api.pools(poolid).put(payload)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to update pool {poolid} membership: {e}")

        return True, self._pool_members_as_dicts(after_vms, after_storages)


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxPoolMemberAnsible(module)

    poolid = module.params["poolid"]
    members = module.params["members"]
    state = module.params["state"]
    exclusive = module.params["exclusive"]

    changed, final_members = proxmox.reconcile_members(poolid, members, exclusive, state)

    module.exit_json(
        changed=changed,
        poolid=poolid,
        members=final_members,
        msg=f"Pool {poolid} membership updated" if changed else f"Pool {poolid} membership already up-to-date",
    )


if __name__ == "__main__":
    main()
