#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2025, Jana Hoch <janahoch91@proton.me>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

# from ansible_collections.community.sap_libs.plugins.modules.sap_control_exec import choices
# from pygments.lexer import default

DOCUMENTATION = r"""
module: proxmox_zone
short_description: Manage Proxmox zone configurations
description:
  - list/create/update/delete proxmox sdn zones
author: 'Jana Hoch <janahoch91@proton.me> (!UNKNOWN)'
attributes:
  check_mode:
    support: none
  diff_mode:
    support: none
options:
  state:
    description:
      - The desired state of the zone configuration.
    type: str
    choices:
      - present
      - absent
      - update
  force:
    description:
      - If state is present and zone exists it'll update.
      - If state is update and zone doesn't exists it'll create new zone
    type: bool
    default: false
  type:
    description:
      - Specify the type of zone.
    type: str
    choices:
      - evpn
      - faucet
      - qinq
      - simple
      - vlan
      - vxlan
  zone:
    description:
      - Unique zone name.
    type: str
  advertise_subnets:
    description:
      - Advertise evpn subnets if you have silent hosts.
    type: bool
  bridge:
    description:
      - Specify the bridge interface to use.
    type: str
  bridge_disable_mac_learning:
    description:
      - Disable auto MAC address learning on the bridge interface.
    type: bool
  controller:
    description:
      - Frr router name.
    type: str
  dhcp:
    description:
      - Type of the DHCP backend for this zone.
    type: str
    choices:
      - dnsmasq
  disable_arp_nd_suppression:
    description:
      - Disable ipv4 arp && ipv6 neighbour discovery suppression.
    type: bool
  dns:
    description:
      - dns api server.
    type: str
  dnszone:
    description:
      - dns domain zone.
    type: str
  dp_id:
    description:
      - Faucet dataplane id.
    type: int
  exitnodes:
    description:
      - List of cluster node names.
    type: str
  exitnodes_local_routing:
    description:
      - Allow exitnodes to connect to evpn guests.
    type: bool
  exitnodes_primary:
    description:
      - Force traffic to this exitnode first.
    type: str
  fabric:
    description:
      - SDN fabric to use as underlay for this VXLAN zone.
    type: str
  ipam:
    description:
      - use a specific ipam.
    type: str
  lock_token:
    description:
      - the token for unlocking the global SDN configuration. If not provided it will generate new token
      - If the playbook fails for some reason you can manually clear lock token by deleting `/etc/pve/sdn/.lock`
    type: str
  mac:
    description:
      - Anycast logical router mac address.
    type: str
  mtu:
    description:
      - Set the Maximum Transmission Unit (MTU).
    type: int
  nodes:
    description:
      - List of cluster node names.
    type: str
  peers:
    description:
      - peers address list.
    type: str
  reversedns:
    description:
      - reverse dns api server
    type: str
  rt_import:
    description:
      - Route-Target import.
    type: str
  tag:
    description:
      - Service-VLAN Tag.
    type: int
  vlan_protocol:
    description:
      - Specify the VLAN protocol to use.
    type: str
    choices:
      - 802.1q
      - 802.1ad
  vrf_vxlan:
    description:
      - Specify the VRF VXLAN identifier.
    type: int
  vxlan_port:
    description:
      - Vxlan tunnel udp port (default 4789).
    type: int
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Get all zones
  community.proxmox.proxmox_zone:
    api_user: "root@pam"
    api_password: "{{ vault.proxmox.root_password }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no

- name: Get all simple zones
  community.proxmox.proxmox_zone:
    api_user: "root@pam"
    api_password: "{{ vault.proxmox.root_password }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no
    type: simple
  register: zones

- name: create a simple zones
  community.proxmox.proxmox_zone:
    api_user: "root@pam"
    api_password: "{{ vault.proxmox.root_password }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no
    type: simple
    zone: ansible
    state: present

- name: create a vlan zones
  community.proxmox.proxmox_zone:
    api_user: "root@pam"
    api_password: "{{ vault.proxmox.root_password }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no
    type: vlan
    zone: ansible
    state: present
    bridge: vmbr0

- name: update a zones
  community.proxmox.proxmox_zone:
    api_user: "root@pam"
    api_password: "{{ vault.proxmox.root_password }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no
    type: vlan
    zone: ansible
    state: update
    mtu: 1200

- name: Delete a zones
  community.proxmox.proxmox_zone:
    api_user: "root@pam"
    api_password: "{{ vault.proxmox.root_password }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: no
    type: simple
    zone: ansible
    state: absent
"""

