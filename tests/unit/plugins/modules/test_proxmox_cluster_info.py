# -*- coding: utf-8 -*-
# Copyright (c) 2025, Florian Paul Azim Hoberg (@gyptazy) <florian.hoberg@credativ.de>
#
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

proxmoxer = pytest.importorskip("proxmoxer")

from ansible_collections.community.proxmox.plugins.modules import proxmox_cluster_info
from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import patch, Mock
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleExitJson,
    ModuleTestCase,
    set_module_args,
)


class TestProxmoxClusterModule(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxClusterModule, self).setUp()
        self.module = proxmox_cluster_info

    @patch("ansible_collections.community.proxmox.plugins.modules.proxmox_cluster_info.ProxmoxAPI")
    def test_get_cluster_info_success(self, mock_proxmox_api):
        proxmox_mock = Mock()
        mock_proxmox_api.return_value = proxmox_mock
        proxmox_mock.cluster.config.join.get.return_value = {"fingerprint": "mock-fingerprint"}

        with set_module_args({
            "api_host": "pve01",
            "api_user": "root@pam",
            "api_password": "secret"
        }):
            with pytest.raises(AnsibleExitJson) as exc_info:
                self.module.main()

            result = exc_info.value.args[0]
            assert result["changed"] is False
            assert result["ansible_facts"]["cluster_join_info"]["fingerprint"] == "mock-fingerprint"
