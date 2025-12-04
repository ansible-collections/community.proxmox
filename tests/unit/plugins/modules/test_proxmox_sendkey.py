# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import patch

import time
import pytest
proxmoxer = pytest.importorskip("proxmoxer")

from ansible_collections.community.proxmox.plugins.modules import proxmox_sendkey
import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleFailJson,
    AnsibleExitJson,
    ModuleTestCase,
    set_module_args,
)


def get_module_args_sendkey(
    name=None,
    vmid=None,
    keys_send=None,
    string_send=None,
    delay=None,
    **kwargs
):
    args = {
        "api_host": "host",
        "api_user": "user",
        "api_password": "password",
    }
    if name:
        args.update({"name": name})
    if vmid:
        args.update({"vmid": vmid})
    if keys_send:
        args.update({"keys_send": keys_send})
    if string_send:
        args.update({"string_send": string_send})
    if delay:
        args.update({"delay": delay})
    args.update(kwargs)
    return args


class TestProxmoxSendkeyModule(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxSendkeyModule, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_sendkey
        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect"
        ).start()
        self.get_node_mock = patch.object(proxmox_utils.ProxmoxAnsible, "get_node").start()
        self.get_vm_mock = patch.object(proxmox_utils.ProxmoxAnsible, "get_vm").start()
        self.get_vmid_mock = patch.object(proxmox_utils.ProxmoxAnsible, "get_vmid").start()

    def tearDown(self):
        self.get_vmid_mock.stop()
        self.get_vm_mock.stop()
        self.get_node_mock.stop()
        self.connect_mock.stop()
        super(TestProxmoxSendkeyModule, self).tearDown()

    def test_module_fail_when_required_args_missing(self):
        args = get_module_args_sendkey()
        with set_module_args(args):
            with self.assertRaises(AnsibleFailJson):
                self.module.main()

    def test_sendkey_resolve_vmid(self):
        with self.assertRaises(AnsibleExitJson) as exc_info:
            args = get_module_args_sendkey(name="existing.vm.local", keys_send=["ctrl-alt-delete"])
            with set_module_args(args):
                self.get_vmid_mock.return_value = 100
                self.module.main()

        assert self.get_vmid_mock.call_count == 1
        result = exc_info.exception.args[0]
        assert result["vmid"] == 100

    def test_sendkey_by_keys_send(self):
        with self.assertRaises(AnsibleExitJson) as exc_info:
            args = get_module_args_sendkey(vmid=100, keys_send=["ctrl-alt-delete"])
            with set_module_args(args):
                self.get_vm_mock.return_value.qemu.return_value.sendkey.put.return_value = None
                self.module.main()
        result = exc_info.exception.args[0]
        assert result["total_keys"] == ["ctrl-alt-delete"]

    def test_sendkey_by_string_send(self):
        with self.assertRaises(AnsibleExitJson) as exc_info:
            args = get_module_args_sendkey(vmid=100, string_send="Hello World!")
            with set_module_args(args):
                self.get_vm_mock.return_value.qemu.return_value.sendkey.put.return_value = None
                self.module.main()

        result = exc_info.exception.args[0]
        assert result["total_keys"] == [
            "shift-h",
            "e",
            "l",
            "l",
            "o",
            "spc",
            "shift-w",
            "o",
            "r",
            "l",
            "d",
            "shift-1",
        ]

    def test_fail_when_validate_invalid_keys(self):
        with self.assertRaises(AnsibleFailJson):
            args = get_module_args_sendkey(vmid=100, keys_send=["invalid"])
            with set_module_args(args):
                self.get_vm_mock.return_value.qemu.return_value.sendkey.put.return_value = None
                self.module.main()

    @patch.object(time, "sleep")
    def test_sleep_key_delay(self, time_sleep_mock):
        with self.assertRaises(AnsibleExitJson) as exc_info:
            args = get_module_args_sendkey(vmid=100, keys_send=["ctrl-alt-delete"], delay=1.0)
            with set_module_args(args):
                self.get_vm_mock.return_value.qemu.return_value.sendkey.put.return_value = None
                self.module.main()

        assert time_sleep_mock.call_count == 1
