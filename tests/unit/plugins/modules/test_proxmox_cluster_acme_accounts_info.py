#
# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


from unittest.mock import patch

import pytest

proxmoxer = pytest.importorskip("proxmoxer")

from ansible.module_utils import basic
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)

from ansible_collections.community.proxmox.plugins.modules import proxmox_cluster_acme_accounts_info


def exit_json(*args, **kwargs):
    kwargs.setdefault("changed", False)
    raise SystemExit(kwargs)


def fail_json(*args, **kwargs):
    kwargs["failed"] = True
    raise SystemExit(kwargs)


def build_args(**overrides):
    return {
        "api_host": "host",
        "api_user": "user",
        "api_password": "password",
        **overrides,
    }


class TestProxmoxClusterAcmeAccountsInfo(ModuleTestCase):
    def setUp(self):
        super().setUp()
        self.module = proxmox_cluster_acme_accounts_info
        self.mock_module_helper = patch.multiple(
            basic.AnsibleModule,
            exit_json=exit_json,
            fail_json=fail_json,
        )
        self.mock_module_helper.start()
        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()
        mock_api = self.connect_mock.return_value
        account_attr = mock_api.cluster.return_value.acme.return_value.account
        self.account_index = account_attr.return_value

    def tearDown(self):
        self.connect_mock.stop()
        self.mock_module_helper.stop()
        super().tearDown()

    def _run_module(self, args):
        with pytest.raises(SystemExit) as exc_info, set_module_args(args):
            self.module.main()
        return exc_info.value.args[0]

    def test_list_names(self):
        self.account_index.get.return_value = [
            {"name": "staging"},
            {"name": "default"},
        ]

        result = self._run_module(build_args())

        assert result["changed"] is False
        assert result["accounts"] == ["default", "staging"]

    def test_list_empty(self):
        self.account_index.get.return_value = []

        result = self._run_module(build_args())

        assert result["accounts"] == []
