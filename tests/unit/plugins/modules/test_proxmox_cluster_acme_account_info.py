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

from ansible_collections.community.proxmox.plugins.modules import proxmox_cluster_acme_account_info

SAMPLE_GET = {
    "account": {
        "contact": ["mailto:example@example.com"],
        "createdAt": "2024-01-01T00:00:00Z",
        "status": "valid",
    },
    "directory": "https://acme-v02.api.letsencrypt.org/directory",
    "location": "https://acme-v02.api.letsencrypt.org/acme/acct/3198781481",
    "tos": "https://letsencrypt.org/documents/LE-SA-v1.3-September-21-2022.pdf",
}


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
        "name": "default",
        **overrides,
    }


class TestProxmoxClusterAcmeAccountInfo(ModuleTestCase):
    def setUp(self):
        super().setUp()
        self.module = proxmox_cluster_acme_account_info
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
        self.named_account = account_attr.return_value
        self.named_account.return_value = self.named_account

    def tearDown(self):
        self.connect_mock.stop()
        self.mock_module_helper.stop()
        super().tearDown()

    def _run_module(self, args):
        with pytest.raises(SystemExit) as exc_info, set_module_args(args):
            self.module.main()
        return exc_info.value.args[0]

    def test_get_one(self):
        self.named_account.get.return_value = SAMPLE_GET

        result = self._run_module(build_args(name="default"))

        assert result["changed"] is False
        assert result["name"] == "default"
        assert result["directory"] == SAMPLE_GET["directory"]
        assert result["account"]["contact"] == ["example@example.com"]

    def test_get_one_missing(self):
        self.named_account.get.side_effect = Exception("404 Not Found: does not exist")

        result = self._run_module(build_args(name="missing"))

        assert result.get("failed") is True
        assert "does not exist" in result["msg"]
