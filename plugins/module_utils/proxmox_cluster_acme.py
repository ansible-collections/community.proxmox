#
# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Helpers for Proxmox cluster ACME."""

from ansible.module_utils.common.text.converters import to_native


def normalize_acme_contacts(contacts):
    """Normalize API contact entries (e.g. mailto:) to plain email strings."""
    if contacts is None:
        return []
    out = []
    for contact in contacts:
        s = to_native(contact).strip()
        if s.startswith("mailto:"):
            out.append(s[7:].strip())
        else:
            out.append(s)
    return out


def acme_account_get_to_ansible(data):
    """Build Ansible module result fields from GET /cluster/acme/account/{name} JSON."""
    acc = data.get("account") or {}
    return {
        "directory": data.get("directory") or "",
        "location": data.get("location") or "",
        "tos": data.get("tos") or "",
        "account": {
            "contact": normalize_acme_contacts(acc.get("contact")),
            "created_at": acc.get("createdAt") or "",
            "status": acc.get("status") or "",
        },
    }
