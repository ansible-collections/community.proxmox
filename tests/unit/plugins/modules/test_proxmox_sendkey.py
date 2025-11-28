# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
from unittest.mock import MagicMock, patch

import pytest

proxmoxer = pytest.importorskip("proxmoxer")

from ansible_collections.community.proxmox.plugins.modules import proxmox_sendkey
import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    ModuleTestCase,
    set_module_args,
)

module_args_base = {
    "api_host": "host",
    "api_user": "user",
    "api_password": "password",
    "vmid": "100",
}
module_args_keys = {
    "keys_send": ["ctrl-alt-delete", "esc"],
}
module_args_string = {
    "string_send": "Hello World!",
}


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

    def tearDown(self):
        self.get_vm_mock.stop()
        self.get_node_mock.stop()
        self.connect_mock.stop()
        super(TestProxmoxSendkeyModule, self).tearDown()

    def test_module_fail_when_required_args_missing(self):
        with self.assertRaises(AnsibleFailJson):
            with set_module_args({}):
                self.module.main()

    def test_module_fail_when_no_string_or_keys(self):
        with self.assertRaises(AnsibleFailJson):
            test_args = dict(**module_args_base)
            with set_module_args(test_args):
                self.module.main()

    def test_module_fail_when_string_and_keys_are_not_exclusive(self):
        """Test that module fails when neither keys_send nor string_send is provided"""
        with self.assertRaises(AnsibleFailJson):
            test_args = dict(**module_args_base, **module_args_keys, **module_args_string)
            with set_module_args(test_args):
                self.module.main()
