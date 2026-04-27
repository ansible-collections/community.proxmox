#!/usr/bin/python
#
# Copyright (c) 2026, (@teslamania) <nicolas.vial@protonmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_ceph_pool
version_added: 2.0.0
short_description: Manage Ceph Pool.
description:
  - Add, edit or delete pool of a ceph cluster.
author: Vial Nicolas (@teslamania)
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none

options:
    add_storages:
        description: Add the new pool to the cluster storage configuration.
        required: false
        type: bool
    crush_rule:
        description: The rule to use for mapping object placement in the cluster.
        required: false
        type: str
    min_size:
        description: Minimum number of replicas per object.
        required: false
        type: int
    name:
        description: The name of the pool. It must be unique.
        required: true
        type: str
    node:
        description: The cluster node name.
        required: true
        type: str
    pg_autoscale_mode:
        description: The automatic placement groups scaling mode of the pool.
        required: false
        type: str
        choices: ["on", "off", "warn"]
    pg_num:
        description: Number of placement groups.
        required: false
        type: int
    pg_num_min:
        description: Minimal number of placement groups.
        required: false
        type: int
    state:
        description: Indicate whether the Ceph pool should be present (created if missing) or absent (deleted if it exists).
        required: true
        choices: ['present', 'absent']
        type: str
    size:
        description: Number of replicas per object.
        required: false
        type: int
    timeout:
        description: Timeout for operations.
        default: 5
        required: false
        type: int
    target_size:
        description: The estimated target size of the pool for the placement groups autoscaler.
        required: false
        type: str
    target_size_ratio:
        description: The estimated target ratio of the pool for the placement groups autoscaler.
        required: false
        type: int

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module
"""


EXAMPLES = r"""
- name: Add a ceph pool
  community.proxmox.proxmox_ceph_pool:
    api_host: proxmox
    api_user: root@pam
    api_password: secret
    node: proxmox
    name: ceph-pool
    state: present

- name: Add a ceph pool and storage
  community.proxmox.proxmox_ceph_pool:
    api_host: proxmox
    api_user: root@pam
    api_password: secret
    node: proxmox
    name: ceph-pool
    state: present
    add_storages: true

- name: Delete a ceph pool
  community.proxmox.proxmox_ceph_pool:
    api_host: proxmox
    api_user: root@pam
    api_password: secret
    node: proxmox
    name: ceph-pool
    state: absent
"""

RETURN = r"""
msg:
    description: The output message that the module generates.
    type: str
    returned: always
"""

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    ansible_to_proxmox_bool,
    create_proxmox_module,
)


def module_args():
    return dict(
        add_storages=dict(type="bool"),
        crush_rule=dict(type="str"),
        min_size=dict(type="int"),
        name=dict(type="str", required=True),
        node=dict(type="str", required=True),
        pg_autoscale_mode=dict(type="str", choices=["on", "off", "warn"]),
        pg_num=dict(type="int"),
        pg_num_min=dict(type="int"),
        size=dict(type="int"),
        timeout=dict(type="int", default=5),
        target_size=dict(type="str"),
        target_size_ratio=dict(type="int"),
        state=dict(choices=["present", "absent"], required=True),
    )


class ProxmoxCephPoolAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def get_params(self):
        params_list = [
            "add_storages",
            "crush_rule",
            "node",
            "name",
            "min_size",
            "pg_autoscale_mode",
            "pg_num",
            "pg_num_min",
            "size",
            "target_size",
            "target_size_ratio",
        ]
        params = {
            k: ansible_to_proxmox_bool(v) if isinstance(v, bool) else v
            for k, v in self.params.items()
            if v is not None and k in params_list
        }
        return params

    def is_equal(self, params, current):
        return all(params[k] == current.get(k) for k in params if k not in ("add_storages", "node"))

    def check_pool(self, node, name):
        pools = self.proxmox_api.nodes(node).ceph.pool.get()
        return any(pool["pool_name"] == name for pool in pools)

    def get_pool(self, node, name):
        return self.proxmox_api.nodes(node).ceph.pool(name).status.get()

    def add_pool(self):
        node = self.params["node"]
        name = self.params["name"]
        self.get_node(node, strict=True)
        pool_params = self.get_params()
        if self.check_pool(node, name):
            pool_current = self.get_pool(node, name)
            if self.is_equal(pool_params, pool_current):
                self.module.exit_json(changed=False, msg=f"Ceph pool {name} already exists.")
            else:
                # Remove add_storage : not in put parameters
                pool_params.pop("add_storages", None)
                if self.module.check_mode:
                    self.module.exit_json(changed=True, msg=f"Ceph pool {name} would be updated.")
                else:
                    current_task_id = self.proxmox_api.nodes(node).ceph.pool(name).put(**pool_params)
                    task_success, fail_reason = self.api_task_complete(
                        node, current_task_id, self.module.params["timeout"]
                    )
                    if task_success:
                        self.module.exit_json(changed=True, msg=f"Ceph pool {name} updated.")
                    else:
                        self.module.fail_json(msg=f"Error occurred on task execution: {fail_reason}")
        elif self.module.check_mode:
            self.module.exit_json(changed=True, msg=f"Ceph pool {name} would be added.")
        else:
            current_task_id = self.proxmox_api.nodes(node).ceph.pool.create(**pool_params)
            task_success, fail_reason = self.api_task_complete(node, current_task_id, self.module.params["timeout"])
            if task_success:
                self.module.exit_json(changed=True, msg=f"Ceph pool {name} added.")
            else:
                self.module.fail_json(msg=f"Error occurred on task execution: {fail_reason}")

    def del_pool(self):
        node = self.params["node"]
        name = self.params["name"]
        self.get_node(node)
        if self.check_pool(node, name):
            if self.module.check_mode:
                self.module.exit_json(changed=True, msg=f"Ceph pool {name} would be deleted.")
            else:
                current_task_id = self.proxmox_api.nodes(node).ceph.pool(name).delete()
                task_success, fail_reason = self.api_task_complete(node, current_task_id, self.module.params["timeout"])
                if task_success:
                    self.module.exit_json(changed=True, msg=f"Ceph pool {name} deleted.")
                else:
                    self.module.fail_json(msg=f"Error occurred on task execution: {fail_reason}")
        else:
            self.module.exit_json(changed=False, msg=f"Ceph pool {name} not present.")


def main():
    module = create_proxmox_module(module_args())
    proxmox = ProxmoxCephPoolAnsible(module)
    state = module.params["state"]

    if state == "present":
        try:
            proxmox.add_pool()
        except Exception as e:
            module.fail_json(msg=f"Adding ceph pool failed with exception: {to_native(e)}")

    elif state == "absent":
        try:
            proxmox.del_pool()
        except Exception as e:
            module.fail_json(msg=f"Deleting ceph pool failed with exception: {to_native(e)}")


if __name__ == "__main__":
    main()
