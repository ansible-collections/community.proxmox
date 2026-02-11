#!/usr/bin/python
#
# Copyright (c) 2025, (@teslamania) <nicolas.vial@protonmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later



DOCUMENTATION = r"""
module: proxmox_ceph_osd
version_added: 1.5.0
short_description: Manage osd.
description:
  - This module allows you to add or delete an osd.
  - You can also in, out or scrub an osd.
author: Vial Nicolas (@teslamania)
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none

options:
    cleanup:
        description:
          - If set remove partition table entries.
          - Used with O(state=absent).
        required: false
        type: bool
        default: false
    crush_device_class:
        description:
          - Set the device class of the OSD in crush.
          - Used with O(state=present).
        required: false
        type: str
    db_dev:
        description:
          - Block device name for block.db.
          - Used with O(state=present).
        required: false
        type: str
    db_dev_size:
        description:
          - If a block.db is requested but the size is not given, will be automatically selected by
          - bluestore_block_db_size from the ceph database (osd or global section) or config (osd or global section) in that order.
          - If this is not available, it will be sized 10% of the size of the OSD device.
          - Fails if the available size is not enough.
          - Used with O(state=present).
        required: false
        type: int
    deep:
        description:
          - If set, instructs a deep scrub instead of a normal one.
          - Used with O(state=scrub).
        required: false
        type: bool
        default: false
    dev:
        description:
          - Block device name.
          - Required when O(state=present).
        required: false
        type: str
    encrypted:
        description:
          - Enables encryption of the OSD.
          - Used with O(state=present).
        required: false
        type: bool
        default: false
    node:
        description: The cluster node name.
        required: true
        type: str
    osdid:
        description:
          - Osd id.
          - Required when O(state=absent), O(state=in), O(state=out), O(state=scrub), O(state=start), O(state=stop) or O-state=restart).
        required: false
        type: int
    osds_per_device:
        description:
          - OSD services per physical device.
          - Used with O(state=present).
        required: false
        type: int
    state:
        description: create, delete, in, out or scrub
        required: true
        choices: ['present', 'absent', 'in', 'out', 'scrub', 'start', 'stop', 'restart']
        type: str
    wal_dev:
        description:
          - Block device name for block.wal.
          - Used with O(state=present).
        required: false
        type: str
    wal_dev_size:
        description:
          - If a block.wal is requested but the size is not given, will be automatically selected by
          - bluestore_block_wal_size from the ceph database (osd or global section) or config (osd or global section) in that order.
          - If this is not available, it will be sized 1% of the size of the OSD device.
          - Fails if the available size is not enough.
          - Used with O(state=present).
        required: false
        type: int

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module
"""


EXAMPLES = r"""
- name: Add an osd
  community.proxmox.proxmox_ceph_osd:
    api_host: proxmox-01.example.com
    api_user: root@pam
    api_password: secret
    node: proxmox-01
    dev: /dev/sdb
    state: present

- name: Delete an osd
  community.proxmox.proxmox_ceph_osd:
    api_host: proxmox-01.example.com
    api_user: root@pam
    api_password: secret
    node: proxmox-01
    osdid: 2
    cleanup: true
    state: absent

- name: Scrub an osd
  community.proxmox.proxmox_ceph_osd:
    api_host: proxmox-01.example.com
    api_user: root@pam
    api_password: secret
    node: proxmox-01
    osdid: 2
    deep: true
    state: scrub

- name: Out an osd
  community.proxmox.proxmox_ceph_osd:
    api_host: proxmox-01.example.com
    api_user: root@pam
    api_password: secret
    node: proxmox-01
    osdid: 2
    state: out

- name: In an osd
  community.proxmox.proxmox_ceph_osd:
    api_host: proxmox-01.example.com
    api_user: root@pam
    api_password: secret
    node: proxmox-01
    osdid: 2
    state: in

- name: Start an osd
  community.proxmox.proxmox_ceph_osd:
    api_host: proxmox-01.example.com
    api_user: root@pam
    api_password: secret
    node: proxmox-01
    osdid: 2
    state: start

- name: Stop an osd
  community.proxmox.proxmox_ceph_osd:
    api_host: proxmox-01.example.com
    api_user: root@pam
    api_password: secret
    node: proxmox-01
    osdid: 2
    state: stop

- name: Restart an osd
  community.proxmox.proxmox_ceph_osd:
    api_host: proxmox-01.example.com
    api_user: root@pam
    api_password: secret
    node: proxmox-01
    osdid: 2
    state: restart
"""

