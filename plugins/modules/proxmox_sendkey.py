#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, (@miyuk) <enough7531@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: proxmox_sendkey
short_description: Send key presses to a Proxmox VM console
version_added: 1.5.0
description:
  - Uses the Proxmox API to send a sequence of key presses to the console of a VM.
  - Keys can be specified explicitly or derived from a plain text string.
author:
  - "miyuk (@miyuk172) <enough7531@gmail.com>"
attributes:
  check_mode:
    support: none
  diff_mode:
    support: none
notes:
  - Keys must match the qemu key names listed in
    L(QEMU ui.QKeyCode,https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html#enum-QMP-ui.QKeyCode).
options:
  name:
    description:
      - The unique name of the VM.
    type: str
  vmid:
    description:
      - The unique ID of the VM.
      - Takes precedence over O(name).
    type: int
  keys_send:
    description:
      - List of keys or key sequence to send in order.
      - Each item must follow the qemu key naming format such as
        C(ctrl-alt-delete) or C(ret).
      - You can specify either O(keys_send) or O(string_send).
    type: list
    elements: str
  string_send:
    description:
      - Raw string that will be transformed to the corresponding key presses
      - Only ASCII-characters are supported.
        before sending.
      - You can specify either O(keys_send) or O(string_send).
    type: str
  delay:
    description:
      - Delay in seconds between each key press.
    type: float
    default: 0.0
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Send Ctrl+Alt+Delete to a Windows VM
  proxmox_sendkey:
    api_host: proxmoxhost
    api_user: root@pam
    api_password: password123
    name: win-test
    keys_send:
      - ctrl-alt-delete

- name: Type a login string into a Linux VM console
  proxmox_sendkey:
    api_host: proxmoxhost
    api_user: root@pam
    api_password: password123
    vmid: 101
    string_send: |
        root
        P@ssw0rd
    delay: 1.0
"""

RETURN = r"""
vmid:
  description: The VM vmid.
  returned: success
  type: int
  sample: 101
total_keys:
  description: List of sent keys that were sent to the VM console.
  returned: success
  type: list
  elements: str
  sample: ["H", "e", "l", "l", "o"]
keys_num:
  description: Number of sent keys that were sent to the VM console.
  returned: success
  type: int
  sample: 5
completed_keys_num:
  returned: success
  description: Number of keys that were sent to the VM console.
  type: int
  sample: 5
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
        keys_send=dict(type="list", elements="str", no_log=False),
        string_send=dict(type="str"),
        delay=dict(type="float", default=0.0),
    )


def get_ansible_module():
    module_args = proxmox_auth_argument_spec()
    module_args.update(get_proxmox_args())

    return AnsibleModule(
        argument_spec=module_args,
        required_together=[
            ("api_token_id", "api_token_secret"),
        ],
        required_one_of=[
            ("keys_send", "string_send"),
            ("vmid", "name"),
            ("api_password", "api_token_id"),
        ],
        mutually_exclusive=[
            ("keys_send", "string_send"),
        ],
        supports_check_mode=False,
    )


class ProxmoxSendkeyAnsible(ProxmoxAnsible):
    """Proxmox sendkey module implementation."""

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
        "a": ["a"],
        "b": ["b"],
        "c": ["c"],
        "d": ["d"],
        "e": ["e"],
        "f": ["f"],
        "g": ["g"],
        "h": ["h"],
        "i": ["i"],
        "j": ["j"],
        "k": ["k"],
        "l": ["l"],
        "m": ["m"],
        "n": ["n"],
        "o": ["o"],
        "p": ["p"],
        "q": ["q"],
        "r": ["r"],
        "s": ["s"],
        "t": ["t"],
        "u": ["u"],
        "v": ["v"],
        "w": ["w"],
        "x": ["x"],
        "y": ["y"],
        "z": ["z"],
        "1": ["1"],
        "2": ["2"],
        "3": ["3"],
        "4": ["4"],
        "5": ["5"],
        "6": ["6"],
        "7": ["7"],
        "8": ["8"],
        "9": ["9"],
        "0": ["0"],
        "-": ["minus"],
        "=": ["equal"],
        "[": ["bracket_left"],
        "]": ["bracket_right"],
        "\\": ["backslash"],
        ";": ["semicolon"],
        "'": ["apostrophe"],
        ",": ["comma"],
        ".": ["dot"],
        "/": ["slash"],
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
        " ": ["spc"],
        "\n": ["ret"],
    }

    def __init__(self, module):
        super(ProxmoxSendkeyAnsible, self).__init__(module)
        self.params = module.params
        self.total_keys = []
        self.completed_keys = []

    def string_to_keys(self, text):
        """Convert text to key list."""
        keys = []
        for ch in str(text):
            ch_keys = self.CHAR_MAP.get(ch, None)
            if ch_keys is None:
                self.module.fail_json(f"The character {ch} passed to string_send is not allowed")
            key = "-".join(ch_keys)
            keys.append(key)
        return keys

    def validate_keys(self, keys):
        """Validate keys."""
        for key_combo in keys:
            for key in key_combo.split("-"):
                if key not in self.ALL_KEYS:
                    self.module.fail_json(f"Key is invalid: {key}")

    def send_keys(self, vmid, keys_send, delay):
        """Send keys to VM console."""
        vm = self.get_vm(vmid)
        for key in keys_send:
            self.proxmox_api.nodes(vm["node"]).qemu(vmid).sendkey.put(key=key)
            self.completed_keys.append(key)
            if delay > 0.0:
                time.sleep(delay)

    def run(self):
        """Main execution method."""
        vmid = self.params.get("vmid")
        name = self.params.get("name")
        keys_send = self.params.get("keys_send")
        string_send = self.params.get("string_send")
        delay = self.params.get("delay")

        # Get vmid from name
        if not vmid:
            vmid = self.get_vmid(name)

        # Convert text to key list
        if string_send:
            keys_send = self.string_to_keys(string_send)
        self.total_keys = keys_send
        self.validate_keys(self.total_keys)

        self.send_keys(vmid, self.total_keys, delay)

        self.module.exit_json(
            changed=True,
            vmid=vmid,
            total_keys=self.total_keys,
            keys_num=len(self.total_keys),
            completed_keys_num=len(self.completed_keys),
        )


def main():
    """Main entry point."""
    module = get_ansible_module()
    proxmox = ProxmoxSendkeyAnsible(module)
    proxmox.run()


if __name__ == "__main__":
    main()
