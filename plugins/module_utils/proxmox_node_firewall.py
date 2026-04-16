from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ansible_to_proxmox_bool,
    proxmox_to_ansible_bool,
)

SCHEMA = {
    "enabled": {
        "api": "enable",
        "default": False,
        "to_api": ansible_to_proxmox_bool,
        "from_api": proxmox_to_ansible_bool,
    },
    "log_level_in": {"default": "nolog"},
    "log_level_out": {"default": "nolog"},
    "log_level_forward": {"default": "nolog"},
    "ndp": {
        "default": True,
        "to_api": ansible_to_proxmox_bool,
        "from_api": proxmox_to_ansible_bool,
    },
    "nftables": {
        "default": False,
        "to_api": ansible_to_proxmox_bool,
        "from_api": proxmox_to_ansible_bool,
    },
    "nosmurfs": {
        "default": True,
        "to_api": ansible_to_proxmox_bool,
        "from_api": proxmox_to_ansible_bool,
    },
    "smurf_log_level": {"default": "nolog"},
    "tcp_flags_log_level": {"default": "nolog"},
    "tcpflags": {
        "default": False,
        "to_api": ansible_to_proxmox_bool,
        "from_api": proxmox_to_ansible_bool,
    },
    "nf_conntrack_allow_invalid": {
        "default": False,
        "to_api": ansible_to_proxmox_bool,
        "from_api": proxmox_to_ansible_bool,
    },
    "nf_conntrack_helpers": {"default": None},
    "nf_conntrack_max": {"default": 262144},
    "nf_conntrack_tcp_timeout_established": {"default": 432000},
    "nf_conntrack_tcp_timeout_syn_recv": {"default": 60},
    "protection_synflood": {
        "default": False,
        "to_api": ansible_to_proxmox_bool,
        "from_api": proxmox_to_ansible_bool,
    },
    "protection_synflood_burst": {"default": 1000},
    "protection_synflood_rate": {"default": 200},
}


def node_firewall_options_to_ansible_result(node_name, raw):
    """Build the Ansible-side node firewall options dict from API data."""
    result = {
        "node_name": node_name,
    }

    for field, meta in SCHEMA.items():
        api_key = meta.get("api", field)
        value = raw.get(api_key, meta.get("default"))

        if "from_api" in meta:
            value = meta["from_api"](value)

        result[field] = value

    return result
