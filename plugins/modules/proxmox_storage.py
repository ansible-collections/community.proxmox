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
    support: none
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
    choices: ['cephfs', 'cifs', 'dir', 'iscsi', 'nfs', 'pbs', 'rbd', 'zfspool']
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
      client_keyring:
        description:
          - The client keyring to be used.
        type: str
      fs_name:
        description:
          - The Ceph filesystem name
        type: str
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
        type: str
      smb_version:
        description:
          - The minimum SMB version to use for.
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
        required: false
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
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Add PBS storage to Proxmox VE Cluster
  community.proxmox.proxmox_storage:
    api_host: proxmoxhost
    api_user: root@pam
    api_password: password123
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
      export: "/mnt/storage01/b01pbs01"
    content: ["backup"]

- name: Add NFS storage to Proxmox VE Cluster
  community.proxmox.proxmox_storage:
    api_host: proxmoxhost
    api_user: root@pam
    api_password: password123
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
    api_host: proxmoxhost
    api_user: root@pam
    api_password: password123
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
    api_host: proxmoxhost
    api_user: root@pam
    api_password: password123
    state: absent
    name: net-nfsshare01
    type: nfs

- name: Add ZFS storage to Proxmox VE Cluster
  community.proxmox.proxmox_storage:
    api_host: proxmoxhost
    api_user: root@pam
    api_password: password123
    state: present
    name: zfspool-storage
    type: zfspool
    content: ["rootdir", "images"]
    zfspool_options:
      pool: rpool/data
      sparse: true
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
)

STORAGE_BACKENDS = {
    "cephfs": {
        "path": ("path", False),
        "monhost": ("monhost", False),
        "subdir": ("subdir", False),
        "username": ("username", False),
        "password": ("password", False),
        "client_keyring": ("keyring", False),
        "fs_name": ("fs-name", False),
    },
    "cifs": {
        "server": ("server", True),
        "share": ("share", True),
        "username": ("username", True),
        "password": ("password", True),
        "domain": ("domain", False),
        "subdir": ("subdir", False),
        "smb_version": ("smbversion", False),
    },
    "dir": {"path": ("path", True)},
    "iscsi": {"portal": ("portal", True), "target": ("target", True)},
    "nfs": {
        "server": ("server", True),
        "export": ("export", True),
        "options": ("options", False),
    },
    "pbs": {
        "server": ("server", True),
        "datastore": ("datastore", True),
        "username": ("username", True),
        "password": ("password", True),
        "namespace": ("namespace", False),
        "fingerprint": ("fingerprint", False),
        "encryption_key": ("encryption-key", False),
    },
    "rbd": {
        "pool": ("pool", True),
    },
    "zfspool": {
        "pool": ("pool", True),
        "sparse": ("sparse", False),
    },
}


