#!/usr/bin/python

# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_acme_account_info
short_description: Retrieve one ACME account
version_added: "2.0.0"
author: Clément Cruau (@PendaGTP)
description:
  - Retrieve information about an ACME account configuration.
  - To list all ACME account names, use M(community.proxmox.proxmox_acme_accounts_info).
  - Requires C(root@pam) authentication.
options:
  name:
    description:
      - The ACME account name (filename).
    type: str
    required: true

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module

seealso:
  - module: community.proxmox.proxmox_acme_accounts_info
    description: List ACME account names.
  - module: community.proxmox.proxmox_acme_account
    description: Create, update or delete an ACME account.
"""

EXAMPLES = r"""
- name: Get ACME account example
  community.proxmox.proxmox_acme_account_info:
    name: example
"""

RETURN = r"""
name:
  description: The ACME account name (filename).
  returned: on success
  type: str
account:
  description: ACME account data returned by the API.
  returned: on success
  type: dict
  contains:
    contact:
      description: Contact email addresses (normalized from C(mailto:)).
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
  returned: on success
  type: str
location:
  description: Account resource URL from the ACME CA.
  returned: on success
  type: str
tos:
  description: Terms of service URL for the account.
  returned: on success
  type: str
"""

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
)
from ansible_collections.community.proxmox.plugins.module_utils.proxmox_acme_account import (
    acme_account_to_ansible_result,
)


def module_args():
    return dict(
        name=dict(type="str", required=True),
    )


def module_options():
    return {}


class ProxmoxClusterAcmeAccountInfoAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def run(self):
        name = self.params["name"]
        data = self._fetch_account(name)
        if data is None:
            self.module.fail_json(msg=f"ACME account {name} does not exist", name=name)

        result = acme_account_to_ansible_result(data)
        self.module.exit_json(
            changed=False,
            name=name,
            **result,
        )

    def _fetch_account(self, name):
        try:
            return self.proxmox_api.cluster().acme().account()(name).get()
        except Exception as e:
            err = str(e).lower()
            if "does not exist" in err or "not found" in err or "404" in err:
                return None
            self.module.fail_json(msg=f"Failed to read ACME account {name}: {to_native(e)}")


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxClusterAcmeAccountInfoAnsible(module)

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f"An error occurred: {to_native(e)}")


if __name__ == "__main__":
    main()
