#!/usr/bin/python

# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_acme_certificates_info
short_description: Retrieves the list of certificates on a Proxmox VE node.
version_added: 2.0.0
author: Clément Cruau (@PendaGTP)
description:
  - Retrieves the list of certificates on a Proxmox VE node.
  - Also returns the ACME configuration (account and domains) from the node config.
options:
  node_name:
    description:
      - The name of the Proxmox VE node to list certificates for.
    type: str
    required: true

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module

seealso:
  - module: community.proxmox.proxmox_acme_certificate
"""

EXAMPLES = r"""
- name: List certificates
  community.proxmox.proxmox_acme_certificates_info:
    node_name: pve-node-01
"""

RETURN = r"""
account:
  description: The ACME account name configured on the node.
  returned: on success
  type: str
domains:
  description: The list of ACME domains configured on the node.
  returned: on success
  type: list
  elements: dict
  contains:
    domain:
      description: The domain name.
      type: str
    plugin:
      description: The DNS plugin used for validation.
      type: str
    alias:
      description: The alias domain used for DNS validation.
      type: str
certificates:
  description: List of certificates on the node.
  returned: on success
  type: list
  elements: dict
  contains:
    certificate:
      description: The PEM-encoded certificate data.
      type: str
    fingerprint:
      description: The certificate fingerprint.
      type: str
    issuer:
      description: The certificate issuer.
      type: str
    subject:
      description: The certificate subject.
      type: str
    not_before:
      description: The certificate start timestamp.
      type: int
    not_after:
      description: The certificate expiration timestamp.
      type: int
    subject_alternative_names:
      description: The certificate subject alternative names (SANs).
      type: list
      elements: str
"""

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
)
from ansible_collections.community.proxmox.plugins.module_utils.proxmox_acme_certificate import (
    cert_info_to_ansible_result,
    parse_acme_config,
)


def module_args():
    return dict(
        node_name=dict(type="str", required=True),
    )


def module_options():
    return {}


class ProxmoxAcmeCertificatesInfoAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def run(self):
        node_name = self.params["node_name"]
        acme_config = self._read_node_acme_config(node_name)
        certificates = self._list_certificates(node_name)
        self.module.exit_json(
            changed=False,
            account=acme_config["account"],
            domains=acme_config["domains"],
            certificates=[cert_info_to_ansible_result(c) for c in certificates],
        )

    def _read_node_acme_config(self, node_name):
        try:
            config = self.proxmox_api.nodes(node_name).config.get()
        except Exception as e:
            self.module.fail_json(msg=f"Failed to read node config for {node_name}: {to_native(e)}")
        return parse_acme_config(config)

    def _list_certificates(self, node_name):
        try:
            return self.proxmox_api.nodes(node_name).certificates.info.get()
        except Exception as e:
            self.module.fail_json(msg=f"Failed to list certificates for node {node_name}: {to_native(e)}")


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxAcmeCertificatesInfoAnsible(module)

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f"An error occurred: {to_native(e)}")


if __name__ == "__main__":
    main()
