#
# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Helpers for Proxmox ACME plugin."""

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    proxmox_to_ansible_bool,
)


def acme_plugin_normalize_data_dict(data):
    """Normalize plugin data dict to native strings."""
    if not data:
        return {}
    return {to_native(k): to_native(v) for k, v in data.items()}


def acme_plugin_data_from_api(raw):
    """Parse Proxmox plugin data string into a dict."""
    data = {}
    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, val = line.split("=", 1)
        data[key.strip()] = val.strip()
    return data


def acme_plugin_to_ansible_result(raw):
    """Build Ansible module result fields from GET /cluster/acme/plugins/{name} JSON."""
    data_raw = raw.get("data", "")
    data = acme_plugin_normalize_data_dict(acme_plugin_data_from_api(data_raw))

    return {
        "type": raw.get("type"),
        "name": raw.get("plugin"),
        "plugin": raw.get("api", ""),
        "disable": proxmox_to_ansible_bool(raw.get("disable", False)),
        "validation_delay": int(raw.get("validation-delay", 30)),
        "data": data,
        "digest": raw.get("digest", ""),
    }
