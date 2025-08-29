#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2025, Jana Hoch <janahoch91@proton.me>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

# from ansible_collections.community.sap_libs.plugins.modules.sap_control_exec import choices
# from pygments.lexer import default

DOCUMENTATION = r""""""

EXAMPLES = r""""""

RETURN = r""""""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    proxmox_auth_argument_spec,
    ProxmoxAnsible
)

def get_proxmox_args():
    return dict(
        state=dict(type="str", choices=["present", "absent"], required=False),
        force=dict(type="bool", default=False, required=False),
        update=dict(type="bool", default=False, required=False),
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
        lock_token=dict(type="str", required=False),
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
            ('update', True, ['zone'])
        ]
    )

class ProxmoxZoneAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super(ProxmoxZoneAnsible, self).__init__(module)
        self.params = module.params

    def run(self):
        state = self.params.get("state")
        force = self.params.get("force")

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

            )
        else:
            zones = self.get_zones(**zone_params)
            self.module.exit_json(
                changed=False, msg=zones
            )

    def get_global_sdn_lock(self):
        try:
            return self.proxmox_api.cluster().sdn().lock().post()
        except Exception as e:
            self.apply_sdn_changes_and_release_lock()
            self.module.fail_json(
                msg=f'Failed to acquire global sdn lock {e}'
            )

    def apply_sdn_changes_and_release_lock(self, lock):
        lock_params = {
            'lock-token': lock,
            'release-lock': 1
        }
        try:
            return self.proxmox_api.cluster().sdn().put(**lock_params)
        except Exception as e:
            self.rollback_sdn_changes_and_release_lock(lock_params)
            self.module.fail_json(
                msg=f'Failed to apply sdn changes {e}. Rolling back all pending changes.'
            )

    def rollback_sdn_changes_and_release_lock(self, lock_params):
        try:
            self.proxmox_api.cluster().sdn().rollback().post(**lock_params)
        except Exception as e:
            self.module.fail_json(
                msg=f'Rollback attempt failed - {e}. Manually clear lock by deleting /etc/pve/sdn/.lock'
            )

    def release_lock(self, lock):
        lock_params = {
            'lock-token': lock,
            'force': 0
        }
        try:
            self.proxmox_api.cluster().sdn().lock().delete(**lock_params)
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to release lock - {e}. Manually clear lock by deleting /etc/pve/sdn/.lock'
            )


    def get_zones(self, **type):
        print("reached")
        try:
            return self.proxmox_api.cluster().sdn().zones().get(**type)
        except Exception as e:
            self.module.fail_json(
                msg=f'Failed to retrieve zone information from cluster: {e}'
            )

    def zone_present(self, force, **kwargs):
        available_zones = {x["zone"]: x["type"] for x in self.get_zones()}
        zone = kwargs.get("zone")
        type = kwargs.get("type")
        lock = kwargs.get('lock-token')

        # Check if zone already exists
        if zone in available_zones.keys() and force:
            if type != available_zones[zone]:
                self.release_lock(lock)
                self.module.fail_json(
                    lock=lock,
                    msg=f'zone {zone} exists with different type and we cannot change type post fact.'
                )
            else:
                del kwargs['type']
                self.zone_update(kwargs)
        elif zone in available_zones.keys() and not force:
            self.release_lock(lock)
            self.module.exit_json(
                changed=False, zone=zone, msg=f'Zone {zone} already exists and force is false!'
            )
        else:
            self.proxmox_api.cluster().sdn().zones().post(**kwargs)
            self.apply_sdn_changes_and_release_lock(lock)
            self.module.exit_json(
                changed=True, zone=zone, msg=f'Created new Zone - {zone}'
            )

    def zone_update(self, **kwargs):
        pass

    def zone_absent(self):
        pass


def main():
    module = get_ansible_module()
    proxmox = ProxmoxZoneAnsible(module)

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f'An error occurred: {e}')

if __name__ == "__main__":
    main()