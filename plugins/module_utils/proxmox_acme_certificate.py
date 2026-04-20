#
# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared helpers for Proxmox ACME certificate modules."""

_ACME_DOMAIN_SLOTS = 6  # acmedomain0 .. acmedomain5


def parse_acme_config(node_config):
    """Parse a node config dict into structured ACME settings.

    Returns a dict with ``account`` (str or None) and ``domains`` (list of dicts
    with keys ``domain``, ``plugin``, ``alias``).
    """
    account = None
    domains = []

    acme_raw = node_config.get("acme")
    if acme_raw:
        for part in acme_raw.split(","):
            kv = part.strip().split("=", 1)
            if len(kv) == 2 and kv[0].strip() == "account":  # noqa: PLR2004
                account = kv[1].strip()

    for i in range(_ACME_DOMAIN_SLOTS):
        key = f"acmedomain{i}"
        raw = node_config.get(key)
        if not raw:
            continue
        domain_entry = _parse_acmedomain_string(raw)
        if domain_entry:
            domains.append(domain_entry)

    return {"account": account, "domains": domains}


def _parse_acmedomain_string(value):
    """Parse a single ``acmedomainN`` property string into a dict."""
    result = {"domain": None, "plugin": None, "alias": None}
    for part in value.split(","):
        kv = part.strip().split("=", 1)
        if len(kv) != 2:  # noqa: PLR2004
            continue
        key, val = kv[0].strip(), kv[1].strip()
        if key in result:
            result[key] = val
    return result if result["domain"] else None


def cert_info_to_ansible_result(cert):
    """Transform a single certificate info dict from the Proxmox API into Ansible return values."""
    san = cert.get("san") or []
    if isinstance(san, str):
        san = [s.strip() for s in san.split(",") if s.strip()]

    fingerprint = cert.get("fingerprint") or ""
    not_before = cert.get("notbefore") or ""
    not_after = cert.get("notafter") or ""

    if isinstance(not_before, (int, float)):
        not_before = str(int(not_before))
    if isinstance(not_after, (int, float)):
        not_after = str(int(not_after))

    return {
        "certificate": cert.get("pem") or "",
        "fingerprint": fingerprint,
        "issuer": cert.get("issuer") or "",
        "subject": cert.get("subject") or "",
        "not_before": int(not_before),
        "not_after": int(not_after),
        "subject_alternative_names": san,
    }
