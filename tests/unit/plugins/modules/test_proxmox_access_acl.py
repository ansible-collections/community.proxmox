#
# Copyright (c) 2025, Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest.mock import patch

import pytest

proxmoxer = pytest.importorskip("proxmoxer")

from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleExitJson,
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
    "ugid": "a01mako@pam",
}

API = {
    "api_user": "root@pam",
    "api_password": "secret",
    "api_host": "127.0.0.1",
}


class TestProxmoxAccessACLModule(ModuleTestCase):
    def setUp(self):
        super().setUp()
        proxmox_utils.HAS_PROXMOXER = True

        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect"
        ).start()
        self.mock_get = patch.object(proxmox_access_acl.ProxmoxAccessACLAnsible, "_get_acls").start()
        self.mock_put = patch.object(proxmox_access_acl.ProxmoxAccessACLAnsible, "_put_acl").start()

        self.mock_get.return_value = [ACE]

    def tearDown(self):
        self.connect_mock.stop()
        self.mock_get.stop()
        self.mock_put.stop()
        super().tearDown()

    def test_present_ace_already_exists(self):
        with set_module_args({**API, "state": "present", **ACE}), pytest.raises(AnsibleExitJson) as exc_info:
            proxmox_access_acl.main()

        result = exc_info.value.args[0]
        assert result["changed"] is False
        assert self.mock_get.call_count == 1
        assert self.mock_put.call_count == 0

    def test_present_ace_does_not_exist(self):
        with set_module_args({**API, "state": "present", **ACE, "path": "/vms/101"}), pytest.raises(
            AnsibleExitJson
        ) as exc_info:
            proxmox_access_acl.main()

        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert self.mock_get.call_count == 2  # noqa: PLR2004
        assert self.mock_put.call_count == 1

    def test_absent_ace_exists(self):
        with set_module_args({**API, "state": "absent", **ACE}), pytest.raises(AnsibleExitJson) as exc_info:
            proxmox_access_acl.main()

        result = exc_info.value.args[0]
        assert result["changed"] is True
        assert self.mock_get.call_count == 2 # noqa: PLR2004
        assert self.mock_put.call_count == 1

    def test_absent_ace_does_not_exist(self):
        with set_module_args({**API, "state": "absent", **ACE, "path": "/vms/101"}), pytest.raises(
            AnsibleExitJson
        ) as exc_info:
            proxmox_access_acl.main()

        result = exc_info.value.args[0]
        assert result["changed"] is False
        assert self.mock_get.call_count == 1
        assert self.mock_put.call_count == 0
