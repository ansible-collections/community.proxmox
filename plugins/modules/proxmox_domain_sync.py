#!/usr/bin/python
#
# Copyright (c) 2026, (@teslamania) <nicolas.vial@protonmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_domain_sync
version_added: 1.6.0
short_description: Sync realms.
description: Sync domain realms, LDAP or AD.
author: Vial Nicolas (@teslamania)
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none

options:
    enable_new:
        description: Enable creation of new users.
        required: false
        type: bool
    scope:
        description: Select what to sync.
        required: false
        choices: ['users', 'groups', 'both']
        type: str
    realm:
        description: Authentication domain ID.
        required: true
        type: str
    remove_vanished:
        description:
            - A semicolon-separated list of things to remove when they or the user vanishes during a sync.
            - The following values are possible
            - C(remove_vanished=acl) removes acls when the user/group is not returned from the sync.
            - C(remove_vanished=properties) removes the set properties on existing user/group that do not appear in the source (even custom ones).
            - C(remove_vanished=entry) removes the user/group when not returned from the sync.
            - Instead of a list it also can be C(remove_vanishe=none).
            - Exemple C(remove_vanished="acl;properties;entry")
        required: false
        type: str

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module
"""

EXAMPLES = r"""
- name: Sync LDAP domain
  community.proxmox.proxmox_domain_sync:
    api_host: 192.168.1.21
    api_user: "root@pam"
    api_password: secret
    realm: "example.test"
    enable_new: true
    scope: both
    removed_vanished: "acl;properties;entry"
"""

RETURN = r"""
msg:
    description: The output message that the module generates.
    type: str
    returned: always
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    ansible_to_proxmox_bool,
    proxmox_auth_argument_spec,
)


class ProxmoxDomainSyncAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def check_domain(self, realm):
        domains = self.proxmox_api.access.domains.get()
        return realm in [item["realm"] for item in domains]

    def build_arg(self):
        options = {}
        if self.params.get("enable_new") is not None:
            options["enable-new"] = ansible_to_proxmox_bool(self.params["enable_new"])
        if self.params.get("remove_vanished") is not None:
            options["remove-vanished"] = self.params["remove_vanished"]
        if self.params.get("scope") is not None:
            options["scope"] = self.params["scope"]

        return options

    def sync_domain(self):
        options = self.build_arg()
        if self.check_domain(self.params["realm"]):
            if not self.module.check_mode:
                self.proxmox_api.access.domains(self.params["realm"]).sync.post(**options)
                msg = f"Domain {self.params['realm']} synced."
            else:
                msg = f"Domain {self.params['realm']} would be synced."

            self.module.exit_json(changed=True, msg=msg)
        else:
            self.module.fail_json(msg=f"Domain {self.params['realm']} not present.")


def main():
    module_args = proxmox_auth_argument_spec()
    domain_args = dict(
        enable_new=dict(type="bool"),
        realm=dict(type="str", required=True),
        remove_vanished=dict(type="str"),
        scope=dict(choices=["users", "groups", "both"]),
    )

    module_args.update(domain_args)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[("api_password", "api_token_id")],
        required_together=[("api_token_id", "api_token_secret")],
    )
    proxmox = ProxmoxDomainSyncAnsible(module)
    try:
        proxmox.sync_domain()
    except Exception as e:
        module.fail_json(msg=f"An error occurred during sync: {e}")


if __name__ == "__main__":
    main()
