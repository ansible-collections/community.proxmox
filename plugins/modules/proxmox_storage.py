#!/usr/bin/python
#
# Copyright (c) 2025, Florian Paul Azim Hoberg (@gyptazy) <florian.hoberg@credativ.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_storage
version_added: 1.3.0
short_description: Manage storage in PVE clusters and nodes
description:
  - Manage storage in PVE clusters and nodes.
author: Florian Paul Azim Hoberg (@gyptazy)
attributes:
  check_mode:
    support: full
  diff_mode:
    support: full
options:
  name:
    description:
      - The name of the storage displayed in the storage list.
    type: str
    required: true
  state:
    description:
      - The state of the defined storage type to perform.
    choices: ["present", "absent"]
    type: str
    default: present
  type:
    description:
      - The storage type/protocol to use when adding the storage.
    choices: ['cephfs', 'cifs', 'dir', 'iscsi', 'iscsidirect', 'lvm', 'lvmthin', 'nfs', 'pbs', 'rbd', 'zfs', 'zfspool']
    type: str
    required: true
  nodes:
    description:
      - A list of nodes where this storage is available.
      - Required when C(state=present).
    type: list
    elements: str
  content:
    description:
      - The content types that can be stored on this storage.
      - V(backup) VM backups.
      - V(images) VM disk images.
      - V(import) VM disk images for import.
      - V(iso) ISO images.
      - V(rootdir) container root directories.
      - V(snippets) cloud-init, hook scripts, etc.
      - V(vztmpl) container templates.
    type: list
    elements: str
    choices: ["backup", "images", "import", "iso", "rootdir", "snippets", "vztmpl"]
  disable:
    description:
     - Flag to disable the storage.
    type: bool
  cephfs_options:
    description:
      - Extended information for adding CephFS storage.
    type: dict
    suboptions:
      path:
        description:
          - The path to be used within the CephFS.
        default: '/'
        type: str
      monhost:
        description:
          - The hostname or IP address of the monhost.
        type: list
        elements: str
      subdir:
        description:
          - The subdir to be used within the CephFS.
          - The Proxmox default is '/'.
        type: str
      username:
        description:
          - The username for the storage system.
        type: str
      password:
        description:
          - The password for the storage system.
        type: str
      keyring:
        description:
          - The client keyring to be used.
        aliases: ["client_keyring"]
        type: str
      fs_name:
        description:
          - The Ceph filesystem name
        type: str
        required: true
  cifs_options:
    description:
      - Extended information for adding CIFS storage.
    type: dict
    suboptions:
      server:
        description:
          - The required hostname or IP address of the remote storage system.
        type: str
        required: true
      share:
        description:
          - The required share to be used from the remote storage system.
        type: str
        required: true
      username:
        description:
          - The required username for the storage system.
        type: str
        required: true
      password:
        description:
          - The required password for the storage system.
        type: str
        required: true
      domain:
        description:
          - The required domain for the CIFS share.
        type: str
      subdir:
        description:
          - The subdir to be used within the CIFS.
        aliases: ["subdirectory"]
        type: str
      smbversion:
        description:
          - The minimum SMB version to use for.
        aliases: ["smb_version"]
        type: str
      snapshot_as_volume_chain:
        description:
          - Enable support for creating snapshots through volume backing-chains.
        type: bool
      preallocation:
        description:
          - The preallocation mode for raw and qcow2 images.
        type: str
  dir_options:
    description:
      - Extended information for adding Directory storage.
    type: dict
    suboptions:
      path:
        description:
          - The required path of the direcotry on the node(s).
        type: str
        required: true
  iscsi_options:
    description:
      - Extended information for adding iSCSI storage.
    type: dict
    suboptions:
      portal:
        description:
          - The required hostname or IP address of the remote storage system as the portal address.
        type: str
        required: true
      target:
        description:
          - The required iSCSI target.
        type: str
        required: true
  iscsidirect_options:
    description:
      - Extended information for adding iSCSI storage.
    type: dict
    suboptions:
      portal:
        description:
          - The required hostname or IP address of the remote storage system as the portal address.
        type: str
        required: true
      target:
        description:
          - The required iSCSI target.
        type: str
        required: true
  lvm_options:
    description:
      - Extended information for adding LVM storage.
    type: dict
    suboptions:
      vgname:
        description:
          - The required LVM volume group name. This must point to an existing volume group.
        type: str
        required: true
      base:
        description:
          - The base volume. This is mostly useful when the LVM volume group resides on a remote iSCSI server.
        type: str
      saferemove:
        description:
          - Called "Wipe Removed Volumes" in the web UI. Zero-out data when removing LVs.
        type: bool
        aliases: ["wipe_remove"]
      saferemove_stepsize:
        description:
          - Wipe step size in MiB.
        type: int
        choices: [1, 2, 4, 8, 16, 32]
        aliases: ["wipe_remove_stepsize"]
      saferemove_throughput:
        description:
          -  Wipe throughput (cstream -t parameter value), up to 10 MiB/s by default.
        type: str
        aliases: ["wipe_remove_throughput"]
      snapshot_as_volume_chain:
        description:
          - Enable support for creating snapshots through volume backing-chains.
        type: bool
  lvmthin_options:
    description:
      - Extended information for adding LVM-Thin storage.
    type: dict
    suboptions:
      vgname:
        description:
          - The required LVM volume group name. This must point to an existing volume group.
        type: str
        required: true
      thinpool:
        description:
          - The required name of the LVM thin pool.
        type: str
        required: true
  nfs_options:
    description:
      - Extended information for adding NFS storage.
    type: dict
    suboptions:
      server:
        description:
          - The required IP address or DNS name of the NFS server.
        type: str
        required: true
      export:
        description:
          - The required path of the NFS export.
        type: str
        required: true
      options:
        description:
          - The options to pass to the NFS service. (e.g., version, pNFS).
        type: str
      preallocation:
        description:
          - The preallocation mode for raw and qcow2 images.
        type: str
  pbs_options:
    description:
      - Extended information for adding Proxmox Backup Server as storage.
    type: dict
    suboptions:
      server:
        description:
          - The hostname or IP address of the Proxmox Backup Server.
        type: str
        required: true
      datastore:
        description:
          - The required datastore to use from the Proxmox Backup Server.
        type: str
        required: true
      username:
        description:
          - The required username for the Proxmox Backup Server.
        type: str
        required: true
      password:
        description:
          - The required password for the Proxmox Backup Server.
        type: str
        required: true
      namespace:
        description:
          - The namespace to use from the Proxmox Backup Server.
        type: str
      fingerprint:
        description:
          - The fingerprint of the Proxmox Backup Server system.
        type: str
      encryption_key:
        description:
          - An existing encryption key for the datastore.
          - Use V(autogen) to generate one automatically without passphrase.
          - Must be provided as a JSON-encoded string.
        type: str
  rbd_options:
    description:
      - Extended information for adding RBD storage.
    type: dict
    suboptions:
      pool:
        description:
          - The required RBD pool name.
        type: str
        required: true
  zfs_options:
    description:
      - Extended information for adding ZFS over iSCSI storage.
    type: dict
    suboptions:
      pool:
        description:
          - The required name of the ZFS pool to use.
        type: str
        required: true
      portal:
        description:
          - The required hostname or IP address of the remote storage system as the portal address.
        type: str
        required: true
      target:
        description:
          - The required iSCSI target.
        type: str
        required: true
      iscsiprovider:
        description:
          - The iSCSI target implementation used on the remote machine .
        type: str
        required: true
        choices: ['lio', 'iet', 'istgt', 'comstar']
      comstar_tg:
        description:
          - The target group for comstar views.
        type: str
      comstar_hg:
        description:
          - The host group for comstar views.
        type: str
      lio_tpg:
        description:
          - The target portal group for Linux LIO targets.
        type: str
      nowritecache:
        description:
          - Disable write caching on the target.
        type: bool
      blocksize:
        description:
          - The ZFS blocksize parameter.
        type: str
      sparse:
        description:
          - Use ZFS thin-provisioning.
        type: bool
  zfspool_options:
    description:
      - Extended information for adding ZFS storage.
    type: dict
    suboptions:
      pool:
        description:
          - The required name of the ZFS pool to use.
        type: str
        required: true
      sparse:
        description:
          - Use ZFS thin-provisioning.
        type: bool
  update:
    description:
      - If V(true), the Storage will be updated with new value.
    type: bool
    default: false
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Add PBS storage to Proxmox VE Cluster
  community.proxmox.proxmox_storage:
    nodes: ["de-cgn01-virt01", "de-cgn01-virt02"]
    state: present
    name: backup-backupserver01
    type: pbs
    pbs_options:
      server: proxmox-backup-server.example.com
      username: backup@pbs
      password: password123
      datastore: backup
      fingerprint: "F3:04:D2:C1:33:B7:35:B9:88:D8:7A:24:85:21:DC:75:EE:7C:A5:2A:55:2D:99:38:6B:48:5E:CA:0D:E3:FE:66"
    content: ["backup"]