RETURN = r"""
msg:
    description: The output message that the module generates.
    type: str
    returned: always
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    ansible_to_proxmox_bool,
    proxmox_auth_argument_spec,
)


class ProxmoxCephOsdAnsible(ProxmoxAnsible):
    def check_node(self, node):
        nodes = self.proxmox_api.cluster.resources.get(type="node")
        if node not in [item["node"] for item in nodes]:
            self.module.fail_json(msg=f"Node {node} does not exist.")

    def check_dev(self, node, dev):
        devs = self.proxmox_api.nodes(node).disks.list.get()
        if dev not in [dev_data["devpath"] for dev_data in devs]:
            self.module.fail_json(msg=f"{dev} does not exist on the node {node}.")
        dev_data = list(filter(lambda d: d["devpath"] == dev, devs))[0]
        if "used" in dev_data.keys():
            if int(dev_data["osdid"]) >= 0:
                self.module.exit_json(
                    changed=False,
                    msg=f"{dev} is already an osd.",
                )
            else:
                self.module.fail_json(msg=f"{dev} is already in use by the node {node}.")

    def check_osd(self, node, osdid):
        try:
            root = self.proxmox_api.nodes(node).ceph.osd.get()
            root = root["root"]["children"][0]["children"]
            return True in [
                any(d.get("id") == str(osdid) for d in host.get("children"))
                for host in root
                if host.get("children") is not None
            ]
        except Exception as e:
            self.module.fail_json(msg=f"Failure checking osd with exception : {to_native(e)}.")

    # If in return True Else return False, fails if osdid not exists
    def check_osd_in(self, node, osdid):
        try:
            root = self.proxmox_api.nodes(node).ceph.osd.get()
            root = root["root"]["children"][0]["children"]
            for host in root:
                if host.get("children") is not None:
                    for osd in host.get("children"):
                        if osd.get("id") == str(osdid):
                            return osd["in"] == 1
            return False
        except Exception as e:
            self.module.fail_json(msg=f"Failure checking osd in with exception : {to_native(e)}.")

    # If status==up return True Else return False, fails if osdid not exists
    def check_osd_started(self, node, osdid):
        try:
            root = self.proxmox_api.nodes(node).ceph.osd.get()
            root = root["root"]["children"][0]["children"]
            for host in root:
                if host.get("children") is not None:
                    for osd in host.get("children"):
                        if osd.get("id") == str(osdid):
                            return osd["status"] == "up"
            return False
        except Exception as e:
            self.module.fail_json(msg=f"Failure checking osd status with exception : {to_native(e)}.")

    def add_osd(self, node, dev, encrypted, args):
        self.check_node(node)
        self.check_dev(node, dev)
        if not self.module.check_mode:
            self.proxmox_api.nodes(node).ceph.osd.create(
                node=node,
                dev=dev,
                encrypted=encrypted,
                **args,
            )
            msg = "Osd added."
        else:
            msg = "Osd would be added."
        self.module.exit_json(
            changed=True,
            msg=msg,
        )

    def in_osd(self, node, osdid):
        self.check_node(node)
        if not self.check_osd(node, osdid):
            self.module.fail_json(msg=f"Osd {osdid} does not exist.")
        if not self.check_osd_in(node, osdid):
            if not self.module.check_mode:
                self.proxmox_api(f"nodes/{node}/ceph/osd/{osdid}/in").create()
                msg = f"In osd {osdid}."
            else:
                msg = f"Would in osd {osdid}."
            self.module.exit_json(changed=True, msg=msg)
        else:
            self.module.exit_json(changed=False, msg=f"Osd {osdid} already in.")

    def out_osd(self, node, osdid):
        self.check_node(node)
        if not self.check_osd(node, osdid):
            self.module.fail_json(msg=f"Osd {osdid} does not exist.")
        if self.check_osd_in(node, osdid):
            if not self.module.check_mode:
                self.proxmox_api.nodes(node).ceph.osd(osdid).out.create()
                msg = f"Out osd {osdid}."
            else:
                msg = f"Would out osd {osdid}."
            self.module.exit_json(changed=True, msg=msg)
        else:
            self.module.exit_json(changed=False, msg=f"Osd {osdid} already out.")

    def scrub_osd(self, node, osdid, deep):
        self.check_node(node)
        if not self.check_osd(node, osdid):
            self.module.fail_json(msg=f"Osd {osdid} does not exist.")
        if self.check_osd_started(node, osdid):
            if not self.module.check_mode:
                self.proxmox_api.nodes(node).ceph.osd(osdid).scrub.create(deep=deep)
                msg = f"Scrub Osd {osdid}."
            else:
                msg = f"Would scrub Osd {osdid}."
            self.module.exit_json(changed=True, msg=msg)
        else:
            self.module.fail_json(msg=f"Osd {osdid} is not up.")

    def del_osd(self, node, osdid, cleanup):
        self.check_node(node)
        if not self.check_osd(node, osdid):
            self.module.exit_json(changed=False, msg=f"Osd {osdid} not present.")
        if not self.check_osd_in(node, osdid):
            if not self.check_osd_started(node, osdid):
                if not self.module.check_mode:
                    self.proxmox_api.nodes(node).ceph.osd(osdid).delete(cleanup=cleanup)
                    msg = f"Osd {osdid} deleted."
                else:
                    msg = f"Osd {osdid} would be deleted."
                self.module.exit_json(changed=True, msg=msg)
            else:
                self.module.fail_json(
                    msg=f"Cannot delete osd {osdid} is started.",
                )
        else:
            self.module.fail_json(
                msg=f"Cannot delete osd {osdid} is in.",
            )

    def start_osd(self, node, osdid):
        self.check_node(node)
        if not self.check_osd(node, osdid):
            self.module.fail_json(msg=f"Osd {osdid} does not exist.")
        if not self.check_osd_started(node, osdid):
            if not self.module.check_mode:
                self.proxmox_api.nodes(node).ceph.start.create(service=f"osd.{osdid}")
                msg = f"Start Osd {osdid}."
            else:
                msg = f"Would start Osd {osdid}."
            self.module.exit_json(changed=True, msg=msg)
        else:
            self.module.exit_json(
                changed=False,
                msg=f"Osd {osdid} already started.",
            )

    def stop_osd(self, node, osdid):
        self.check_node(node)
        if not self.check_osd(node, osdid):
            self.module.fail_json(msg=f"Osd {osdid} does not exist.")
        if self.check_osd_started(node, osdid):
            if not self.module.check_mode:
                self.proxmox_api.nodes(node).ceph.stop.create(service=f"osd.{osdid}")
                msg = f"Stop Osd {osdid}."
            else:
                msg = f"Would stop Osd {osdid}."
            self.module.exit_json(changed=True, msg=msg)
        else:
            self.module.exit_json(
                changed=False,
                msg=f"Osd {osdid} already stopped.",
            )

    def restart_osd(self, node, osdid):
        self.check_node(node)
        if not self.check_osd(node, osdid):
            self.module.fail_json(msg=f"Osd {osdid} does not exist.")
        if not self.module.check_mode:
            self.proxmox_api.nodes(node).ceph.restart.create(service=f"osd.{osdid}")
            msg = f"Restart Osd {osdid}."
        else:
            msg = f"Would restart Osd {osdid}."

        self.module.exit_json(changed=True, msg=msg)


def get_present_optional_args(args):
    args_list = [
        "db_dev",
        "db_dev_size",
        "wal_dev",
        "wal_dev_size",
    ]
    o_args = {k: args[k] for k in args_list if args[k] is not None}
    if args["osds_per_device"] is not None:
        o_args["osds-per-device"] = args["osds_per_device"]
    if args["crush_device_class"] is not None:
        o_args["crush-device-class"] = args["crush_device_class"]
    return o_args


def main():
    module_args = proxmox_auth_argument_spec()
    osd_args = dict(
        node=dict(type="str", required=True),
        state=dict(choices=["present", "absent", "in", "out", "scrub", "start", "stop", "restart"], required=True),
        dev=dict(type="str"),
        osdid=dict(type="int"),
        cleanup=dict(type="bool", default=False),
        crush_device_class=dict(type="str"),
        db_dev=dict(type="str"),
        db_dev_size=dict(type="int"),
        deep=dict(type="bool", default=False),
        encrypted=dict(type="bool", default=False),
        osds_per_device=dict(type="int"),
        wal_dev=dict(type="str"),
        wal_dev_size=dict(type="int"),
    )

    module_args.update(osd_args)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[("api_password", "api_token_id")],
        required_together=[("api_token_id", "api_token_secret")],
        required_if=[
            ("state", "present", ["dev"]),
            ("state", "absent", ["osdid"]),
            ("state", "in", ["osdid"]),
            ("state", "out", ["osdid"]),
            ("state", "scrub", ["osdid"]),
            ("state", "start", ["osdid"]),
            ("state", "stop", ["osdid"]),
            ("state", "restart", ["osdid"]),
        ],
    )

    proxmox = ProxmoxCephOsdAnsible(module)
    state = module.params["state"]

    if state == "present":
        optional_args = get_present_optional_args(module.params)
        proxmox.add_osd(
            module.params["node"],
            module.params["dev"],
            ansible_to_proxmox_bool(module.params["encrypted"]),
            optional_args,
        )

    elif state == "absent":
        proxmox.del_osd(
            module.params["node"],
            module.params["osdid"],
            ansible_to_proxmox_bool(module.params["cleanup"]),
        )

    elif state == "in":
        proxmox.in_osd(
            module.params["node"],
            module.params["osdid"],
        )

    elif state == "out":
        proxmox.out_osd(
            module.params["node"],
            module.params["osdid"],
        )

    elif state == "scrub":
        proxmox.scrub_osd(
            module.params["node"],
            module.params["osdid"],
            ansible_to_proxmox_bool(module.params["deep"]),
        )

    elif state == "start":
        proxmox.start_osd(
            module.params["node"],
            module.params["osdid"],
        )

    elif state == "stop":
        proxmox.stop_osd(
            module.params["node"],
            module.params["osdid"],
        )

    elif state == "restart":
        proxmox.restart_osd(
            module.params["node"],
            module.params["osdid"],
        )


if __name__ == "__main__":
    main()
