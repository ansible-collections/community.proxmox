#!/usr/bin/python
#
# Copyright (c) 2026, (@clementdlg) <0xkrem@proton.me>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_ceph_init
version_added: 3.1.0
short_description: Initialize a Ceph cluster on a Proxmox VE node
description:
  - Creates the initial Ceph default configuration on the specified node through the Proxmox VE API.
  - Idempotent - detects an already initialized Ceph cluster and compares the provided parameters against the current configuration.
  - The network related parameters O(network) and O(cluster_network) are mutable and can be updated after initialization.
  - O(size) and O(min_size) can only be set during the initial creation; the module fails if they drift from the initialized configuration.
author: clementdlg (@clementdlg)
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none

options:
  node:
    description:
      - The cluster node name on which the Ceph cluster is initialized.
    required: true
    type: str
  network:
    description:
      - Use specific network for all ceph related traffic.
      - Applied to both the public and the cluster network unless O(cluster_network) is set.
      - Can be updated after initialization.
    type: str
  cluster_network:
    description:
      - Declare a separate cluster network, OSDs will route heartbeat, object replication and recovery traffic over it.
      - Requires O(network).
      - Can be updated after initialization.
    type: str
  size:
    description:
      - Targeted number of replicas per object.
      - Can only be set during the initial creation of the Ceph cluster.
    type: int
  min_size:
    description:
      - Minimum number of available replicas per object to allow I/O.
      - Can only be set during the initial creation of the Ceph cluster.
    type: int

notes:
  - Ceph must be installed on the node before initialization (C(pveceph install)), otherwise the module fails.
  - Ceph clusters cannot be purged through the Proxmox VE API; use the C(pveceph purge) CLI command instead.
    This module therefore has no C(state) parameter.
  - O(size) and O(min_size) drift cannot be remediated through the API, the module fails fast when they differ
    from the initialized configuration.
  - Drift is detected against C(ceph.conf); values changed out-of-band through the Ceph monitor configuration
    database (C(ceph config set)) are not visible to this module.
  - The module talks to the Proxmox VE API and never touches the local filesystem, so it can be run with
    C(delegate_to) set to localhost like all other modules of this collection.

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""


EXAMPLES = r"""
- name: Initialize the Ceph cluster on a node with a dedicated network
  community.proxmox.proxmox_ceph_init:
    node: pve01
    network: 10.0.10.0/24

- name: Initialize the Ceph cluster with separate public and cluster networks
  community.proxmox.proxmox_ceph_init:
    node: pve01
    network: 10.0.10.0/24
    cluster_network: 10.0.20.0/24
    size: 3
    min_size: 2

- name: Ensure the Ceph cluster is initialized (idempotent)
  community.proxmox.proxmox_ceph_init:
    node: pve01
    network: 10.0.10.0/24

- name: Update the ceph network of an initialized cluster
  community.proxmox.proxmox_ceph_init:
    node: pve01
    network: 10.0.30.0/24
"""


