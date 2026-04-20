#!/usr/bin/python

# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_acme_certificate
short_description: Manages ACME SSL certificates for Proxmox VE nodes
version_added: 2.0.0
author: Clément Cruau (@PendaGTP)
description:
  - Order, renew or remove ACME certificates from a Certificate Authority
    for a specific Proxmox VE node.
  - Before using this module, ensure that an ACME account is configured
    (using M(community.proxmox.proxmox_acme_account)) and DNS plugins are
    configured if using DNS-01 challenge
    (using M(community.proxmox.proxmox_acme_plugin_dns)).
  - Requires C(root@pam) authentication.
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  state:
    description:
      - Desired state of the ACME certificate on the node.
    type: str
    choices:
      - present
      - absent
    default: present
  node_name:
    description:
      - The name of the Proxmox VE node for which to order/manage the ACME certificate.
    type: str
    required: true
  account:
    description:
      - The ACME account name to use for ordering the certificate.
    type: str
  domains:
    description:
      - The list of domains to include in the certificate.
      - At least one domain is required when O(state=present).
    type: list
    elements: dict
    suboptions:
      domain:
        description:
          - The domain name to include in the certificate.
        type: str
        required: true
      plugin:
        description:
          - The DNS plugin to use for DNS-01 challenge validation.
          - If not specified, the standalone HTTP-01 challenge will be used.
        type: str
      alias:
        description:
          - An optional alias domain for DNS validation.
        type: str
  force:
    description:
      - Force certificate renewal even if the certificate is not due for renewal yet.
      - Setting this to V(true) will trigger a new certificate order.
    type: bool
    default: false

seealso:
  - name: Certificate management (Proxmox documentation)
    description: ACME accounts and certificates in Proxmox VE
    link: https://pve.proxmox.com/pve-docs/pve-admin-guide.html#sysadmin_certificate_management
  - module: community.proxmox.proxmox_acme_certificates_info
  - module: community.proxmox.proxmox_acme_account

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Order ACME certificate with HTTP-01 challenge (standalone)
  community.proxmox.proxmox_acme_certificate:
    node_name: pve-node-01
    account: production
    domains:
      - domain: pve.example.com

- name: Order ACME certificate with DNS-01 challenge using Cloudflare
  community.proxmox.proxmox_acme_certificate:
    node_name: pve-node-01
    account: production
    domains:
      - domain: pve.example.com
        plugin: cloudflare

- name: Multiple domains with mixed challenge types
  community.proxmox.proxmox_acme_certificate:
    node_name: pve-node-01
    account: production
    domains:
      - domain: pve.example.com
        plugin: cloudflare
      - domain: pve2.example.com

- name: Force certificate renewal
  community.proxmox.proxmox_acme_certificate:
    node_name: pve-node-01
    account: production
    force: true
    domains:
      - domain: pve.example.com
        plugin: cloudflare

- name: Remove ACME certificate and configuration
  community.proxmox.proxmox_acme_certificate:
    node_name: pve-node-01
    state: absent
"""

RETURN = r"""
node_name:
  description: The Proxmox VE node name.
  returned: on success
  type: str
account:
  description: The ACME account name used for the certificate.
  returned: when O(state=present)
  type: str
domains:
  description: The list of domains included in the certificate.
  returned: when O(state=present)
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
certificate:
  description: The PEM-encoded certificate data.
  returned: when O(state=present) and a certificate exists
  type: str
fingerprint:
  description: The certificate fingerprint.
  returned: when O(state=present) and a certificate exists
  type: str
issuer:
  description: The certificate issuer.
  returned: when O(state=present) and a certificate exists
  type: str
subject:
  description: The certificate subject.
  returned: when O(state=present) and a certificate exists
  type: str
not_after:
  description: The certificate expiration timestamp.
  returned: when O(state=present) and a certificate exists
  type: str
not_before:
  description: The certificate start timestamp.
  returned: when O(state=present) and a certificate exists
  type: str
subject_alternative_names:
  description: The certificate subject alternative names (SANs).
  returned: when O(state=present) and a certificate exists
  type: list
  elements: str
msg:
  description: Short description of the action taken.
  returned: always
  type: str