- name: Add NFS storage to Proxmox VE Cluster
  community.proxmox.proxmox_storage:
    nodes: ["de-cgn01-virt01", "de-cgn01-virt02"]
    state: present
    name: net-nfsshare01
    type: nfs
    nfs_options:
      server: 10.10.10.94
      export: "/mnt/storage01/s01nfs01"
    content: ["rootdir", "images"]

- name: Add iSCSI storage to Proxmox VE Cluster
  community.proxmox.proxmox_storage:
    nodes: ["de-cgn01-virt01", "de-cgn01-virt02", "de-cgn01-virt03"]
    state: present
    type: iscsi
    name: net-iscsi01
    iscsi_options:
      portal: 10.10.10.94
      target: "iqn.2005-10.org.freenas.ctl:s01-isci01"
    content: ["rootdir", "images"]

- name: Remove storage from Proxmox VE Cluster
  community.proxmox.proxmox_storage:
    state: absent
    name: net-nfsshare01
    type: nfs

- name: Add ZFS storage to Proxmox VE Cluster
  community.proxmox.proxmox_storage:
    state: present
    name: zfspool-storage
    type: zfspool
    content: ["rootdir", "images"]
    zfspool_options:
      pool: rpool/data
      sparse: true

- name: Update ZFS storage on Proxmox VE Cluster
  community.proxmox.proxmox_storage:
    state: present
    name: zfspool-storage
    type: zfspool
    content: ["images"]
    zfspool_options:
      pool: rpool/data
      sparse: true
    update: true
