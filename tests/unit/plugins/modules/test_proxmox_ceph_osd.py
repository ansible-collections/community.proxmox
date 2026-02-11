#
# Copyright (c) 2025, teslamania <nicolas.vial@protonmail.com>
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
    proxmox_ceph_osd,
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

RAW_DISK_LIST = [
    {
        "type": "unknown",
        "used": "BIOS boot",
        "health": "OK",
        "vendor": "QEMU    ",
        "size": 34359738368,
        "model": "QEMU_HARDDISK",
        "wwn": "unknown",
        "osdid-list": None,
        "devpath": "/dev/sda",
        "serial": "drive-scsi0",
        "gpt": 1,
        "wearout": "N/A",
        "osdid": -1,
        "by_id_link": "/dev/disk/by-id/scsi-0QEMU_QEMU_HARDDISK_drive-scsi0",
        "rpm": -1,
    },
    {
        "by_id_link": "/dev/disk/by-id/scsi-0QEMU_QEMU_HARDDISK_drive-scsi1",
        "osdid": -1,
        "wearout": "N/A",
        "gpt": 0,
        "rpm": -1,
        "vendor": "QEMU    ",
        "health": "OK",
        "type": "unknown",
        "devpath": "/dev/sdb",
        "osdid-list": None,
        "serial": "drive-scsi1",
        "size": 17179869184,
        "model": "QEMU_HARDDISK",
        "wwn": "unknown",
    },
    {
        "rpm": -1,
        "gpt": 0,
        "bluestore": 1,
        "wearout": "N/A",
        "osdencrypted": 0,
        "osdid": "0",
        "by_id_link": "/dev/disk/by-id/scsi-0QEMU_QEMU_HARDDISK_drive-scsi2",
        "wwn": "unknown",
        "model": "QEMU_HARDDISK",
        "size": 17179869184,
        "devpath": "/dev/sdc",
        "osdid-list": ["0"],
        "serial": "drive-scsi2",
        "used": "LVM",
        "type": "unknown",
        "vendor": "QEMU    ",
        "health": "OK",
    },
]

RAW_OSD = {
    "root": {
        "leaf": 0,
        "children": [
            {
                "pgs": 0,
                "name": "default",
                "leaf": 0,
                "id": "-1",
                "type": "root",
                "children": [
                    {
                        "leaf": 0,
                        "type": "host",
                        "id": "-5",
                        "name": "srv-proxmox-02",
                        "version": "19.2.3",
                        "pgs": 0,
                        "reweight": -1,
                    },
                    {
                        "type": "host",
                        "id": "-7",
                        "leaf": 0,
                        "name": "srv-proxmox-03",
                        "version": "19.2.3",
                        "pgs": 0,
                        "reweight": -1,
                        "children": [
                            {
                                "status": "down",
                                "device_class": "hdd",
                                "pgs": 0,
                                "host": "srv-proxmox-03",
                                "leaf": 1,
                                "blfsdev": "/dev/dm-5",
                                "crush_weight": 0.015594482421875,
                                "commit_latency_ms": 0,
                                "ceph_version_short": "19.2.3",
                                "type": "osd",
                                "apply_latency_ms": 0,
                                "percent_used": 0,
                                "osdtype": "bluestore",
                                "dbdev": None,
                                "id": "1",
                                "ceph_version": "ceph version 19.2.3 \
                                    (2f03f1cd83e5d40cdf1393cb64a662a8e8bb07c6) \
                                    squid (stable)",
                                "in": 0,
                                "name": "osd.1",
                                "reweight": 0,
                                "total_space": 1024,
                                "bytes_used": 0,
                                "waldev": None,
                            }
                        ],
                    },
                    {
                        "name": "srv-proxmox-01",
                        "id": "-3",
                        "type": "host",
                        "leaf": 0,
                        "pgs": 0,
                        "version": "19.2.3",
                        "children": [
                            {
                                "host": "srv-proxmox-01",
                                "leaf": 1,
                                "blfsdev": "/dev/dm-8",
                                "status": "up",
                                "device_class": "hdd",
                                "pgs": 0,
                                "ceph_version_short": "19.2.3",
                                "type": "osd",
                                "apply_latency_ms": 0,
                                "commit_latency_ms": 0,
                                "crush_weight": 0.015594482421875,
                                "percent_used": 2.60750534188034,
                                "dbdev": None,
                                "osdtype": "bluestore",
                                "in": 1,
                                "ceph_version": "ceph version 19.2.3 \
                                    (2f03f1cd83e5d40cdf1393cb64a662a8e8bb07c6) \
                                    squid (stable)",
                                "id": "0",
                                "name": "osd.0",
                                "waldev": None,
                                "reweight": 1,
                                "total_space": 17175674880,
                                "bytes_used": 447856640,
                            }
                        ],
                        "reweight": -1,
                    },
                ],
                "reweight": -1,
            }
        ],
    },
    "flags": "sortbitwise,recovery_deletes,purged_snapdirs,pglog_hardlimit",
}


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


def build_common_arg(node, state, check=False):
    args = {"api_user": "root@pam", "api_password": "secret", "api_host": "192.168.1.21", "node": node, "state": state}
    if check:
        args["_ansible_check_mode"] = True
    return args


