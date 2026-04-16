#!/usr/bin/python

# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_acme_accounts_info
short_description: Retrieves the list of ACME accounts.
version_added: "2.0.0"
author: Clément Cruau (@PendaGTP)
description:
  - Retrieves the list of ACME accounts.
  - For information about one account, use M(community.proxmox.proxmox_acme_account_info).

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module

seealso:
  - module: community.proxmox.proxmox_acme_account_info
    description: Retrieve information about a single ACME account.
  - module: community.proxmox.proxmox_acme_account
    description: Create, update or delete an ACME account.
"""

EXAMPLES = r"""
- name: List ACME account names
  community.proxmox.proxmox_acme_accounts_info:
"""

RETURN = r"""
accounts:
  description: List of ACME account names (filenames).
  returned: on success
  type: list
  elements: str
"""

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
)


def module_args():
    return dict()


def module_options():
    return {}


class ProxmoxClusterAcmeAccountsInfoAnsible(ProxmoxAnsible):
    def run(self):
        self.module.exit_json(
            changed=False,
            accounts=self._list_account_names(),
        )

    def _list_account_names(self):
        try:
            accounts = self.proxmox_api.cluster().acme().account().get()
        except Exception as e:
            self.module.fail_json(msg=f"Failed to list ACME accounts: {to_native(e)}")
        names = []
        for account in accounts:
            names.append(account["name"])
        return sorted(set(names))


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxClusterAcmeAccountsInfoAnsible(module)

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f"An error occurred: {to_native(e)}")


if __name__ == "__main__":
    main()
