# -*- coding: utf-8 -*-
# Copyright (c) 2025, Florian Paul Azim Hoberg (@gyptazy) <florian.hoberg@credativ.de>
#
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import sys
import pytest

proxmoxer = pytest.importorskip("proxmoxer")
mandatory_py_version = pytest.mark.skipif(
    sys.version_info < (2, 7),
    reason="The proxmoxer dependency requires python2.7 or higher",
)

from ansible_collections.community.proxmox.plugins.modules import proxmox_cluster
from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import patch, Mock
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleFailJson,
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
            "action": "create_cluster",
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
            "action": "join_cluster",
            "api_host": "pve02",
            "api_user": "root@pam",
            "api_password": "secret"
        }):
            with pytest.raises(AnsibleFailJson) as exc_info:
                self.module.main()

            result = exc_info.value.args[0]
            assert "requires 'master_ip' and 'fingerprint'" in result["msg"]

    @patch("ansible_collections.community.proxmox.plugins.modules.proxmox_cluster.ProxmoxAPI")
    def test_get_cluster_info_success(self, mock_proxmox_api):
        proxmox_mock = Mock()
        mock_proxmox_api.return_value = proxmox_mock
        proxmox_mock.cluster.config.join.get.return_value = {"fingerprint": "mock-fingerprint"}

        with set_module_args({
            "action": "get_cluster_info",
            "api_host": "pve01",
            "api_user": "root@pam",
            "api_password": "secret"
        }):
            with pytest.raises(AnsibleExitJson) as exc_info:
                self.module.main()

            result = exc_info.value.args[0]
            assert result["changed"] is False
            assert result["ansible_facts"]["cluster_join_info"]["fingerprint"] == "mock-fingerprint"