def module_args():
    return dict(
        name=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        type=dict(
            type="str", choices=["cephfs", "cifs", "dir", "iscsi", "nfs", "pbs", "rbd", "zfspool"], required=True
        ),
        content=dict(
            type="list", elements="str", choices=["backup", "images", "import", "iso", "rootdir", "snippets", "vztmpl"]
        ),
        nodes=dict(
            type="list",
            elements="str",
        ),
        cephfs_options=dict(
            type="dict",
            options={
                "monhost": dict(type="list", elements="str"),
                "username": dict(type="str"),
                "password": dict(type="str", no_log=True),
                "path": dict(type="str", default="/"),
                "subdir": dict(type="str"),
                "fs_name": dict(type="str"),
                "client_keyring": dict(type="str", no_log=True),
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
                "subdir": dict(type="str"),
                "smb_version": dict(type="str"),
            },
        ),
        dir_options=dict(
            type="dict",
            options={"path": dict(type="str", required=True)},
        ),
        iscsi_options=dict(
            type="dict",
            options={"portal": dict(type="str", required=True), "target": dict(type="str", required=True)},
        ),
        nfs_options=dict(
            type="dict",
            options={
                "server": dict(type="str", required=True),
                "export": dict(type="str", required=True),
                "options": dict(type="str"),
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
        rbd_options=dict(type="dict", options={"pool": dict(type="str")}),
        zfspool_options=dict(
            type="dict",
            options={
                "pool": dict(type="str", required=True),
                "sparse": dict(type="bool"),
            },
        ),
    )


def module_options():
    return {}


class ProxmoxNodeAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def _get_storage(self, storage_name):
        try:
            return self.proxmox_api.storage.get(storage_name)
        except Exception as e:
            error_str = str(e).lower()
            if "does not exist" in error_str:
                return None
            self.module.fail_json(msg=f"Failed to retrieve storage {storage_name}: {e}")

    def _validate_storage_params(self, storage_type, params):
        backend = STORAGE_BACKENDS.get(storage_type, {})
        missing_required = []
        for ansible_key, (_proxmox_key, required) in backend.items():
            value = params.get(ansible_key)
            if value is None and required:
                missing_required.append(ansible_key)
        if missing_required:
            self.module.fail_json(
                msg=f"{storage_type} storage is missing required option(s): {', '.join(missing_required)}"
            )

    def _normalize_storage_params(self, storage_type, backend_params):
        backend = STORAGE_BACKENDS.get(storage_type, {})
        result = {}
        for ansible_key, (proxmox_key, _required) in backend.items():
            value = backend_params.get(ansible_key)
            if value is not None:
                normalized = ansible_to_proxmox_bool(value) if isinstance(value, bool) else value
                result[proxmox_key] = normalized
        return result

    def run(self):
        state = self.params.get("state")

        storage_params = {
            "storage": self.params.get("name"),
            "type": self.params.get("type"),
        }

        if self.params.get("nodes") is not None:
            storage_params["nodes"] = self.params.get("nodes")
        if self.params.get("content") is not None:
            storage_params["content"] = self.params.get("content")

        storage_type = self.params.get("type")
        storage_backend_params = self.params.get(f"{storage_type}_options") or {}

        if state == "present":
            self._validate_storage_params(storage_type, storage_backend_params)
            storage_params.update(self._normalize_storage_params(storage_type, storage_backend_params))
            self.add_storage(storage_params)
        elif state == "absent":
            self.remove_storage(storage_params)

    def add_storage(self, storage_params):
        name = storage_params["storage"]

        if self.module.check_mode:
            current_storage = self._get_storage(name)
            if current_storage:
                self.module.exit_json(changed=False, msg=f"Storage '{name}' already present.")
            self.module.exit_json(changed=True, msg=f"Storage '{name}' would be created.")

        try:
            self.proxmox_api.storage.post(**storage_params)
            self.module.exit_json(changed=True, msg=f"Storage '{name}' created successfully.")
        except Exception as e:
            error_msg = str(e)
            if "already defined" in error_msg:
                self.module.exit_json(changed=False, msg=f"Storage '{name}' already present.")
            self.module.fail_json(msg=f"Failed to create storage: {error_msg}")

    def remove_storage(self, storage_params):
        name = storage_params["storage"]

        if self.module.check_mode:
            current_storage = self._get_storage(name)
            if current_storage:
                self.module.exit_json(changed=True, msg=f"Storage '{name}' would be deleted.")
            self.module.exit_json(changed=False, msg=f"Storage '{name}' does not exist.")

        current_storage = self._get_storage(name)
        if not current_storage:
            self.module.exit_json(changed=False, msg=f"Storage '{name}' does not exist.")

        try:
            self.proxmox_api.storage(name).delete()
            self.module.exit_json(changed=True, msg=f"Storage '{name}' removed successfully.")
        except Exception as e:
            self.module.fail_json(msg=f"Failed to delete storage '{name}': {e}")


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxNodeAnsible(module)

    proxmox.run()


if __name__ == "__main__":
    main()
