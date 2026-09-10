#
# Copyright (c) 2025, Ryan Smith <ryan.smith220@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

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
