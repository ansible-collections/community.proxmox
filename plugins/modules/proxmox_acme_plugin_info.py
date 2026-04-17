#!/usr/bin/python

# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_acme_plugin_info
short_description: Retrieves a single ACME plugin
version_added: "2.0.0"
author:
  - Clément Cruau (@PendaGTP)
description:
  - Retrieves a single ACME plugin by plugin ID name.
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  name:
    description:
      - The ACME Plugin ID name.
    type: str
    required: true
    aliases: ["id"]

seealso:
  - module: community.proxmox.proxmox_acme_plugin_dns
    description: Manage ACME DNS plugins on a Proxmox VE.
  - module: community.proxmox.proxmox_acme_plugins_info
    description: Retrieves the list of ACME plugins.

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Get ACME plugin example
  community.proxmox.proxmox_acme_plugin_info:
    name: example
"""

RETURN = r"""
name:
  description: ACME plugin instance identifier.
  returned: on success
  type: str
type:
  description: ACME challenge type (dns, standalone).
  returned: on success
  type: str
plugin:
  description: API implementation name.
  returned: on success
  type: str
data:
  description: Plugin settings as string key/value pairs (value are masked).
  returned: on success
  type: dict
disable:
  description: Whether the plugin configuration is disabled.
  returned: on success
  type: bool
validation_delay:
  description: Validation delay in seconds.
  returned: on success
  type: int
digest:
  description: Digest of the plugin configuration.
  returned: on success
  type: str
"""

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
    is_not_found_error,
)
from ansible_collections.community.proxmox.plugins.module_utils.proxmox_acme_plugin import (
    acme_plugin_to_ansible_result,
)


def module_args():
    return dict(
        name=dict(type="str", required=True, aliases=["id"]),
    )


def module_options():
    return dict()


class ProxmoxClusterAcmePluginInfoAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def run(self):
        name = self.params["name"]
        data = self._fetch_plugin(name)
        if data is None:
            self.module.fail_json(msg=f"ACME plugin {name} does not exist", name=name)

        result = acme_plugin_to_ansible_result(data)
        self.module.exit_json(
            changed=False,
            **result,
        )

    def _fetch_plugin(self, name):
        try:
            return self.proxmox_api.cluster().acme().plugins()(name).get()
        except Exception as e:
            if is_not_found_error(e):
                return None
            self.module.fail_json(msg=f"Failed to read ACME plugin {name}: {to_native(e)}")


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxClusterAcmePluginInfoAnsible(module)

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f"An error occurred: {to_native(e)}")


if __name__ == "__main__":
    main()