RETURN = r"""
zones:
    description:
      - List of zones. if you do not pass zone name.
      - If you are creating/updating/deleting it'll just return a msg with status
    returned: on success
    type: list
    elements: dict
    sample:
      [
        {
            "digest": "e29dea494461aa699ab3bfb7264d95631c8d0e0d",
            "type": "simple",
            "zone": "ans1"
        },
        {
            "bridge": "vmbr0",
            "digest": "e29dea494461aa699ab3bfb7264d95631c8d0e0d",
            "mtu": 1200,
            "type": "vlan",
            "zone": "ansible"
        },
        {
            "bridge": "vmbr100",
            "digest": "e29dea494461aa699ab3bfb7264d95631c8d0e0d",
            "ipam": "pve",
            "type": "vlan",
            "zone": "lab"
        },
        {
            "dhcp": "dnsmasq",
            "digest": "e29dea494461aa699ab3bfb7264d95631c8d0e0d",
            "ipam": "pve",
            "type": "simple",
            "zone": "test1"
        },
        {
            "digest": "e29dea494461aa699ab3bfb7264d95631c8d0e0d",
            "ipam": "pve",
            "type": "simple",
            "zone": "tsjsfv"
        }
      ]

"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    proxmox_auth_argument_spec,
    ProxmoxAnsible
)


def get_proxmox_args():
    return dict(
        state=dict(type="str", choices=["present", "absent", "update"], required=False),
        force=dict(type="bool", default=False, required=False),
        type=dict(type="str",
                  choices=["evpn", "faucet", "qinq", "simple", "vlan", "vxlan"],
                  required=False),
        zone=dict(type="str", required=False),
        advertise_subnets=dict(type="bool", required=False),
        bridge=dict(type="str", required=False),
        bridge_disable_mac_learning=dict(type="bool", required=False),
        controller=dict(type="str", required=False),
        dhcp=dict(type="str", choices=["dnsmasq"], required=False),
        disable_arp_nd_suppression=dict(type="bool", required=False),
        dns=dict(type="str", required=False),
        dnszone=dict(type="str", required=False),
        dp_id=dict(type="int", required=False),
        exitnodes=dict(type="str", required=False),
        exitnodes_local_routing=dict(type="bool", required=False),
        exitnodes_primary=dict(type="str", required=False),
        fabric=dict(type="str", required=False),
        ipam=dict(type="str", required=False),
        lock_token=dict(type="str", required=False, no_log=False),
        mac=dict(type="str", required=False),
        mtu=dict(type="int", required=False),
        nodes=dict(type="str", required=False),
        peers=dict(type="str", required=False),
        reversedns=dict(type="str", required=False),
        rt_import=dict(type="str", required=False),
        tag=dict(type="int", required=False),
        vlan_protocol=dict(type="str", choices=["802.1q", "802.1ad"], required=False),
        vrf_vxlan=dict(type="int", required=False),
        vxlan_port=dict(type="int", required=False),
    )


def get_ansible_module():
    module_args = proxmox_auth_argument_spec()
    module_args.update(get_proxmox_args())

    return AnsibleModule(
        argument_spec=module_args,
        required_if=[
            ('state', 'present', ['type', 'zone']),
            ('state', 'update', ['type', 'zone']),
            ('state', 'absent', ['zone'])
        ]
    )


class ProxmoxZoneAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super(ProxmoxZoneAnsible, self).__init__(module)
        self.params = module.params

    def validate_params(self):
        type = self.params.get('type')
        if self.params.get('state') in ['present', 'update']:
            if type == 'vlan':
                return self.params.get('bridge')
            elif type == 'qinq':
                return self.params.get('tag') and self.params.get('vlan_protocol')
            elif type == 'vxlan':
                return self.params.get('fabric')
            elif type == 'evpn':
                return self.params.get('controller') and self.params.get('vrf_vxlan')
        else:
            return True

    def run(self):
        state = self.params.get("state")
        force = self.params.get("force")
        type = self.params['type']

        if not self.validate_params():
            required_params = {
                'vlan': ['bridge'],
                'qinq': ['bridge', 'tag', 'vlan_protocol'],
                'vxlan': ['fabric'],
                'evpn': ['controller', 'vrf_vxlan']
            }
            self.module.fail_json(
                msg=f'to create zone of type {type} it needs - {required_params[type]}'
            )

        zone_params = {
            "type": self.params.get("type"),
            "zone": self.params.get("zone"),
            "advertise-subnets": self.params.get("advertise_subnets"),
            "bridge": self.params.get("bridge"),
            "bridge-disable-mac-learning": self.params.get("bridge_disable_mac_learning"),
            "controller": self.params.get("controller"),
            "dhcp": self.params.get("dhcp"),
            "disable-arp-nd-suppression": self.params.get("disable_arp_nd_suppression"),
            "dns": self.params.get("dns"),
            "dnszone": self.params.get("dnszone"),
            "dp-id": self.params.get("dp_id"),
            "exitnodes": self.params.get("exitnodes"),
            "exitnodes-local-routing": self.params.get("exitnodes_local_routing"),
            "exitnodes-primary": self.params.get("exitnodes_primary"),
            "fabric": self.params.get("fabric"),
            "ipam": self.params.get("ipam"),
            "lock-token": self.params.get("lock_token"),
            "mac": self.params.get("mac"),
            "mtu": self.params.get("mtu"),
            "nodes": self.params.get("nodes"),
            "peers": self.params.get("peers"),
            "reversedns": self.params.get("reversedns"),
            "rt-import": self.params.get("rt_import"),
            "tag": self.params.get("tag"),
            "vlan-protocol": self.params.get("vlan_protocol"),
            "vrf-vxlan": self.params.get("vrf_vxlan"),
            "vxlan-port": self.params.get("vxlan_port"),
        }

        if zone_params['lock-token'] is None and state is not None:
            zone_params['lock-token'] = self.get_global_sdn_lock()

        if state == "present":
            self.zone_present(force, **zone_params)

        elif state == "update":
            self.zone_update(**zone_params)

        elif state == "absent":
            self.zone_absent(
                zone_name=zone_params.get('zone'),
                lock=zone_params.get('lock-token')
            )
        else:
            zones = self.get_zones(**zone_params)
            self.module.exit_json(
                changed=False, msg=zones
            )

    def get_zones(self, **type):
        try:
            return self.proxmox_api.cluster().sdn().zones().get(**type)
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve zone information from cluster: {e}'
            )

    def zone_present(self, force, **kwargs):
        available_zones = {x['zone']: {'type': x["type"], 'digest': x['digest']} for x in self.get_zones()}
        zone = kwargs.get("zone")
        type = kwargs.get("type")
        lock = kwargs.get('lock-token')

        # Check if zone already exists
        if zone in available_zones.keys() and force:
            if type != available_zones[zone]['type']:
                self.release_lock(lock)
                self.module.fail_json(
                    msg=f'zone {zone} exists with different type and we cannot change type post fact.'
                )
            else:
                self.zone_update(**kwargs)
        elif zone in available_zones.keys() and not force:
            self.release_lock(lock)
            self.module.exit_json(
                changed=False, zone=zone, msg=f'Zone {zone} already exists and force is false!'
            )
        else:
            try:
                self.proxmox_api.cluster().sdn().zones().post(**kwargs)
                self.apply_sdn_changes_and_release_lock(lock)
                self.module.exit_json(
                    changed=True, zone=zone, msg=f'Created new Zone - {zone}'
                )
            except Exception as e:
                self.rollback_sdn_changes_and_release_lock(lock)
                self.module.fail_json(
                    msg=f'Failed to create zone {zone}'
                )

    def zone_update(self, **kwargs):
        available_zones = {x['zone']: {'type': x["type"], 'digest': x['digest']} for x in self.get_zones()}
        type = kwargs.get("type")
        zone_name = kwargs.get("zone")
        lock = kwargs.get('lock-token')

        try:
            # If zone is not present create it
            if zone_name not in available_zones.keys():
                self.zone_present(force=False, **kwargs)
            elif type == available_zones[zone_name]['type']:
                del kwargs['type']
                del kwargs['zone']
                kwargs['digest'] = available_zones[zone_name]['digest']

                zone = getattr(self.proxmox_api.cluster().sdn().zones(), zone_name)
                zone.put(**kwargs)
                self.apply_sdn_changes_and_release_lock(lock)
                self.module.exit_json(
                    changed=True, msg=f'Updated zone {zone_name}'
                )
            else:
                self.release_lock(lock)
                self.module.fail_json(
                    msg=f'zone {zone_name} already exists with different type'
                )
        except Exception as e:
            self.rollback_sdn_changes_and_release_lock(lock)
            self.module.fail_json(
                msg=f'Failed to update zone {e}'
            )

    def zone_absent(self, zone_name, lock):
        available_zones = [x['zone'] for x in self.get_zones()]
        params = {'lock-token': lock}

        try:
            if zone_name not in available_zones:
                self.release_lock(lock)
                self.module.exit_json(
                    changed=False, msg=f"zone {zone_name} already doesn't exist."
                )
            else:
                zone = getattr(self.proxmox_api.cluster().sdn().zones(), zone_name)
                zone.delete(**params)
                self.apply_sdn_changes_and_release_lock(lock)
                self.module.exit_json(
                    changed=True, msg=f'Successfully deleted zone {zone_name}'
                )
        except Exception as e:
            self.rollback_sdn_changes_and_release_lock(lock)
            self.module.fail_json(
                msg=f'Failed to delete zone {zone_name} {e}. Rolling back all pending changes.'
            )


def main():
    module = get_ansible_module()
    proxmox = ProxmoxZoneAnsible(module)

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f'An error occurred: {e}')


if __name__ == "__main__":
    main()
