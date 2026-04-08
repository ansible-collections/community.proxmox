#!/usr/bin/python

# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_acme_plugins_info
short_description: Retrieves the list of ACME plugins.
version_added: "2.0.0"
author:
  - Clément Cruau (@PendaGTP)
description:
  - Retrieves the list of ACME plugins.
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  type:
    description:
      - ACME challenge type.
    choices:
      - dns
      - standalone
    type: str
    aliases: ["plugin_type"]

seealso:
  - module: community.proxmox.proxmox_acme_plugin_dns
    description: Manage ACME DNS plugins on a Proxmox VE.
  - module: community.proxmox.proxmox_acme_plugin_info
    description: Retrieves a single ACME plugin

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: List ACME plugins
  community.proxmox.proxmox_acme_plugins_info:
"""

RETURN = r"""
plugins:
  description: List of ACME plugins.
  returned: on success
  type: list
  elements: dict
  contains:
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
      description: Plugin settings as string key/value pairs (values are masked).
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
)
from ansible_collections.community.proxmox.plugins.module_utils.proxmox_acme_plugin import (
    acme_plugin_to_ansible_result,
)


def module_args():
    return dict(
        type=dict(type="str", aliases=["plugin_type"], choices=["dns", "standalone"]),
    )


def module_options():
    return dict()


class ProxmoxClusterAcmePluginInfoAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def run(self):
        plugin_type = self.params.get("type")
        data = self._fetch_plugins(plugin_type)
        result = []
        for plugin in data:
            result.append(acme_plugin_to_ansible_result(plugin))
        self.module.exit_json(changed=False, plugins=result)

    def _fetch_plugins(self, plugin_type):
        try:
            return self.proxmox_api.cluster().acme().plugins().get(type=plugin_type)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to list ACME plugins: {to_native(e)}")


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxClusterAcmePluginInfoAnsible(module)

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f"An error occurred: {to_native(e)}")


if __name__ == "__main__":
    main()
