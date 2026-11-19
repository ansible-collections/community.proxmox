# Copyright (c) 2026, FingerlessGloves
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared translation helpers for the cluster options modules.

The Proxmox VE C(/cluster/options) endpoint is sparse: every option is optional and the API
only returns options that are actually set. This module centralises the mapping between the
Ansible-facing option names and the raw Proxmox API representation so that both
M(community.proxmox.proxmox_cluster_options) and
M(community.proxmox.proxmox_cluster_options_info) share a single source of truth.
"""

import base64
import binascii

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ansible_to_proxmox_bool,
    proxmox_to_ansible_bool,
)

# Scalar options. Each maps an Ansible option name to its raw Proxmox API name and the kind used
# to normalise the value read back from the API (and to encode it on the way out):
#   - "str":     used as-is
#   - "int":     the API may return it as a string (e.g. max_workers as "4"), so cast to int
#   - "text":   free text that Proxmox stores with a trailing newline (e.g. description), so strip it
#   - "base64": multi-line/markdown text that Proxmox stores base64-encoded (e.g. consent-text, as
#               the web UI does); base64-encode on write and decode on read
SCALAR_FIELDS = {
    "keyboard": {"api": "keyboard", "kind": "str"},
    "language": {"api": "language", "kind": "str"},
    "console": {"api": "console", "kind": "str"},
    "mac_prefix": {"api": "mac_prefix", "kind": "str"},
    "max_workers": {"api": "max_workers", "kind": "int"},
    "email_from": {"api": "email_from", "kind": "str"},
    "http_proxy": {"api": "http_proxy", "kind": "str"},
    "fencing": {"api": "fencing", "kind": "str"},
    "description": {"api": "description", "kind": "text"},
    "consent_text": {"api": "consent-text", "kind": "base64"},
}

# A few options are always returned by the API with their default value, even when they are not
# set in the datacenter configuration (the API has no "unset" representation for them). When the
# current value equals the default, the option is effectively unset, so a delete is a no-op.
# This keeps deleting these fields idempotent.
ECHOED_DEFAULTS = {
    "mac_prefix": "BC:24:11",
    "description": "",
}

# Property-string fields: an Ansible dict whose suboptions are encoded by Proxmox as a single
# "key=value,key=value" string. The value lists the (ansible_subkey, api_subkey, kind) triples,
# where kind is one of "str", "int", "bool".
PROPERTY_STRING_FIELDS = {
    "migration": {
        "api": "migration",
        # Proxmox marks ``type`` as the default key, so it is returned as a bare token
        # (for example ``secure,network=10.0.0.0/24`` rather than ``type=secure,...``).
        "default_key": "type",
        "subkeys": [
            ("type", "type", "str"),
            ("network", "network", "str"),
        ],
    },
    "replication": {
        "api": "replication",
        # Same shape as ``migration``; ``type`` is the default key.
        "default_key": "type",
        "subkeys": [
            ("type", "type", "str"),
            ("network", "network", "str"),
        ],
    },
    "bwlimit": {
        "api": "bwlimit",
        "subkeys": [
            ("clone", "clone", "int"),
            ("default", "default", "int"),
            ("migration", "migration", "int"),
            ("move", "move", "int"),
            ("restore", "restore", "int"),
        ],
    },
    "ha": {
        "api": "ha",
        "subkeys": [
            ("shutdown_policy", "shutdown_policy", "str"),
        ],
    },
    "crs": {
        "api": "crs",
        "subkeys": [
            ("ha", "ha", "str"),
            ("ha_auto_rebalance", "ha-auto-rebalance", "bool"),
            ("ha_auto_rebalance_hold_duration", "ha-auto-rebalance-hold-duration", "int"),
            ("ha_auto_rebalance_margin", "ha-auto-rebalance-margin", "int"),
            ("ha_auto_rebalance_method", "ha-auto-rebalance-method", "str"),
            ("ha_auto_rebalance_threshold", "ha-auto-rebalance-threshold", "int"),
            ("ha_rebalance_on_start", "ha-rebalance-on-start", "bool"),
        ],
    },
    "next_id": {
        "api": "next-id",
        "subkeys": [
            ("lower", "lower", "int"),
            ("upper", "upper", "int"),
        ],
    },
    "location": {
        "api": "location",
        "subkeys": [
            ("latitude", "latitude", "float"),
            ("longitude", "longitude", "float"),
            ("name", "name", "str"),
        ],
    },
    "u2f": {
        "api": "u2f",
        "subkeys": [
            ("appid", "appid", "str"),
            ("origin", "origin", "str"),
        ],
    },
    "webauthn": {
        "api": "webauthn",
        "subkeys": [
            ("allow_subdomains", "allow-subdomains", "bool"),
            ("id", "id", "str"),
            ("origin", "origin", "str"),
            ("rp", "rp", "str"),
        ],
    },
    "notify": {
        "api": "notify",
        "subkeys": [
            ("fencing", "fencing", "str"),
            ("package_updates", "package-updates", "str"),
            ("replication", "replication", "str"),
            ("target_fencing", "target-fencing", "str"),
            ("target_package_updates", "target-package-updates", "str"),
            ("target_replication", "target-replication", "str"),
        ],
    },
    "tag_style": {
        "api": "tag-style",
        "subkeys": [
            ("case_sensitive", "case-sensitive", "bool"),
            ("color_map", "color-map", "str"),
            ("ordering", "ordering", "str"),
            ("shape", "shape", "str"),
        ],
    },
    "user_tag_access": {
        "api": "user-tag-access",
        "subkeys": [
            ("user_allow", "user-allow", "str"),
            ("user_allow_list", "user-allow-list", "taglist"),
        ],
    },
}

# List options: a bare list that Proxmox encodes as a separated string but the JSON API may
# return as a list.
LIST_FIELDS = {
    "registered_tags": {"api": "registered-tags", "sep": ";"},
}

# Map an Ansible option name to the raw Proxmox API option name (only where they differ).
ANSIBLE_TO_API = {name: cfg["api"] for name, cfg in SCALAR_FIELDS.items()}
ANSIBLE_TO_API.update({field: meta["api"] for field, meta in PROPERTY_STRING_FIELDS.items()})
ANSIBLE_TO_API.update({name: cfg["api"] for name, cfg in LIST_FIELDS.items()})


def ansible_option_to_api(name):
    """Return the Proxmox API option name for an Ansible option name.

    Args:
        name(str): The Ansible-facing option name.

    Returns:
        str: The matching Proxmox API option name (unchanged when no mapping exists).
    """
    return ANSIBLE_TO_API.get(name, name)


def scalar_to_api(name, value):
    """Encode a scalar Ansible value for the Proxmox API.

    Most scalars are sent unchanged, but C(base64) fields (e.g. C(consent_text)) must be
    base64-encoded, matching the Proxmox VE web interface: Proxmox stores them base64-encoded
    in the line-based datacenter configuration, and sending raw text would both truncate
    multi-line content at the first newline and render incorrectly in the UI/login screen.

    Args:
        name(str): The Ansible scalar option name (key of C(SCALAR_FIELDS)).
        value: The value provided by the user.

    Returns:
        The value ready to send to the API.
    """
    if SCALAR_FIELDS[name]["kind"] == "base64" and isinstance(value, str):
        return base64.b64encode(value.encode("utf-8")).decode("ascii")
    return value


def _cast_subvalue(value, kind):
    """Cast a raw property sub-value into the Ansible-side type.

    The Proxmox JSON API is inconsistent and may return numeric sub-values either as
    integers or as strings (for example C(ha-auto-rebalance-margin) as C('15') but
    C(ha-rebalance-on-start) as C(1)), so casting must accept both.

    Args:
        value: The raw value (string or number) parsed from the API.
        kind(str): One of C(str), C(int), C(float) or C(bool).

    Returns:
        The value converted to the requested type, or C(None) when a numeric cast fails.
    """
    if value is None:
        return None
    if kind == "taglist":
        # A semicolon-separated tag list; the JSON API may return it as a list or a string.
        items = value if isinstance(value, list) else [t for t in str(value).split(";") if t]
        return [str(t) for t in items] or None
    if kind in ("int", "float"):
        caster = int if kind == "int" else float
        try:
            return caster(value)
        except (TypeError, ValueError):
            return None
    if kind == "bool":
        return proxmox_to_ansible_bool(1 if str(value).strip() == "1" else 0)
    return value


def parse_property_string(field, value):
    """Parse a Proxmox property string into an Ansible dict.

    Args:
        field(str): The property-string field name (key of C(PROPERTY_STRING_FIELDS)).
        value(str): The raw C(key=value,key=value) string from the API.

    Returns:
        dict | None: The decoded suboptions, or C(None) when nothing could be parsed.
    """
    if not value or not isinstance(value, str):
        return None

    field_cfg = PROPERTY_STRING_FIELDS[field]
    by_api = {api_key: (ans_key, kind) for ans_key, api_key, kind in field_cfg["subkeys"]}
    kind_by_ans = {ans_key: kind for ans_key, api_key, kind in field_cfg["subkeys"]}
    default_key = field_cfg.get("default_key")

    result = {}
    for raw_part in value.strip().split(","):
        part = raw_part.strip()
        if not part:
            continue
        if "=" not in part:
            # A bare token is the value of the default key (for example ``secure`` for migration).
            if default_key:
                cast = _cast_subvalue(part, kind_by_ans[default_key])
                if cast is not None:
                    result[default_key] = cast
            continue
        key, val = part.split("=", 1)
        key = key.strip()
        val = val.strip()
        if key not in by_api:
            continue
        ans_key, kind = by_api[key]
        cast = _cast_subvalue(val, kind)
        if cast is not None:
            result[ans_key] = cast
    return result or None


def decode_property_value(field, value):
    """Decode a property field returned by the Proxmox JSON API into an Ansible dict.

    Depending on the field and the Proxmox version, the JSON API returns such a field
    either as a raw C(key=value,key=value) string (for example C(bwlimit)) or as an
    already-decoded dict keyed by the raw API sub-keys, for example
    C({'ha-rebalance-on-start': 1, 'ha': 'static'}) for C(crs). Both forms are handled
    and normalised to the Ansible sub-option names and types.

    Args:
        field(str): The property-string field name (key of C(PROPERTY_STRING_FIELDS)).
        value: The raw value from the API (string or dict).

    Returns:
        dict | None: The decoded suboptions, or C(None) when nothing could be decoded.
    """
    if isinstance(value, dict):
        by_api = {api_key: (ans_key, kind) for ans_key, api_key, kind in PROPERTY_STRING_FIELDS[field]["subkeys"]}
        result = {}
        for api_key, raw in value.items():
            if api_key not in by_api:
                continue
            ans_key, kind = by_api[api_key]
            cast = _cast_subvalue(raw, kind)
            if cast is not None:
                result[ans_key] = cast
        return result or None

    return parse_property_string(field, value)


def build_property_string(field, data):
    """Build a Proxmox property string from an Ansible dict.

    Args:
        field(str): The property-string field name (key of C(PROPERTY_STRING_FIELDS)).
        data(dict): The user-provided suboptions (values may be C(None)).

    Returns:
        str | None: The encoded C(key=value,key=value) string, or C(None) when no
            suboption was provided.
    """
    if not data:
        return None

    parts = []
    for ans_key, api_key, kind in PROPERTY_STRING_FIELDS[field]["subkeys"]:
        value = data.get(ans_key)
        if value is None:
            continue
        if kind == "bool":
            parts.append(f"{api_key}={ansible_to_proxmox_bool(value)}")
        elif kind == "int":
            parts.append(f"{api_key}={int(value)}")
        elif kind == "float":
            parts.append(f"{api_key}={float(value)}")
        elif kind == "taglist":
            parts.append(f"{api_key}={';'.join(str(t) for t in value)}")
        else:
            parts.append(f"{api_key}={value}")
    return ",".join(parts) if parts else None


def _normalize_scalar(kind, value):
    """Normalise a scalar value read from the API into its Ansible-side representation."""
    if kind == "int":
        return _cast_subvalue(value, "int")
    if kind == "text" and isinstance(value, str):
        # Proxmox stores free-text fields (e.g. description) with a trailing newline.
        return value.rstrip("\n")
    if kind == "base64" and isinstance(value, str):
        # Proxmox stores this field base64-encoded; decode it back to plain text.
        try:
            return base64.b64decode(value, validate=True).decode("utf-8")
        except (binascii.Error, ValueError, UnicodeDecodeError):
            return value
    return value


def cluster_options_to_ansible_result(raw):
    """Translate the raw C(/cluster/options) API response into Ansible-friendly values.

    Only keys that are actually present in the API response are translated. Property-string
    fields are decoded into dicts. Any key the modules do not model (for example the read-only
    C(allowed-tags)) is passed through unchanged so callers see the complete datacenter
    configuration.

    Args:
        raw(dict): The raw response from C(GET /cluster/options).

    Returns:
        dict: The translated option set.
    """
    if not raw:
        return {}

    result = {}
    api_to_field = {meta["api"]: field for field, meta in PROPERTY_STRING_FIELDS.items()}
    api_to_scalar = {cfg["api"]: (name, cfg["kind"]) for name, cfg in SCALAR_FIELDS.items()}
    api_to_list = {cfg["api"]: (name, cfg["sep"]) for name, cfg in LIST_FIELDS.items()}

    for api_key, value in raw.items():
        if api_key in api_to_list:
            name, sep = api_to_list[api_key]
            # The API may return a list directly or a separated string.
            result[name] = value if isinstance(value, list) else [t for t in str(value).split(sep) if t]
        elif api_key in api_to_scalar:
            name, kind = api_to_scalar[api_key]
            result[name] = _normalize_scalar(kind, value)
        elif api_key in api_to_field:
            decoded = decode_property_value(api_to_field[api_key], value)
            if decoded is not None:
                result[api_to_field[api_key]] = decoded
        else:
            # Unmodelled key (e.g. allowed-tags): surface it untouched.
            result[api_key] = value

    return result
