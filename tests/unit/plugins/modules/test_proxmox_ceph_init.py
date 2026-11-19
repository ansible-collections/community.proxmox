#
# Copyright (c) 2026, (@clementdlg) <0xkrem@proton.me>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


from unittest.mock import Mock, patch

import pytest
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)

import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
from ansible_collections.community.proxmox.plugins.modules import (
    proxmox_ceph_init,
)

proxmoxer = pytest.importorskip("proxmoxer")

NODE = "pve01"

RAW_NODES = [
    {
        "type": "node",
        "status": "online",
        "id": f"node/{NODE}",
        "node": NODE,
        "maxcpu": 4,
        "maxmem": 2063962112,
        "maxdisk": 15517192192,
    },
]

RAW_CEPH_CONF = """[global]
    fsid = 11111111-2222-3333-4444-555555555555
    auth_cluster_required = cephx
    auth_service_required = cephx
    auth_client_required = cephx
    public_network = 10.0.10.0/24
    cluster_network = 10.0.20.0/24
    osd_pool_default_size = 3
    osd_pool_default_min_size = 2
    mon_allow_pool_delete = true

[client]
    keyring = /etc/pve/priv/$cluster.$name.keyring
"""

RAW_CEPH_CONF_SAME_NETWORK = """[global]
    fsid = 11111111-2222-3333-4444-555555555555
    auth_cluster_required = cephx
    auth_service_required = cephx
    auth_client_required = cephx
    public_network = 10.0.10.0/24
    cluster_network = 10.0.10.0/24
    osd_pool_default_size = 3
    osd_pool_default_min_size = 2
    mon_allow_pool_delete = true
"""

NOT_INITIALIZED_ERROR = Exception(
    "500 Internal Server Error: pveceph configuration not initialized - missing '/etc/pve/ceph.conf'"
)
OTHER_ERROR = Exception("500 Internal Server Error: ceph binary not installed")
INIT_ERROR = Exception("Ceph Nautilus required - please run 'pveceph install'")


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


def build_arg(check=False, **kwargs):
    args = {"api_user": "root@pam", "api_password": "secret", "api_host": "192.168.1.21", "node": NODE}
    args.update(kwargs)
    if check:
        args["_ansible_check_mode"] = True
    return args