"""

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    ansible_to_proxmox_bool,
    create_proxmox_module,
)
from ansible_collections.community.proxmox.plugins.module_utils.proxmox_acme_certificate import (
    cert_info_to_ansible_result,
    parse_acme_config,
)

CERTIFICATE_TASK_TIMEOUT = 120
ACME_DOMAIN_SLOTS = 6  # acmedomain0 .. acmedomain5


def build_acme_property_string(account):
    """Build the ``acme`` node config property string.

    Example output: ``"account=production"``
    """
    return f"account={account}"


def build_acmedomain_property_string(domain, plugin=None, alias=None):
    """Build an ``acmedomainN`` node config property string.

    Example output: ``"domain=pve.example.com,plugin=cloudflare,alias=alt.example.com"``
    """
    parts = [f"domain={domain}"]
    if plugin:
        parts.append(f"plugin={plugin}")
    if alias:
        parts.append(f"alias={alias}")
    return ",".join(parts)


def find_acme_certificate(certificates):
    """Find the ACME/custom certificate from the node's certificate list.

    The Proxmox API returns a ``filename`` field for each certificate.
    ACME and custom certificates are stored as ``pveproxy-ssl.pem``,
    while the self-signed cert is ``pve-ssl.pem``.

    Returns the matching certificate dict, or None.
    """
    if not certificates:
        return None

    for cert in certificates:
        filename = cert.get("filename") or ""
        if filename == "pveproxy-ssl.pem":
            return cert

    return None


def normalize_domain_list(domains):
    """Normalize a list of domain dicts for comparison.

    Sorts by domain name and normalises None/empty plugin/alias to None.
    """
    normalized = []
    for d in domains:
        normalized.append(
            {
                "domain": d["domain"].strip().lower(),
                "plugin": d["plugin"].strip() if d.get("plugin") else None,
                "alias": d["alias"].strip() if d.get("alias") else None,
            }
        )
    return sorted(normalized, key=lambda x: x["domain"])


def module_args():
    return dict(
        state=dict(choices=["present", "absent"], default="present"),
        node_name=dict(type="str", required=True),
        account=dict(type="str"),
        domains=dict(
            type="list",
            elements="dict",
            options=dict(
                domain=dict(type="str", required=True),
                plugin=dict(type="str"),
                alias=dict(type="str"),
            ),
        ),
        force=dict(type="bool", default=False),
    )


def module_options():
    return dict(
        required_if=[("state", "present", ["account", "domains"])],
    )


class ProxmoxAcmeCertificateAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def run(self):
        state = self.params["state"]
        node_name = self.params["node_name"]

        if state == "present":
            self._ensure_present(node_name)
        else:
            self._ensure_absent(node_name)

    def validate_params(self):
        domains = self.params.get("domains")
        if domains and len(domains) > ACME_DOMAIN_SLOTS:
            self.module.fail_json(
                msg=f"Proxmox supports a maximum of {ACME_DOMAIN_SLOTS} ACME domains, got {len(domains)}",
            )

    def _ensure_present(self, node_name):
        current_config = self._read_node_acme_config(node_name)
        desired_config = self._build_desired_config()
        force = self.params["force"]

        cert = self._read_certificate_info(node_name)

        config_changed = self._is_config_changed(current_config, desired_config)
        needs_order = config_changed or force or current_config["account"] is None or cert is None

        if not needs_order:
            result = cert_info_to_ansible_result(cert)
            self.module.exit_json(
                changed=False,
                node_name=node_name,
                account=self.params["account"],
                domains=self.params["domains"],
                msg=f"ACME certificate for node {node_name} is already up to date",
                **result,
            )

        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                node_name=node_name,
                account=self.params["account"],
                domains=self.params["domains"],
                msg=f"ACME certificate for node {node_name} would be ordered",
            )

        self._configure_node_acme(node_name, desired_config)
        self._order_certificate(node_name)

        cert = self._read_certificate_info(node_name)
        result = cert_info_to_ansible_result(cert) if cert else {}

        self.module.exit_json(
            changed=True,
            node_name=node_name,
            account=self.params["account"],
            domains=self.params["domains"],
            msg=f"ACME certificate for node {node_name} successfully ordered",
            **result,
        )

    def _ensure_absent(self, node_name):
        current_config = self._read_node_acme_config(node_name)

        if current_config["account"] is None and not current_config["domains"]:
            self.module.exit_json(changed=False, node_name=node_name, msg=f"No ACME configuration on node {node_name}")

        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                node_name=node_name,
                msg=f"ACME certificate and configuration for node {node_name} would be removed",
            )

        self._delete_certificate(node_name)
        self._cleanup_node_acme_config(node_name)

        self.module.exit_json(
            changed=True,
            node_name=node_name,
            msg=f"ACME certificate and configuration for node {node_name} successfully removed",
        )

    def _read_node_acme_config(self, node_name):
        try:
            config = self.proxmox_api.nodes(node_name).config.get()
        except Exception as e:
            self.module.fail_json(msg=f"Failed to read node config for {node_name}: {to_native(e)}")
        return parse_acme_config(config)

    def _configure_node_acme(self, node_name, desired_config):
        account = desired_config["account"]
        domains = desired_config["domains"]

        params = {"acme": build_acme_property_string(account)}

        for i, domain in enumerate(domains):
            key = f"acmedomain{i}"
            params[key] = build_acmedomain_property_string(
                domain["domain"],
                plugin=domain.get("plugin"),
                alias=domain.get("alias"),
            )

        unused_slots = [f"acmedomain{i}" for i in range(len(domains), ACME_DOMAIN_SLOTS)]
        if unused_slots:
            params["delete"] = ",".join(unused_slots)

        try:
            self.proxmox_api.nodes(node_name).config.put(**params)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to configure ACME settings on node {node_name}: {to_native(e)}")

    def _cleanup_node_acme_config(self, node_name):
        slots = [f"acmedomain{i}" for i in range(ACME_DOMAIN_SLOTS)]
        delete_keys = ",".join(["acme"] + slots)

        try:
            self.proxmox_api.nodes(node_name).config.put(delete=delete_keys)
        except Exception as e:
            self.module.warn(f"Failed to clean up ACME configuration on node {node_name}: {to_native(e)}.")

    def _order_certificate(self, node_name):
        force = self.params["force"]

        try:
            taskid = self.proxmox_api.nodes(node_name).certificates.acme.certificate.post(
                force=ansible_to_proxmox_bool(force),
            )
        except Exception as e:
            err = to_native(e)
            if "'force' is not set" in err or "Custom certificate exists" in err:
                self.module.fail_json(
                    msg=(
                        f"A custom certificate already exists on node {node_name}. "
                        "Set force=true to replace it with an ACME certificate."
                    )
                )
            self.module.fail_json(msg=f"Failed to order ACME certificate for node {node_name}: {err}")

        if taskid:
            self._wait_certificate_task(node_name, taskid)

    def _delete_certificate(self, node_name):
        try:
            taskid = self.proxmox_api.nodes(node_name).certificates.acme.certificate.delete()
        except Exception as e:
            self.module.warn(f"Failed to delete ACME certificate on node {node_name}: {to_native(e)}")
            return

        if taskid and "acmerevoke" in to_native(taskid):
            self._wait_revocation_task(node_name, taskid)

    def _read_certificate_info(self, node_name):
        try:
            certs = self.proxmox_api.nodes(node_name).certificates.info.get()
        except Exception as e:
            self.module.fail_json(msg=f"Failed to read certificates info for node {node_name}: {to_native(e)}")
        return find_acme_certificate(certs)

    def _wait_certificate_task(self, node_name, taskid):
        node = self.upid_to_node(taskid)
        ok, err = self.api_task_complete(node, taskid, CERTIFICATE_TASK_TIMEOUT)

        if not ok:
            self.module.fail_json(
                msg=f"ACME certificate task failed: {err}",
                task=taskid,
            )

    def _wait_revocation_task(self, node_name, taskid):
        node = self.upid_to_node(taskid)
        ok, err = self.api_task_complete(node, taskid, CERTIFICATE_TASK_TIMEOUT)

        if not ok:
            self.module.fail_json(
                msg=f"ACME certificate revocation failed on node {node_name}: {err}",
                task=taskid,
            )

    def _build_desired_config(self):
        return {
            "account": self.params["account"],
            "domains": self.params["domains"] or [],
        }

    def _is_config_changed(self, current, desired):
        if (current["account"] or "") != (desired["account"] or ""):
            return True

        current_domains = normalize_domain_list(current["domains"])
        desired_domains = normalize_domain_list(desired["domains"])

        return current_domains != desired_domains


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxAcmeCertificateAnsible(module)
    proxmox.validate_params()

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f"An error occurred: {to_native(e)}")


if __name__ == "__main__":
    main()
