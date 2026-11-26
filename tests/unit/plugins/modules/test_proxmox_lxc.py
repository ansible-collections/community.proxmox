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
    ("overrides", "error"),
    [
        ({"disk": "bad volume"}, ValueError),
        ({"disk_volume": {"storage": "local-lvm", "volume": "vm-100-disk-9", "size": 8}}, SystemExit),
        ({"mounts": {"mp0": "bad volume"}}, ValueError),
        ({"mount_volumes": [{"id": "mp0", "mountpoint": "/mnt/data"}]}, ValueError),
        ({"mount_devices": [{"id": "notadev", "path": "/dev/null"}]}, SystemExit),
        ({"tags": ["bad!tag"]}, SystemExit),
    ],
)
def test_present_force_keeps_container_when_input_is_invalid(lxc_ansible, overrides, error):
    lxc_ansible.params = _present_params(**overrides)
    lxc_ansible.get_lxc_resource = MagicMock(return_value={"id": "lxc/100", "node": "node1", "name": "ct1"})
    lxc_ansible.content_check = MagicMock(return_value=True)
    lxc_ansible.get_storage_content = MagicMock(return_value=[])
    lxc_ansible.handle_api_timeout = MagicMock()
    lxc_ansible.module.fail_json.side_effect = SystemExit

    with pytest.raises(error):
        lxc_ansible.lxc_present(100, "ct1", "node1", update=True, force=True)

    lxc_ansible.proxmox_api.nodes.return_value.lxc.delete.assert_not_called()


def test_present_force_builds_volumes_again_after_removal(lxc_ansible):
    lxc_ansible.params = _present_params(
        disk_volume={"storage": "local-lvm", "size": 8},
        mount_volumes=[{"id": "mp0", "host_path": "/srv/data", "mountpoint": "/mnt/data"}],
    )
    lxc_ansible.get_lxc_resource = MagicMock(return_value={"id": "lxc/100", "node": "node1", "name": "ct1"})
    lxc_ansible.content_check = MagicMock(return_value=True)
    lxc_ansible.handle_api_timeout = MagicMock()
    lxc_ansible.module.exit_json.side_effect = SystemExit
    lxc_api = lxc_ansible.proxmox_api.nodes.return_value.lxc

    def get_config(_path):
        if lxc_api.delete.called:
            raise LookupError("Configuration file does not exist")
        return {"rootfs": "local-lvm:vm-100-disk-0,size=8G"}

    lxc_api.return_value.get.side_effect = get_config

    with pytest.raises(SystemExit):
        lxc_ansible.lxc_present(100, "ct1", "node1", update=True, force=True)

    assert lxc_api.create.call_args[1]["rootfs"] == "local-lvm:8"
    assert lxc_api.create.call_args[1]["mp0"] == "/srv/data,mp=/mnt/data"
    lxc_api.return_value.pending.get.assert_not_called()


OLD_CONTAINER_CONFIG = [
    {"key": "memory", "value": 512},
    {"key": "description", "value": "local-lvm:vm-100-disk-2"},
    {"key": "rootfs", "value": "local-lvm:vm-100-disk-0,size=8G"},
    {
        "key": "mp0",
        "value": "local-lvm:vm-100-disk-1,mp=/mnt/data,size=4G",
        "pending": "mp=/mnt/data,volume=local-lvm:vm-100-disk-3",
    },
    {"key": "unused0", "value": "local-lvm:vm-100-disk-20"},
]


