#!/usr/bin/python
#
# Copyright (c) 2023, Sergei Antipov (UnderGreen) <greendayonfire@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_pool
short_description: Pool management for Proxmox VE
description: Resource Pool management for Proxmox VE
author: "Sergei Antipov (@UnderGreen) <greendayonfire@gmail.com>"
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  poolid:
    description:
      - The pool identifier.
    type: str
    aliases: ["name", "pool_id"]
    required: true
  state:
    description:
      - Indicate desired state of the pool.
    choices: ["present", "absent"]
    default: present
    type: str
  comment:
    description:
      - The pool comment.
    type: str
  members:
    description:
      - The pool members.
      - Each list entry must set exactly one of O(members[].vm_id) or O(members[].storage_id).
    type: list
    elements: dict
    suboptions:
      vm_id:
        description:
          - The CT or VM identifier.
        type: int
        aliases: ["vmid"]
      storage_id:
        description:
          - The storage identifier.
        type: str
        aliases: ["storageid"]

seealso:
  - name: Proxmox VE Resource Pools documentation
    description: Proxmox VE Resource Pools documentation.
    link: "https://pve.proxmox.com/pve-docs/pve-admin-guide.html#pveum_resource_pools"

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Create Resource Pool with members
  community.proxmox.proxmox_pool:
    poolid: example
    members:
      - vm_id: 100
      - vm_id: 200
      - storage_id: local

- name: Delete Resource Pool
  community.proxmox.proxmox_pool:
    poolid: example
    state: absent
"""

RETURN = r"""
poolid:
  description: The pool identifier.
  returned: on success
  type: str
  sample: example
comment:
  description:
    - The pool comment from API state.
    - In check mode, the value reflects desired state.
  returned: on success
  type: str
  sample: Example pool
members:
  description:
    - Pool members from API state.
    - In check mode, the value reflects desired state.
  returned: on success
  type: list
  elements: dict
  sample:
    - id: 100
      type: vm
    - id: local
      type: storage
msg:
  description: A short message on what the module did.
  returned: always
  type: str
  sample: "Pool example successfully created"
