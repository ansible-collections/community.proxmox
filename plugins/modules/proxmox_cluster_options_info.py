#!/usr/bin/python

# Copyright (c) 2026, FingerlessGloves
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_cluster_options_info
short_description: Retrieve datacenter-wide options for a Proxmox VE cluster
version_added: "2.1.0"
description:
  - Retrieve the datacenter-wide cluster options exposed by the Proxmox VE C(/cluster/options) API endpoint.
  - These are the settings found under B(Datacenter -> Options) in the Proxmox VE web interface.
author: FingerlessGloves (@FingerlessGlov3s)
seealso:
  - module: community.proxmox.proxmox_cluster_options
    description: Manage the datacenter-wide cluster options.
  - name: Proxmox VE datacenter configuration
    description: Reference for the Proxmox VE datacenter configuration file (datacenter.cfg).
    link: https://pve.proxmox.com/wiki/Manual:_datacenter.cfg
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module
"""

EXAMPLES = r"""
- name: Retrieve the datacenter-wide cluster options
  community.proxmox.proxmox_cluster_options_info:
  register: cluster_options

- name: Show the configured keyboard layout
  ansible.builtin.debug:
    msg: "Keyboard layout is {{ cluster_options.cluster_options.keyboard | default('not set') }}"
"""

RETURN = r"""
cluster_options:
  description:
    - The datacenter-wide cluster options that are currently set.
    - Only options that are set are returned, mirroring the sparse behaviour of the Proxmox VE API.
    - Options not managed by M(community.proxmox.proxmox_cluster_options), such as the read-only C(allowed-tags),
      are passed through unchanged.
  returned: always
  type: dict
  contains:
    keyboard:
      description: Default keyboard layout for the VNC console.
      returned: when set
      type: str
    language:
      description: Default language used in the web interface.
      returned: when set
      type: str
    console:
      description: Default console viewer.
      returned: when set
      type: str
    mac_prefix:
      description: Prefix used for automatically generated MAC addresses.
      returned: when set
      type: str
    max_workers:
      description: Maximum number of workers running in parallel per node during cluster-wide tasks.
      returned: when set
      type: int
    email_from:
      description: Sender address used for notification emails.
      returned: when set
      type: str
    http_proxy:
      description: HTTP proxy used for updates and subscription information.
      returned: when set
      type: str
    fencing:
      description: Fencing mode used for the high availability stack.
      returned: when set
      type: str
    description:
      description: Datacenter description or notes.
      returned: when set
      type: str
    migration:
      description: Cluster-wide migration settings.
      returned: when set
      type: dict
    replication:
      description: Cluster-wide storage replication settings.
      returned: when set
      type: dict
    bwlimit:
      description: Default bandwidth limits, in KiB/s, for cluster-wide operations.
      returned: when set
      type: dict
    ha:
      description: Cluster-wide high availability settings.
      returned: when set
      type: dict
    crs:
      description: Cluster resource scheduling settings.
      returned: when set
      type: dict
    next_id:
      description: Bounds for the next free VMID range offered by the web interface.
      returned: when set
      type: dict
    consent_text:
      description: Consent text shown to the user before login.
      returned: when set
      type: str
    location:
      description: Geographic location of the datacenter.
      returned: when set
      type: dict
    u2f:
      description: U2F two-factor authentication settings.
      returned: when set
      type: dict
    webauthn:
      description: WebAuthn two-factor authentication settings.
      returned: when set
      type: dict
    notify:
      description: Cluster-wide notification settings.
      returned: when set
      type: dict
    tag_style:
      description: Tag style overrides for the web interface.
      returned: when set
      type: dict
    user_tag_access:
      description: Policy controlling which tags non-privileged users may set.
      returned: when set
      type: dict
    registered_tags:
      description: Tags that require C(Sys.Modify) on C(/) to set or remove.
      returned: when set
      type: list
      elements: str
  sample:
    keyboard: en-gb
    mac_prefix: "BC:24:11"
    description: "Production datacenter"
"""

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
)
from ansible_collections.community.proxmox.plugins.module_utils.proxmox_cluster_options import (
    cluster_options_to_ansible_result,
)


def module_args():
    return dict()


def module_options():
    return {}


class ProxmoxClusterOptionsInfoAnsible(ProxmoxAnsible):
    def get_cluster_options(self):
        try:
            raw = self.proxmox_api.cluster().options.get()
        except Exception as e:
            self.module.fail_json(msg=f"Failed to retrieve cluster options: {to_native(e)}")
        return cluster_options_to_ansible_result(raw)


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxClusterOptionsInfoAnsible(module)

    result = dict(changed=False)
    result["cluster_options"] = proxmox.get_cluster_options()

    module.exit_json(**result)


if __name__ == "__main__":
    main()
