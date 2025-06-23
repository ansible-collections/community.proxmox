#!/usr/bin/python

# Copyright: (c) 2025, Markus Kötter <koetter@cispa.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_cluster_ha_groups

short_description: Management of HA groups in Proxmox VE Cluster

version_added: "1.1.0"

description: 
  - Configure HA groups via /cluster/ha/groups

options:
    state:
        description: create or delete
        required: true
        choices: ['present', 'absent']
        type: str
    name:
        description: group name
        required: true
        type: str
    comment:
        description: Description
        required: false
        type: str
    nodes:
        description: List of cluster node members, where a priority can be given to each node. A resource bound to a group will run on the available nodes with the highest priority. If there are more nodes in the highest priority class, the services will get distributed to those nodes. The priorities have a relative meaning only. The higher the number, the higher the priority.
        required: false
        type: bool
    nofailback:
        description: The CRM tries to run services on the node with the highest priority. If a node with higher priority comes online, the CRM migrates the service to that node. Enabling nofailback prevents that behavior.
        required: false
        type: bool
    restricted:
        description: Resources bound to restricted groups may only run on nodes defined by the group. The resource will be placed in the stopped state if no group node member is online. Resources on unrestricted groups may run on any cluster node if all group members are offline, but they will migrate back as soon as a group member comes online. One can implement a 'preferred node' behavior using an unrestricted group with only one member.
        required: False
        type: bool

author:
    - Markus Kötter (@commonism)
'''

EXAMPLES = r'''
- name: Create HA group
  community.proxmox.proxmox_cluster_ha_groups:
    api_host: "{{ ansible_host }}"
    api_password: "{{ proxmox_root_pw | default(lookup('ansible.builtin.env', 'PROXMOX_PASSWORD', default='')) }}"
    api_user: root@pam

    state: "present"
    name: ha0
    comment: yes
    nodes: node0:0,node1:1
    nofailback: true
    restricted: false

- name: Delete HA group
  community.proxmox.proxmox_cluster_ha_groups:
    api_host: "{{ ansible_host }}"
    api_password: "{{ proxmox_root_pw | default(lookup('ansible.builtin.env', 'PROXMOX_PASSWORD', default='')) }}"
    api_user: root@pam

    state: "absent"
    name: ha0
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
old_groups:
    description: The original name param that was passed in.
    type: list
    returned: always
new_groups:
    description: The output message that the test module generates.
    type: list
    returned: when changed
'''

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (proxmox_auth_argument_spec,
                                                                                ProxmoxAnsible)


class ProxmoxClusterHAGroupsAnsible(ProxmoxAnsible):
    def _get(self):
        acls = self.proxmox_api.cluster.ha.groups.get()
        return acls

    def _post(self, **data):
        return self.proxmox_api.cluster.ha.groups.post(**data)

    def _put(self, name, data):
        return self.proxmox_api.cluster.ha.groups(name).put(**data)

    def _delete(self, name):
        return self.proxmox_api.cluster.ha.groups(name).delete()

    def create(self, groups, name, comment, nodes, nofailback, restricted):
        data = {
            "comment": comment,
            "nodes": nodes,
            "nofailback": int(nofailback),
            "restricted": int(restricted)
        }

        for group in groups:
            if group["group"] != name:
                continue

            if (group["comment"], group["nodes"], group["nofailback"], group["restricted"]) == (comment, nodes, nofailback, restricted):
                return False
            else:
                self._put(name, data)
                return True

        self._post(group=name, **data)

    def delete(self, groups, name):
        for ace in groups:
            if ace["group"] != name:
                continue
            self._delete(name)
            return True

        return False



def run_module():
    module_args = proxmox_auth_argument_spec()

    acl_args = dict(
        state=dict(choices=['present', 'absent'], required=True),
        name=dict(type='str', required=True),
        comment=dict(type='str', required=False),
        nodes=dict(type='str', required=False),
        nofailback=dict(type='bool', default=False),
        restricted=dict(type='bool', default=False),
    )

    module_args.update(acl_args)

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    proxmox = ProxmoxClusterHAGroupsAnsible(module)

    name = module.params['name']
    comment = module.params['comment']
    nodes = module.params['nodes']
    nofailback = module.params['nofailback']
    restricted = module.params['restricted']
    try:
        groups = proxmox._get()

        if module.params["state"] == "present":
            r = proxmox.create(groups, name, comment, nodes, nofailback, restricted)
        else:
            r = proxmox.delete(groups, name)

        result['changed'] = r
    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
