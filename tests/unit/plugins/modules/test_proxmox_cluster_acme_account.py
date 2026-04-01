#
# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


from unittest.mock import Mock, patch

import pytest

proxmoxer = pytest.importorskip("proxmoxer")

from ansible.module_utils import basic
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)

from ansible_collections.community.proxmox.plugins.modules import proxmox_cluster_acme_account

SAMPLE_GET = {
    "account": {
        "contact": ["mailto:example@example.com"],
        "createdAt": "2026-01-01T00:00:00Z",
        "status": "valid",
    },
    "directory": "https://acme-staging-v02.api.letsencrypt.org/directory",
    "location": "https://acme-v02.api.letsencrypt.org/acme/acct/3198781481",
    "tos": "https://letsencrypt.org/documents/LE-SA-v1.3-September-21-2022.pdf",
}

SAMPLE_GET_NO_CONTACT = {
    "account": {
        "contact": [],
        "createdAt": "2026-01-01T00:00:00Z",
        "status": "valid",
    },
    "directory": "https://acme-staging-v02.api.letsencrypt.org/directory",
    "location": "https://acme-v02.api.letsencrypt.org/acme/acct/3198781481",
    "tos": "https://letsencrypt.org/documents/LE-SA-v1.3-September-21-2022.pdf",
}

UPID = "UPID:pve:0018BD11:0188245B:69CCD6A7:acmeregister::root@pam:"


def exit_json(*args, **kwargs):
    kwargs.setdefault("changed", False)
    raise SystemExit(kwargs)


def fail_json(*args, **kwargs):
    kwargs["failed"] = True
    raise SystemExit(kwargs)


def build_module_args(state="present", omit_contact=False, **overrides):
    args = {
        "api_host": "host",
        "api_user": "user",
        "api_password": "password",
        "name": "default",
        "state": state,
    }
    args.update(overrides)
    if not omit_contact and "contact" not in args:
        args["contact"] = "example@example.com"
    return args


class TestProxmoxClusterAcmeAccountModule(ModuleTestCase):
    def setUp(self):
        super().setUp()
        self.module = proxmox_cluster_acme_account
        self.warn_mock = Mock()
        self.mock_module_helper = patch.multiple(
            basic.AnsibleModule,
            exit_json=exit_json,
            fail_json=fail_json,
            warn=self.warn_mock,
        )
        self.mock_module_helper.start()
        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()
        mock_api = self.connect_mock.return_value
        account_attr = mock_api.cluster.return_value.acme.return_value.account
        self.named_account = account_attr.return_value
        self.named_account.return_value = self.named_account
        self.named_account.post.return_value = UPID
        self.named_account.put.return_value = UPID
        self.named_account.delete.return_value = UPID
        self.wait_mock = patch.object(
            proxmox_cluster_acme_account.ProxmoxClusterAcmeAccountAnsible,
            "_wait_acme_task",
        ).start()

    def tearDown(self):
        self.wait_mock.stop()
        self.connect_mock.stop()
        self.mock_module_helper.stop()
        super().tearDown()

    def _run_module(self, args):
        with pytest.raises(SystemExit) as exc_info, set_module_args(args):
            self.module.main()
        return exc_info.value.args[0]

    def test_create_requires_contact(self):
        self.named_account.get.return_value = None

        result = self._run_module(build_module_args(omit_contact=True))

        assert result.get("failed") is True
        assert "contact is required to create" in result["msg"]

    def test_existing_omit_contact_no_put(self):
        self.named_account.get.return_value = SAMPLE_GET

        result = self._run_module(build_module_args(omit_contact=True))

        assert result["changed"] is False
        assert "no update attempted" in result["msg"]
        assert self.named_account.put.call_count == 0

    def test_existing_contact_api_missing_warn_and_put(self):
        self.named_account.get.side_effect = [SAMPLE_GET_NO_CONTACT, SAMPLE_GET_NO_CONTACT]

        result = self._run_module(build_module_args(contact="example@example.com"))

        assert result["changed"] is True
        self.named_account.put.assert_called_once()
        assert self.warn_mock.call_count == 1
        assert "cannot verify drift" in self.warn_mock.call_args[0][0]

    def test_existing_contact_api_match_no_put(self):
        self.named_account.get.return_value = SAMPLE_GET

        result = self._run_module(build_module_args(contact="example@example.com"))

        assert result["changed"] is False
        assert self.named_account.put.call_count == 0

    def test_existing_contact_api_diff_put(self):
        other = {
            **SAMPLE_GET,
            "account": {**SAMPLE_GET["account"], "contact": ["mailto:other@example.com"]},
        }
        self.named_account.get.side_effect = [other, SAMPLE_GET]

        result = self._run_module(build_module_args(contact="example@example.com"))

        assert result["changed"] is True
        self.named_account.put.assert_called_once_with(contact="example@example.com")
