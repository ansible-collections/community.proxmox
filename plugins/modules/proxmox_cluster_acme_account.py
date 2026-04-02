#!/usr/bin/python

# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_cluster_acme_account
short_description: ACME account management for Proxmox VE cluster
version_added: "2.1.0"
author: Clément Cruau (@PendaGTP)
description:
  - Create, update or delete an ACME account on the Proxmox VE cluster.
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
  - module: community.proxmox.proxmox_cluster_acme_accounts_info
    description: List ACME account names.
  - module: community.proxmox.proxmox_cluster_acme_account_info
    description: Retrieve information about a single ACME account.

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Create ACME account
  community.proxmox.proxmox_cluster_acme_account:
    name: example
    contact: example@example.com
    directory: https://acme-staging-v02.api.letsencrypt.org/directory
    tos: https://letsencrypt.org/documents/LE-SA-v1.3-September-21-2022.pdf

- name: Update ACME account contact
  community.proxmox.proxmox_cluster_acme_account:
    name: example
    contact: other@example.com

- name: Ensure ACME account exists
  community.proxmox.proxmox_cluster_acme_account:
    name: example

- name: Remove ACME account
  community.proxmox.proxmox_cluster_acme_account:
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
)
from ansible_collections.community.proxmox.plugins.module_utils.proxmox_cluster_acme import (
    acme_account_get_to_ansible,
    normalize_acme_contacts,
)

DIRECTORY_URL_PATTERN = re.compile(r"^https?://.*$")
ACME_TASK_WAIT_SECONDS = 30
_UPID_MIN_SEGMENTS = 2


def _contact_provided(params):
    c = params.get("contact")
    if c is None:
        return False
    return bool(to_native(c).strip())


def _api_returns_contact(data):
    """True if GET includes a non-empty contact list."""
    acc = data.get("account") or {}
    if acc["contact"] is None:
        return False
    return len(normalize_acme_contacts(acc["contact"])) > 0


def module_args():
    return dict(
        state=dict(choices=["present", "absent"], default="present"),
        name=dict(type="str", default="default"),
        contact=dict(type="str"),
        directory=dict(type="str"),
        eab_hmac_key=dict(type="str", no_log=True),
        eab_kid=dict(type="str"),
        tos=dict(type="str", aliases=["tos_url"]),
    )


def module_options():
    return {}


class ProxmoxClusterAcmeAccountAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def validate_params(self):
        directory = self.params.get("directory")
        if directory and not DIRECTORY_URL_PATTERN.match(directory):
            self.module.fail_json(
                msg="directory must be a valid URL (http:// or https://)",
                directory=directory,
            )

    def _acme_account_api(self, name=None):
        base = self.proxmox_api.cluster().acme().account()
        if name in (None, ""):
            return base
        return base(name)

    def _node_from_upid(self, upid):
        """Extract the cluster node from a Proxmox task id so api_task_complete can poll task status."""
        parts = to_native(upid).split(":")
        if len(parts) >= _UPID_MIN_SEGMENTS and parts[0] == "UPID":
            return parts[1]
        self.module.fail_json(msg=f"Unexpected task id from Proxmox API: {upid!r}")

    def _wait_acme_task(self, taskid):
        node = self._node_from_upid(taskid)
        ok, err = self.api_task_complete(node, taskid, ACME_TASK_WAIT_SECONDS)
        if not ok:
            self.module.fail_json(msg=f"ACME background task failed: {err}", task=taskid)

    def _get_account(self, name):
        try:
            return self._acme_account_api(name).get()
        except Exception as e:
            err = str(e).lower()
            if "does not exist" in err or "not found" in err or "404" in err:
                return None
            self.module.fail_json(msg=f"Failed to read ACME account {name}: {to_native(e)}")

    def _desired_contact_matches(self, data):
        if not _contact_provided(self.params):
            return False
        desired = self.params["contact"].strip()
        current_list = normalize_acme_contacts((data.get("account") or {}).get("contact"))
        if not current_list:
            return False
        return current_list[0] == desired

    def _build_create_payload(self):
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

    def run(self):
        state = self.params["state"]
        name = self.params["name"]

        if state == "present":
            self._present(name)
        else:
            self._absent(name)

    def _put_contact_update(self, name):
        try:
            taskid = self._acme_account_api(name).put(contact=self.params["contact"])
            if taskid:
                self._wait_acme_task(taskid)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to update ACME account {name}: {to_native(e)}")

        updated = self._get_account(name)
        if updated is None:
            self.module.fail_json(msg=f"ACME account {name} not found after update", name=name)
        result = acme_account_get_to_ansible(updated)
        self.module.exit_json(
            changed=True,
            name=name,
            msg=f"ACME account {name} successfully updated",
            **result,
        )

    def _present(self, name):
        existing = self._get_account(name)

        if existing is None:
            if not _contact_provided(self.params):
                self.module.fail_json(
                    msg="contact is required to create a new ACME account",
                    name=name,
                )
            if self.module.check_mode:
                self.module.exit_json(
                    changed=True,
                    name=name,
                    msg=f"ACME account {name} would be created",
                )

            try:
                taskid = self._acme_account_api().post(**self._build_create_payload())
                if taskid:
                    self._wait_acme_task(taskid)
            except Exception as e:
                self.module.fail_json(msg=f"Failed to create ACME account {name}: {to_native(e)}")

            data = self._get_account(name)
            if data is None:
                self.module.fail_json(msg=f"ACME account {name} not found after create", name=name)
            result = acme_account_get_to_ansible(data)
            self.module.exit_json(
                changed=True,
                name=name,
                msg=f"ACME account {name} successfully created",
                **result,
            )

        if not _contact_provided(self.params):
            result = acme_account_get_to_ansible(existing)
            self.module.exit_json(
                changed=False,
                name=name,
                msg=f"ACME account {name} exists; contact not specified, no update attempted",
                **result,
            )

        if not _api_returns_contact(existing):
            self.module.warn(
                "Proxmox API did not return contact addresses; cannot verify drift; applying contact update.",
            )
            if self.module.check_mode:
                result = acme_account_get_to_ansible(existing)
                self.module.exit_json(
                    changed=True,
                    name=name,
                    msg=f"ACME account {name} contact would be updated",
                    **result,
                )
            self._put_contact_update(name)

        if self._desired_contact_matches(existing):
            result = acme_account_get_to_ansible(existing)
            self.module.exit_json(
                changed=False,
                name=name,
                msg=f"ACME account {name} already has desired contact",
                **result,
            )

        if self.module.check_mode:
            result = acme_account_get_to_ansible(existing)
            self.module.exit_json(
                changed=True,
                name=name,
                msg=f"ACME account {name} contact would be updated",
                **result,
            )

        self._put_contact_update(name)

    def _absent(self, name):
        existing = self._get_account(name)
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

        try:
            taskid = self._acme_account_api(name).delete()
            if taskid:
                self._wait_acme_task(taskid)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to delete ACME account {name}: {to_native(e)}")

        self.module.exit_json(
            changed=True,
            name=name,
            msg=f"ACME account {name} successfully deleted",
        )


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
