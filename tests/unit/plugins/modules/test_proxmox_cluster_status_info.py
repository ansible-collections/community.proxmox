# -*- coding: utf-8 -*-
# Copyright (c) 2025, Michael Dombek (@michaelwdombek)
#
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
from unittest.mock import patch

import pytest

proxmoxer = pytest.importorskip('proxmoxer')

from ansible_collections.community.proxmox.plugins.modules import proxmox_cluster_status_info
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import set_module_args
import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils


CLUSTER_STATUS = [
    {
        "id": "cluster",
        "name": "testcluster",
        "nodes": 3,
        "quorate": True,
        "type": "cluster",
        "version": 5
    },
    {
        "id": "node/node1",
        "ip": "192.168.1.10",
        "level": "c",
        "local": True,
        "name": "node1",
        "nodeid": 1,
        "online": True,
        "type": "node"
    },
    {
        "id": "node/node2",
        "ip": "192.168.1.11",
        "level": "c",
        "local": False,
        "name": "node2",
        "nodeid": 2,
        "online": True,
        "type": "node"
    },
    {
        "id": "node/node3",
        "ip": "192.168.1.12",
        "level": "",
        "local": False,
        "name": "node3",
        "nodeid": 3,
        "online": False,
        "type": "node"
    }
]


@patch('ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect')
def test_without_required_parameters(connect_mock, capfd):
    with set_module_args({}):
        with pytest.raises(SystemExit):
            proxmox_cluster_status_info.main()
    out, err = capfd.readouterr()
    assert not err
    assert json.loads(out)["failed"]


def mock_api_cluster_status(mocker):
    # Mock returns raw Proxmox API response with integers for booleans
    raw_response = [
        {
            "id": "cluster",
            "name": "testcluster",
            "nodes": 3,
            "quorate": 1,
            "type": "cluster",
            "version": 5
        },
        {
            "id": "node/node1",
            "ip": "192.168.1.10",
            "level": "c",
            "local": 1,
            "name": "node1",
            "nodeid": 1,
            "online": 1,
            "type": "node"
        },
        {
            "id": "node/node2",
            "ip": "192.168.1.11",
            "level": "c",
            "local": 0,
            "name": "node2",
            "nodeid": 2,
            "online": 1,
            "type": "node"
        },
        {
            "id": "node/node3",
            "ip": "192.168.1.12",
            "level": "",
            "local": 0,
            "name": "node3",
            "nodeid": 3,
            "online": 0,
            "type": "node"
        }
    ]

    cluster = mocker.MagicMock()
    status = mocker.MagicMock()
    status.get.return_value = raw_response
    cluster.status = status

    api = mocker.MagicMock()
    api.cluster = cluster
    return api


@patch('ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect')
def test_cluster_status_success(connect_mock, capfd, mocker):
    with set_module_args({
        "api_host": "proxmoxhost",
        "api_user": "root@pam",
        "api_password": "supersecret"
    }):
        connect_mock.side_effect = lambda: mock_api_cluster_status(mocker)
        proxmox_utils.HAS_PROXMOXER = True

        with pytest.raises(SystemExit):
            proxmox_cluster_status_info.main()

    out, err = capfd.readouterr()
    assert not err
    result = json.loads(out)
    assert result['cluster_status'] == CLUSTER_STATUS
    assert result['changed'] is False


@patch('ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect')
def test_cluster_status_failure(connect_mock, capfd, mocker):
    with set_module_args({
        "api_host": "proxmoxhost",
        "api_user": "root@pam",
        "api_password": "supersecret"
    }):
        def raise_resource_exception():
            raise proxmoxer.core.ResourceException("Cluster not configured")

        cluster = mocker.MagicMock()
        status = mocker.MagicMock()
        status.get.side_effect = raise_resource_exception
        cluster.status = status

        api = mocker.MagicMock()
        api.cluster = cluster
        connect_mock.return_value = api

        proxmox_utils.HAS_PROXMOXER = True

        with pytest.raises(SystemExit):
            proxmox_cluster_status_info.main()

    out, err = capfd.readouterr()
    assert not err
    result = json.loads(out)
    assert result['failed']
    assert 'Failed to retrieve cluster status' in result['msg']
    assert 'cluster_status' not in result
