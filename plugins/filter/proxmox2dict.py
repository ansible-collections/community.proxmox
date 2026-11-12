from __future__ import absolute_import, division, print_function

__metaclass__ = type

import re
from ansible.errors import AnsibleFilterError


# ------------------------------------------------------------
# DOCUMENTATION (ANSIBLE BEST PRACTICE)
# ------------------------------------------------------------

DOCUMENTATION = r'''
---
name: proxmox2dict
short_description: Transform Proxmox VM info into structured canonical schema
version_added: "1.0.0"
description:
  - Converts raw Proxmox VM info into a structured dictionary.
  - Produces canonical schema: parsed.network, parsed.storage, parsed.metadata
options:
  convert_types:
    description:
      - Convert numeric strings to integers where safe.
    type: bool
    default: true
  build_netconfig:
    description:
      - Build extended network structures (dict/list variants).
    type: bool
    default: true
'''

EXAMPLES = r"""
- name: Get a VM configuration by name
  community.proxmox.proxmox_vm_config:
    type: qemu
    name: generic-vm
    config: current
  register: vm_infos

# Example input
#
# vm_infos:
#   proxmox_vms: [
#  {
#   "agent": "1",
#   "memory": "2048",
#   "name": "generic-vm",
#   "ipconfig0": "ip=10.0.1.10/24,gw=10.0.1.1",
#   "net0": "virtio=AA:BB:CC:DD:EE:01,bridge=vmbr100,firewall=0",
#   "net1": "virtio=AA:BB:CC:DD:EE:02,bridge=vmbr200,firewall=0",
#   "scsi0": "STORAGE_POOL:vm-100-disk-0.qcow2,size=40G",
#   "tags": "managed;linux;example",
#   "meta": "creation-qemu=10.0.0,ctime=1700000000"
# }
#]
- name: Transform raw Proxmox VM data into a structured dictionary
  ansible.builtin.debug:
    msg: >-
      {{
        vm_infos.proxmox_vms
        | first
        | community.proxmox.proxmox2dict
      }}


# Example output
#
# {
#   "parsed": {
#     "metadata": {
#       "agent": 1,
#       "memory": 2048,
#       "name": "generic-vm",
#       "tags": [
#         "managed",
#         "linux",
#         "example"
#       ],
#       "meta": {
#         "creation-qemu": "10.0.0",
#         "ctime": "1700000000"
#       }
#     },
#     "network": {
#       "net_dict": {
#         "net0": {
#           "bridge": "vmbr100",
#           "firewall": "0",
#           "type": "virtio",
#           "mac": "AA:BB:CC:DD:EE:01"
#         },
#         "net1": {
#           "bridge": "vmbr200",
#           "firewall": "0",
#           "type": "virtio",
#           "mac": "AA:BB:CC:DD:EE:02"
#         }
#       },
#       "net_dict_macless": {
#         "net0": {
#           "bridge": "vmbr100",
#           "firewall": "0",
#           "type": "virtio"
#         },
#         "net1": {
#           "bridge": "vmbr200",
#           "firewall": "0",
#           "type": "virtio"
#         }
#       }
#     },
#     "storage": {
#       "disks": {
#         "scsi0": {
#           "storage": "STORAGE_POOL",
#           "volume": "vm-100-disk-0.qcow2",
#           "size": "40G"
#         }
#       }
#     }
#   }
# }
"""
RETURN = r"""
_value:
  description: a dict with disk and network information as a dict 
  type: dict
"""

# ------------------------------------------------------------
# GLOBAL CONFIG
# ------------------------------------------------------------

_IGNORE_KEYS = {
    "scsihw"
}

_NET_TYPES = {
    "virtio", "e1000", "vmxnet3", "rtl8139", "ne2k_pci", "pcnet"
}

_DISK_PREFIXES = (
    "scsi",
    "sata",
    "ide",
    "virtio",
    "efidisk",
    "tpmstate",
    "unused",
    "mp"
)


# ------------------------------------------------------------
# REQUIRED VALIDATION (INTEGRATED SNIPPET)
# ------------------------------------------------------------