"""

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
)


def _members_result_from_api(raw_members):
    result = []
    for m in raw_members or []:
        if m.get("type") == "storage":
            storage_id = m.get("storage")
            result.append({"id": storage_id, "type": "storage"})
        else:
            vmid = m.get("vmid")
            result.append({"id": int(vmid), "type": "vm"})
    return result


def _parse_members(members):
    vms = []
    storage = []
    if not members:
        return vms, storage
    for member in members:
        if member.get("type") == "storage":
            sid = member.get("storage")
            if sid is not None:
                storage.append(sid)
        else:
            vmid = member.get("vmid")
            if vmid is not None:
                vms.append(int(vmid))
    return vms, storage


def _desired_members_from_params(members):
    if not members:
        return [], []
    vms = []
    storages = []
    for item in members:
        if item.get("vm_id") is not None:
            vms.append(item["vm_id"])
        if item.get("storage_id"):
            storages.append(item["storage_id"])
    return vms, storages


def module_args():
    return dict(
        pool_id=dict(type="str", aliases=["name", "poolid"], required=True),
        comment=dict(type="str"),
        state=dict(default="present", choices=["present", "absent"]),
        members=dict(
            type="list",
            elements="dict",
            options=dict(
                vm_id=dict(type="int", aliases=["vmid"]),
                storage_id=dict(type="str", aliases=["storageid"]),
            ),
        ),
    )


def module_options():
    return {}


class ProxmoxPoolAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def run(self):
        self.validate_params()

        pool_id = self.params.get("pool_id")

        if self.params.get("state") == "present":
            self.pool_present(pool_id)
        else:
            self.pool_absent(pool_id)

    def validate_params(self):
        members = self.params.get("members")
        if members is None:
            return
        for member in members:
            has_vm = member.get("vm_id") is not None
            has_storage = bool(member.get("storage_id"))
            if not has_vm and not has_storage or (has_vm and has_storage):
                self.module.fail_json(msg="Each member entry must set exactly one of vm_id or storage_id")

    def _get_pool(self, pool_id):
        try:
            return self.proxmox_api.pools.get(pool_id)
        except Exception as e:
            if "does not exist" in str(e).lower():
                return None
            self.module.fail_json(msg=f"Failed to retrieve pool {pool_id}: {e}")

    def _create_pool(self, pool_id, vms, storages, comment=None):
        self.proxmox_api.pools.post(poolid=pool_id)

        kwargs = dict(poolid=pool_id, vms=vms, storage=storages)
        if comment is not None:
            kwargs["comment"] = comment
        self.proxmox_api.pools(pool_id).put(**kwargs)

    def _update_pool(self, pool, vms, storages, comment=None):
        pool_id = pool.get("poolid")

        current_vms, current_storages = _parse_members(pool.get("members", []))
        members_changed = current_vms != vms or current_storages != storages
        if members_changed:
            vms_to_remove = [vm for vm in current_vms if vm not in vms]
            storages_to_remove = [storage for storage in current_storages if storage not in storages]
            if vms_to_remove or storages_to_remove:
                self.proxmox_api.pools(pool_id).put(vms=vms_to_remove, storage=storages_to_remove, delete=1)

            vms_to_add = [vm for vm in vms if vm not in current_vms]
            storages_to_add = [storage for storage in storages if storage not in current_storages]
            if vms_to_add or storages_to_add:
                self.proxmox_api.pools(pool_id).put(vms=vms_to_add, storage=storages_to_add)

        comment_changed = comment is not None and (pool.get("comment") or "") != comment
        if comment_changed:
            self.proxmox_api.pools(pool_id).put(comment=comment)

    def _delete_pool(self, pool):
        pool_id = pool.get("poolid")
        self._delete_pool_members(pool)
        self.proxmox_api.pools.delete(poolid=pool_id)

    def _delete_pool_members(self, pool):
        pool_id = pool.get("poolid")
        vms, storages = _parse_members(pool.get("members", []))
        self.proxmox_api.pools(pool_id).put(vms=vms, storage=storages, delete=1)

    def _is_members_update_needed(self, pool, desired_vms, desired_storages):
        current_vms, current_storages = _parse_members(pool.get("members", []))
        return current_vms != desired_vms or current_storages != desired_storages

    def _present_result(self, pool_id, pool, members_param, comment_param, changed):
        """Current API state in normal mode; desired state in check mode."""
        if self.module.check_mode:
            if pool is None:
                return {
                    "poolid": pool_id,
                    "comment": comment_param if comment_param is not None else "",
                    "members": members_param if members_param is not None else [],
                }
            comment = comment_param if comment_param is not None else (pool.get("comment") or "")
            members = members_param if members_param is not None else _members_result_from_api(pool.get("members", []))
            return {"poolid": pool_id, "comment": comment, "members": members}

        if changed:
            state = self._get_pool(pool_id)
        else:
            state = pool
        return {
            "poolid": pool_id,
            "comment": (state.get("comment") or "") if state else "",
            "members": _members_result_from_api(state.get("members", []) if state else []),
        }

    def _absent_result(self, pool_id, pool, changed):
        """After delete there is no pool; return empty comment and members. Check mode uses desired end state."""
        if self.module.check_mode and changed:
            return {"poolid": pool_id, "comment": "", "members": []}
        if not changed:
            return {
                "poolid": pool_id,
                "comment": (pool.get("comment") or "") if pool else "",
                "members": _members_result_from_api(pool.get("members", []) if pool else []),
            }
        return {"poolid": pool_id, "comment": "", "members": []}

    def pool_present(self, pool_id):
        pool = self._get_pool(pool_id)
        members_param = self.params.get("members")
        desired_vms, desired_storages = _desired_members_from_params(members_param)
        comment_param = self.params.get("comment")

        if pool is None:
            if self.module.check_mode:
                r = self._present_result(pool_id, None, members_param, comment_param, True)
                self.module.exit_json(changed=True, msg=f"Pool {pool_id} would be created", **r)
            try:
                self._create_pool(pool_id, desired_vms, desired_storages, comment_param)
                r = self._present_result(pool_id, None, members_param, comment_param, True)
                self.module.exit_json(changed=True, msg=f"Pool {pool_id} successfully created", **r)
            except Exception as e:
                self.module.fail_json(msg=f"Failed to create pool {pool_id}: {e}")
        elif members_param is None:
            r = self._present_result(pool_id, pool, None, comment_param, False)
            self.module.exit_json(changed=False, msg=f"Pool {pool_id} already exists", **r)
        else:
            is_update_needed = self._is_members_update_needed(pool, desired_vms, desired_storages) or (
                comment_param is not None and (pool.get("comment") or "") != comment_param
            )
            if not is_update_needed:
                r = self._present_result(pool_id, pool, members_param, comment_param, False)
                self.module.exit_json(changed=False, msg=f"Pool {pool_id} already up to date", **r)

            if self.module.check_mode:
                r = self._present_result(pool_id, pool, members_param, comment_param, True)
                self.module.exit_json(changed=True, msg=f"Pool {pool_id} would be updated", **r)

            try:
                self._update_pool(pool, desired_vms, desired_storages, comment_param)
                r = self._present_result(pool_id, pool, members_param, comment_param, True)
                self.module.exit_json(changed=True, msg=f"Pool {pool_id} successfully updated", **r)
            except Exception as e:
                self.module.fail_json(msg=f"Failed to update pool {pool_id}: {e}")

    def pool_absent(self, pool_id):
        pool = self._get_pool(pool_id)

        if pool is None:
            r = self._absent_result(pool_id, None, False)
            self.module.exit_json(changed=False, msg=f"Pool {pool_id} doesn't exist", **r)

        if self.module.check_mode:
            r = self._absent_result(pool_id, pool, True)
            self.module.exit_json(changed=True, msg=f"Pool {pool_id} would be deleted", **r)
        try:
            self._delete_pool(pool)
            r = self._absent_result(pool_id, pool, True)
            self.module.exit_json(changed=True, msg=f"Pool {pool_id} successfully deleted", **r)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to delete pool {pool_id}: {e}")


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxPoolAnsible(module)

    proxmox.run()


if __name__ == "__main__":
    main()
