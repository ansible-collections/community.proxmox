#!/usr/bin/python

# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_acme_account
short_description: Manages an ACME account
version_added: "2.0.0"
author: Clément Cruau (@PendaGTP)
description:
  - Create, update or delete an ACME account on the Proxmox VE.
  - When an account already exists, only the contact email can be updated (Proxmox API limitation).
  - Requires C(root@pam) authentication.
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  state:
    description:
      - Desired state of the ACME account.
    type: str
    choices:
      - present
      - absent
    default: present
  name:
    description:
      - The ACME account name (filename).
    type: str
    default: default
  contact:
    description:
      - Contact email address for the ACME account.
      - Required when creating a new account (Proxmox API).
    type: str
  directory:
    description:
      - URL of the ACME CA directory endpoint.
    type: str
  eab_hmac_key:
    description:
      - HMAC key for External Account Binding (EAB).
    type: str
  eab_kid:
    description:
      - Key identifier for External Account Binding (EAB).
    type: str
  tos:
    description:
      - URL of the CA terms of service.
    type: str
    aliases:
      - tos_url

seealso:
  - name: Certificate management (Proxmox documentation)
    description: ACME accounts and certificates in Proxmox VE
    link: https://pve.proxmox.com/pve-docs/pve-admin-guide.html#sysadmin_certificate_management
  - module: community.proxmox.proxmox_acme_accounts_info
    description: List ACME account names.
  - module: community.proxmox.proxmox_acme_account_info
    description: Retrieve information about a single ACME account.

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Create ACME account
  community.proxmox.proxmox_acme_account:
    name: example
    contact: example@example.com
    directory: https://acme-staging-v02.api.letsencrypt.org/directory
    tos: https://letsencrypt.org/documents/LE-SA-v1.3-September-21-2022.pdf

- name: Update ACME account contact
  community.proxmox.proxmox_acme_account:
    name: example
    contact: other@example.com

- name: Ensure ACME account exists
  community.proxmox.proxmox_acme_account:
    name: example

- name: Remove ACME account
  community.proxmox.proxmox_acme_account:
    name: example
    state: absent
"""

RETURN = r"""
name:
  description: The ACME account configuration name.
  returned: on success
  type: str
account:
  description: ACME account data returned by the API.
  returned: when O(state=present) and the account exists
  type: dict
  contains:
    contact:
      description: Contact email addresses.
      type: list
      elements: str
    created_at:
      description: Account creation timestamp from the ACME API.
      type: str
    status:
      description: Account status (for example V(valid), V(deactivated), V(revoked)).
      type: str
directory:
  description: Directory URL of the ACME account.
  returned: when O(state=present) and the account exists
  type: str
location:
  description: Account resource URL from the ACME CA.
  returned: when O(state=present) and the account exists
  type: str
tos:
  description: Terms of service URL for the account.
  returned: when O(state=present) and the account exists
  type: str
msg:
  description: Short description of the action taken.
  returned: always
  type: str
