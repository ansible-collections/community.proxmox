#!/usr/bin/python
#
# Copyright (c) 2025, Peter Tselios (@icultus) <27899013+itcultus@users.noreply.github.com>
# Copyright (c) 2025, Florian Paul Azim Hoberg (@gyptazy) <florian.hoberg@credativ.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_node
version_added: 1.2.0
short_description: Manage Proxmox VE nodes
description:
  - Manage the Proxmox VE nodes itself.
author:
  - Florian Paul Azim Hoberg (@gyptazy)
  - Peter Tselios (@itcultus)
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  node_name:
    description:
      - The targeted node to perform actions on.
    type: str
    aliases: ["node"]
    required: true
  power_state:
    description:
      - Manages the power state of the node.
    type: str
    required: false
    choices: ["online", "offline"]
  certificates:
    description:
      - Manages the x509 certificates of the node.
    type: dict
    suboptions:
      cert:
        description:
          - The public certificate file path (including chain) in PEM format.
          - Mutually exclusive with O(certificates.certificate).
        type: str
        aliases: ["certificate_file_path"]
      certificate:
        description:
          - The public certificate as a raw PEM encoded string (including chain).
          - Mutually exclusive with O(certificates.cert).
        type: str
        aliases: ["certificate_raw"]
      key:
        description:
          - The private key file path in PEM format.
          - Mutually exclusive with O(certificates.private_key).
        type: str
        aliases: ["private_key_file_path"]
      private_key:
        description:
          - The private key as a raw PEM encoded string.
          - Mutually exclusive with O(certificates.key).
        type: str
        aliases: ["private_key_raw"]
      state:
        description:
          - Defines the actions for the certificate.
        choices: ["present", "absent"]
        type: str
      restart:
        description:
          - Restart pveproxy to rehash the new certificates.
        type: bool
        default: false
      force:
        description:
          - Overwrite existing custom certificate files.
        type: bool
        default: false
  dns:
    description:
      - Manages the resolving DNS options of the node.
    type: dict
    suboptions:
      dns1:
        description:
          - The IP address of the first DNS resolver.
        type: str
      dns2:
        description:
          - The IP address of the second DNS resolver.
        type: str
      dns3:
        description:
          - The IP address of the third DNS resolver.
        type: str
      search:
        description:
          - The default search domain.
        type: str
        required: true
  subscription:
    description:
      - Manages the license subscription of the node.
    type: dict
    suboptions:
      state:
        description:
          - Defines the actions for the subscription file.
        choices: ["present", "absent"]
        type: str
      key:
        description:
          - The subscription license key.
        type: str
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Start a Proxmox VE Node
  community.proxmox.node:
    api_host: proxmoxhost
    api_user: root@pam
    api_password: password123
    node_name: de-cgn01-virt01
    power_state: online

- name: Update SSL certificates on a Proxmox VE Node (from files)
  community.proxmox.node:
    api_host: proxmoxhost
    api_user: root@pam
    api_password: password123
    node_name: de-cgn01-virt01
    certificates:
        private_key_file_path: /opt/ansible/key.pem
        certificate_file_path: /opt/ansible/cert.pem
        state: present
        force: false

- name: Update SSL certificates on a Proxmox VE Node (raw PEM)
  community.proxmox.node:
    api_host: proxmoxhost
    api_user: root@pam
    api_password: password123
    node_name: de-cgn01-virt01
    certificates:
        certificate: "{{ pve_node_certificate_content }}"
        private_key: "{{ pve_node_private_key_content }}"
        state: present

- name: Place a subscription license on a Proxmox VE Node
  community.proxmox.node:
    api_host: proxmoxhost
    api_user: root@pam
    api_password: password123
    node_name: de-cgn01-virt01
    subscription:
        state: present
        key: ABCD-EFGH-IJKL-MNOP-QRST-UVWX-YZ0123456789
"""

RETURN = r"""
certificates:
  description: Status message about the certificate on the node.
  returned: success
  type: str
  sample: "Certificate for node 'dev-virt01' is already present."
