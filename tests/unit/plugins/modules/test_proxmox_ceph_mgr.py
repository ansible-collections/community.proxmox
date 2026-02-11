# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, teslamania <nicolas.vial@protonmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import Mock, patch

import pytest
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)

import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
from ansible_collections.community.proxmox.plugins.modules import (
    proxmox_ceph_mgr,
)

proxmoxer = pytest.importorskip("proxmoxer")

RAW_RESOURCES_NODES = [
    {
        "maxdisk": 15517192192,
        "maxmem": 2063962112,
        "disk": 3952242688,
        "mem": 1556987904,
        "type": "node",
        "cpu": 0.00688637481554353,
        "level": "",
        "status": "online",
        "id": "node/srv-proxmox-02",
        "uptime": 697,
        "cgroup-mode": 2,
        "maxcpu": 4,
        "node": "srv-proxmox-02",
    },
    {
        "maxmem": 2063958016,
        "maxdisk": 15517192192,
        "level": "",
        "cpu": 0.0118168389955687,
        "type": "node",
        "mem": 1854046208,
        "disk": 3955453952,
        "uptime": 697,
        "id": "node/srv-proxmox-01",
        "status": "online",
        "node": "srv-proxmox-01",
        "maxcpu": 4,
        "cgroup-mode": 2,
    },
    {
        "level": "",
        "type": "node",
        "cpu": 0.00760922925871379,
        "disk": 3907559424,
        "mem": 1550610432,
        "maxdisk": 15517192192,
        "maxmem": 2063953920,
        "maxcpu": 4,
        "node": "srv-proxmox-03",
        "cgroup-mode": 2,
        "uptime": 697,
        "id": "node/srv-proxmox-03",
        "status": "online",
    },
]

RAW_MGR = [
    {
        "ceph_version_short": "19.2.3",
        "ceph_version": "ceph version 19.2.3 \
                        (2f03f1cd83e5d40cdf1393cb64a662a8e8bb07c6) \
                        squid (stable)",
        "addr": "192.168.1.21",
        "service": 1,
        "direxists": 1,
        "state": "active",
        "host": "srv-proxmox-01",
        "name": "srv-proxmox-01",
    },
    {
        "ceph_version_short": "19.2.3",
        "ceph_version": "ceph version 19.2.3 \
                        (2f03f1cd83e5d40cdf1393cb64a662a8e8bb07c6) \
                        squid (stable)",
        "addr": "192.168.1.22",
        "service": 1,
        "direxists": 1,
        "host": "srv-proxmox-02",
        "state": "standby",
        "name": "srv-proxmox-02",
    },
]


def exit_json(*args, **kwargs):
    """function to patch over exit_json;
    package return data into an exception"""
    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise SystemExit(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json;
    package return data into an exception"""
    kwargs["failed"] = True
    raise SystemExit(kwargs)


def build_arg(node, state, check=False):
    args = {"api_user": "root@pam", "api_password": "secret", "api_host": "192.168.1.21", "node": node, "state": state}
    if check:
        args["_ansible_check_mode"] = True
    return args


class TestProxmoxCephMgr(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxCephMgr, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_ceph_mgr

        self.fail_json_patcher = patch(
            "ansible.module_utils.basic.AnsibleModule.fail_json", new=Mock(side_effect=fail_json)
        )
        self.exit_json_patcher = patch("ansible.module_utils.basic.AnsibleModule.exit_json", new=exit_json)

        self.fail_json_mock = self.fail_json_patcher.start()
        self.exit_json_patcher.start()

        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()

        mock_obj = self.connect_mock.return_value
        mock_obj.cluster.resources.get.return_value = RAW_RESOURCES_NODES
        mock_obj.nodes.return_value.ceph.mgr.get.return_value = RAW_MGR

    def tearDown(self):
        self.connect_mock.stop()
        self.exit_json_patcher.stop()
        self.fail_json_patcher.stop()
        super(TestProxmoxCephMgr, self).tearDown()

    def test_proxmox_ceph_missing_argument(self):
        with set_module_args({"api_user": "root@pam", "api_password": "secret", "api_host": "192.168.1.21"}):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mgr.main()

        result = exc_info.value.args[0]
        msg = "missing required arguments: node, state"

        assert result["failed"] is True
        assert result["msg"] == msg

    def test_add_mgr_check_mode(self):
        manager = "srv-proxmox-03"
        with set_module_args(build_arg(manager, "present", True)):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mgr.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == f"Manager {manager} would be added"
        assert result["manager"] == manager

    def test_add_mgr(self):
        manager = "srv-proxmox-03"
        with set_module_args(build_arg(manager, "present")):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mgr.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == f"Manager {manager} added"
        assert result["manager"] == manager

    def test_add_mgr_not_exist(self):
        manager = "srv-proxmox-04"
        with set_module_args(build_arg(manager, "present")):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mgr.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert result["msg"] == f"Node {manager} does not exist in the cluster"

    def test_add_mgr_already_mgr(self):
        manager = "srv-proxmox-02"
        with set_module_args(build_arg(manager, "present")):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mgr.main()

        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert result["msg"] == "Manager already exists"
        assert result["manager"] == manager

    def test_del_mgr_check_mode(self):
        manager = "srv-proxmox-02"
        with set_module_args(build_arg(manager, "absent", True)):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mgr.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == f"Manager {manager} would be deleted"
        assert result["manager"] == manager

    def test_del_mgr(self):
        manager = "srv-proxmox-02"
        with set_module_args(build_arg(manager, "absent")):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mgr.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == f"Manager {manager} deleted"
        assert result["manager"] == manager

    def test_del_mgr_not_exist(self):
        manager = "srv-proxmox-04"
        with set_module_args(build_arg(manager, "absent")):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mgr.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert result["msg"] == f"Node {manager} does not exist in the cluster"

    def test_del_mgr_already_not_mgr(self):
        manager = "srv-proxmox-03"
        with set_module_args(build_arg(manager, "absent")):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mgr.main()

        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert result["msg"] == "Manager not present"
        assert result["manager"] == manager
