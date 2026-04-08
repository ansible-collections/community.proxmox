#!/usr/bin/python

# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_acme_plugin_dns
short_description: Manage ACME DNS plugins on a Proxmox VE.
version_added: "2.1.0"
author:
  - Clément Cruau (@PendaGTP)
description:
  - Create, update or delete a DNS challenge ACME plugin configuration.
  - Requires C(root@pam) authentication.
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  state:
    description:
      - Desired state of the ACME DNS plugin.
    type: str
    choices:
      - present
      - absent
    default: present
  name:
    description:
      - The ACME plugin instance identifier.
    type: str
    required: true
    aliases: ["id"]
  plugin:
    description:
      - DNS API implementation name (for example V(cf) for Cloudflare or V(googledomains) for Google Cloud DNS).
    type: str
  data:
    description:
      - DNS plugin settings as string key/value pairs.
    type: dict
  disable:
    description:
      - Disable this plugin configuration.
    type: bool
    default: false
  validation_delay:
    description:
      - Extra delay in seconds to wait before requesting validation. Allows to cope with a long TTL of DNS records (0 - 172800).
    type: int
    default: 30

seealso:
  - name: ACME DNS API Challenge Plugin
    description: ACME DNS API Challenge Plugin (Proxmox documentation)
    link: https://pve.proxmox.com/pve-docs/chapter-sysadmin.html#sysadmin_certs_acme_dns_challenge

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Configure ACME Plugin DNS (Cloudflare)
  community.proxmox.proxmox_acme_plugin_dns:
    name: cloudflare
    plugin: cf
    data:
      CF_Account_ID: example
      CF_Token: example

- name: Remove ACME DNS plugin
  community.proxmox.proxmox_acme_plugin_dns:
    name: cloudflare
    state: absent
"""

RETURN = r"""
name:
  description: ACME plugin instance identifier.
  returned: on success
  type: str
plugin:
  description: DNS API implementation name.
  returned: on success when O(state=present)
  type: str
data:
  description: DNS plugin settings as string key/value pairs (value are masked).
  returned: on success when O(state=present)
  type: dict
disable:
  description: Whether the plugin configuration is disabled.
  returned: on success when O(state=present)
  type: bool
validation_delay:
  description: Validation delay in seconds.
  returned: on success when O(state=present)
  type: int
digest:
  description: Digest of the plugin configuration.
  returned: on success when O(state=present)
  type: str
msg:
  description: Short description of the action taken.
  returned: always
  type: str