RETURN = r"""
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""


import configparser

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
)

NOT_INITIALIZED_ERROR = "not initialized"
INT_RANGE = (1, 7)

# module option -> ceph.conf [global] key
MUTABLE_PARAMS = {
    "network": "public_network",
    "cluster_network": "cluster_network",
}
IMMUTABLE_PARAMS = {
    "size": "osd_pool_default_size",
    "min_size": "osd_pool_default_min_size",
}


def module_args():
    return dict(
        node=dict(type="str", required=True),
        network=dict(type="str"),
        cluster_network=dict(type="str"),
        size=dict(type="int"),
        min_size=dict(type="int"),
    )


def module_options():
    return dict(
        required_by={"cluster_network": ["network"]},
    )


class ProxmoxCephInitAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def get_ceph_conf(self, node):
        """
        Retrieve the raw ceph.conf file content.

        Args:
            node(str): Node to query.

        Returns:
            str | None: The ceph.conf content, or None if the Ceph cluster
            is not initialized on the node.
        """
        try:
            return self.proxmox_api.nodes(node).ceph.cfg.raw.get()
        except Exception as e:
            if NOT_INITIALIZED_ERROR in to_native(e).lower():
                return None
            self.module.fail_json(msg=f"Unable to retrieve Ceph configuration from node {node}: {to_native(e)}")

    def get_current_config(self, ceph_conf):
        """
        Parse the [global] section of the ceph.conf file content.

        Args:
            ceph_conf(str): Raw ceph.conf content.

        Returns:
            dict: The keys and values of the [global] section.
        """
        parser = configparser.ConfigParser(
            interpolation=None,
            strict=False,
            delimiters=("=",),
            inline_comment_prefixes=(
                "#",
                ";",
            ),
        )
        parser.read_string(to_native(ceph_conf))
        if not parser.has_section("global"):
            self.module.fail_json(msg="ceph.conf has no [global] section, cannot detect the current Ceph configuration")
        return dict(parser.items("global"))

    def get_init_params(self):
        """game
        Build the API parameters for the initial creation from the module parameters.

        Returns:
            dict: API parameter names mapped to the values provided by the user.
        """
        params = {}
        if self.params["network"] is not None:
            params["network"] = self.params["network"]
        if self.params["cluster_network"] is not None:
            params["cluster-network"] = self.params["cluster_network"]
        if self.params["size"] is not None:
            params["size"] = self.params["size"]
        if self.params["min_size"] is not None:
            params["min_size"] = self.params["min_size"]
        return params

    def get_mutable_drift(self, current):
        """
        Compare the mutable module parameters against the current configuration.

        Args:
            current(dict): Current [global] configuration.

        Returns:
            dict: Drifted mutable module option names mapped to the current values.
        """
        drift = {}
        for name, key in MUTABLE_PARAMS.items():
            if self.params[name] is not None and self.params[name] != current.get(key):
                drift[name] = current.get(key)
        return drift

    def get_immutable_drift(self, current):
        """
        Compare the immutable module parameters against the current configuration.

        Args:
            current(dict): Current [global] configuration.

        Returns:
            dict: Drifted immutable module option names mapped to the current values.
        """
        drift = {}
        for name, key in IMMUTABLE_PARAMS.items():
            if self.params[name] is None:
                continue
            current_value = current.get(key)
            # ceph.conf values are always strings; normalize the desired
            # integer the same way so a plain string comparison suffices.
            if current_value != str(self.params[name]):
                drift[name] = current_value
        return drift

    def get_update_params(self, current):
        """
        Build the reconciled API parameters to update the network configuration
        of an initialized cluster.

        The PVE API sets both public_network and cluster_network from the
        network parameter, so a separately configured cluster network is
        preserved by sending it along.

        Args:
            current(dict): Current [global] configuration.

        Returns:
            dict: API parameter names mapped to the values to apply.
        """
        params = {}
        if self.params["network"] is not None:
            params["network"] = self.params["network"]
            # Avoid overwriting the cluster_network param with value of network if user did not explicitly set a value
            # but Ceph was previsouly configured with a dedicated cluster_network
            if self.params["cluster_network"] is None:
                current_cluster_network = current.get("cluster_network")
                if current_cluster_network is not None and current_cluster_network != current.get("public_network"):
                    params["cluster-network"] = current_cluster_network
        # User explicitly provided a value for cluster_network
        if self.params["cluster_network"] is not None:
            params["cluster-network"] = self.params["cluster_network"]
        return params

    def init_cluster(self, node, params):
        """
        Call the Ceph init API endpoint.

        Args:
            node(str): Node to initialize Ceph on.
            params(dict): API parameters to pass to the endpoint.
        """
        self.proxmox_api.nodes(node).ceph.init.create(**params)


def main():
    module = create_proxmox_module(module_args(), **module_options())

    # Fail fast on out-of-range values before talking to the API.
    for name in IMMUTABLE_PARAMS:
        value = module.params[name]
        if value is not None and not INT_RANGE[0] <= value <= INT_RANGE[1]:
            module.fail_json(msg=f"Parameter {name} must be in the range {INT_RANGE[0]}-{INT_RANGE[1]}, got {value}")

    proxmox = ProxmoxCephInitAnsible(module)
    node = module.params["node"]

    # Fail fast if the target node does not exist.
    proxmox.get_node(node, strict=True)

    # The ceph.conf file is the state marker of the init endpoint
    ceph_conf = proxmox.get_ceph_conf(node)

    # Ceph is not initialized yet: create the initial configuration.
    if ceph_conf is None:
        if module.check_mode:
            module.exit_json(changed=True, msg=f"Ceph cluster would be initialized on node {node}")
        try:
            proxmox.init_cluster(node, proxmox.get_init_params())
        except Exception as e:
            module.fail_json(msg=f"Initializing the Ceph cluster on node {node} failed: {to_native(e)}")
        module.exit_json(changed=True, msg=f"Ceph cluster initialized on node {node}")

    # Ceph is already initialized: drift detection
    current = proxmox.get_current_config(ceph_conf)

    # Fail if user tries to update an immutable parameter
    immutable_drift = proxmox.get_immutable_drift(current)
    if immutable_drift:
        drift = ", ".join(
            f"{name} (current: '{value if value is not None else 'unset'}', desired: '{module.params[name]}')"
            for name, value in immutable_drift.items()
        )
        module.fail_json(
            msg=(
                f"Cannot change immutable parameter(s) of the initialized Ceph cluster on node {node}: {drift}. "
                "These can only be set during initial creation."
            )
        )

    # The cluster already matches the desired state.
    if not proxmox.get_mutable_drift(current):
        module.exit_json(changed=False, msg=f"Ceph cluster is already initialized on node {node}")

    # Mutable parameters have drifted, calling the init endpoint with reconciled payload
    if module.check_mode:
        module.exit_json(changed=True, msg=f"Ceph cluster network configuration would be updated on node {node}")
    try:
        proxmox.init_cluster(node, proxmox.get_update_params(current))
    except Exception as e:
        module.fail_json(msg=f"Updating the Ceph cluster network configuration on node {node} failed: {to_native(e)}")
    module.exit_json(changed=True, msg=f"Ceph cluster network configuration updated on node {node}")


if __name__ == "__main__":
    main()
