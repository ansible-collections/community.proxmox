# -*- coding: utf-8 -*-
# Copyright (c) 2025, Florian Paul Azim Hoberg (@gyptazy) <florian.hoberg@credativ.de>
#
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
from unittest.mock import patch

import pytest

proxmoxer = pytest.importorskip('proxmoxer')

from ansible_collections.community.proxmox.plugins.modules import proxmox_cluster_join_info
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import set_module_args
import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils


JOIN_INFO = {
    "config_digest": "111418c98000acfda99059d29cd89123583020a0",
    "nodelist": [
        {
            "name": "pmx01",
            "nodeid": "1",
            "pve_addr": "10.10.10.75",
            "pve_fp": "95:AC:F2:21:0C:09:A8:5F:06:9A:BD:0D:FB:68:8B:32:4A:26:36:DE:29:23:88:D2:49:C5:BB:91:AB:39:6E:48",
            "quorum_votes": "1",
            "ring0_addr": "10.10.10.75"
        },
        {
            "name": "pmxcdev02",
            "nodeid": "2",
            "pve_addr": "10.10.10.76",
            "pve_fp": "BD:D0:A4:04:E6:05:30:74:30:E6:5A:83:78:A8:8F:F7:4C:25:71:DB:07:92:7C:A1:04:B9:CB:12:BB:3C:BE:4D",
            "quorum_votes": "1",
            "ring0_addr": "10.10.10.76"
        }
    ],
    "preferred_node": "pmxcdev02",
    "totem": {
        "cluster_name": "devcluster",
        "config_version": "2",
        "interface": {
            "0": {
                "linknumber": "0"
            }
        },
        "ip_version": "ipv4-6",
        "link_mode": "passive",
        "secauth": "on",
        "version": "2"
    }
}


@patch('ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect')
def test_without_required_parameters(connect_mock, capfd):
    with set_module_args({}):
        with pytest.raises(SystemExit):
            proxmox_cluster_join_info.main()
    out, err = capfd.readouterr()
    assert not err
    assert json.loads(out)["failed"]


def mock_api_join_info(mocker):
    cluster = mocker.MagicMock()
    config = mocker.MagicMock()
    join = mocker.MagicMock()
    join.get.return_value = JOIN_INFO
    config.join = join
    cluster.config = config

    api = mocker.MagicMock()
    api.cluster = cluster
    return api


@patch('ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect')
def test_cluster_join_success(connect_mock, capfd, mocker):
    with set_module_args({
        "api_host": "proxmoxhost",
        "api_user": "root@pam",
        "api_password": "supersecret"
    }):
        connect_mock.side_effect = lambda: mock_api_join_info(mocker)
        proxmox_utils.HAS_PROXMOXER = True

        with pytest.raises(SystemExit):
            proxmox_cluster_join_info.main()

    out, err = capfd.readouterr()
    assert not err
    result = json.loads(out)
    assert result['cluster_join'] == JOIN_INFO
    assert result['changed'] is False


@patch('ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect')
def test_cluster_join_node_not_in_cluster(connect_mock, capfd, mocker):
    with set_module_args({
        "api_host": "proxmoxhost",
        "api_user": "root@pam",
        "api_password": "supersecret"
    }):
        def raise_resource_exception():
            raise proxmoxer.core.ResourceException("Not in cluster")

        cluster = mocker.MagicMock()
        config = mocker.MagicMock()
        join = mocker.MagicMock()
        join.get.side_effect = raise_resource_exception
        config.join = join
        cluster.config = config

        api = mocker.MagicMock()
        api.cluster = cluster
        connect_mock.return_value = api

        proxmox_utils.HAS_PROXMOXER = True

        with pytest.raises(SystemExit):
            proxmox_cluster_join_info.main()

    out, err = capfd.readouterr()
    assert not err
    result = json.loads(out)
    assert result['failed']
    assert 'join information' in result['msg']
    assert 'cluster_join' not in result
