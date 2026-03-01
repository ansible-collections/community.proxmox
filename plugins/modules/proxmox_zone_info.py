#!/usr/bin/python

# Copyright (c) 2025, Jana Hoch <janahoch91@proton.me>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_zone_info
short_description: Get Proxmox zone info.
description:
  - List all available zones.
version_added: "1.4.0"
author: 'Jana Hoch <janahoch91@proton.me> (!UNKNOWN)'
options:
  type:
    description:
      - Filter zones on based on type.
    type: str
    choices:
      - evpn
      - faucet
      - qinq
      - simple
      - vlan
      - vxlan
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module
"""

EXAMPLES = r"""
- name: Get all zones
  community.proxmox.proxmox_zone_info:
    api_user: "root@pam"
    api_password: "{{ vault.proxmox.root_password }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: false

- name: Get all simple zones
  community.proxmox.proxmox_zone_info:
    api_user: "root@pam"
    api_password: "{{ vault.proxmox.root_password }}"
    api_host: "{{ pc.proxmox.api_host }}"
    validate_certs: false
    type: simple
  register: zones
"""

RETURN = r"""
zones:
    description:
      - List of zones.
      - If type is passed it'll filter based on type
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

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import create_proxmox_module
from ansible_collections.community.proxmox.plugins.module_utils.proxmox_sdn import ProxmoxSdnAnsible


def module_args():
    return dict(type=dict(type="str", choices=["evpn", "faucet", "qinq", "simple", "vlan", "vxlan"], required=False))


def module_options():
    return {}


class ProxmoxZoneInfoAnsible(ProxmoxSdnAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def run(self):
        zones = self.get_zones(zone_type=self.params.get("type"))
        self.module.exit_json(changed=False, zones=zones, msg="Successfully retrieved zone info.")


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxZoneInfoAnsible(module)

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f"An error occurred: {e}")


if __name__ == "__main__":
    main()
