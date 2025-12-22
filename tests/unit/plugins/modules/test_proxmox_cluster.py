# -*- coding: utf-8 -*-
# Copyright (c) 2025, Florian Paul Azim Hoberg (@gyptazy) <florian.hoberg@credativ.de>
#
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type
import pytest
from unittest.mock import MagicMock, patch, Mock
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.proxmox.plugins.modules import proxmox_cluster
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import ProxmoxAnsible
from ansible_collections.community.proxmox.plugins.modules.proxmox_cluster import validate_cluster_name

from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)
import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils

proxmoxer = pytest.importorskip("proxmoxer")

SINGLE_NODE = [
    {
        'level': '',
        'online': 1,
        'nodeid': 0,
        'ip': '192.168.1.2',
        'name': 'pve',
        'id': 'node/pve',
        'type': 'node',
        'local': 1
    }
]

CLUSTER = [
    {
        'nodes': 3,
        'id': 'cluster',
        'version': 3,
        'quorate': 1,
        'name': 'devcluster',
        'type': 'cluster'
    },
    {
        'id': 'node/srv-proxmox-03',
        'online': 1,
        'ip': '192.168.1.23',
        'name': 'srv-proxmox-03',
        'level': '',
        'type': 'node',
        'local': 1,
        'nodeid': 3
    },
    {
        'nodeid': 1,
        'type': 'node',
        'local': 0,
        'level': '',
        'name': 'srv-proxmox-01',
        'ip': '192.168.1.21',
        'online': 1,
        'id': 'node/srv-proxmox-01'
    },
    {
        'nodeid': 2,
        'type': 'node',
        'local': 0,
        'name': 'srv-proxmox-02',
        'level': '',
        'online': 1,
        'ip': '192.168.1.22',
        'id': 'node/srv-proxmox-02'
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


class TestProxmoxCluster(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxCluster, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_cluster

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

    def tearDown(self):
        self.connect_mock.stop()
        self.exit_json_patcher.stop()
        self.fail_json_patcher.stop()
        super(TestProxmoxCluster, self).tearDown()

    def test_create_check_mode(self):
        mock_obj = self.connect_mock.return_value
        mock_obj.cluster.status.get.return_value = (
            SINGLE_NODE
        )
        with set_module_args({
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "192.168.1.21",
            "link0": "192.192.168.21",
            "link1": "10.10.2.1",
            "cluster_name": "devcluster",
            "state": "present",
            "_ansible_check_mode": True
        }):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_cluster.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Cluster 'devcluster' would be created (check mode)."
        assert result["cluster"] == "devcluster"

    def test_create(self):
        mock_obj = self.connect_mock.return_value
        mock_obj.cluster.status.get.return_value = (
            SINGLE_NODE
        )
        with set_module_args({
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "192.168.1.21",
            "link0": "192.192.168.21",
            "link1": "10.10.2.1",
            "cluster_name": "devcluster",
            "state": "present",
        }):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_cluster.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Cluster 'devcluster' created."
        assert result["cluster"] == "devcluster"

    def test_create_idempotent(self):
        mock_obj = self.connect_mock.return_value
        mock_obj.cluster.status.get.return_value = (
            CLUSTER
        )
        with set_module_args({
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "192.168.1.21",
            "link0": "192.192.168.21",
            "link1": "10.10.2.1",
            "cluster_name": "devcluster",
            "state": "present",
        }):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_cluster.main()

        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert result["msg"] == "Cluster 'devcluster' already present."
        assert result["cluster"] == "devcluster"

    def test_create_fail(self):
        mock_obj = self.connect_mock.return_value
        mock_obj.cluster.status.get.return_value = (
            CLUSTER
        )
        with set_module_args({
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "192.168.1.21",
            "link0": "192.192.168.21",
            "link1": "10.10.2.1",
            "cluster_name": "devcluster2",
            "state": "present",
        }):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_cluster.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert result["msg"] == 'Error creating cluster: Node is already part of a different cluster - "devcluster"!'

    def test_join_check_mode(self):
        mock_obj = self.connect_mock.return_value
        mock_obj.cluster.status.get.return_value = (
            SINGLE_NODE
        )
        with set_module_args({
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "192.168.1.22",
            "master_api_password": "secret",
            "master_ip": "192.168.1.21",
            "fingerprint": "BD:D0:A4:04:E6:05:30:74:30:E6:5A:83:78:A8:8F:F7:4C:25:71:DB:07:92:7C:A1:04:B9:CB:12:BB:3C:BE:4D",
            "state": "present",
            "_ansible_check_mode": True
        }):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_cluster.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Node would join the cluster (check mode)."

    def test_join(self):
        mock_obj = self.connect_mock.return_value
        mock_obj.cluster.status.get.return_value = (
            SINGLE_NODE
        )
        with set_module_args({
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "192.168.1.22",
            "master_api_password": "secret",
            "master_ip": "192.168.1.21",
            "fingerprint": "BD:D0:A4:04:E6:05:30:74:30:E6:5A:83:78:A8:8F:F7:4C:25:71:DB:07:92:7C:A1:04:B9:CB:12:BB:3C:BE:4D",
            "state": "present",
        }):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_cluster.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert result["msg"] == "Node joined the cluster."

    def test_join_idempotent(self):
        mock_obj = self.connect_mock.return_value
        mock_obj.cluster.status.get.return_value = (
            CLUSTER
        )
        with set_module_args({
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "192.168.1.22",
            "master_api_password": "secret",
            "master_ip": "192.168.1.21",
            "fingerprint": "BD:D0:A4:04:E6:05:30:74:30:E6:5A:83:78:A8:8F:F7:4C:25:71:DB:07:92:7C:A1:04:B9:CB:12:BB:3C:BE:4D",
            "state": "present",
        }):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_cluster.main()

        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert result["msg"] == "Node already in the cluster."

    def test_join_failed(self):
        mock_obj = self.connect_mock.return_value
        mock_obj.cluster.status.get.return_value = (
            CLUSTER
        )
        with set_module_args({
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "192.168.1.22",
            "master_api_password": "secret",
            "master_ip": "192.168.1.10",
            "fingerprint": "BD:D0:A4:04:E6:05:30:74:30:E6:5A:83:78:A8:8F:F7:4C:25:71:DB:07:92:7C:A1:04:B9:CB:12:BB:3C:BE:4D",
            "state": "present",
        }):
            with pytest.raises(SystemExit) as exc_info:
                proxmox_cluster.main()

        result = exc_info.value.args[0]

        assert result["failed"] is True
        assert result["msg"] == "Error while joining cluster: Node is already part of a cluster!"


@pytest.fixture
def module_args_join():
    return {
        "api_host": "10.10.10.76",
        "api_user": "root@pam",
        "api_password": "secret",
        "state": "present",
        "master_ip": "10.10.10.75",
        "fingerprint": "BD:D0:A4:04:E6:05:30:74:30:E6:5A:83:78:A8:8F:F7:4C:25:71:DB:07:92:7C:A1:04:B9:CB:12:BB:3C:BE:4D",
        "cluster_name": "devcluster"
    }


@pytest.fixture
def module_args_create():
    return {
        "api_host": "10.10.10.76",
        "api_user": "root@pam",
        "api_password": "secret",
        "state": "present",
        "cluster_name": "devcluster",
        "link0": "10.10.1.1",
        "link1": "10.10.2.1",
    }


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_cluster_join(mock_api, mock_init, module_args_join):
    module = MagicMock(spec=AnsibleModule)
    module.params = module_args_join
    module.check_mode = False

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance
    mock_api_instance.cluster.config.join.post.return_value = {}

    module.exit_json = lambda **kwargs: (x for x in ()).throw(SystemExit(kwargs))
    module.fail_json = lambda **kwargs: (x for x in ()).throw(SystemExit(kwargs))

    proxmox = proxmox_cluster.ProxmoxClusterAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    with pytest.raises(SystemExit) as exc:
        proxmox.cluster_join()

    result = exc.value.args[0]
    assert result["changed"] is True
    assert result["msg"] == "Node joined the cluster."

    mock_api_instance.cluster.config.join.post.assert_called_once_with(
        hostname="10.10.10.75",
        fingerprint=module_args_join["fingerprint"],
        password="secret"
    )


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_cluster_create(mock_api, mock_init, module_args_create):
    module = MagicMock(spec=AnsibleModule)
    module.params = module_args_create
    module.check_mode = False

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance
    mock_api_instance.cluster.config.nodes.get.return_value = []
    mock_api_instance.cluster.config.post.return_value = {}

    module.exit_json = lambda **kwargs: (x for x in ()).throw(SystemExit(kwargs))
    module.fail_json = lambda **kwargs: (x for x in ()).throw(SystemExit(kwargs))

    proxmox = proxmox_cluster.ProxmoxClusterAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    with pytest.raises(SystemExit) as exc:
        proxmox.cluster_create()

    result = exc.value.args[0]
    assert result["changed"] is True
    assert result["msg"] == "Cluster 'devcluster' created."
    assert result["cluster"] == "devcluster"

    expected_payload = {
        "clustername": module_args_create["cluster_name"],
        "link0": module_args_create["link0"],
        "link1": module_args_create["link1"],
    }

    mock_api_instance.cluster.config.post.assert_called_once_with(**expected_payload)


def test_validate_cluster_name_valid(module_args_create):
    module = MagicMock(spec=AnsibleModule)
    module.params = module_args_create

    validate_cluster_name(module)