class TestProxmoxCephOsd(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxCephOsd, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_ceph_osd

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
        mock_obj.nodes.return_value.disks.list.get.return_value = RAW_DISK_LIST
        mock_obj.nodes.return_value.ceph.osd.get.return_value = RAW_OSD

    def tearDown(self):
        self.connect_mock.stop()
        self.exit_json_patcher.stop()
        self.fail_json_patcher.stop()
        super(TestProxmoxCephOsd, self).tearDown()

    def test_add_osd_node_not_present(self):
        args = build_common_arg("srv-proxmox-04", "present", False)
        args["dev"] = "/dev/sdb"
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert result["msg"] == "Node srv-proxmox-04 does not exist."

    def test_add_osd_disk_not_exist(self):
        args = build_common_arg("srv-proxmox-01", "present", False)
        args["dev"] = "/dev/sdd"
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert result["msg"] == "/dev/sdd does not exist on the node srv-proxmox-01."

    def test_add_osd_disk_already_used(self):
        args = build_common_arg("srv-proxmox-01", "present", False)
        args["dev"] = "/dev/sda"
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert result["msg"] == "/dev/sda is already in use by the node srv-proxmox-01."

    def test_add_osd_disk_already_osd(self):
        args = build_common_arg("srv-proxmox-01", "present", False)
        args["dev"] = "/dev/sdc"
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert result["msg"] == "/dev/sdc is already an osd."

    def test_add_osd_check_mode(self):
        args = build_common_arg("srv-proxmox-01", "present", True)
        args["dev"] = "/dev/sdb"
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Osd would be added."

    def test_add_osd(self):
        args = build_common_arg("srv-proxmox-01", "present", False)
        args["dev"] = "/dev/sdb"
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Osd added."

    def test_in_osd_not_present(self):
        args = build_common_arg("srv-proxmox-01", "in", False)
        args["osdid"] = 2
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert result["msg"] == "Osd 2 does not exist."

    def test_in_osd_already_in(self):
        args = build_common_arg("srv-proxmox-01", "in", False)
        args["osdid"] = 0
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert result["msg"] == "Osd 0 already in."

    def test_in_osd_check_mode(self):
        args = build_common_arg("srv-proxmox-03", "in", True)
        args["osdid"] = 1
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Would in osd 1."

    def test_in_osd(self):
        args = build_common_arg("srv-proxmox-03", "in", False)
        args["osdid"] = 1
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "In osd 1."

    def test_out_osd_already_out(self):
        args = build_common_arg("srv-proxmox-03", "out", False)
        args["osdid"] = 1
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert result["msg"] == "Osd 1 already out."

    def test_out_osd_check_mode(self):
        args = build_common_arg("srv-proxmox-01", "out", True)
        args["osdid"] = 0
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Would out osd 0."

    def test_out_osd(self):
        args = build_common_arg("srv-proxmox-01", "out", False)
        args["osdid"] = 0
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Out osd 0."

    def test_scrub_osd_down(self):
        args = build_common_arg("srv-proxmox-03", "scrub", False)
        args["osdid"] = 1
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert result["msg"] == "Osd 1 is not up."

    def test_scrub_osd_check_mode(self):
        args = build_common_arg("srv-proxmox-01", "scrub", True)
        args["osdid"] = 0
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Would scrub Osd 0."

    def test_scrub_osd(self):
        args = build_common_arg("srv-proxmox-01", "scrub", False)
        args["osdid"] = 0
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Scrub Osd 0."

    def test_start_osd_already_started(self):
        args = build_common_arg("srv-proxmox-01", "start", False)
        args["osdid"] = 0
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert result["msg"] == "Osd 0 already started."

    def test_start_osd_check_mode(self):
        args = build_common_arg("srv-proxmox-03", "start", True)
        args["osdid"] = 1
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Would start Osd 1."

    def test_start_osd(self):
        args = build_common_arg("srv-proxmox-03", "start", False)
        args["osdid"] = 1
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Start Osd 1."

    def test_stop_osd_already_down(self):
        args = build_common_arg("srv-proxmox-03", "stop", False)
        args["osdid"] = 1
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert result["msg"] == "Osd 1 already stopped."

    def test_stop_osd_check_mode(self):
        args = build_common_arg("srv-proxmox-01", "stop", True)
        args["osdid"] = 0
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Would stop Osd 0."

    def test_stop_osd(self):
        args = build_common_arg("srv-proxmox-01", "stop", False)
        args["osdid"] = 0
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Stop Osd 0."

    def test_restart_osd_check_mode(self):
        args = build_common_arg("srv-proxmox-01", "restart", True)
        args["osdid"] = 0
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Would restart Osd 0."

    def test_restart_osd(self):
        args = build_common_arg("srv-proxmox-01", "restart", False)
        args["osdid"] = 0
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Restart Osd 0."

    def test_del_osd_not_present(self):
        args = build_common_arg("srv-proxmox-01", "absent", False)
        args["osdid"] = 2
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert result["msg"] == "Osd 2 not present."

    def test_del_osd_still_in(self):
        args = build_common_arg("srv-proxmox-01", "absent", False)
        args["osdid"] = 0
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert result["msg"] == "Cannot delete osd 0 is in."

    def test_del_osd_check_mode(self):
        args = build_common_arg("srv-proxmox-03", "absent", True)
        args["osdid"] = 1
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Osd 1 would be deleted."

    def test_del_osd(self):
        args = build_common_arg("srv-proxmox-03", "absent", False)
        args["osdid"] = 1
        with set_module_args(args), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_osd.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Osd 1 deleted."