@pytest.mark.parametrize(
    ("overrides", "volids"),
    [
        ({"disk": "local-lvm:vm-100-disk-0,size=8G"}, "local-lvm:vm-100-disk-0"),
        ({"disk_volume": {"storage": "local-lvm", "volume": "vm-100-disk-0", "size": 8}}, "local-lvm:vm-100-disk-0"),
        ({"mounts": {"mp0": "local-lvm:vm-100-disk-1,mp=/mnt/data,size=4G"}}, "local-lvm:vm-100-disk-1"),
        (
            {"mount_volumes": [{"id": "mp0", "storage": "local-lvm", "volume": "vm-100-disk-1", "size": 4}]},
            "local-lvm:vm-100-disk-1",
        ),
        (
            {"mount_volumes": [{"id": "mp0", "storage": "local-lvm", "volume": "vm-100-disk-20", "size": 4}]},
            "local-lvm:vm-100-disk-20",
        ),
        (
            {"mount_volumes": [{"id": "mp0", "storage": "local-lvm", "volume": "vm-100-disk-3", "size": 4}]},
            "local-lvm:vm-100-disk-3",
        ),
        (
            {
                "disk_volume": {"storage": "local-lvm", "volume": "vm-100-disk-0", "size": 8},
                "mount_volumes": [{"id": "mp0", "storage": "local-lvm", "volume": "vm-100-disk-1", "size": 4}],
            },
            "local-lvm:vm-100-disk-0, local-lvm:vm-100-disk-1",
        ),
    ],
)
def test_present_force_keeps_container_when_volume_belongs_to_it(lxc_ansible, overrides, volids):
    lxc_ansible.params = _present_params(**overrides)
    lxc_ansible.get_lxc_resource = MagicMock(return_value={"id": "lxc/100", "node": "node1", "name": "ct1"})
    lxc_ansible.content_check = MagicMock(return_value=True)
    lxc_ansible.get_storage_content = MagicMock(return_value=[{"volid": volid} for volid in volids.split(", ")])
    lxc_ansible.handle_api_timeout = MagicMock()
    lxc_ansible.module.fail_json.side_effect = SystemExit
    lxc_api = lxc_ansible.proxmox_api.nodes.return_value.lxc
    lxc_api.return_value.pending.get.return_value = OLD_CONTAINER_CONFIG

    with pytest.raises(SystemExit):
        lxc_ansible.lxc_present(100, "ct1", "node1", update=True, force=True)

    lxc_api.delete.assert_not_called()
    lxc_ansible.module.fail_json.assert_called_once_with(
        vmid=100, msg=f"VM 100 was not removed, because the forced removal would also delete {volids}."
    )


@pytest.mark.parametrize(("storage", "volume"), [("local-lvm", "vm-100-disk-2"), ("tank", "vm-100-disk-1")])
def test_present_force_reuses_volume_that_container_does_not_use(lxc_ansible, storage, volume):
    lxc_ansible.params = _present_params(mount_volumes=[{"id": "mp0", "storage": storage, "volume": volume, "size": 4}])
    lxc_ansible.get_lxc_resource = MagicMock(return_value={"id": "lxc/100", "node": "node1", "name": "ct1"})
    lxc_ansible.content_check = MagicMock(return_value=True)
    lxc_ansible.get_storage_content = MagicMock(return_value=[{"volid": f"{storage}:{volume}"}])
    lxc_ansible.handle_api_timeout = MagicMock()
    lxc_ansible.module.exit_json.side_effect = SystemExit
    lxc_api = lxc_ansible.proxmox_api.nodes.return_value.lxc
    lxc_api.return_value.pending.get.return_value = OLD_CONTAINER_CONFIG

    with pytest.raises(SystemExit):
        lxc_ansible.lxc_present(100, "ct1", "node1", update=True, force=True)

    lxc_ansible.module.fail_json.assert_not_called()
    lxc_api.delete.assert_called_once_with(100, force=1)
    assert lxc_api.create.call_args[1]["mp0"] == f"{storage}:{volume},size=4G"