def _require_dict(value, name="input"):
    if not isinstance(value, dict):
        raise AnsibleFilterError(
            f"proxmox2dict: {name} must be a dict, got {type(value).__name__}"
        )


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def _convert_scalar(value):
    if isinstance(value, str) and re.fullmatch(r"\d+", value):
        return int(value)
    return value


def _parse_kv_string(value):
    if not isinstance(value, str):
        raise AnsibleFilterError(
            f"Expected string for kv parsing, got {type(value).__name__}"
        )

    out = {}
    for part in value.split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def _split_tags(value):
    if isinstance(value, str):
        return [t.strip() for t in value.split(";") if t.strip()]
    return value


# ------------------------------------------------------------
# NETWORK PARSER
# ------------------------------------------------------------

def _parse_network(vm):
    net_dict = {}
    net_list = []

    net_dict_macless = {}
    net_list_macless = []

    for k, v in vm.items():

        if k in _IGNORE_KEYS:
            continue

        if not re.match(r"^net\d+$", k):
            continue

        if not isinstance(v, str):
            raise AnsibleFilterError(
                f"Network field {k} must be string"
            )

        parsed = _parse_kv_string(v)

        net_type = None
        mac = None

        # detect interface type + mac
        for t in _NET_TYPES:
            if t in parsed:
                net_type = t
                mac = parsed.pop(t)
                break

        # -----------------------------
        # FULL VERSION (WITH MAC)
        # -----------------------------
        net_obj = dict(parsed)

        if net_type:
            net_obj["type"] = net_type
        if mac:
            net_obj["mac"] = mac

        net_dict[k] = net_obj
        net_list.append({k: net_obj})

        # -----------------------------
        # MACLESS VERSION (NEW)
        # -----------------------------
        net_obj_macless = dict(parsed)

        if net_type:
            net_obj_macless["type"] = net_type

        net_dict_macless[k] = net_obj_macless
        net_list_macless.append({k: net_obj_macless})

    return {
        "net_dict": net_dict,
        "net_list": net_list,
        "net_dict_macless": net_dict_macless,
        "net_list_macless": net_list_macless
    }
# ------------------------------------------------------------
# STORAGE PARSER
# ------------------------------------------------------------

def _parse_storage(vm):
    disks = {}

    for k, v in vm.items():

        if k in _IGNORE_KEYS:
            continue

        if not any(k.startswith(prefix) for prefix in _DISK_PREFIXES):
            continue

        if not isinstance(v, str):
            raise AnsibleFilterError(
                f"Storage field {k} must be string"
            )

        storage = None
        volume = None
        size = None

        parts = v.split(",")

        if ":" in parts[0]:
            storage, volume = parts[0].split(":", 1)
        else:
            volume = parts[0]

        for p in parts[1:]:
            if "=" in p:
                pk, pv = p.split("=", 1)
                if pk == "size":
                    size = pv

        disks[k] = {
            "storage": storage,
            "volume": volume,
            "size": size
        }

    return {"disks": disks}


# ------------------------------------------------------------
# METADATA PARSER
# ------------------------------------------------------------

def _parse_metadata(vm):
    meta = {}

    for k, v in vm.items():

        if k in _IGNORE_KEYS:
            continue

        if k == "meta":
            meta[k] = _parse_kv_string(v)

        elif k == "tags":
            meta[k] = _split_tags(v)

        else:
            meta[k] = _convert_scalar(v)

    return meta


# ------------------------------------------------------------
# MAIN FILTER
# ------------------------------------------------------------

def proxmox2dict(vm_info, convert_types=True, build_netconfig=True):

    _require_dict(vm_info, "vm_info")

    vm = dict(vm_info)

    parsed = {
        "metadata": _parse_metadata(vm),
        "storage": _parse_storage(vm),
        "network": _parse_network(vm) if build_netconfig else {}
    }

    return {"parsed": parsed}


# ------------------------------------------------------------
# ANSIBLE ENTRYPOINT
# ------------------------------------------------------------

class FilterModule(object):

    def filters(self):
        return {
            "proxmox2dict": proxmox2dict
        }
