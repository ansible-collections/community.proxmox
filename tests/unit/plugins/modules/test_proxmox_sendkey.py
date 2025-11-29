# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import MagicMock, patch, call
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

module_args_base = {
    "api_host": "host",
    "api_user": "user",
    "api_password": "password",
    "vmid": 100,
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
        self.get_vmid_mock = patch.object(
            proxmox_utils.ProxmoxAnsible, "get_vmid"
        ).start()
        
        # Setup mock API
        self.proxmox_api_mock = MagicMock()
        self.sendkey_mock = MagicMock()
        self.proxmox_api_mock.nodes.return_value.qemu.return_value.sendkey = self.sendkey_mock
        
        # Mock VM data
        self.vm_data = {"node": "test-node", "vmid": 100, "name": "test-vm"}
        self.get_vm_mock.return_value = self.vm_data
        self.get_vmid_mock.return_value = 100

    def tearDown(self):
        self.get_vmid_mock.stop()
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
        with self.assertRaises(AnsibleFailJson):
            test_args = dict(**module_args_base, **module_args_keys, **module_args_string)
            with set_module_args(test_args):
                self.module.main()

    @patch.object(proxmox_sendkey.ProxmoxSendkeyAnsible, "proxmox_api")
    def test_send_keys_success(self, mock_api):
        mock_api.nodes.return_value.qemu.return_value.sendkey = self.sendkey_mock
        
        with self.assertRaises(AnsibleExitJson) as result:
            test_args = dict(**module_args_base, **module_args_keys)
            with set_module_args(test_args):
                self.module.main()
        
        # Verify the result
        self.assertTrue(result.exception.args[0]["changed"])
        self.assertEqual(result.exception.args[0]["vmid"], 100)
        self.assertEqual(result.exception.args[0]["total_keys"], ["ctrl-alt-delete", "esc"])
        self.assertEqual(result.exception.args[0]["keys_num"], 2)
        self.assertEqual(result.exception.args[0]["completed_keys_num"], 2)

    @patch.object(proxmox_sendkey.ProxmoxSendkeyAnsible, "proxmox_api")
    def test_send_string_success(self, mock_api):
        """Test successful key sending with string_send"""
        mock_api.nodes.return_value.qemu.return_value.sendkey = self.sendkey_mock
        
        with self.assertRaises(AnsibleExitJson) as result:
            test_args = dict(**module_args_base, string_send="Hi")
            with set_module_args(test_args):
                self.module.main()
        
        # Verify the result
        self.assertTrue(result.exception.args[0]["changed"])
        self.assertEqual(result.exception.args[0]["vmid"], 100)
        # "Hi" should be converted to ["shift-h", "i"]
        expected_keys = ["shift-h", "i"]
        self.assertEqual(result.exception.args[0]["total_keys"], expected_keys)
        self.assertEqual(result.exception.args[0]["keys_num"], 2)

    @patch.object(proxmox_sendkey.ProxmoxSendkeyAnsible, "proxmox_api")
    def test_send_keys_with_name(self, mock_api):
        """Test key sending using VM name instead of vmid"""
        mock_api.nodes.return_value.qemu.return_value.sendkey = self.sendkey_mock
        
        with self.assertRaises(AnsibleExitJson) as result:
            test_args = {
                "api_host": "host",
                "api_user": "user", 
                "api_password": "password",
                "name": "test-vm",
                "keys_send": ["ret"]
            }
            with set_module_args(test_args):
                self.module.main()
        
        # Verify get_vmid was called with the name
        self.get_vmid_mock.assert_called_once_with("test-vm")
        self.assertTrue(result.exception.args[0]["changed"])

    @patch.object(proxmox_sendkey.ProxmoxSendkeyAnsible, "proxmox_api")
    @patch("time.sleep")
    def test_send_keys_with_delay(self, mock_sleep, mock_api):
        mock_api.nodes.return_value.qemu.return_value.sendkey = self.sendkey_mock
        
        with self.assertRaises(AnsibleExitJson):
            test_args = dict(**module_args_base, keys_send=["a", "b"], delay=1.0)
            with set_module_args(test_args):
                self.module.main()
        
        # Verify sleep was called with correct delay
        mock_sleep.assert_has_calls([call(1.0), call(1.0)])

    def test_string_to_keys_conversion(self):
        module = MagicMock()
        sendkey_module = proxmox_sendkey.ProxmoxSendkeyAnsible(module)
        
        # Test lowercase
        result = sendkey_module.string_to_keys("abc")
        self.assertEqual(result, ["a", "b", "c"])
        
        # Test uppercase (should use shift)
        result = sendkey_module.string_to_keys("ABC")
        self.assertEqual(result, ["shift-a", "shift-b", "shift-c"])
        
        # Test mixed case and symbols
        result = sendkey_module.string_to_keys("A1!")
        self.assertEqual(result, ["shift-a", "1", "shift-1"])
        
        # Test space and newline
        result = sendkey_module.string_to_keys(" \n")
        self.assertEqual(result, ["spc", "ret"])

    def test_string_to_keys_invalid_character(self):
        module = MagicMock()
        sendkey_module = proxmox_sendkey.ProxmoxSendkeyAnsible(module)
        
        with self.assertRaises(Exception) as context:
            sendkey_module.string_to_keys("€")  # Euro symbol not in CHAR_MAP
        
        self.assertIn("Unknown key character", str(context.exception))

    def test_validate_keys_valid(self):
        module = MagicMock()
        sendkey_module = proxmox_sendkey.ProxmoxSendkeyAnsible(module)
        
        # Should not raise exception
        sendkey_module.validate_keys("ctrl-alt-delete")
        sendkey_module.validate_keys("ret")
        sendkey_module.validate_keys("shift-a")

    def test_validate_keys_invalid(self):
        module = MagicMock()
        sendkey_module = proxmox_sendkey.ProxmoxSendkeyAnsible(module)
        
        with self.assertRaises(Exception) as context:
            sendkey_module.validate_keys("invalid-key")
        
        self.assertIn("Key is not correct", str(context.exception))

    @patch.object(proxmox_sendkey.ProxmoxSendkeyAnsible, "proxmox_api")
    def test_send_keys_api_calls(self, mock_api):
        mock_api.nodes.return_value.qemu.return_value.sendkey = self.sendkey_mock
        
        module = MagicMock()
        sendkey_module = proxmox_sendkey.ProxmoxSendkeyAnsible(module)
        sendkey_module.proxmox_api = mock_api
        sendkey_module.get_vm = MagicMock(return_value=self.vm_data)
        
        keys = ["a", "b", "c"]
        sendkey_module.send_keys(100, keys, 0.0)
        
        # Verify API calls
        mock_api.nodes.assert_called_once_with("test-node")
        mock_api.nodes.return_value.qemu.assert_called_once_with(100)
        
        # Verify sendkey was called for each key
        expected_calls = [call(key="a"), call(key="b"), call(key="c")]
        self.sendkey_mock.put.assert_has_calls(expected_calls)
        
        # Verify completed keys tracking
        self.assertEqual(sendkey_module.completed_keys, ["a", "b", "c"])

    def test_char_map_completeness(self):
        char_map = proxmox_sendkey.ProxmoxSendkeyAnsible.CHAR_MAP
        
        # Test basic ASCII letters
        for c in "abcdefghijklmnopqrstuvwxyz":
            self.assertIn(c, char_map)
            self.assertIn(c.upper(), char_map)
        
        # Test digits
        for c in "0123456789":
            self.assertIn(c, char_map)
        
        # Test common symbols
        for c in " \n-=[]\\;',./":
            self.assertIn(c, char_map)
        
        # Test shifted symbols
        for c in "!@#$%^&*()_+{}|:\"<>?":
            self.assertIn(c, char_map)

    def test_all_keys_list(self):
        all_keys = proxmox_sendkey.ProxmoxSendkeyAnsible.ALL_KEYS
        
        # Test some essential keys are present
        essential_keys = [
            "shift", "ctrl", "alt", "ret", "esc", "spc",
            "a", "b", "c", "1", "2", "3",
            "f1", "f2", "f3", "home", "end", "delete"
        ]
        
        for key in essential_keys:
            self.assertIn(key, all_keys, f"Key `{key}` should be in ALL_KEYS")

    @patch.object(proxmox_sendkey.ProxmoxSendkeyAnsible, "proxmox_api")
    def test_module_with_vmid_and_name(self, mock_api):
        """Test module when both vmid and name are provided"""
        mock_api.nodes.return_value.qemu.return_value.sendkey = self.sendkey_mock
        
        with self.assertRaises(AnsibleExitJson) as result:
            test_args = {
                "api_host": "host",
                "api_user": "user",
                "api_password": "password", 
                "vmid": 100,
                "name": "test-vm",
                "keys_send": ["ret"]
            }
            with set_module_args(test_args):
                self.module.main()
        
        # Should use vmid and not call get_vmid
        self.get_vmid_mock.assert_not_called()
        self.assertEqual(result.exception.args[0]["vmid"], 100)

    @patch.object(proxmox_sendkey.ProxmoxSendkeyAnsible, "proxmox_api")
    def test_module_exception_handling(self, mock_api):
        """Test module exception handling"""
        # Mock an exception during sendkey
        mock_api.nodes.return_value.qemu.return_value.sendkey.put.side_effect = Exception("API Error")
        
        with self.assertRaises(AnsibleFailJson) as result:
            test_args = dict(**module_args_base, **module_args_keys)
            with set_module_args(test_args):
                self.module.main()
        
        self.assertIn("An error occurred", result.exception.args[0]["msg"])

    def test_get_proxmox_args(self):
        """Test get_proxmox_args function returns correct structure"""
        args = proxmox_sendkey.get_proxmox_args()
        
        expected_keys = ["vmid", "name", "keys_send", "string_send", "delay"]
        for key in expected_keys:
            self.assertIn(key, args)
        
        # Test default delay
        self.assertEqual(args["delay"]["default"], 0.0)
        
        # Test types
        self.assertEqual(args["vmid"]["type"], "int")
        self.assertEqual(args["name"]["type"], "str")
        self.assertEqual(args["keys_send"]["type"], "list")
        self.assertEqual(args["string_send"]["type"], "str")
        self.assertEqual(args["delay"]["type"], "float")

    def test_get_ansible_module(self):
        """Test get_ansible_module function returns AnsibleModule with correct specs"""
        with patch("ansible_collections.community.proxmox.plugins.modules.proxmox_sendkey.AnsibleModule") as mock_module:
            proxmox_sendkey.get_ansible_module()
            
            # Verify AnsibleModule was called
            mock_module.assert_called_once()
            
            # Get the call arguments
            call_args = mock_module.call_args[1]
            
            # Verify mutually exclusive
            self.assertIn("mutually_exclusive", call_args)
            self.assertIn(("keys_send", "string_send"), call_args["mutually_exclusive"])
            
            # Verify required_one_of
            self.assertIn("required_one_of", call_args)
            required_one_of = call_args["required_one_of"]
            self.assertIn(("keys_send", "string_send"), required_one_of)
            self.assertIn(("vmid", "name"), required_one_of)
            
            # Verify check mode support
            self.assertFalse(call_args["supports_check_mode"])
