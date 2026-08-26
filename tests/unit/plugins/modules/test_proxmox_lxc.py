#
# Copyright (c) 2025, Ryan Smith <ryan.smith220@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
import unittest
from unittest.mock import MagicMock, patch

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.compat.version import LooseVersion

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import ProxmoxAnsible
from ansible_collections.community.proxmox.plugins.modules import proxmox


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "version", return_value=LooseVersion("4.0"))
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
@patch.object(ProxmoxAnsible, "module", create=True)
def test_mount_formatting(mock_api, *_):
    """Test the process_mount_keys method correctly formats mounts."""
    lxc_ansible = proxmox.ProxmoxLxcAnsible(MagicMock(spec=AnsibleModule))
    mount_volumes = [
        {
            "host_path": "/mnt/dir",
            "mountpoint": "mnt/dir",
            "id": "mp0",
            "storage": None,
            "volume": None,
            "size": None,
            "options": None,
        }
    ]
    mounts = lxc_ansible.process_mount_keys(100, "my-node", None, mount_volumes)
    assert mounts == {"mp0": "/mnt/dir,mp=mnt/dir"}


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "version", return_value=LooseVersion("4.0"))
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
@patch.object(ProxmoxAnsible, "module", create=True)
def test_device_string_generation(mock_api, *_):
    """Test that build_device correctly formats a device string"""
    lxc_ansible = proxmox.ProxmoxLxcAnsible(MagicMock(spec=AnsibleModule))
    lxc_ansible.module.fail_json.side_effect = SystemExit
    device_entry = {
        "id": "dev0",
        "path": "/dev/render0",
        "deny_write": True,
        "uid": 0,
        "gid": 0,
        "mode": "060",
    }

    device = "/dev/render0,deny-write=1,uid=0,gid=0,mode=060"
    assert lxc_ansible.build_device(device_entry) == {"dev0": device}


class TestProcessDeviceKeys(unittest.TestCase):
    @patch.object(ProxmoxAnsible, "__init__", return_value=None)
    @patch.object(ProxmoxAnsible, "version", return_value=LooseVersion("4.0"))
    @patch.object(ProxmoxAnsible, "proxmox_api", create=True)
    @patch.object(ProxmoxAnsible, "module", create=True)
    def test_keys_processed_correctly(self, mock_api, *_):
        """Verify that given proper arguments, process_device_keys correctly builds device entries"""
        lxc_ansible = proxmox.ProxmoxLxcAnsible(MagicMock(spec=AnsibleModule))
        lxc_ansible.module.fail_json.side_effect = SystemExit

        devices = [
            {
                "id": "dev0",
                "path": "/dev/render0",
                "deny_write": False,
                "uid": 100,
                "gid": 200,
                "mode": "070",
            },
            {
                "id": "dev1",
                "path": "/dev/video0",
                "uid": 300,
            },
            {
                "id": "dev2",
                "path": "/dev/video1",
                "gid": 400,
                "mode": "060",
            },
        ]

        result = lxc_ansible.process_device_keys(devices)
        assert result == {
            "dev0": "/dev/render0,deny-write=0,uid=100,gid=200,mode=070",
            "dev1": "/dev/video0,uid=300",
            "dev2": "/dev/video1,gid=400,mode=060",
        }

    @patch.object(ProxmoxAnsible, "__init__", return_value=None)
    @patch.object(ProxmoxAnsible, "version", return_value=LooseVersion("4.0"))
    @patch.object(ProxmoxAnsible, "proxmox_api", create=True)
    @patch.object(ProxmoxAnsible, "module", create=True)
    def test_fails_on_empty_missing_path(self, mock_module, *_):
        """Test that process_device_keys fails if a device is listed without a path"""
        lxc_ansible = proxmox.ProxmoxLxcAnsible(MagicMock(spec=AnsibleModule))
        lxc_ansible.module.fail_json.side_effect = SystemExit

        # Missing path
        self.assertRaises(SystemExit, lxc_ansible.process_device_keys, [{"id": "dev0"}])

        # Empty path
        self.assertRaises(SystemExit, lxc_ansible.process_device_keys, [{"id": "dev0", "path": ""}])

    @patch.object(ProxmoxAnsible, "__init__", return_value=None)
    @patch.object(ProxmoxAnsible, "version", return_value=LooseVersion("4.0"))
    @patch.object(ProxmoxAnsible, "proxmox_api", create=True)
    @patch.object(ProxmoxAnsible, "module", create=True)
    def test_device_id_validation(self, mock_api, *_):
        """Test that process_device_keys correctly validates device ID format"""
        lxc_ansible = proxmox.ProxmoxLxcAnsible(MagicMock(spec=AnsibleModule))
        lxc_ansible.module.fail_json.side_effect = SystemExit

        # This should work fine and not raise an exception
        device_keys = lxc_ansible.process_device_keys(
            [
                {"id": "dev0", "path": "/dev/render0"},
                {"id": "dev1", "path": "/dev/video0"},
            ]
        )
        assert device_keys == {"dev0": "/dev/render0", "dev1": "/dev/video0"}

        # Anything that's not "dev#" for a device ID should raise an exception
        self.assertRaises(
            SystemExit,
            lxc_ansible.process_device_keys,
            [
                {"id": "notadev", "path": "/dev/render0"},
            ],
        )

    @patch.object(ProxmoxAnsible, "__init__", return_value=None)
    @patch.object(ProxmoxAnsible, "version", return_value=LooseVersion("4.0"))
    @patch.object(ProxmoxAnsible, "proxmox_api", create=True)
    @patch.object(ProxmoxAnsible, "module", create=True)
    def test_device_uniqueness_validation(self, mock_api, *_):
        """Test that process_device_keys does not allow duplicate device IDs"""
        lxc_ansible = proxmox.ProxmoxLxcAnsible(MagicMock(spec=AnsibleModule))
        lxc_ansible.module.fail_json.side_effect = SystemExit

        self.assertRaises(
            SystemExit,
            lxc_ansible.process_device_keys,
            [
                {"id": "dev0", "path": "/dev/render0"},
                {"id": "dev0", "path": "/dev/video0"},
            ],
        )