changed:
  description: Indicates whether any changes were made.
  returned: success
  type: bool
  sample: true
dns:
  description: Status message about the DNS configuration on the node.
  returned: success
  type: str
  sample: "DNS configuration for node 'dev-virt01' has been updated."
power_state:
  description: Status message about the power state of the node.
  returned: success
  type: str
  sample: "Node 'dev-virt01' is already online."
"""


import hashlib
import re
import ssl

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
)


def module_args():
    return dict(
        node_name=dict(type="str", required=True),
        power_state=dict(choices=["online", "offline"]),
        certificates=dict(
            type="dict",
            options=dict(
                cert=dict(type="str", required=False, no_log=True),
                key=dict(type="str", required=False, no_log=True),
                state=dict(type="str", required=False, choices=["present", "absent"]),
                restart=dict(type="bool", default=False, required=False),
                force=dict(type="bool", default=False, required=False),
            ),
        ),
        dns=dict(
            type="dict",
            options=dict(
                dns1=dict(type="str", default=None, required=False),
                dns2=dict(type="str", default=None, required=False),
                dns3=dict(type="str", default=None, required=False),
                search=dict(type="str", required=True),
            ),
        ),
        subscription=dict(
            type="dict",
            options=dict(
                state=dict(type="str", required=False, choices=["present", "absent"]),
                key=dict(type="str", default=None, required=False, no_log=True),
            ),
        ),
    )


def module_options():
    return {}


class ProxmoxNodeAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def get_nodes(self):
        nodes = {"nodes": {}}
        for node in self.proxmox_api.nodes.get():
            nodes["nodes"][node["node"]] = {}
            nodes["nodes"][node["node"]]["name"] = node["node"]
            nodes["nodes"][node["node"]]["status"] = node["status"]
        return nodes

    def validate_node_name(self, nodes):
        node = self.params.get("node_name")
        if node not in nodes["nodes"]:
            self.module.fail_json(msg=f"Node '{node}' not found in the Proxmox cluster.")

    def read_file(self, file_path):
        try:
            with open(file_path, "r") as file_handler:
                file_content = file_handler.read()
                return file_content
        except Exception as e:
            self.module.fail_json(msg=f"Failed to read certificate or key file '{file_path}': {e}")

    def get_certificate_fingerprints_file(self, pem_data, hash_alg="sha256"):
        certs = re.findall(r"-----BEGIN CERTIFICATE-----(.*?)-----END CERTIFICATE-----", pem_data, re.DOTALL)

        fingerprints = []
        for cert_body in certs:
            full_pem = f"-----BEGIN CERTIFICATE-----{cert_body}-----END CERTIFICATE-----"
            der = ssl.PEM_cert_to_DER_cert(full_pem)
            digest = getattr(hashlib, hash_alg)(der).hexdigest()
            # Format the fingerprint as uppercase hex pairs separated by colons to match Proxmox's output
            # e.g., "A1:B2:C3:D4:E5:F6:G7:H8:I9:J0:K1:L2:M3:N4:O5:P6:Q7:R8:S9:T0"
            formatted = ":".join(digest[i : i + 2].upper() for i in range(0, len(digest), 2))
            fingerprints.append(formatted)
        return fingerprints

    def get_certificate_fingerprints_api(self, certificates):
        fingerprints = []
        for cert in certificates:
            fingerprints.append(cert.get("fingerprint"))
        return fingerprints

    def dicts_differ(self, d1, d2):
        keys = set(d1) | set(d2)
        return any(d1.get(k) != d2.get(k) for k in keys)

    def power_state(self, nodes):
        state = self.params.get("power_state")
        node = self.params.get("node_name")
        changed = False
        result = "Unchanged"

        if state == "online":
            if nodes["nodes"][node]["status"] == "online":
                changed = False
                result = f"Node '{node}' is already online."
            else:
                if not self.module.check_mode:
                    self.proxmox_api.nodes(node).wakeonlan.post(node_name=node)
                changed = True
                result = f"Node '{node}' has been powered on."

        if state == "offline":
            if nodes["nodes"][node]["status"] != "online":
                changed = False
                result = f"Node '{node}' is already offline."
            else:
                if not self.module.check_mode:
                    self.proxmox_api.nodes(node).status.post(command="shutdown")
                changed = True
                result = f"Node '{node}' has been powered off."

        return changed, result

    def _get_custom_certificates(self, node):
        try:
            certs = self.proxmox_api.nodes(node).certificates.info.get()
            # Filter out default Proxmox certificates
            custom_certs = [cert for cert in certs if cert.get("filename") not in ["pve-root-ca.pem", "pve-ssl.pem"]]
            return custom_certs
        except Exception as e:
            self.module.fail_json(msg=f"Failed to get certificates information: {str(e)}")

    def _certificate_absent(self, node, restart):
        existing_certificates = self._get_custom_certificates(node)

        if existing_certificates:
            if self.module.check_mode:
                return True, f"Certificate on node '{node}' would be deleted."
            try:
                self.proxmox_api.nodes(node).certificates.custom.delete(restart=ansible_to_proxmox_bool(restart))
                return True, f"Certificate on node '{node}' deleted."
            except Exception as e:
                self.module.fail_json(changed=False, msg=f"Failed to delete certificate on node '{node}': {str(e)}")
        else:
            return False, f"Certificate on node '{node}' already absent."

    def _certificate_present(self, node, restart, force):  # noqa:PLR0912
        # Certificate: cert (file path) OR certificate (raw string) - at least one required for present
        # Private key: key (file path) OR private_key (raw string) - both optional

        certificate_params = self.params["certificates"]
        certificate_file_path = certificate_params.get("cert")
        certificate_raw = certificate_params.get("certificate")
        private_key_file_path = certificate_params.get("key")
        private_key_raw = certificate_params.get("private_key")

        if certificate_file_path and certificate_raw:
            self.module.fail_json(msg="Cannot specify both cert (file path) and certificate (raw string).")
        if private_key_file_path and private_key_raw:
            self.module.fail_json(msg="Cannot specify both key (file path) and private_key (raw string).")

        if not certificate_file_path and not certificate_raw:
            self.module.fail_json(
                msg="Either cert (file path) or certificate (raw string) is required for state=present."
            )

        if certificate_file_path:
            cert_content = self.read_file(certificate_file_path)
        else:
            cert_content = certificate_raw

        key_content = None
        if private_key_file_path:
            key_content = self.read_file(private_key_file_path)
        elif private_key_raw:
            key_content = private_key_raw

        our_fingerprints = self.get_certificate_fingerprints_file(cert_content)
        if not our_fingerprints:
            self.module.fail_json(msg="Failed to parse certificate: no valid PEM certificate found.")
        our_fingerprint = our_fingerprints[0]

        existing_certificates = self._get_custom_certificates(node)
        existing_fingerprints = self.get_certificate_fingerprints_api(existing_certificates)

        certificate_already_present = our_fingerprint in existing_fingerprints

        if certificate_already_present and not force:
            return False, f"Certificate for node '{node}' is already present."

        if self.module.check_mode:
            if certificate_already_present and force:
                return True, f"Certificate for node '{node}' would be overwritten."
            return True, f"Certificate for node '{node}' would be updated."

        post_params = {
            "certificates": cert_content,
            "force": ansible_to_proxmox_bool(force),
            "restart": ansible_to_proxmox_bool(restart),
        }
        if key_content:
            post_params["key"] = key_content

        try:
            self.proxmox_api.nodes(node).certificates.custom.post(**post_params)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to upload certificate on node '{node}': {str(e)}")

        if certificate_already_present and force:
            return True, f"Certificate for node '{node}' has been overwritten."
        return True, f"Certificate for node '{node}' has been updated."

    def _restart_pve_proxy_service(self, node):
        if self.module.check_mode:
            return True, "The service pveproxy would be restarted."

        try:
            self.proxmox_api.nodes(node).service("pveproxy").restart.pos()
            return True, "The service pveproxy has been restarted."
        except Exception as e:
            self.module.warn(f"Failed to restart the service pveproxy: {str(e)}")

    def certificates(self):
        state = self.params["certificates"].get("state")
        node = self.params["node_name"]
        restart = self.params["certificates"]["restart"]
        force = self.params["certificates"].get("force")

        if force and state is None:
            self.module.fail_json(msg="Force is only supported when state is present or absent.")
            return False, "Unchanged"

        if state == "absent":
            changed, msg = self._certificate_absent(node, restart)
        elif state == "present":
            changed, msg = self._certificate_present(node, restart, force)
        elif state is None and restart:
            changed, msg = self._restart_pve_proxy_service(node)
        elif state is None and force:
            self.module.fail_json(msg="Force is only supported when state is present or absent.")
            return False, "Unchanged"
        else:
            return False, "Unchanged"

        if not changed:
            return False, msg

        return True, msg

    def dns(self):
        node_name = self.params.get("node_name")
        dns1 = self.params.get("dns", {}).get("dns1", None)
        dns2 = self.params.get("dns", {}).get("dns2", None)
        dns3 = self.params.get("dns", {}).get("dns3", None)
        search = self.params.get("dns", {}).get("search", None)
        dns_config_current = self.proxmox_api.nodes(node_name).dns.get()
        changed = False
        result_dns = "Unchanged"

        dns_config = {}
        if dns1:
            dns_config["dns1"] = dns1
        if dns2:
            dns_config["dns2"] = dns2
        if dns3:
            dns_config["dns3"] = dns3
        if search:
            dns_config["search"] = search

        if self.dicts_differ(dns_config_current, dns_config):
            if not self.module.check_mode:
                self.proxmox_api.nodes(node_name).dns.put(**dns_config)
            changed = True
            result_dns = f"DNS configuration for node '{node_name}' has been updated."

        return changed, result_dns

    def subscription(self):
        subscription_state = self.params.get("subscription", {}).get("state")
        node_name = self.params.get("node_name")
        subscription_current = self.proxmox_api.nodes(node_name).subscription.get()
        changed = False
        result_subscription = "Unchanged"

        if subscription_state == "present":
            license_key = self.params.get("subscription", {}).get("key", None)
            if subscription_current.get("key", None) != license_key:
                if not self.module.check_mode:
                    try:
                        self.proxmox_api.nodes(node_name).subscription.put(key=license_key)
                    except Exception as e:
                        self.module.fail_json(msg=f"Failed to upload subscription key: {e}")
                changed = True
                result_subscription = f"License subscription for node '{node_name}' has been uploaded."

        if subscription_state == "absent":
            if subscription_current.get("status", None) != "notfound":
                if not self.module.check_mode:
                    try:
                        self.proxmox_api.nodes(node_name).subscription.delete()
                    except Exception as e:
                        self.module.fail_json(msg=f"Failed to delete subscription key: {e}")
                changed = True
                result_subscription = f"License subscription for node '{node_name}' has been deleted."

        return changed, result_subscription


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxNodeAnsible(module)

    # Initialize objects and avoid re-polling the current
    # nodes in the cluster in each function call.
    nodes = proxmox.get_nodes()
    proxmox.validate_node_name(nodes)
    result = {"changed": False}

    # Actions
    if module.params.get("power_state") is not None:
        changed, power_result = proxmox.power_state(nodes)
        result["changed"] = result["changed"] or changed
        result["power_state"] = power_result

    if module.params.get("certificates") is not None:
        changed, certificates_result = proxmox.certificates()
        result["changed"] = result["changed"] or changed
        result["certificates"] = certificates_result

    if module.params.get("dns") is not None:
        changed, dns_result = proxmox.dns()
        result["changed"] = result["changed"] or changed
        result["dns"] = dns_result

    if module.params.get("subscription") is not None:
        changed, subscription_result = proxmox.subscription()
        result["changed"] = result["changed"] or changed
        result["subscription"] = subscription_result

    module.exit_json(**result)


if __name__ == "__main__":
    main()
