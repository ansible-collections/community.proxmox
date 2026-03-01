#!/usr/bin/python
#
# Copyright Tristan Le Guern (@tleguern) <tleguern at bouledef.eu>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_domain_info
short_description: Retrieve information about one or more Proxmox VE domains
description:
  - Retrieve information about one or more Proxmox VE domains.
options:
  domain:
    description:
      - Restrict results to a specific authentication realm.
    aliases: ['realm', 'name']
    type: str
author: Tristan Le Guern (@tleguern)
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module
"""


EXAMPLES = r"""
- name: List existing domains
  community.proxmox.proxmox_domain_info:
    api_host: helldorado
    api_user: root@pam
    api_password: "{{ password | default(omit) }}"
    api_token_id: "{{ token_id | default(omit) }}"
    api_token_secret: "{{ token_secret | default(omit) }}"
  register: proxmox_domains

- name: Retrieve information about the pve domain
  community.proxmox.proxmox_domain_info:
    api_host: helldorado
    api_user: root@pam
    api_password: "{{ password | default(omit) }}"
    api_token_id: "{{ token_id | default(omit) }}"
    api_token_secret: "{{ token_secret | default(omit) }}"
    domain: pve
  register: proxmox_domain_pve
"""


RETURN = r"""
proxmox_domains:
  description: List of authentication domains.
  returned: always, but can be empty
  type: list
  elements: dict
  contains:
    comment:
      description: Short description of the realm.
      returned: on success
      type: str
    realm:
      description: Realm name.
      returned: on success
      type: str
    type:
      description: Realm type.
      returned: on success
      type: str
    digest:
      description: Realm hash.
      returned: on success, can be absent
      type: str
"""


from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
)


def module_args():
    return dict(
        domain=dict(type="str", aliases=["realm", "name"]),
    )


def module_options():
    return {}


class ProxmoxDomainInfoAnsible(ProxmoxAnsible):
    def get_domain(self, realm):
        try:
            domain = self.proxmox_api.access.domains.get(realm)
        except Exception:
            self.module.fail_json(msg=f"Domain '{realm}' does not exist")
        domain["realm"] = realm
        return domain

    def get_domains(self):
        domains = self.proxmox_api.access.domains.get()
        return domains


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxDomainInfoAnsible(module)

    result = dict(changed=False)

    domain = module.params["domain"]

    if domain:
        domains = [proxmox.get_domain(realm=domain)]
    else:
        domains = proxmox.get_domains()
    result["proxmox_domains"] = domains

    module.exit_json(**result)


if __name__ == "__main__":
    main()
