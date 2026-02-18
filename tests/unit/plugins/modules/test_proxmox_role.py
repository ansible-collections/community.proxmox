#
# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


from unittest.mock import Mock, patch

import pytest

proxmoxer = pytest.importorskip("proxmoxer")

from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)

import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
from ansible_collections.community.proxmox.plugins.modules import proxmox_role

ROLE_ID = "role-test"


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise SystemExit(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs["failed"] = True
    raise SystemExit(kwargs)


def get_module_args(roleid, privs=None, state="present"):
    return {
        "api_host": "host",
        "api_user": "user",
        "api_password": "password",
        "roleid": roleid,
        "privs": privs,
        "state": state,
    }


class TestProxmoxRoleModule(ModuleTestCase):
    def setUp(self):
        super().setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_role
        self.fail_json_patcher = patch(
            "ansible.module_utils.basic.AnsibleModule.fail_json", new=Mock(side_effect=fail_json)
        )
        self.exit_json_patcher = patch("ansible.module_utils.basic.AnsibleModule.exit_json", new=exit_json)
        self.fail_json_mock = self.fail_json_patcher.start()
        self.exit_json_patcher.start()
        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect"
        ).start()
        self.mock_get_role = patch.object(proxmox_role.ProxmoxRoleAnsible, "_get_role").start()

    def tearDown(self):
        self.connect_mock.stop()
        self.exit_json_patcher.stop()
        self.fail_json_patcher.stop()
        self.mock_get_role.stop()
        super().tearDown()

    def _run_module(self, args):
        with pytest.raises(SystemExit) as exc_info, set_module_args(args):
            self.module.main()
        return exc_info.value.args[0]

    def _check_mode_args(self, **kwargs):
        return {**get_module_args(**kwargs), "_ansible_check_mode": True}

    def test_role_present(self):
        self.mock_get_role.return_value = None
        result = self._run_module(get_module_args(roleid=ROLE_ID))
        assert result["changed"] is True
        assert result["msg"] == f"Role {ROLE_ID} successfully created"
        assert result["roleid"] == ROLE_ID

        self.mock_get_role.return_value = {}
        result = self._run_module(get_module_args(roleid=ROLE_ID))
        assert result["changed"] is False
        assert result["msg"] == f"Role {ROLE_ID} already exists with desired configuration"
        assert result["roleid"] == ROLE_ID

        self.mock_get_role.return_value = {"VM.Console": True, "VM.PowerMgmt": False}
        result = self._run_module(get_module_args(roleid=ROLE_ID))
        assert result["changed"] is False
        assert result["msg"] == f"Role {ROLE_ID} already exists with desired configuration"
        assert result["roleid"] == ROLE_ID

        self.mock_get_role.return_value = {}
        result = self._run_module(get_module_args(roleid=ROLE_ID, privs=["VM.Console"]))
        assert result["changed"] is True
        assert result["msg"] == f"Role {ROLE_ID} successfully updated"
        assert result["roleid"] == ROLE_ID

    def test_role_absent(self):
        self.mock_get_role.return_value = {}
        result = self._run_module(get_module_args(roleid=ROLE_ID, state="absent"))
        assert result["changed"] is True
        assert result["msg"] == f"Role {ROLE_ID} successfully deleted"
        assert result["roleid"] == ROLE_ID

        self.mock_get_role.return_value = None
        result = self._run_module(get_module_args(roleid=ROLE_ID, state="absent"))
        assert result["changed"] is False
        assert result["msg"] == f"Role {ROLE_ID} does not exist"
        assert result["roleid"] == ROLE_ID

    def test_role_present_check_mode(self):
        self.mock_get_role.return_value = None
        result = self._run_module(self._check_mode_args(roleid=ROLE_ID))
        assert result["changed"] is True
        assert result["msg"] == f"Role {ROLE_ID} would be created"
        assert result["roleid"] == ROLE_ID

        self.mock_get_role.return_value = {}
        result = self._run_module(self._check_mode_args(roleid=ROLE_ID))
        assert result["changed"] is False
        assert result["msg"] == f"Role {ROLE_ID} already exists with desired configuration"
        assert result["roleid"] == ROLE_ID

        self.mock_get_role.return_value = {"VM.Console": True}
        result = self._run_module(self._check_mode_args(roleid=ROLE_ID))
        assert result["changed"] is False
        assert result["msg"] == f"Role {ROLE_ID} already exists with desired configuration"
        assert result["roleid"] == ROLE_ID

        self.mock_get_role.return_value = {}
        result = self._run_module(self._check_mode_args(roleid=ROLE_ID, privs=["VM.Console"]))
        assert result["changed"] is True
        assert result["msg"] == f"Role {ROLE_ID} would be updated"
        assert result["roleid"] == ROLE_ID

    def test_role_absent_check_mode(self):
        self.mock_get_role.return_value = {}
        result = self._run_module(self._check_mode_args(roleid=ROLE_ID, state="absent"))
        assert result["changed"] is True
        assert result["msg"] == f"Role {ROLE_ID} would be deleted"
        assert result["roleid"] == ROLE_ID

        self.mock_get_role.return_value = None
        result = self._run_module(self._check_mode_args(roleid=ROLE_ID, state="absent"))
        assert result["changed"] is False
        assert result["msg"] == f"Role {ROLE_ID} does not exist"
        assert result["roleid"] == ROLE_ID