def test_present_force_removes_container_on_requested_node(lxc_ansible):
    lxc_ansible.params = _present_params(disk_volume={"storage": "local-lvm", "volume": "vm-100-disk-2", "size": 8})
    lxc_ansible.get_lxc_resource = MagicMock(return_value={"id": "lxc/100", "node": "node2", "name": "ct1"})
    lxc_ansible.content_check = MagicMock(return_value=True)
    lxc_ansible.get_storage_content = MagicMock(return_value=[{"volid": "local-lvm:vm-100-disk-2"}])
    lxc_ansible.remove_lxc_instance = MagicMock()
    lxc_ansible.new_lxc_instance = MagicMock()

    lxc_ansible.lxc_present(100, "ct1", "node1", update=True, force=True)

    lxc_ansible.proxmox_api.nodes.assert_called_once_with("node1")
    assert lxc_ansible.remove_lxc_instance.call_args[0] == (100, "node1")


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


def test_lxc_stopped_force_unmounts_on_container_node(lxc_ansible):
    """A mounted container is unmounted on its node, and not shut down afterwards."""
    lxc_ansible.get_lxc_resource = MagicMock(return_value={"id": "lxc/100", "name": "my-lxc", "node": "pve1"})
    lxc_ansible.get_lxc_status = MagicMock(return_value="mounted")
    lxc_ansible.handle_api_timeout = MagicMock()
    lxc_ansible.module.exit_json.side_effect = SystemExit

    with pytest.raises(SystemExit):
        lxc_ansible.lxc_stopped(None, "my-lxc", None, 30, True)

    lxc_ansible.proxmox_api.nodes.assert_called_once_with("pve1")
    status = lxc_ansible.proxmox_api.nodes.return_value.lxc.return_value.status
    status.unmount.post.assert_called_once_with()
    status.shutdown.post.assert_not_called()
    lxc_ansible.module.exit_json.assert_called_once_with(changed=True, vmid="100", msg="VM my-lxc (100) unmounted.")


NET0 = "name=eth0,bridge=vmbr0,ip=dhcp,type=veth"
NET0_HWADDR = "hwaddr=BC:24:11:AA:BB:CC"


@pytest.mark.parametrize(
    ("current", "requested", "expected"),
    [
        (
            {"net0": f"name=eth0,bridge=vmbr0,{NET0_HWADDR},ip=dhcp,type=veth", "description": "old"},
            {"netif": {"net0": NET0}, "description": "new"},
            {"net0": f"{NET0},{NET0_HWADDR}", "description": "new"},
        ),
        (
            {"net0": f"name=eth0,bridge=vmbr0,{NET0_HWADDR},ip=dhcp,type=veth"},
            {"netif": {"net0": "name=eth0,bridge=vmbr0,ip=10.0.0.2/24,type=veth"}},
            {"net0": f"name=eth0,bridge=vmbr0,ip=10.0.0.2/24,type=veth,{NET0_HWADDR}"},
        ),
        (
            {"net0": f"name=eth0,bridge=vmbr0,{NET0_HWADDR},ip=dhcp,type=veth"},
            {"netif": {"net0": f"{NET0},hwaddr=BC:24:11:00:00:01"}},
            {"net0": f"{NET0},hwaddr=BC:24:11:00:00:01"},
        ),
        ({}, {"netif": {"net0": NET0}}, {"net0": NET0}),
    ],
)
def test_update_lxc_keeps_hwaddr(lxc_ansible, current, requested, expected):
    config = lxc_ansible.proxmox_api.nodes.return_value.lxc.return_value.config
    config.get.return_value = current

    lxc_ansible.update_lxc_instance(1003, "example", **requested)

    config.put.assert_called_once_with(**expected)


def test_update_lxc_netif_without_hwaddr_unchanged(lxc_ansible):
    config = lxc_ansible.proxmox_api.nodes.return_value.lxc.return_value.config
    config.get.return_value = {"net0": f"name=eth0,bridge=vmbr0,{NET0_HWADDR},ip=dhcp,type=veth"}
    lxc_ansible.module.exit_json.side_effect = SystemExit

    with pytest.raises(SystemExit):
        lxc_ansible.update_lxc_instance(1003, "example", netif={"net0": NET0})

    config.put.assert_not_called()
