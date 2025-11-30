# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import MagicMock, patch, call

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
    name="existing.vm.local",
    vmid=None,
    keys_send=None,
    string_send=None,
    delay=0.0,
    **kwargs
):
    args = {
        "api_host": "host",
        "api_user": "user",
        "api_password": "password",
        "name": name,
        "vmid": vmid,
        "keys_send": keys_send,
        "string_send": string_send,
        "delay": delay,
    }
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
        self.get_node_mock = patch.object(
            proxmox_utils.ProxmoxAnsible, "get_node"
        ).start()
        self.get_vm_mock = patch.object(proxmox_utils.ProxmoxAnsible, "get_vm").start()
        self.get_vmid_mock = patch.object(
            proxmox_utils.ProxmoxAnsible, "get_vmid"
        ).start()


    def tearDown(self):
        self.get_vmid_mock.stop()
        self.get_vm_mock.stop()
        self.get_node_mock.stop()
        self.connect_mock.stop()
        super(TestProxmoxSendkeyModule, self).tearDown()

    def test_module_fail_when_required_args_missing(self):
        with self.assertRaises(AnsibleFailJson):
            args = get_module_args_sendkey()
            with set_module_args(args):
                self.module.main()

    def test_sendkey_by_keys_send(self):
        pass

    def test_sendkey_by_string_send(self):
        pass

    def test_fail_when_validate_invalid_keys(self):
        pass

    def test_sleep_key_delay(self):
        pass
