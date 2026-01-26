#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Michael Dombek (@michaelwdombek) <michael_w_dombek@proton.me>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
module: proxmox_cluster_status_info
short_description: Retrieve Proxmox VE cluster status information
description:
  - Retrieve status information about the Proxmox VE cluster.
  - Returns information about both the cluster itself and the nodes within it.
author: Michael Dombek (@michaelwdombek)
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module
"""


EXAMPLES = r"""
- name: Get cluster status
  community.proxmox.proxmox_cluster_status_info:
    api_host: proxmox1
    api_user: root@pam
    api_password: "{{ password | default(omit) }}"
    api_token_id: "{{ token_id | default(omit) }}"
    api_token_secret: "{{ token_secret | default(omit) }}"
  register: cluster_status

- name: Display cluster quorum status
  ansible.builtin.debug:
    msg: "Cluster has quorum: {{ cluster_status.cluster_status | selectattr('type', 'equalto', 'cluster') | map(attribute='quorate') | first }}"
"""


RETURN = r"""
cluster_status:
  description: List containing cluster and node status information.
  returned: always, but can be empty
  type: list
  elements: dict
  contains:
    id:
      description: Unique identifier for the entry.
      returned: always
      type: str
    name:
      description: Name of the cluster or node.
      returned: always
      type: str
    type:
      description: Type of entry, either 'cluster' or 'node'.
      returned: always
      type: str
    ip:
      description: IP address of the resolved nodename.
      returned: when type is 'node'
      type: str
    level:
      description: Proxmox VE Subscription level, indicates if eligible for enterprise support.
      returned: when type is 'node'
      type: str
    local:
      description: Indicates if this is the responding node.
      returned: when type is 'node'
      type: bool
    nodeid:
      description: ID of the node from the corosync configuration.
      returned: when type is 'node'
      type: int
    nodes:
      description: Total count of nodes in the cluster, including offline nodes.
      returned: when type is 'cluster'
      type: int
    online:
      description: Indicates if the node is online or offline.
      returned: when type is 'node'
      type: bool
    quorate:
      description: Indicates if there is a majority of nodes online to make decisions.
      returned: when type is 'cluster'
      type: bool
    version:
      description: Current version of the corosync configuration file.
      returned: when type is 'cluster'
      type: int
"""


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    proxmox_auth_argument_spec,
    ProxmoxAnsible,
    proxmox_to_ansible_bool,
)


class ProxmoxClusterStatusEntry:
    def __init__(self, entry):
        self.entry = entry
        # Convert proxmox representation of boolean fields for easier
        # manipulation within ansible.
        if "quorate" in self.entry:
            self.entry["quorate"] = proxmox_to_ansible_bool(self.entry["quorate"])
        if "local" in self.entry:
            self.entry["local"] = proxmox_to_ansible_bool(self.entry["local"])
        if "online" in self.entry:
            self.entry["online"] = proxmox_to_ansible_bool(self.entry["online"])

    def to_dict(self):
        return self.entry


class ProxmoxClusterStatusInfoAnsible(ProxmoxAnsible):
    def get_cluster_status(self):
        try:
            status = self.proxmox_api.cluster.status.get()
            status = [ProxmoxClusterStatusEntry(entry).to_dict() for entry in status]
            return status
        except Exception as e:
            self.module.fail_json(msg="Failed to retrieve cluster status: %s" % str(e))


def proxmox_cluster_status_info_argument_spec():
    return dict()


def main():
    module_args = proxmox_auth_argument_spec()
    cluster_status_info_args = proxmox_cluster_status_info_argument_spec()
    module_args.update(cluster_status_info_args)

    module = AnsibleModule(
        argument_spec=module_args,
        required_one_of=[("api_password", "api_token_id")],
        required_together=[("api_token_id", "api_token_secret")],
        supports_check_mode=True,
    )
    result = dict(changed=False)

    proxmox = ProxmoxClusterStatusInfoAnsible(module)

    cluster_status = proxmox.get_cluster_status()
    result["cluster_status"] = cluster_status

    module.exit_json(**result)


if __name__ == "__main__":
    main()