class TestProxmoxCephInit(ModuleTestCase):
    def setUp(self):
        super().setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_ceph_init

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
        mock_obj.nodes.get.return_value = RAW_NODES
        self.node_mock = mock_obj.nodes.return_value
        self.ceph_conf_get = self.node_mock.ceph.cfg.raw.get
        self.init_create = self.node_mock.ceph.init.create

    def tearDown(self):
        self.connect_mock.stop()
        self.exit_json_patcher.stop()
        self.fail_json_patcher.stop()
        super().tearDown()

    def set_initialized(self, ceph_conf=RAW_CEPH_CONF):
        self.ceph_conf_get.return_value = ceph_conf

    def set_not_initialized(self):
        self.ceph_conf_get.side_effect = NOT_INITIALIZED_ERROR

    # 1. missing required argument node

    def test_missing_node_argument(self):
        with set_module_args(
            {"api_user": "root@pam", "api_password": "secret", "api_host": "192.168.1.21"}
        ), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_init.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert "missing required arguments" in result["msg"]
        assert "node" in result["msg"]

    # 2. cluster_network requires network

    def test_cluster_network_requires_network(self):
        with set_module_args(build_arg(cluster_network="10.0.20.0/24")), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_init.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert "cluster_network" in result["msg"]
        assert "network" in result["msg"]

    # 3. size / min_size out of range

    def test_size_out_of_range(self):
        for size in (0, 8):
            with set_module_args(build_arg(size=size)), pytest.raises(SystemExit) as exc_info:
                proxmox_ceph_init.main()

            result = exc_info.value.args[0]

            assert result["failed"] is True
            assert result["msg"] == f"Parameter size must be in the range 1-7, got {size}"

    def test_min_size_out_of_range(self):
        with set_module_args(build_arg(min_size=8)), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_init.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert result["msg"] == "Parameter min_size must be in the range 1-7, got 8"

    # 4. not initialized

    def test_not_initialized(self):
        self.set_not_initialized()

        with set_module_args(
            build_arg(network="10.0.10.0/24", cluster_network="10.0.20.0/24", size=3, min_size=2)
        ), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_init.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == f"Ceph cluster initialized on node {NODE}"
        self.init_create.assert_called_once_with(
            network="10.0.10.0/24", **{"cluster-network": "10.0.20.0/24"}, size=3, min_size=2
        )

    # 5. not initialized + check mode

    def test_not_initialized_check_mode(self):
        self.set_not_initialized()

        with set_module_args(build_arg(check=True, network="10.0.10.0/24")), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_init.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == f"Ceph cluster would be initialized on node {NODE}"
        self.init_create.assert_not_called()

    # 6. initialized, no drift, no parameters

    def test_initialized_no_parameters(self):
        self.set_initialized()

        with set_module_args(build_arg()), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_init.main()

        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert result["msg"] == f"Ceph cluster is already initialized on node {NODE}"
        self.init_create.assert_not_called()

    # 7. initialized, all provided parameters match

    def test_initialized_no_drift(self):
        self.set_initialized()

        with set_module_args(
            build_arg(network="10.0.10.0/24", cluster_network="10.0.20.0/24", size=3, min_size=2)
        ), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_init.main()

        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert result["msg"] == f"Ceph cluster is already initialized on node {NODE}"
        self.init_create.assert_not_called()

    # 8./9. initialized, network drift (with and without a separate cluster network)

    def test_initialized_network_drift_preserves_separate_cluster_network(self):
        self.set_initialized()

        with set_module_args(build_arg(network="10.0.30.0/24")), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_init.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == f"Ceph cluster network configuration updated on node {NODE}"
        # the separately configured cluster network must not be clobbered
        self.init_create.assert_called_once_with(network="10.0.30.0/24", **{"cluster-network": "10.0.20.0/24"})

    def test_initialized_network_drift_without_separate_cluster_network(self):
        self.set_initialized(RAW_CEPH_CONF_SAME_NETWORK)

        with set_module_args(build_arg(network="10.0.30.0/24")), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_init.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        # cluster network was set via network, both follow the new network
        self.init_create.assert_called_once_with(network="10.0.30.0/24")

    # 10. initialized, only cluster_network drift

    def test_initialized_cluster_network_drift(self):
        self.set_initialized()

        with set_module_args(build_arg(network="10.0.10.0/24", cluster_network="10.0.30.0/24")), pytest.raises(
            SystemExit
        ) as exc_info:
            proxmox_ceph_init.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        self.init_create.assert_called_once_with(network="10.0.10.0/24", **{"cluster-network": "10.0.30.0/24"})

    # 11. initialized, size drift

    def test_initialized_size_drift(self):
        self.set_initialized()

        with set_module_args(build_arg(size=2)), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_init.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert "Cannot change immutable parameter(s)" in result["msg"]
        assert "size (current: '3', desired: '2')" in result["msg"]
        self.init_create.assert_not_called()

    # 12. initialized, min_size drift

    def test_initialized_min_size_drift(self):
        self.set_initialized()

        with set_module_args(build_arg(min_size=1)), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_init.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert "min_size (current: '2', desired: '1')" in result["msg"]
        self.init_create.assert_not_called()

    # 13. immutable drift + check mode

    def test_initialized_size_drift_check_mode(self):
        self.set_initialized()

        with set_module_args(build_arg(check=True, size=2)), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_init.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert "Cannot change immutable parameter(s)" in result["msg"]
        self.init_create.assert_not_called()

    # 14. cfg/raw raises a non not-initialized error

    def test_ceph_conf_unexpected_error(self):
        self.ceph_conf_get.side_effect = OTHER_ERROR

        with set_module_args(build_arg()), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_init.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert f"Unable to retrieve Ceph configuration from node {NODE}: " in result["msg"]
        assert "ceph binary not installed" in result["msg"]
        self.init_create.assert_not_called()

    # 15. cfg/raw raises the not-initialized error + check mode

    def test_not_initialized_error_check_mode(self):
        self.set_not_initialized()

        with set_module_args(build_arg(check=True)), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_init.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == f"Ceph cluster would be initialized on node {NODE}"
        self.init_create.assert_not_called()

    # 16. POST init raises

    def test_init_fails(self):
        self.set_not_initialized()
        self.init_create.side_effect = INIT_ERROR

        with set_module_args(build_arg(network="10.0.10.0/24")), pytest.raises(SystemExit) as exc_info:
            proxmox_ceph_init.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert f"Initializing the Ceph cluster on node {NODE} failed: Ceph Nautilus required" in result["msg"]
