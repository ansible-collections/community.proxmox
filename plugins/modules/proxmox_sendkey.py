#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, (@teslamania) <nicolas.vial@protonmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: proxmox_sendkey
short_description: Send key presses to a Proxmox VM console
version_added: "TODO"
description:
  - Uses the Proxmox API to send a sequence of key presses to the console of a VM.
  - Keys can be specified explicitly or derived from a plain text string.
author:
  - "miyuk (@miyuk172) <enough7531@gmail.com>"
notes:
  - This module relies on the same authentication parameters as the modules from C(community.proxmox).
  - Keys must match the qemu key names listed in L(QEMU ui.QKeyCode,https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html#enum-QMP-ui.QKeyCode).
options:
  name:
    description:
      - The unique name of the VM.
      - You can specify either O(name) or O(vmid) or both of them.
    type: str
  vmid:
    description:
      - The unique ID of the VM.
      - You can specify either O(vmid) or O(name) or both of them.
    type: int
  keys_send:
    description:
      - List of keys or key chords to send in order.
      - Each item must follow the qemu key naming format such as C(ctrl-alt-delete) or C(ret).
      - You can specify either O(keys_send) or O(string_send) or both of them.
    type: list
    elements: str
  string_send:
    description:
      - Raw string that will be transformed to the corresponding key presses before sending.
      - You can specify either O(string_send) or O(keys_send) or both of them.
    type: str
  key_delay:
    description:
      - Delay in seconds between each key press.
    type: int
    default: 0
"""

EXAMPLES = r"""
- name: Send Ctrl+Alt+Delete to a Windows VM
  proxmox_sendkey:
    api_host: "{{ proxmox_host }}"
    api_user: "{{ proxmox_user }}"
    api_password: "{{ proxmox_password }}"
    name: win-test
    keys_send:
      - ctrl-alt-delete

- name: Type a login string into a Linux VM console
  proxmox_sendkey:
    api_host: "{{ proxmox_host }}"
    api_token_id: "{{ proxmox_token_id }}"
    api_token_secret: "{{ proxmox_token_secret }}"
    vmid: 101
    string_send: |
        root
        P@ssw0rd
    key_delay: 1
"""

RETURN = r"""
vmid:
  description: The VM vmid.
  returned: success
  type: int
  sample: 101
keys_send:
  description: Final list of keys that were sent to the VM console.
  returned: success
  type: list
  elements: str
"""

import time

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    proxmox_auth_argument_spec,
)


def get_proxmox_args():
    return dict(
        vmid=dict(type="int"),
        name=dict(type="str"),
        keys_send=dict(type="list", default=[], elements="str", no_log=False),
        string_send=dict(type="str"),
        key_delay=dict(type="int", default=0),
    )

def get_ansible_module():
    module_args = proxmox_auth_argument_spec()
    module_args.update(get_proxmox_args())

    return AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[
            ("keys_send", "string_send"),
        ],
        required_together=[
            ("api_token_id", "api_token_secret"),
        ],
        required_one_of=[
            ("keys_send", "string_send"),
            ("vmid", "name"),
            ("api_password", "api_token_id"),
        ],
        supports_check_mode=False,
    )

class ProxmoxSendkeyAnsible(ProxmoxAnsible):
    # List of keys can be found at QEMU reference
    # https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html#enum-QMP-ui.QKeyCode
    ALL_KEYS = [
        "unmapped",
        "pause",
        "ro",
        "kp_comma",
        "kp_equals",
        "power",
        "hiragana",
        "henkan",
        "yen",
        "sleep",
        "wake",
        "audionext",
        "audioprev",
        "audiostop",
        "audioplay",
        "audiomute",
        "volumeup",
        "volumedown",
        "mediaselect",
        "mail",
        "calculator",
        "computer",
        "ac_home",
        "ac_back",
        "ac_forward",
        "ac_refresh",
        "ac_bookmarks",
        "muhenkan",
        "katakanahiragana",
        "lang1",
        "lang2",
        "f13",
        "f14",
        "f15",
        "f16",
        "f17",
        "f18",
        "f19",
        "f20",
        "f21",
        "f22",
        "f23",
        "f24",
        "shift",
        "shift_r",
        "alt",
        "alt_r",
        "ctrl",
        "ctrl_r",
        "menu",
        "esc",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "0",
        "minus",
        "equal",
        "backspace",
        "tab",
        "q",
        "w",
        "e",
        "r",
        "t",
        "y",
        "u",
        "i",
        "o",
        "p",
        "bracket_left",
        "bracket_right",
        "ret",
        "a",
        "s",
        "d",
        "f",
        "g",
        "h",
        "j",
        "k",
        "l",
        "semicolon",
        "apostrophe",
        "grave_accent",
        "backslash",
        "z",
        "x",
        "c",
        "v",
        "b",
        "n",
        "m",
        "comma",
        "dot",
        "slash",
        "asterisk",
        "spc",
        "caps_lock",
        "f1",
        "f2",
        "f3",
        "f4",
        "f5",
        "f6",
        "f7",
        "f8",
        "f9",
        "f10",
        "num_lock",
        "scroll_lock",
        "kp_divide",
        "kp_multiply",
        "kp_subtract",
        "kp_add",
        "kp_enter",
        "kp_decimal",
        "sysrq",
        "kp_0",
        "kp_1",
        "kp_2",
        "kp_3",
        "kp_4",
        "kp_5",
        "kp_6",
        "kp_7",
        "kp_8",
        "kp_9",
        "less",
        "f11",
        "f12",
        "print",
        "home",
        "pgup",
        "pgdn",
        "end",
        "left",
        "up",
        "down",
        "right",
        "insert",
        "delete",
        "stop",
        "again",
        "props",
        "undo",
        "front",
        "copy",
        "open",
        "paste",
        "find",
        "cut",
        "lf",
        "help",
        "meta_l",
        "meta_r",
        "compose",
    ]
    CHAR_MAP = {
    "A": ["shift", "a"],
    "B": ["shift", "b"],
    "C": ["shift", "c"],
    "D": ["shift", "d"],
    "E": ["shift", "e"],
    "F": ["shift", "f"],
    "G": ["shift", "g"],
    "H": ["shift", "h"],
    "I": ["shift", "i"],
    "J": ["shift", "j"],
    "K": ["shift", "k"],
    "L": ["shift", "l"],
    "M": ["shift", "m"],
    "N": ["shift", "n"],
    "O": ["shift", "o"],
    "P": ["shift", "p"],
    "Q": ["shift", "q"],
    "R": ["shift", "r"],
    "S": ["shift", "s"],
    "T": ["shift", "t"],
    "U": ["shift", "u"],
    "V": ["shift", "v"],
    "W": ["shift", "w"],
    "X": ["shift", "x"],
    "Y": ["shift", "y"],
    "Z": ["shift", "z"],
    "!": ["shift", "1"],
    "@": ["shift", "2"],
    "#": ["shift", "3"],
    "$": ["shift", "4"],
    "%": ["shift", "5"],
    "^": ["shift", "6"],
    "&": ["shift", "7"],
    "*": ["shift", "8"],
    "(": ["shift", "9"],
    ")": ["shift", "0"],
    "_": ["shift", "minus"],
    "+": ["shift", "equal"],
    "{": ["shift", "bracket_left"],
    "}": ["shift", "bracket_right"],
    "|": ["shift", "backslash"],
    ":": ["shift", "semicolon"],
    "\"": ["shift", "apostrophe"],
    "<": ["shift", "comma"],
    ">": ["shift", "dot"],
    "?": ["shift", "slash"],
    "\n": ["ret"],
}

    def __init__(self, module):
        super(ProxmoxSendkeyAnsible, self).__init__(module)
        self.params = module.params

    def string_to_keys(self, text):
        """Cnvert text to key list"""
        keys = []
        for ch in text:
            keys.append(self.CHAR_MAP[ch] if ch in self.CHAR_MAP else ch)
        return keys

    def validate_keys(self, keys):
        """Validate keys"""
        for key in keys.split("-"):
            if key not in self.ALL_KEYS:
                raise Exception(f"key is not corrected: {key}")

    def run(self):
        vmid = self.params.get("vmid")
        name = self.params.get("name")
        keys_send = self.params.get("keys_send")
        string_send = self.params.get("string_send")
        key_delay = self.params.get("key_delay")

        # get vmid from name
        if not vmid:
            vmid = self.get_vmid(name)

        # convert text to key list
        if string_send:
            keys_send = self.string_to_keys(string_send)

        self.send_keys(vmid, keys_send, key_delay)

        self.module.exit_json(
            changed=True,
            vmid=vmid,
            keys_send=keys_send,
        )

    def send_keys(self, vmid, keys_send, key_delay):
        vm = self.get_vm(vmid)
        for key in keys_send:
            self.proxmox_api.nodes(vm["node"]).qemu(vmid).sendkey.put(key=key)
            if key_delay > 0:
                time.sleep(float(key_delay))


def main():
    module = get_ansible_module()
    proxmox = ProxmoxSendkeyAnsible(module)

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f"An error occured: {e}")    


if __name__ == "__main__":
    main()