"""

import re

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
    is_not_found_error,
)
from ansible_collections.community.proxmox.plugins.module_utils.proxmox_acme_account import (
    acme_account_to_ansible_result,
    normalize_contact_list,
)

DIRECTORY_URL_PATTERN = re.compile(r"^https?://.*$")


def module_args():
    return dict(
        state=dict(choices=["present", "absent"], default="present"),
        name=dict(type="str", default="default"),
        contact=dict(type="str"),
        directory=dict(type="str"),
        eab_hmac_key=dict(type="str", no_log=True),
        eab_kid=dict(type="str", no_log=True),
        tos=dict(type="str", aliases=["tos_url"]),
    )


def module_options():
    return {}


class ProxmoxClusterAcmeAccountAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def run(self):
        state = self.params["state"]
        name = self.params["name"]

        if state == "present":
            self._ensure_present(name)
        else:
            self._ensure_absent(name)

    def validate_params(self):
        directory = self.params.get("directory")
        if directory and not DIRECTORY_URL_PATTERN.match(directory):
            self.module.fail_json(
                msg="directory must be a valid URL (http:// or https://)",
                directory=directory,
            )

    def _ensure_present(self, name):
        existing = self._fetch_account(name)

        if existing is None:
            if self.module.check_mode:
                self.module.exit_json(
                    changed=True,
                    name=name,
                    msg=f"ACME account {name} would be created",
                )

            result = self._create_account(name)
            self.module.exit_json(**result)

        result = self._reconcile_existing(name, existing)
        self.module.exit_json(**result)

    def _ensure_absent(self, name):
        existing = self._fetch_account(name)

        if existing is None:
            self.module.exit_json(
                changed=False,
                name=name,
                msg=f"ACME account {name} does not exist",
            )

        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                name=name,
                msg=f"ACME account {name} would be deleted",
            )

        self._delete_account(name)

        self.module.exit_json(
            changed=True,
            name=name,
            msg=f"ACME account {name} successfully deleted",
        )

    def _reconcile_existing(self, name, existing):
        # No contact provided, nothing to do
        if not self._has_contact():
            result = acme_account_to_ansible_result(existing)
            return {
                "changed": False,
                "name": name,
                "msg": f"ACME account {name} exists; contact not specified, no update attempted",
                **result,
            }

        # API does not return contact, cannot detect drift
        if not self._has_api_contact(existing):
            self.module.warn(
                "Proxmox API did not return contact addresses; cannot verify drift; applying contact update.",
            )

            if self.module.check_mode:
                result = acme_account_to_ansible_result(existing)
                return {
                    "changed": True,
                    "name": name,
                    "msg": f"ACME account {name} contact would be updated",
                    **result,
                }

            return self._update_contact(name)

        # Already match
        if self._is_contact_up_to_date(existing):
            result = acme_account_to_ansible_result(existing)
            return {
                "changed": False,
                "name": name,
                "msg": f"ACME account {name} already has desired contact",
                **result,
            }

        # Needs update
        if self.module.check_mode:
            result = acme_account_to_ansible_result(existing)
            return {
                "changed": True,
                "name": name,
                "msg": f"ACME account {name} contact would be updated",
                **result,
            }

        return self._update_contact(name)

    def _has_contact(self):
        contact = self.params.get("contact")
        return bool(contact and to_native(contact).strip())

    def _has_api_contact(self, data):
        account = data.get("account") or {}
        contacts = account.get("contact")
        return bool(contacts and normalize_contact_list(contacts))

    def _is_contact_up_to_date(self, data):
        desired = to_native(self.params["contact"]).strip()
        account = data.get("account") or {}
        current = normalize_contact_list(account.get("contact"))

        return bool(current and current[0] == desired)

    def _create_account(self, name):
        if not self._has_contact():
            self.module.fail_json(
                msg="contact is required to create a new ACME account",
                name=name,
            )

        try:
            taskid = self._account_endpoint().post(**self._build_create_params())
            if taskid:
                self._wait_acme_task(taskid)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to create ACME account {name}: {to_native(e)}")

        data = self._fetch_account(name)
        if data is None:
            self.module.fail_json(
                msg=f"ACME account {name} not found after create",
                name=name,
            )

        result = acme_account_to_ansible_result(data)
        return {
            "changed": True,
            "name": name,
            "msg": f"ACME account {name} successfully created",
            **result,
        }

    def _update_contact(self, name):
        try:
            taskid = self._account_endpoint(name).put(contact=self.params["contact"])
            if taskid:
                self._wait_acme_task(taskid)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to update ACME account {name}: {to_native(e)}")

        updated = self._fetch_account(name)
        if updated is None:
            self.module.fail_json(
                msg=f"ACME account {name} not found after update",
                name=name,
            )

        result = acme_account_to_ansible_result(updated)
        return {
            "changed": True,
            "name": name,
            "msg": f"ACME account {name} successfully updated",
            **result,
        }

    def _delete_account(self, name):
        try:
            taskid = self._account_endpoint(name).delete()
            if taskid:
                self._wait_acme_task(taskid)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to delete ACME account {name}: {to_native(e)}")

    def _fetch_account(self, name):
        try:
            return self._account_endpoint(name).get()
        except Exception as e:
            if is_not_found_error(e):
                return None
            self.module.fail_json(msg=f"Failed to read ACME account {name}: {to_native(e)}")

    def _account_endpoint(self, name=None):
        base = self.proxmox_api.cluster().acme().account()
        return base if not name else base(name)

    def _wait_acme_task(self, taskid):
        node = self._node_from_upid(taskid)
        ok, err = self.api_task_complete(node, taskid, 30)

        if not ok:
            self.module.fail_json(
                msg=f"ACME background task failed: {err}",
                task=taskid,
            )

    def _node_from_upid(self, upid):
        parts = to_native(upid).split(":")
        if len(parts) >= 2 and parts[0] == "UPID":  # noqa: PLR2004
            return parts[1]

        self.module.fail_json(msg=f"Unexpected task id from Proxmox API: {upid}")

    def _build_create_params(self):
        p = self.params

        payload = {
            "name": p["name"],
            "contact": to_native(p["contact"]).strip(),
        }

        if p.get("directory"):
            payload["directory"] = p["directory"]
        if p.get("eab_hmac_key"):
            payload["eab-hmac-key"] = p["eab_hmac_key"]
        if p.get("eab_kid"):
            payload["eab-kid"] = p["eab_kid"]
        if p.get("tos"):
            payload["tos_url"] = p["tos"]

        return payload


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxClusterAcmeAccountAnsible(module)
    proxmox.validate_params()

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f"An error occurred: {to_native(e)}")


if __name__ == "__main__":
    main()
