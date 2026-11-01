#
# Copyright (c) 2025, Ryan Smith <ryan.smith220@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
import unittest
from unittest.mock import MagicMock, patch

import pytest
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


@pytest.mark.parametrize("mode", ["0060", "060", "666", "0666", "07777", "0888"])
def test_device_string_generation(lxc_ansible, mode):
    """Test that build_device correctly formats a device string"""
    lxc_ansible.module.fail_json.side_effect = SystemExit
    device_entry = {
        "id": "dev0",
        "path": "/dev/render0",
        "deny_write": True,
        "uid": 0,
        "gid": 0,
        "mode": mode,
    }

    device = f"/dev/render0,deny-write=1,uid=0,gid=0,mode={mode}"
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
                "mode": "0070",
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
                "mode": "0060",
            },
        ]

        result = lxc_ansible.process_device_keys(devices)
        assert result == {
            "dev0": "/dev/render0,deny-write=0,uid=100,gid=200,mode=0070",
            "dev1": "/dev/video0,uid=300",
            "dev2": "/dev/video1,gid=400,mode=0060",
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


@pytest.fixture
def lxc_ansible():
    instance = proxmox.ProxmoxLxcAnsible.__new__(proxmox.ProxmoxLxcAnsible)
    instance.VZ_TYPE = "lxc"
    instance.module = MagicMock(spec=AnsibleModule)
    instance.proxmox_api = MagicMock()
    return instance


@pytest.mark.parametrize(
    ("current", "requested", "expected"),
    [
        ({}, {"hostname": "my-lxc"}, {"hostname": "my-lxc"}),
        ({}, {"tags": ["foo"]}, {"tags": "foo"}),
        ({"tags": "old"}, {"tags": ["foo", "bar"]}, {"tags": "foo;bar"}),
        ({"tags": "foo"}, {"tags": []}, {"tags": ""}),
        ({"tags": "foo"}, {"tags": None, "hostname": "my-lxc"}, {"hostname": "my-lxc"}),
        (
            {"tags": "bar;foo", "hostname": "old"},
            {"tags": ["foo", "bar"], "hostname": "my-lxc"},
            {"tags": "foo;bar", "hostname": "my-lxc"},
        ),
    ],
)
def test_update_lxc_payload(lxc_ansible, current, requested, expected):
    config = lxc_ansible.proxmox_api.nodes.return_value.lxc.return_value.config
    config.get.return_value = current

    lxc_ansible.update_lxc_instance(1003, "example", **requested)

    lxc_ansible.proxmox_api.nodes.assert_called_once_with("example")
    lxc_ansible.proxmox_api.nodes.return_value.lxc.assert_called_with(1003)
    config.put.assert_called_once_with(**expected)


@pytest.mark.parametrize(("current", "tags"), [("bar;foo", ["foo", "bar"]), ("", [])])
def test_update_lxc_tags_unchanged(lxc_ansible, current, tags):
    config = lxc_ansible.proxmox_api.nodes.return_value.lxc.return_value.config
    config.get.return_value = {"tags": current}
    lxc_ansible.module.exit_json.side_effect = SystemExit

    with pytest.raises(SystemExit):
        lxc_ansible.update_lxc_instance(1003, "example", tags=tags)

    lxc_ansible.module.exit_json.assert_called_once_with(
        changed=False, vmid=1003, msg="Container config is already up to date."
    )
    config.put.assert_not_called()


def _present_params(**overrides):
    params = {"clone": None, "ostemplate": "local:vztmpl/debian.tar.zst", "timeout": 30}
    params.update(overrides)
    return params


def test_present_force_removes_existing_container_before_create(lxc_ansible):
    lxc_ansible.params = _present_params()
    lxc_ansible.get_lxc_resource = MagicMock(return_value={"id": "lxc/100", "node": "node1", "name": "ct1"})
    lxc_ansible.content_check = MagicMock(return_value=True)
    calls = MagicMock()
    lxc_ansible.remove_lxc_instance = calls.remove
    lxc_ansible.new_lxc_instance = calls.create

    lxc_ansible.lxc_present(100, "ct1", "node1", update=True, force=True)

    assert [c[0] for c in calls.mock_calls] == ["remove", "create"]
    calls.remove.assert_called_once_with(
        100, "node1", timeout=30, purge=False, destroy_unreferenced_disks=False, force=True
    )
    lxc_ansible.content_check.assert_called_once_with("node1", "local:vztmpl/debian.tar.zst", "local")


def test_present_force_creates_missing_container_without_remove(lxc_ansible):
    lxc_ansible.params = _present_params()
    lxc_ansible.get_lxc_resource = MagicMock(side_effect=LookupError)
    lxc_ansible.remove_lxc_instance = MagicMock()
    lxc_ansible.new_lxc_instance = MagicMock()

    lxc_ansible.lxc_present(100, "ct1", "node1", update=True, force=True)

    lxc_ansible.remove_lxc_instance.assert_not_called()
    lxc_ansible.new_lxc_instance.assert_called_once()


def test_present_force_keeps_container_when_ostemplate_is_missing(lxc_ansible):
    lxc_ansible.params = _present_params()
    lxc_ansible.get_lxc_resource = MagicMock(return_value={"id": "lxc/100", "node": "node1", "name": "ct1"})
    lxc_ansible.content_check = MagicMock(return_value=False)
    lxc_ansible.module.fail_json.side_effect = SystemExit
    lxc_ansible.remove_lxc_instance = MagicMock()

    with pytest.raises(SystemExit):
        lxc_ansible.lxc_present(100, "ct1", "node1", update=True, force=True)

    lxc_ansible.remove_lxc_instance.assert_not_called()


@pytest.mark.parametrize(
    ("params", "update", "force"),
    [
        (_present_params(), False, False),
        (_present_params(clone=200, ostemplate=None), False, True),
    ],
)
def test_present_does_not_remove_existing_container(lxc_ansible, params, update, force):
    lxc_ansible.params = params
    lxc_ansible.get_lxc_resource = MagicMock(return_value={"id": "lxc/100", "node": "node1", "name": "ct1"})
    lxc_ansible.module.exit_json.side_effect = SystemExit
    lxc_ansible.remove_lxc_instance = MagicMock()
    lxc_ansible.new_lxc_instance = MagicMock()

    try:
        lxc_ansible.lxc_present(100, "ct1", "node1", update=update, force=force)
    except SystemExit:
        pass

    lxc_ansible.remove_lxc_instance.assert_not_called()
