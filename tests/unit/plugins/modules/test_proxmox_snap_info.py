#
# Copyright (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

import json
from unittest.mock import MagicMock, patch

import pytest
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import set_module_args

import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
from ansible_collections.community.proxmox.plugins.modules import proxmox_snap_info

proxmoxer = pytest.importorskip("proxmoxer")


def get_resources(type):
    return [{"vmid": 100, "node": "localhost", "type": "lxc", "name": "test-lxc"}]


def get_snapshots():
    return [
        {"name": "current", "description": "You are here"},
        {"name": "before-upgrade", "description": "Pre-upgrade backup", "snaptime": 1600000000},
        {"name": "after-upgrade", "description": "Post-upgrade state", "snaptime": 1600000001},
    ]


def fake_api(mocker):
    r = mocker.MagicMock()
    r.cluster.resources.get = MagicMock(side_effect=get_resources)
    r.nodes.return_value.lxc.return_value.snapshot.get = MagicMock(return_value=get_snapshots())
    return r


@patch("ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect")
def test_list_all_snapshots(connect_mock, capfd, mocker):
    with set_module_args({"api_user": "root@pam", "api_password": "secret", "api_host": "127.0.0.1", "vmid": "100"}):
        proxmox_utils.HAS_PROXMOXER = True
        connect_mock.side_effect = lambda: fake_api(mocker)

        with pytest.raises(SystemExit):
            proxmox_snap_info.main()

    out, err = capfd.readouterr()
    result = json.loads(out)

    assert not err
    assert not result.get("failed")
    assert len(result["snapshots"]) == 3
    assert result["snapshots"][1]["name"] == "before-upgrade"


@patch("ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect")
def test_get_specific_snapshot(connect_mock, capfd, mocker):
    with set_module_args(
        {
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "127.0.0.1",
            "vmid": "100",
            "snapname": "before-upgrade",
        }
    ):
        proxmox_utils.HAS_PROXMOXER = True
        connect_mock.side_effect = lambda: fake_api(mocker)

        with pytest.raises(SystemExit):
            proxmox_snap_info.main()

    out, err = capfd.readouterr()
    result = json.loads(out)

    assert not err
    assert result["snapshot"]["name"] == "before-upgrade"
    assert "snapshots" not in result


@patch("ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect")
def test_snapshot_not_found(connect_mock, capfd, mocker):
    with set_module_args(
        {
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "127.0.0.1",
            "vmid": "100",
            "snapname": "non-existent",
        }
    ):
        proxmox_utils.HAS_PROXMOXER = True
        connect_mock.side_effect = lambda: fake_api(mocker)

        with pytest.raises(SystemExit):
            proxmox_snap_info.main()

    out, err = capfd.readouterr()
    result = json.loads(out)

    assert not err
    assert result["msg"] == "Snapshot 'non-existent' not found"
    assert result["snapshots"] == []