"""

RETURN = r"""
storage:
  description: Status message about the storage action.
  returned: success
  type: str
  sample: "Storage 'net-nfsshare01' created successfully."
"""


from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    ansible_to_proxmox_bool,
    create_proxmox_module,
    is_not_found_error,
)

PROXMOX_FIELD_TRANSLATIONS = {
    "fs_name": "fs-name",
    "saferemove_stepsize": "saferemove-stepsize",
    "snapshot_as_volume_chain": "snapshot-as-volume-chain",
    "encryption_key": "encryption-key",
}


PROXMOX_FIELD_READONLY = [
    "type",
    "base",
    "datastore",
    "export",
    "iscsiprovider",
    "path",
    "share",
    "target",
    "thinpool",
    "vgname",
]


def module_args():
    return dict(
        name=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        type=dict(
            type="str",
            choices=[
                "cephfs",
                "cifs",
                "dir",
                "iscsi",
                "iscsidirect",
                "lvm",
                "lvmthin",
                "nfs",
                "pbs",
                "rbd",
                "zfs",
                "zfspool",
            ],
        ),
        content=dict(
            type="list", elements="str", choices=["backup", "images", "import", "iso", "rootdir", "snippets", "vztmpl"]
        ),
        nodes=dict(
            type="list",
            elements="str",
        ),
        disable=dict(type="bool"),
        cephfs_options=dict(
            type="dict",
            options={
                "monhost": dict(type="list", elements="str"),
                "username": dict(type="str"),
                "password": dict(type="str", no_log=True),
                "path": dict(type="str", default="/"),
                "subdir": dict(type="str"),
                "fs_name": dict(type="str", required=True),
                "keyring": dict(type="str", aliases=["client_keyring"], no_log=True),
            },
        ),
        cifs_options=dict(
            type="dict",
            options={
                "server": dict(type="str", required=True),
                "share": dict(type="str", required=True),
                "username": dict(type="str", required=True),
                "password": dict(type="str", no_log=True, required=True),
                "domain": dict(type="str"),
                "subdir": dict(type="str", aliases=["subdirectory"]),
                "smbversion": dict(type="str", aliases=["smb_version"]),
                "snapshot_as_volume_chain": dict(type="bool"),
                "preallocation": dict(type="str"),
            },
        ),
        dir_options=dict(
            type="dict",
            options={"path": dict(type="str", required=True)},
        ),
        lvm_options=dict(
            type="dict",
            options={
                "vgname": dict(type="str", required=True),
                "base": dict(type="str"),
                "saferemove": dict(type="bool", aliases=["wipe_remove"]),
                "saferemove_stepsize": dict(type="int", aliases=["wipe_remove_stepsize"], choices=[1, 2, 4, 8, 16, 32]),
                "saferemove_throughput": dict(type="str", aliases=["wipe_remove_throughput"]),
                "snapshot_as_volume_chain": dict(type="bool"),
            },
        ),
        lvmthin_options=dict(
            type="dict",
            options={
                "vgname": dict(type="str", required=True),
                "thinpool": dict(type="str", required=True),
            },
        ),
        iscsi_options=dict(
            type="dict",
            options={"portal": dict(type="str", required=True), "target": dict(type="str", required=True)},
        ),
        iscsidirect_options=dict(
            type="dict",
            options={"portal": dict(type="str", required=True), "target": dict(type="str", required=True)},
        ),
        nfs_options=dict(
            type="dict",
            options={
                "server": dict(type="str", required=True),
                "export": dict(type="str", required=True),
                "options": dict(type="str"),
                "preallocation": dict(type="str"),
            },
        ),
        pbs_options=dict(
            type="dict",
            options={
                "server": dict(type="str", required=True),
                "username": dict(type="str", required=True),
                "password": dict(type="str", required=True, no_log=True),
                "datastore": dict(type="str", required=True),
                "namespace": dict(type="str"),
                "fingerprint": dict(type="str"),
                "encryption_key": dict(type="str", no_log=True),
            },
        ),
        rbd_options=dict(type="dict", options={"pool": dict(type="str", required=True)}),
        zfs_options=dict(
            type="dict",
            options={
                "pool": dict(type="str", required=True),
                "portal": dict(type="str", required=True),
                "target": dict(type="str", required=True),
                "iscsiprovider": dict(type="str", required=True, choices=["lio", "iet", "istgt", "comstar"]),
                "comstar_tg": dict(type="str"),
                "comstar_hg": dict(type="str"),
                "lio_tpg": dict(type="str"),
                "nowritecache": dict(type="bool"),
                "blocksize": dict(type="str"),
                "sparse": dict(type="bool"),
            },
        ),
        zfspool_options=dict(
            type="dict",
            options={
                "pool": dict(type="str", required=True),
                "sparse": dict(type="bool"),
            },
        ),
        update=dict(type="bool", default=False),
    )


def module_options():
    return dict(
        required_if=[("state", "present", ["type"])],
    )

class ProxmoxNodeAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def _get_storage(self, storage_name):
        try:
            return self.proxmox_api.storage.get(storage_name)
        except Exception as e:
            if is_not_found_error(e):
                return None
            self.module.fail_json(msg=f"Failed to retrieve storage {storage_name}: {e}")

    def _normalized_storage_params(self):
        storage_type = self.params.get("type")
        storage_params = self.params.get(f"{storage_type}_options") or {}
        storage_argument_spec = self.module.argument_spec.get(f"{storage_type}_options")

        storage_params = {
            PROXMOX_FIELD_TRANSLATIONS.get(key, key): ansible_to_proxmox_bool(value)
            if isinstance(value, bool)
            else value
            for key, value in storage_params.items()
            if key in storage_argument_spec["options"] and value is not None
        }

        if self.params.get("disable") is not None:
            storage_params["disable"] = ansible_to_proxmox_bool(self.params.get("disable"))
        if self.params.get("nodes") is not None:
            storage_params["nodes"] = ",".join(sorted(self.params.get("nodes")))
        if self.params.get("content") is not None:
            storage_params["content"] = ",".join(sorted(self.params.get("content")))

        return storage_params

    def _update_storage_params(self, current_storage, desired_storage):
        update = {
            param: desired_value
            for param, desired_value in desired_storage.items()
            if desired_value != current_storage.get(param)
        }
        deletable_params = [
            PROXMOX_FIELD_TRANSLATIONS.get(key, key) for key in self.params.get(f"{current_storage['type']}_options") or {}
        ]
        deleted_params = [
            param
            for param, current_value in current_storage.items()
            if current_value is not None and desired_storage.get(param) is None and param in deletable_params
        ]
        if deleted_params:
            update["delete"] = ",".join(sorted(deleted_params))
        return update

    def run(self):
        storage_name = self.params.get("name")
        storage_type = self.params.get("type")
        state = self.params.get("state")

        current_storage = self._get_storage(storage_name)
        desired_storage = self._normalized_storage_params()

        if state == "present" and current_storage is None:
            changed, msg = self.add_storage(storage_name, storage_type, desired_storage)
        elif state == "present":
            changed, msg = self.update_storage(storage_name, storage_type, current_storage, desired_storage)
        elif state == "absent" and current_storage is not None:
            changed, msg = self.remove_storage(storage_name)
        elif state == "absent":
            self.module.exit_json(changed=False, msg=f"Storage '{storage_name}' does not exist.")

        if self.module._diff:
            if self.module.check_mode:
                new_storage = {"storage": storage_name, "type": storage_type, **desired_storage}
            else:
                new_storage = self._get_storage(storage_name)
            if new_storage is not None and "digest" in new_storage:
                del new_storage["digest"]
            if current_storage is not None and "digest" in current_storage:
                del current_storage["digest"]
            self.module.exit_json(
                changed=changed,
                msg=msg,
                diff=[
                    {
                        "before_header": f"{storage_name} ({storage_type})",
                        "before": current_storage,
                        "after_header": f"{storage_name} ({storage_type})",
                        "after": new_storage,
                    }
                ],
            )

        self.module.exit_json(changed=changed, msg=msg)

    def add_storage(self, name, storage_type, storage_params):
        if self.module.check_mode:
            return True, f"Storage '{name}' would be created."

        try:
            self.proxmox_api.storage.post(storage=name, type=storage_type, **storage_params)
            return True, f"Storage '{name}' created successfully."
        except Exception as e:
            self.module.fail_json(msg=f"Failed to create storage: {e}")

    def update_storage(self, name, storage_type, current_storage, desired_storage):
        if storage_type != current_storage["type"]:
            self.module.fail_json(msg=f"Storage '{name}' type can not be changed.")

        update_storage = self._update_storage_params(current_storage, desired_storage)

        if len(update_storage) == 0 or self.params.get("update") is False:
            return False, f"Storage '{name}' already present."

        readonly_param = next((param for param in PROXMOX_FIELD_READONLY if param in update_storage), None)
        if readonly_param is not None:
            self.module.fail_json(msg=f"Storage '{name}' parameter '{readonly_param}' is readonly.")

        if self.module.check_mode:
            return True, f"Storage '{name}' would be updated."

        update_storage["digest"] = current_storage["digest"]

        try:
            self.proxmox_api.storage(name).put(**update_storage)
            return True, f"Storage '{name}' updated successfully."
        except Exception as e:
            self.module.fail_json(msg=f"Failed to update storage '{name}': {e}")

    def remove_storage(self, name):
        if self.module.check_mode:
            return True, f"Storage '{name}' would be deleted."

        try:
            self.proxmox_api.storage(name).delete()
            return True, f"Storage '{name}' removed successfully."
        except Exception as e:
            self.module.fail_json(msg=f"Failed to delete storage '{name}': {e}")


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxNodeAnsible(module)

    proxmox.run()


if __name__ == "__main__":
    main()
