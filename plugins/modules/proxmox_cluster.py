#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Florian Paul Azim Hoberg (@gyptazy) <florian.hoberg@credativ.de>
#
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
module: proxmox_cluster
version_added: 0.1.0
short_description: Management of Proxmox Nodes for creating a Proxmox VE cluster
description:
  - Allows you to create/join a Proxmox VE cluster from an empty Proxmox VE node.
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
  link0:
    description:
      - The first IP address to use for cluster communication.
    type: str
    required: false
  link1:
    description:
      - The second IP address to use for cluster communication.
    type: str
    required: false
  master_ip:
    description:
      - The IP address of the cluster master when joining the cluster.
    type: str
    required: false
  fingerprint:
    description:
      - The fingerprint of the cluster master when joining the cluster.
    type: str
    required: false
  cluster_name:
    description:
      - The cluster name to use for cluster creation.
    type: str
    required: false
  action:
    description:
      - Possible module actions to perform by the Proxmox VE API.
    choices: ['create_cluster', 'join_cluster', "get_cluster_info"]
    type: str
    required: true
notes:
  - Requires Proxmox VE to be installed on the target node(s).
requirements:
  - python3-proxmoxer
"""

EXAMPLES = r"""
- name: Create a Proxmox VE Cluster
  community.general.proxmox_cluster:
    action: create_cluster
    api_host: "{{ primary_node }}"
    api_user: root@pam
    api_password: password123
    api_ssl_verify: false
    link0: 10.10.1.1
    link1: 10.10.2.1
    cluster_name: "devcluster"

- name: Get join information of the Proxmox VE Cluster
  community.general.proxmox_cluster:
    action: get_cluster_info
    api_host: "{{ primary_node }}"
    api_user: root@pam
    api_password: password123
  register: cluster_info

- name: Join a Proxmox VE Cluster
  community.general.proxmox_cluster:
    action: join_cluster
    api_host: "{{ secondary_node }}"
    api_user: root@pam
    api_password: password123
    master_ip: "{{ primary_node }}"
    fingerprint: "{{ cluster_fingerprint }}"
    cluster_name: "devcluster"
"""

RETURN = r"""
cluster:
  description: The name of the cluster that was created or joined.
  returned: success
  type: str
  sample: "devcluster"
msg:
  description: A short message.
  returned: always
  type: str
  sample: "Cluster devcluster created."
cluster_join_info:
  description: >
    Detailed cluster join information. Only returned when action is 'get_cluster_info'.
  returned: when action == 'get_cluster_info'
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


def create_cluster(proxmox, module):
    cluster_name = module.params.get("cluster_name") or module.params.get("api_host")
    payload = {"clustername": cluster_name}

    if module.params.get("link0") is not None:
        payload["link0"] = module.params.get("link0")
    if module.params.get("link1") is not None:
        payload["link1"] = module.params.get("link1")

    if module.check_mode:
        module.exit_json(changed=True, msg="Cluster '{}' would be created (check mode).".format(cluster_name), cluster=cluster_name)

    try:
        proxmox.cluster.config.post(**payload)
    except Exception as e:
        module.fail_json(msg="Error while creating cluster: {}".format(str(e)))

    module.exit_json(changed=True, msg="Cluster '{}' created.".format(cluster_name), cluster=cluster_name)


def get_cluster_info(proxmox, module):
    try:
        data = proxmox.cluster.config.join.get()
    except Exception as e:
        module.fail_json(msg="Error while obtaining cluster join information: {}".format(str(e)))

    module.exit_json(changed=False, ansible_facts={"cluster_join_info": data})


def join_cluster(proxmox, module):
    master_ip = module.params.get("master_ip")
    fingerprint = module.params.get("fingerprint")
    api_password = module.params.get("api_password")
    cluster_name = module.params.get("cluster_name")

    if master_ip is None or fingerprint is None:
        module.fail_json(msg="Action 'join_cluster' requires 'master_ip' and 'fingerprint' arguments.")

    if module.check_mode:
        module.exit_json(changed=True, msg="Node would join the cluster (check mode).", cluster=cluster_name)

    try:
        proxmox.cluster.config.join.post(
            hostname=master_ip,
            fingerprint=fingerprint,
            password=api_password
        )

    except Exception as e:
        module.fail_json(msg="Error while joining the cluster: {}".format(str(e)))

    module.exit_json(changed=True, msg="Node joined the cluster.", cluster=cluster_name)


def main():
    module_args = dict(
        action=dict(type='str', required=True, choices=["create_cluster", "get_cluster_info", "join_cluster"]),
        api_host=dict(type='str', required=True),
        api_user=dict(type='str', required=True),
        api_password=dict(type='str', required=True, no_log=True),
        api_ssl_verify=dict(type='bool', required=False, default=True),
        cluster_name=dict(type='str', required=False, default=None),
        link0=dict(type='str', required=False, default=None),
        link1=dict(type='str', required=False, default=None),
        master_ip=dict(type='str', required=False),
        fingerprint=dict(type='str', required=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if not PROXMOXER_LIBRARY:
        module.fail_json(msg=missing_required_lib('proxmoxer'), exception=PROXMOXER_LIBRARY_IMPORT_ERROR)

    action = module.params.get("action")
    api_host = module.params.get("api_host")
    api_user = module.params.get("api_user")
    api_password = module.params.get("api_password")
    api_ssl_verify = module.params.get("api_ssl_verify")

    try:
        proxmox = ProxmoxAPI(api_host, user=api_user, password=api_password, verify_ssl=api_ssl_verify)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Proxmox API: {}".format(str(e)))

    if action == "create_cluster":
        create_cluster(proxmox, module)
    elif action == "get_cluster_info":
        get_cluster_info(proxmox, module)
    elif action == "join_cluster":
        join_cluster(proxmox, module)


if __name__ == '__main__':
    main()
