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


def fake_vm():
    return {"vmid": "100", "node": "pve", "name": "test-vm", "status": "running"}


def fake_api(mocker):
    r = mocker.MagicMock()
    sendkey_mock = MagicMock()
    r.nodes.return_value.qemu.return_value.sendkey = sendkey_mock
    return r


class TestProxmoxSendkeyModule(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxSendkeyModule, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_sendkey
        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect"
        ).start()
        self.get_vm_mock = patch.object(proxmox_utils.ProxmoxAnsible, "get_vm").start()
        self.get_vmid_mock = patch.object(
            proxmox_utils.ProxmoxAnsible, "get_vmid"
        ).start()

    def tearDown(self):
        self.get_vmid_mock.stop()
        self.get_vm_mock.stop()
        self.connect_mock.stop()
        super(TestProxmoxSendkeyModule, self).tearDown()

    def test_module_fail_when_required_args_missing(self):
        """Test that module fails when required arguments are missing"""
        with self.assertRaises(AnsibleFailJson):
            with set_module_args({}):
                self.module.main()

    def test_module_fail_when_no_vm_identifier(self):
        """Test that module fails when neither vmid nor name is provided"""
        with self.assertRaises(AnsibleFailJson):
            with set_module_args({
                "api_host": "host",
                "api_user": "user",
                "api_password": "password",
                "keys_send": ["ctrl-alt-delete"]
            }):
                self.module.main()

    def test_module_fail_when_no_keys_or_string(self):
        """Test that module fails when neither keys_send nor string_send is provided"""
        with self.assertRaises(AnsibleFailJson):
            with set_module_args({
                "api_host": "host",
                "api_user": "user",
                "api_password": "password",
                "vmid": "100"
            }):
                self.module.main()

    @patch('ansible_collections.community.proxmox.plugins.modules.proxmox_sendkey.ProxmoxSendkeyAnsible.send_keys')
    def test_send_keys_with_vmid(self, send_keys_mock, capfd):
        """Test sending keys using vmid"""
        with set_module_args({
            "api_host": "host",
            "api_user": "user",
            "api_password": "password",
            "vmid": "100",
            "keys_send": ["ctrl-alt-delete"]
        }):
            self.get_vm_mock.return_value = fake_vm()
            
            with pytest.raises(SystemExit) as exc_info:
                self.module.main()

        out, err = capfd.readouterr()
        assert not err
        result = json.loads(out)
        assert result["changed"] is True
        assert result["vmid"] == "100"
        assert result["keys"] == ["ctrl-alt-delete"]
        assert result["keys_num"] == 1
        assert result["completed_keys_num"] == 0  # send_keys_mockなのでcompletedは0
        assert send_keys_mock.called

    @patch('ansible_collections.community.proxmox.plugins.modules.proxmox_sendkey.ProxmoxSendkeyAnsible.send_keys')
    def test_send_keys_with_name(self, send_keys_mock, capfd):
        """Test sending keys using VM name"""
        with set_module_args({
            "api_host": "host",
            "api_user": "user",
            "api_password": "password",
            "name": "test-vm",
            "keys_send": ["ret"]
        }):
            self.get_vmid_mock.return_value = "100"
            self.get_vm_mock.return_value = fake_vm()
            
            with pytest.raises(SystemExit) as exc_info:
                self.module.main()

        out, err = capfd.readouterr()
        assert not err
        result = json.loads(out)
        assert result["changed"] is True
        assert result["vmid"] == "100"
        assert result["keys"] == ["ret"]
        assert result["keys_num"] == 1
        assert result["completed_keys_num"] == 0  # send_keys_mockなのでcompletedは0
        assert self.get_vmid_mock.called

    @patch('ansible_collections.community.proxmox.plugins.modules.proxmox_sendkey.ProxmoxSendkeyAnsible.send_keys')
    def test_send_string_conversion(self, send_keys_mock, capfd):
        """Test string to keys conversion"""
        with set_module_args({
            "api_host": "host",
            "api_user": "user",
            "api_password": "password",
            "vmid": "100",
            "string_send": "Hello\n"
        }):
            self.get_vm_mock.return_value = fake_vm()
            
            with pytest.raises(SystemExit) as exc_info:
                self.module.main()

        out, err = capfd.readouterr()
        assert not err
        result = json.loads(out)
        assert result["changed"] is True
        # Check that string was converted to keys
        expected_keys = ["shift-h", "e", "l", "l", "o", "ret"]
        assert result["keys"] == expected_keys
        assert result["keys_num"] == 6
        assert result["completed_keys_num"] == 0  # send_keys_mockなのでcompletedは0

    @patch('ansible_collections.community.proxmox.plugins.modules.proxmox_sendkey.ProxmoxSendkeyAnsible.send_keys')
    def test_key_delay_parameter(self, send_keys_mock, capfd):
        """Test key_delay parameter is passed correctly"""
        with set_module_args({
            "api_host": "host",
            "api_user": "user",
            "api_password": "password",
            "vmid": "100",
            "keys_send": ["a", "b"],
            "key_delay": 2
        }):
            self.get_vm_mock.return_value = fake_vm()
            
            with pytest.raises(SystemExit) as exc_info:
                self.module.main()

        out, err = capfd.readouterr()
        assert not err
        result = json.loads(out)
        assert result["changed"] is True
        assert result["keys"] == ["a", "b"]
        assert result["keys_num"] == 2
        assert result["completed_keys_num"] == 0  # send_keys_mockなのでcompletedは0
        # Verify send_keys was called with correct delay
        send_keys_mock.assert_called_once_with("100", ["a", "b"], 2)

    def test_string_to_keys_conversion(self):
        """Test the string_to_keys method directly"""
        module = self.module.get_ansible_module()
        with patch.object(proxmox_utils.ProxmoxAnsible, '_connect'):
            sendkey_ansible = self.module.ProxmoxSendkeyAnsible(module)
        
        # Test basic conversion
        result = sendkey_ansible.string_to_keys("AB")
        expected = ["shift-a", "shift-b"]
        assert result == expected
        
        # Test mixed case with symbols
        result = sendkey_ansible.string_to_keys("A1!")
        expected = ["shift-a", "1", "shift-1"]
        assert result == expected
        
        # Test newline
        result = sendkey_ansible.string_to_keys("\n")
        expected = ["ret"]
        assert result == expected

    def test_validate_keys_valid(self):
        """Test validate_keys with valid keys"""
        module = self.module.get_ansible_module()
        with patch.object(proxmox_utils.ProxmoxAnsible, '_connect'):
            sendkey_ansible = self.module.ProxmoxSendkeyAnsible(module)
        
        # Should not raise exception for valid keys
        sendkey_ansible.validate_keys("ctrl-alt-delete")
        sendkey_ansible.validate_keys("ret")
        sendkey_ansible.validate_keys("shift-a")

    def test_validate_keys_invalid(self):
        """Test validate_keys with invalid keys"""
        module = self.module.get_ansible_module()
        with patch.object(proxmox_utils.ProxmoxAnsible, '_connect'):
            sendkey_ansible = self.module.ProxmoxSendkeyAnsible(module)
        
        # Should raise exception for invalid keys
        with pytest.raises(Exception, match="Key is not correct"):
            sendkey_ansible.validate_keys("invalid-key")

    @patch('time.sleep')
    def test_send_keys_with_delay(self, sleep_mock, mocker):
        """Test send_keys method with delay"""
        module = self.module.get_ansible_module()
        with patch.object(proxmox_utils.ProxmoxAnsible, '_connect'):
            sendkey_ansible = self.module.ProxmoxSendkeyAnsible(module)
        
        # Mock the API
        sendkey_ansible.proxmox_api = fake_api(mocker)
        sendkey_ansible.get_vm = MagicMock(return_value=fake_vm())
        
        # Test with delay
        sendkey_ansible.send_keys("100", ["a", "b"], 1)
        
        # Verify sleep was called for each key except potentially the last
        assert sleep_mock.call_count == 2

    def test_send_keys_without_delay(self, mocker):
        """Test send_keys method without delay"""
        module = self.module.get_ansible_module()
        with patch.object(proxmox_utils.ProxmoxAnsible, '_connect'):
            sendkey_ansible = self.module.ProxmoxSendkeyAnsible(module)
        
        # Mock the API
        api_mock = fake_api(mocker)
        sendkey_ansible.proxmox_api = api_mock
        sendkey_ansible.get_vm = MagicMock(return_value=fake_vm())
        
        # Test without delay
        with patch('time.sleep') as sleep_mock:
            sendkey_ansible.send_keys("100", ["a", "b"], 0)
            # Sleep should not be called when delay is 0
            sleep_mock.assert_not_called()

    def test_token_authentication(self, capfd):
        """Test module with token authentication"""
        with set_module_args({
            "api_host": "host",
            "api_token_id": "root@pam!mytoken",
            "api_token_secret": "secret",
            "vmid": "100",
            "keys_send": ["esc"]
        }):
            self.get_vm_mock.return_value = fake_vm()
            
            with patch('ansible_collections.community.proxmox.plugins.modules.proxmox_sendkey.ProxmoxSendkeyAnsible.send_keys'):
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

        out, err = capfd.readouterr()
        assert not err
        result = json.loads(out)
        assert result["changed"] is True

    def test_special_characters_conversion(self):
        """Test conversion of special characters"""
        module = self.module.get_ansible_module()
        with patch.object(proxmox_utils.ProxmoxAnsible, '_connect'):
            sendkey_ansible = self.module.ProxmoxSendkeyAnsible(module)
        
        # Test various special characters
        test_cases = {
            "!": [["shift", "1"]],
            "@": [["shift", "2"]],
            "#": [["shift", "3"]],
            "$": [["shift", "4"]],
            "%": [["shift", "5"]],
            "^": [["shift", "6"]],
            "&": [["shift", "7"]],
            "*": [["shift", "8"]],
            "(": [["shift", "9"]],
            ")": [["shift", "0"]],
            "_": [["shift", "minus"]],
            "+": [["shift", "equal"]],
            "{": [["shift", "bracket_left"]],
            "}": [["shift", "bracket_right"]],
            "|": [["shift", "backslash"]],
            ":": [["shift", "semicolon"]],
            "\"": [["shift", "apostrophe"]],
            "<": [["shift", "comma"]],
            ">": [["shift", "dot"]],
            "?": [["shift", "slash"]],
        }
        
        for char, expected in test_cases.items():
            result = sendkey_ansible.string_to_keys(char)
            assert result == expected, f"Failed for character '{char}'"

    def test_multiple_keys_sequence(self, capfd):
        """Test sending multiple keys in sequence"""
        with set_module_args({
            "api_host": "host",
            "api_user": "user",
            "api_password": "password",
            "vmid": "100",
            "keys_send": ["ctrl-alt-delete", "ret", "esc"]
        }):
            self.get_vm_mock.return_value = fake_vm()
            
            with patch('ansible_collections.community.proxmox.plugins.modules.proxmox_sendkey.ProxmoxSendkeyAnsible.send_keys') as send_keys_mock:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

        out, err = capfd.readouterr()
        assert not err
        result = json.loads(out)
        assert result["changed"] is True
        assert result["keys"] == ["ctrl-alt-delete", "ret", "esc"]
        assert result["keys_num"] == 3
        assert result["completed_keys_num"] == 0  # send_keys_mockなのでcompletedは0
        send_keys_mock.assert_called_once_with("100", ["ctrl-alt-delete", "ret", "esc"], 0.0)

    def test_module_exception_handling(self, capfd):
        """Test module exception handling"""
        with set_module_args({
            "api_host": "host",
            "api_user": "user",
            "api_password": "password",
            "vmid": "100",
            "keys_send": ["ret"]
        }):
            # Mock an exception during execution
            with patch('ansible_collections.community.proxmox.plugins.modules.proxmox_sendkey.ProxmoxSendkeyAnsible.run') as run_mock:
                run_mock.side_effect = Exception("Test error")
                
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

        out, err = capfd.readouterr()
        assert not err
        result = json.loads(out)
        assert result["failed"] is True
        assert "An error occurred: Test error" in result["msg"]