"""

import base64

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    ansible_to_proxmox_bool,
    create_proxmox_module,
)
from ansible_collections.community.proxmox.plugins.module_utils.proxmox_acme_plugin import (
    acme_plugin_normalize_data_dict,
    acme_plugin_to_ansible_result,
)

MIN_VALIDATION_DELAY = 0
MAX_VALIDATION_DELAY = 172800


def _data_to_api(data):
    """Encode plugin data dict to the base64 string expected by the API."""
    norm = acme_plugin_normalize_data_dict(data)
    out = "\n".join(f"{k}={norm[k]}" for k in sorted(norm))
    return base64.b64encode(out.encode("utf-8")).decode("ascii")


def module_args():
    return dict(
        state=dict(choices=["present", "absent"], default="present"),
        name=dict(type="str", required=True, aliases=["id"]),
        plugin=dict(type="str"),
        data=dict(type="dict", no_log=True),
        disable=dict(type="bool", default=False),
        validation_delay=dict(type="int", default=30),
    )


def module_options():
    return dict(
        required_if=[("state", "present", ["plugin"])],
    )


class ProxmoxClusterAcmePluginDnsAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def validate_params(self):
        delay = self.params.get("validation_delay")
        if delay is not None and (delay < MIN_VALIDATION_DELAY or delay > MAX_VALIDATION_DELAY):
            self.module.fail_json(
                msg=f"validation_delay should be between {MIN_VALIDATION_DELAY} and {MAX_VALIDATION_DELAY}",
            )

    def run(self):
        state = self.params["state"]
        name = self.params["name"]

        if state == "present":
            self._ensure_present(name)
        else:
            self._ensure_absent(name)

    def _ensure_present(self, name):
        existing = self._fetch_plugin(name)

        if existing is None:
            if self.module.check_mode:
                self.module.exit_json(
                    changed=True,
                    name=name,
                    msg=f"ACME DNS plugin {name} would be created",
                )

            result = self._create_plugin(name)
            self.module.exit_json(**result)

        result = self._reconcile_existing(name, existing)
        self.module.exit_json(**result)

    def _ensure_absent(self, name):
        existing = self._fetch_plugin(name)

        if existing is None:
            self.module.exit_json(
                changed=False,
                name=name,
                msg=f"ACME DNS plugin {name} does not exist",
            )

        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                name=name,
                msg=f"ACME DNS plugin {name} would be deleted",
            )

        self._delete_plugin(name)

        self.module.exit_json(
            changed=True,
            name=name,
            msg=f"ACME DNS plugin {name} successfully deleted",
        )

    def _reconcile_existing(self, name, existing):
        current = acme_plugin_to_ansible_result(existing)
        desired = self._build_desired(name)

        if not self._is_update_required(current, desired):
            return {
                "changed": False,
                "msg": f"ACME DNS plugin {name} already up to date",
                **current,
            }

        if self.module.check_mode:
            return {
                "changed": True,
                "name": name,
                "msg": f"ACME DNS plugin {name} would be updated",
            }

        return self._update_plugin(name)

    def _is_update_required(self, current, desired):
        return (
            current["plugin"] != desired["plugin"]
            or current["disable"] != desired["disable"]
            or current["validation_delay"] != desired["validation_delay"]
            or (desired.get("data") is not None and current["data"] != desired["data"])
        )

    def _create_plugin(self, name):
        payload = {"type": "dns", **self._build_params()}

        try:
            self._plugin_endpoint().post(id=name, **payload)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to create ACME DNS plugin {name}: {to_native(e)}")

        created = self._fetch_plugin(name)
        if created is None:
            self.module.fail_json(
                msg=f"ACME DNS plugin {name} not found after create",
                name=name,
            )

        result = acme_plugin_to_ansible_result(created)
        return {
            "changed": True,
            "msg": f"ACME DNS plugin {name} successfully created",
            **result,
        }

    def _update_plugin(self, name):
        payload = self._build_params()

        try:
            self._plugin_endpoint(name).put(**payload)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to update ACME DNS plugin {name}: {to_native(e)}")

        updated = self._fetch_plugin(name)
        if updated is None:
            self.module.fail_json(
                msg=f"ACME DNS plugin {name} not found after update",
                name=name,
            )

        result = acme_plugin_to_ansible_result(updated)
        return {
            "changed": True,
            "msg": f"ACME DNS plugin {name} successfully updated",
            **result,
        }

    def _delete_plugin(self, name):
        try:
            self._plugin_endpoint(name).delete()
        except Exception as e:
            self.module.fail_json(msg=f"Failed to delete ACME DNS plugin {name}: {to_native(e)}")

    def _fetch_plugin(self, name):
        try:
            return self._plugin_endpoint(name).get()
        except Exception as e:
            if "not defined" in str(e).lower():
                return None
            self.module.fail_json(msg=f"Failed to read ACME plugin {name}: {to_native(e)}")

    def _plugin_endpoint(self, name=None):
        base = self.proxmox_api.cluster().acme().plugins()
        return base if not name else base(name)

    def _build_desired(self, name):
        p = self.params
        raw_data = p.get("data")

        return {
            "name": name,
            "plugin": p["plugin"],
            "disable": p["disable"],
            "validation_delay": p["validation_delay"],
            "data": None if raw_data is None else acme_plugin_normalize_data_dict(raw_data),
        }

    def _build_params(self):
        p = self.params

        payload = {
            "api": p["plugin"],
            "validation-delay": p["validation_delay"],
            "disable": ansible_to_proxmox_bool(p["disable"]),
        }

        if p.get("data") is not None:
            payload["data"] = _data_to_api(p["data"])

        return payload


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxClusterAcmePluginDnsAnsible(module)
    proxmox.validate_params()

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f"An error occurred: {to_native(e)}")


if __name__ == "__main__":
    main()
