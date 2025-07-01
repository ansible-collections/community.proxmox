# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import patch

import pytest

proxmoxer = pytest.importorskip("proxmoxer")

from ansible_collections.community.proxmox.plugins.modules import proxmox_kvm
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    ModuleTestCase,
    set_module_args,
)
import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
from ansible_collections.community.proxmox.plugins.modules import proxmox_access_acl

ACE = {
    "path": "/vms/100",
    "propagate": 1,
    "roleid": "PVEVMUser",
    "type": "user",
    "ugid": "a01mako@pam"
}

API = {
    "api_user": "root@pam",
    "api_password": "secret",
    "api_host": "127.0.0.1",
}


def return_get_api():
    return [ACE]


class TestProxmoxAccessACLModule(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxAccessACLModule, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_kvm
        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect"
        ).start()
        self.mock_get = patch.object(proxmox_access_acl.ProxmoxAccessACLAnsible, "_get").start()
        self.mock_put = patch.object(proxmox_access_acl.ProxmoxAccessACLAnsible, "_put").start()

        self.mock_get.side_effect = return_get_api

    def tearDown(self):
        self.connect_mock.stop()
        super(TestProxmoxAccessACLModule, self).tearDown()

    def test_module_present_missing_args(self):
        with set_module_args(
            {
                **API,
                "state": "present",
                "path": "/vms/100",
                "roleid": "PVEVMUser",
            }
        ):
            with pytest.raises(AnsibleFailJson) as exc_info:
                proxmox_access_acl.main()

        result = exc_info.value.args[0]
        assert result["failed"] is True
        assert result["missing_parameters"] == frozenset({'ugid', 'type'})
        assert result["changed"] is False, result
        assert self.mock_get.call_count == 0
        assert self.mock_put.call_count == 0

    def test_module_present_exists(self):
        with set_module_args(
            {
                **API,
                "state": "present",
                **ACE,
            }
        ):
            with pytest.raises(AnsibleExitJson) as exc_info:
                proxmox_access_acl.main()

        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert self.mock_get.call_count == 1
        assert self.mock_put.call_count == 0

    def test_module_present_missing(self):

        with set_module_args(
            {
                **API,
                "state": "present",
                **ACE,
                "path": "/vms/101"
            }
        ):
            with pytest.raises(AnsibleExitJson) as exc_info:
                proxmox_access_acl.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert self.mock_get.call_count == 2
        assert self.mock_put.call_count == 1

    def test_module_absent_exists(self):
        with set_module_args(
            {
                **API,
                "state": "absent",
                **ACE,
            }
        ):
            with pytest.raises(AnsibleExitJson) as exc_info:
                proxmox_access_acl.main()

        result = exc_info.value.args[0]

        assert result["changed"] is True
        assert self.mock_get.call_count == 2
        assert self.mock_put.call_count == 1

    def test_module_absent_missing(self):
        with set_module_args(
            {
                **API,
                "state": "absent",
                **ACE,
                "path": "/vms/101"
            }
        ):
            with pytest.raises(AnsibleExitJson) as exc_info:
                proxmox_access_acl.main()

        result = exc_info.value.args[0]

        assert result["changed"] is False
        assert self.mock_get.call_count == 1
        assert self.mock_put.call_count == 0
