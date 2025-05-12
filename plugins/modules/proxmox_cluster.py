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
  state:
    description:
      - Possible module state to perform the required steps within the Proxmox VE API.
    choices: ["present"]
    type: str
    required: true
notes:
  - Requires Proxmox VE to be installed on the target node(s).
requirements:
  - python3-proxmoxer
"""

EXAMPLES = r"""
- name: Create a Proxmox VE Cluster
  community.proxmox.proxmox_cluster:
    state: present
    api_host: "{{ primary_node }}"
    api_user: root@pam
    api_password: password123
    api_ssl_verify: false
    link0: 10.10.1.1
    link1: 10.10.2.1
    cluster_name: "devcluster"

- name: Join a Proxmox VE Cluster
  community.proxmox.proxmox_cluster:
    state: present
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
"""

import socket
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
        cluster_objects = proxmox.cluster.config.nodes.get()
        if len(cluster_objects) > 0:
            module.fail_json(msg="Error while creating cluster: Node is already part of a cluster!")
        else:
            module.exit_json(changed=True, msg="Cluster '{}' would be created (check mode).".format(cluster_name), cluster=cluster_name)

    try:
        proxmox.cluster.config.post(**payload)
    except Exception as e:
        module.fail_json(msg="Error while creating cluster: {}".format(str(e)))

    module.exit_json(changed=True, msg="Cluster '{}' created.".format(cluster_name), cluster=cluster_name)


def join_cluster(proxmox, module):
    master_ip = module.params.get("master_ip")
    fingerprint = module.params.get("fingerprint")
    api_password = module.params.get("api_password")
    cluster_name = module.params.get("cluster_name")

    if module.check_mode:
        node_name = socket.gethostname()
        cluster_objects = proxmox.cluster.status.get()
        is_in_cluster = any(entry['type'] == 'node' and entry['name'] == node_name for entry in cluster_objects)

        if is_in_cluster:
            module.fail_json(msg="Error while joining cluster: Node is already part of a cluster!")
        else:
            module.exit_json(changed=True, msg="Node would join the cluster '{}' (check mode).".format(cluster_name), cluster=cluster_name)

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
        state=dict(type='str', required=True, choices=["present"]),
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

    state = module.params.get("state")
    api_host = module.params.get("api_host")
    api_user = module.params.get("api_user")
    api_password = module.params.get("api_password")
    api_ssl_verify = module.params.get("api_ssl_verify")
    master_ip = module.params.get("master_ip")
    fingerprint = module.params.get("fingerprint")

    try:
        proxmox = ProxmoxAPI(api_host, user=api_user, password=api_password, verify_ssl=api_ssl_verify)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Proxmox API: {}".format(str(e)))

    # The Proxmox VE API currently does not support leaving a cluster
    # or removing a node from a cluster. Therefore, we only support creating
    # and joining a cluster. (https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/config/nodes)
    if state == "present":
        if master_ip and fingerprint:
            join_cluster(proxmox, module)
        else:
            create_cluster(proxmox, module)


if __name__ == '__main__':
    main()
