# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, teslamania <nicolas.vial@protonmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import patch, Mock
import pytest

from ansible_collections.community.proxmox.plugins.modules import (
    proxmox_ceph_mon,
)
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)
import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils

proxmoxer = pytest.importorskip("proxmoxer")

RAW_RESOURCES_NODES = [
    {
        'maxdisk': 15517192192,
        'maxmem': 2063962112,
        'disk': 3952242688,
        'mem': 1556987904,
        'type': 'node',
        'cpu': 0.00688637481554353,
        'level': '',
        'status': 'online',
        'id': 'node/srv-proxmox-02',
        'uptime': 697,
        'cgroup-mode': 2,
        'maxcpu': 4,
        'node': 'srv-proxmox-02'
    },
    {
        'maxmem': 2063958016,
        'maxdisk': 15517192192,
        'level': '',
        'cpu': 0.0118168389955687,
        'type': 'node',
        'mem': 1854046208,
        'disk': 3955453952,
        'uptime': 697,
        'id': 'node/srv-proxmox-01',
        'status': 'online',
        'node': 'srv-proxmox-01',
        'maxcpu': 4,
        'cgroup-mode': 2
    },
    {
        'level': '',
        'type': 'node',
        'cpu': 0.00760922925871379,
        'disk': 3907559424,
        'mem': 1550610432,
        'maxdisk': 15517192192,
        'maxmem': 2063953920,
        'maxcpu': 4,
        'node': 'srv-proxmox-03',
        'cgroup-mode': 2,
        'uptime': 697,
        'id': 'node/srv-proxmox-03',
        'status': 'online'
    }
]

RAW_MON = [
    {
        'service': 1,
        'rank': 0,
        'ceph_version_short': '19.2.3',
        'ceph_version': 'ceph version 19.2.3 \
                        (2f03f1cd83e5d40cdf1393cb64a662a8e8bb07c6) \
                        squid (stable)',
        'addr': '192.168.1.21:6789/0',
        'quorum': 1,
        'name': 'srv-proxmox-01',
        'state': 'running',
        'host': 'srv-proxmox-01',
        'direxists': 1
    },
    {
        'ceph_version': 'ceph version 19.2.3 \
                        (2f03f1cd83e5d40cdf1393cb64a662a8e8bb07c6) \
                        squid (stable)',
        'addr': '192.168.1.22:6789/0',
        'ceph_version_short': '19.2.3',
        'rank': 1,
        'service': 1,
        'direxists': 1,
        'host': 'srv-proxmox-02',
        'state': 'running',
        'name': 'srv-proxmox-02',
        'quorum': 1
    }
]


def exit_json(*args, **kwargs):
    """function to patch over exit_json;
        package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise SystemExit(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json;
        package return data into an exception"""
    kwargs['failed'] = True
    raise SystemExit(kwargs)


def build_arg(node, state, check=False):
    args = {
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "192.168.1.21",
            "node": node,
            "state": state
    }
    if check:
        args["_ansible_check_mode"] = True
    return args


class TestProxmoxCephMon(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxCephMon, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_ceph_mon

        self.fail_json_patcher = patch(
            'ansible.module_utils.basic.AnsibleModule.fail_json',
            new=Mock(side_effect=fail_json)
        )
        self.exit_json_patcher = patch(
            'ansible.module_utils.basic.AnsibleModule.exit_json',
            new=exit_json)

        self.fail_json_mock = self.fail_json_patcher.start()
        self.exit_json_patcher.start()

        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()

        mock_obj = self.connect_mock.return_value
        mock_obj.cluster.resources.get.return_value = (
            RAW_RESOURCES_NODES
        )
        mock_obj.nodes.return_value.ceph.mon.get.return_value = (
            RAW_MON
        )

    def tearDown(self):
        self.connect_mock.stop()
        self.exit_json_patcher.stop()
        self.fail_json_patcher.stop()
        super(TestProxmoxCephMon, self).tearDown()

    def test_proxmox_ceph_missing_argument(self):
        with set_module_args(
            {
                "api_user": "root@pam",
                "api_password": "secret",
                "api_host": "192.168.1.21"
            }
        ):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mon.main()

        result = exc_info.value.args[0]
        msg = "missing required arguments: node, state"

        assert result["failed"] is True
        assert result["msg"] == msg

    def test_add_mon_check_mode(self):
        monitor = "srv-proxmox-03"
        with set_module_args(build_arg(monitor, "present", True)):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mon.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == f"Monitor {monitor} would be added"
        assert result["monitor"] == monitor

    def test_add_mon(self):
        monitor = "srv-proxmox-03"
        with set_module_args(build_arg(monitor, "present")):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mon.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == f"Monitor {monitor} added"
        assert result["monitor"] == monitor

    def test_add_mon_not_exist(self):
        monitor = "srv-proxmox-04"
        with set_module_args(build_arg(monitor, "present")):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mon.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert result["msg"] == f"Node {monitor} does not exist in the cluster"

    def test_add_mon_already_mon(self):
        monitor = "srv-proxmox-02"
        with set_module_args(build_arg(monitor, "present")):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mon.main()

        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert result["msg"] == "Monitor already exists"
        assert result["monitor"] == monitor

    def test_del_mon_check_mode(self):
        monitor = "srv-proxmox-02"
        with set_module_args(build_arg(monitor, "absent", True)):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mon.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == f"Monitor {monitor} would be deleted"
        assert result["monitor"] == monitor

    def test_del_mon(self):
        monitor = "srv-proxmox-02"
        with set_module_args(build_arg(monitor, "absent")):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mon.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == f"Monitor {monitor} deleted"
        assert result["monitor"] == monitor

    def test_del_mon_not_exist(self):
        monitor = "srv-proxmox-04"
        with set_module_args(build_arg(monitor, "absent")):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mon.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert result["msg"] == f"Node {monitor} does not exist in the cluster"

    def test_del_mon_already_not_mon(self):
        monitor = "srv-proxmox-03"
        with set_module_args(build_arg(monitor, "absent")):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_mon.main()

        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert result["msg"] == "Monitor not present"
        assert result["monitor"] == monitor
