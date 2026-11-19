#
# Copyright (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


import json
from unittest.mock import MagicMock, patch

import pytest

proxmoxer = pytest.importorskip("proxmoxer")

from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import set_module_args

import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
from ansible_collections.community.proxmox.plugins.modules import proxmox_snap


def get_resources(**_):
    return [
        {
            "diskwrite": 0,
            "vmid": 100,
            "node": "localhost",
            "id": "lxc/100",
            "maxdisk": 10000,
            "template": 0,
            "disk": 10000,
            "uptime": 10000,
            "maxmem": 10000,
            "maxcpu": 1,
            "netin": 10000,
            "type": "lxc",
            "netout": 10000,
            "mem": 10000,
            "diskread": 10000,
            "cpu": 0.01,
            "name": "test-lxc",
            "status": "running",
        }
    ]


def fake_api(mocker):
    r = mocker.MagicMock()
    r.cluster.resources.get = MagicMock(side_effect=get_resources)
    return r


def test_proxmox_snap_without_argument(capfd):
    with set_module_args({}), pytest.raises(SystemExit):
        proxmox_snap.main()

    out, err = capfd.readouterr()
    assert not err
    assert json.loads(out)["failed"]


@patch("ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect")
def test_create_snapshot_check_mode(connect_mock, capfd, mocker):
    with set_module_args(
        {
            "hostname": "test-lxc",
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "127.0.0.1",
            "state": "present",
            "snapname": "test",
            "timeout": "1",
            "force": True,
            "_ansible_check_mode": True,
        }
    ):
        proxmox_utils.HAS_PROXMOXER = True
        connect_mock.side_effect = lambda: fake_api(mocker)
        with pytest.raises(SystemExit):
            proxmox_snap.main()

    out, err = capfd.readouterr()
    assert not err
    output = json.loads(out)
    assert output["changed"]
    assert output["msg"] == "Snapshot test would be created"


@patch("ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect")
def test_remove_snapshot_check_mode(connect_mock, capfd, mocker):
    with set_module_args(
        {
            "hostname": "test-lxc",
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "127.0.0.1",
            "state": "absent",
            "snapname": "test",
            "timeout": "1",
            "force": True,
            "_ansible_check_mode": True,
        }
    ):
        proxmox_utils.HAS_PROXMOXER = True
        connect_mock.side_effect = lambda: fake_api(mocker)
        with pytest.raises(SystemExit):
            proxmox_snap.main()

    out, err = capfd.readouterr()
    assert not err
    assert not json.loads(out)["changed"]


@patch("ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect")
def test_rollback_snapshot_check_mode(connect_mock, capfd, mocker):
    with set_module_args(
        {
            "hostname": "test-lxc",
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "127.0.0.1",
            "state": "rollback",
            "snapname": "test",
            "timeout": "1",
            "force": True,
            "_ansible_check_mode": True,
        }
    ):
        proxmox_utils.HAS_PROXMOXER = True
        connect_mock.side_effect = lambda: fake_api(mocker)
        with pytest.raises(SystemExit):
            proxmox_snap.main()

    out, err = capfd.readouterr()
    assert not err
    output = json.loads(out)
    assert not output["changed"]
    assert output["msg"] == "Snapshot test does not exist"


def fake_api_with_snapshot(mocker):
    r = fake_api(mocker)
    snapshot = r.nodes.return_value.lxc.return_value.snapshot
    snapshot.get.return_value = [{"name": "test", "snaptime": 1700000000}, {"name": "current"}]
    return r


@patch("ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect")
def test_remove_existing_snapshot_check_mode(connect_mock, capfd, mocker):
    api = fake_api_with_snapshot(mocker)
    with set_module_args(
        {
            "hostname": "test-lxc",
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "127.0.0.1",
            "state": "absent",
            "snapname": "test",
            "timeout": "1",
            "_ansible_check_mode": True,
        }
    ):
        proxmox_utils.HAS_PROXMOXER = True
        connect_mock.side_effect = lambda: api
        with pytest.raises(SystemExit):
            proxmox_snap.main()

    out, err = capfd.readouterr()
    assert not err
    output = json.loads(out)
    assert output["changed"]
    assert output["msg"] == "Snapshot test would be removed"
    api.nodes.return_value.lxc.return_value.snapshot.delete.assert_not_called()


@patch("ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect")
def test_create_existing_snapshot_check_mode(connect_mock, capfd, mocker):
    api = fake_api_with_snapshot(mocker)
    with set_module_args(
        {
            "hostname": "test-lxc",
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "127.0.0.1",
            "state": "present",
            "snapname": "test",
            "timeout": "1",
            "_ansible_check_mode": True,
        }
    ):
        proxmox_utils.HAS_PROXMOXER = True
        connect_mock.side_effect = lambda: api
        with pytest.raises(SystemExit):
            proxmox_snap.main()

    out, err = capfd.readouterr()
    assert not err
    output = json.loads(out)
    assert not output["changed"]
    assert output["msg"] == "Snapshot test is already present"
    api.nodes.return_value.lxc.return_value.snapshot.post.assert_not_called()
