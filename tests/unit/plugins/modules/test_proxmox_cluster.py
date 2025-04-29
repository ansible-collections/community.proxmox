# -*- coding: utf-8 -*-
# Copyright (c) 2025, Florian Paul Azim Hoberg (@gyptazy) <florian.hoberg@credativ.de>
#
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

proxmoxer = pytest.importorskip("proxmoxer")

from ansible_collections.community.proxmox.plugins.modules import proxmox_cluster
from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import patch, Mock
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleExitJson,
    ModuleTestCase,
    set_module_args,
)


class TestProxmoxClusterModule(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxClusterModule, self).setUp()
        self.module = proxmox_cluster

    @patch("ansible_collections.community.proxmox.plugins.modules.proxmox_cluster.ProxmoxAPI")
    def test_create_cluster_success(self, mock_proxmox_api):
        proxmox_mock = Mock()
        mock_proxmox_api.return_value = proxmox_mock
        proxmox_mock.cluster.config.post.return_value = {}

        with set_module_args({
            "state": "present",
            "api_host": "pve01",
            "api_user": "root@pam",
            "api_password": "secret",
            "cluster_name": "testcluster"
        }):
            with pytest.raises(AnsibleExitJson) as exc_info:
                self.module.main()

            result = exc_info.value.args[0]
            assert result["changed"] is True
            assert result["msg"] == "Cluster 'testcluster' created."
            assert result["cluster"] == "testcluster"

    @patch("ansible_collections.community.proxmox.plugins.modules.proxmox_cluster.ProxmoxAPI")
    def test_join_cluster_missing_params(self, mock_proxmox_api):
        proxmox_mock = Mock()
        mock_proxmox_api.return_value = proxmox_mock

        with set_module_args({
            "state": "present",
            "api_host": "pve02",
            "api_user": "root@pam",
            "api_password": "secret",
            "cluster_name": "testcluster",
            "master_ip": "10.10.10.10",
            "fingerprint": "00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00"

        }):
            with pytest.raises(AnsibleExitJson) as exc_info:
                self.module.main()

            result = exc_info.value.args[0]
            assert result["changed"] is True
            assert result["msg"] == "Node joined the cluster."
            assert result["cluster"] == "testcluster"
