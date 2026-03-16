#
# Copyright (c) 2026, teslamania <nicolas.vial@protonmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


from unittest.mock import Mock, patch

import pytest
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)

import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
from ansible_collections.community.proxmox.plugins.modules import (
    proxmox_ceph_pool,
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

RAW_POOL = [
    {
        "pg_num": 128,
        "bytes_used": 0,
        "crush_rule": "0",
        "pool_name": "test",
        "min_size": 2,
        "pool": "20",
        "target_size_ratio": None,
        "application_metadata": {"rbd": {}},
        "pg_autoscale_mode": "warn",
        "size": 3,
        "autoscale_status": {
            "pg_num_target": 128,
            "raw_used": 0,
            "bulk": False,
            "effective_target_ratio": 0,
            "raw_used_rate": 3,
            "bias": 1,
            "pool_name": "test",
            "target_bytes": 0,
            "pg_num_final": 32,
            "pg_num_ideal": 0,
            "subtree_capacity": 51527024640,
            "pg_autoscale_mode": "warn",
            "would_adjust": False,
            "crush_root_id": -1,
            "capacity_ratio": 0,
            "actual_capacity_ratio": 0,
            "pool_id": 20,
            "target_ratio": 0,
            "actual_raw_used": 0,
            "logical_used": 0,
        },
        "type": "replicated",
        "percent_used": 0,
        "pg_num_final": 32,
        "crush_rule_name": "replicated_rule",
        "target_size": None,
        "pg_num_min": None,
    }
]

RAW_POOL_TEST = {
    "id": 20,
    "pgp_num": 128,
    "min_size": 2,
    "hashpspool": "1",
    "name": "test",
    "nodelete": "0",
    "fast_read": "0",
    "pg_num": 128,
    "crush_rule": "replicated_rule",
    "use_gmt_hitset": "1",
    "size": 3,
    "target_size": None,
    "pg_num_min": None,
    "nodeep-scrub": "0",
    "nopgchange": "0",
    "nosizechange": "0",
    "pg_autoscale_mode": "warn",
    "target_size_ratio": None,
    "write_fadvise_dontneed": "0",
    "noscrub": "0",
}

RAW_TASK = {"status": "stopped", "exitstatus": "OK"}


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


def build_arg(state, name, check=False):
    args = {
        "api_user": "root@pam",
        "api_password": "secret",
        "api_host": "192.168.1.21",
        "node": "srv-proxmox-01",
        "name": name,
        "state": state,
    }
    if check:
        args["_ansible_check_mode"] = True
    return args


class TestProxmoxCephPool(ModuleTestCase):
    def setUp(self):
        super().setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_ceph_pool

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
        mock_obj.nodes.return_value.ceph.pool.get.return_value = RAW_POOL
        mock_obj.nodes.return_value.ceph.pool.return_value.status.get.return_value = RAW_POOL_TEST
        mock_obj.nodes.return_value.tasks.return_value.status.get.return_value = RAW_TASK

    def tearDown(self):
        self.connect_mock.stop()
        self.exit_json_patcher.stop()
        self.fail_json_patcher.stop()
        super().tearDown()

    def test_add_pool_check_mode(self):
        with set_module_args(build_arg("present", "test2", True)), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_pool.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Ceph pool test2 would be added."

    def test_add_pool(self):
        with set_module_args(build_arg("present", "test2")), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_pool.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Ceph pool test2 added."

    def test_add_pool_idempotent(self):
        with set_module_args(build_arg("present", "test")), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_pool.main()
        result = exc_info.value.args[0]
        assert result["changed"] is False
        assert result["msg"] == "Ceph pool test already exists."

    def test_edit_pool_check_mode(self):
        args = build_arg("present", "test", True)
        args["pg_autoscale_mode"] = "off"
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_pool.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Ceph pool test would be updated."

    def test_edit_pool(self):
        args = build_arg("present", "test")
        args["pg_autoscale_mode"] = "off"
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_pool.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Ceph pool test updated."

    def test_del_pool_check_mode(self):
        args = build_arg("absent", "test", True)
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_pool.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Ceph pool test would be deleted."

    def test_del_pool(self):
        args = build_arg("absent", "test")
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_pool.main()
        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert result["msg"] == "Ceph pool test deleted."

    def test_del_pool_not_present(self):
        args = build_arg("absent", "test2")
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_pool.main()
        result = exc_info.value.args[0]
        assert result["changed"] is False
        assert result["msg"] == "Ceph pool test2 not present."
