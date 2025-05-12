#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Florian Paul Azim Hoberg (@gyptazy) <florian.hoberg@credativ.de>
#
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
module: proxmox_cluster_info
version_added: 0.1.0
short_description: Retrieve information about Proxmox Nodes in Proxmox VE clusters
description:
  - Retrieve information about Proxmox Nodes in Proxmox VE clusters.
author: Florian Paul Azim Hoberg (@gyptazy) <florian.hoberg@credativ.de>
options:
  api_host:
    description:
      - The hostname of the Proxmox VE node to perform actions.
    type: str
    required: true
  api_user:
    description:
      - The username to use to login to the Proxmox VE API.
    type: str
    required: true
  api_password:
    description:
      - The password to use to login to the Proxmox VE API.
    type: str
    required: true
  api_ssl_verify:
    description:
      - Whether to verify the SSL certificate of the Proxmox VE API.
    type: bool
    required: false
    default: true
notes:
  - Requires Proxmox VE to be installed on the target node(s).
requirements:
  - python3-proxmoxer
"""

EXAMPLES = r"""
- name: Get join information of the Proxmox VE Cluster
  community.proxmox.proxmox_cluster:
    api_host: "{{ primary_node }}"
    api_user: root@pam
    api_password: password123
  register: cluster_info
"""

RETURN = r"""
cluster_join_info:
  description: >
    Detailed cluster join information. Only returned when action is 'get_cluster_info'.
  returned: success
  type: dict
  contains:
    config_digest:
      description: Digest of the cluster configuration.
      type: str
      sample: "aef68412f7976505ed083e6173b96274a281da25"
    nodelist:
      description: List of nodes in the cluster.
      type: list
      elements: dict
      contains:
        name:
          description: Node name.
          type: str
          sample: "pve2"
        nodeid:
          description: Node ID.
          type: str
          sample: "1"
        pve_addr:
          description: Proxmox VE address.
          type: str
          sample: "10.10.10.159"
        pve_fp:
          description: Proxmox VE fingerprint.
          type: str
          sample: "08:B5:B2:F9:EC:01:0B:D0:..."
        quorum_votes:
          description: Quorum votes assigned to the node.
          type: str
          sample: "1"
        ring0_addr:
          description: Address for ring0.
          type: str
          sample: "vmbr0"
    preferred_node:
      description: The preferred cluster node.
      type: str
      sample: "pve2"
    totem:
      description: Totem protocol configuration.
      type: dict
      contains:
        cluster_name:
          description: Cluster name from totem.
          type: str
          sample: "devcluster"
        config_version:
          description: Config version.
          type: str
          sample: "1"
        interface:
          description: Interface configuration.
          type: dict
        ip_version:
          description: IP version.
          type: str
          sample: "ipv4-6"
        link_mode:
          description: Link mode.
          type: str
          sample: "passive"
        secauth:
          description: Whether secure authentication is on.
          type: str
          sample: "on"
        version:
          description: Totem protocol version.
          type: str
          sample: "2"
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import missing_required_lib

try:
    from proxmoxer import ProxmoxAPI
except ImportError:
    PROXMOXER_LIBRARY = False
    PROXMOXER_LIBRARY_IMPORT_ERROR = traceback.format_exc()
else:
    PROXMOXER_LIBRARY = True
    PROXMOXER_LIBRARY_IMPORT_ERROR = None


def get_cluster_info(proxmox, module):
    try:
        data = proxmox.cluster.config.join.get()
    except Exception as e:
        module.fail_json(msg="Error while obtaining cluster join information: {}".format(str(e)))

    module.exit_json(changed=False, ansible_facts={"cluster_join_info": data})


def main():
    module_args = dict(
        api_host=dict(type='str', required=True),
        api_user=dict(type='str', required=True),
        api_password=dict(type='str', required=True, no_log=True),
        api_ssl_verify=dict(type='bool', required=False, default=True),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if not PROXMOXER_LIBRARY:
        module.fail_json(msg=missing_required_lib('proxmoxer'), exception=PROXMOXER_LIBRARY_IMPORT_ERROR)

    api_host = module.params.get("api_host")
    api_user = module.params.get("api_user")
    api_password = module.params.get("api_password")
    api_ssl_verify = module.params.get("api_ssl_verify")

    try:
        proxmox = ProxmoxAPI(api_host, user=api_user, password=api_password, verify_ssl=api_ssl_verify)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Proxmox API: {}".format(str(e)))

    get_cluster_info(proxmox, module)


if __name__ == '__main__':
    main()
