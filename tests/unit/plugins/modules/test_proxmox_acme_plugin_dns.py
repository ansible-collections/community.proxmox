#
# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


import base64
from unittest.mock import Mock, patch

import pytest

proxmoxer = pytest.importorskip("proxmoxer")

from ansible.module_utils import basic
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)

from ansible_collections.community.proxmox.plugins.module_utils.proxmox_acme_plugin import (
    acme_plugin_data_from_api,
)
from ansible_collections.community.proxmox.plugins.modules import proxmox_acme_plugin_dns

PLUGIN_NAME = "cloudflare"

SAMPLE_PLUGIN = {
    "api": "cf",
    "plugin": "cloudflare",
    "data": "CF_Account_ID=example\nCF_Token=example",
    "disable": 0,
    "validation-delay": 30,
    "digest": "digest-abc",
}


def exit_json(*args, **kwargs):
    kwargs.setdefault("changed", False)
    raise SystemExit(kwargs)


def fail_json(*args, **kwargs):
    kwargs["failed"] = True
    raise SystemExit(kwargs)


def build_module_args(state="present", **overrides):
    args = {
        "api_host": "host",
        "api_user": "user",
        "api_password": "password",
        "name": PLUGIN_NAME,
        "plugin": "cf",
        "state": state,
    }
    args.update(overrides)
    return args


class TestProxmoxClusterAcmePluginDnsHelpers:
    def test_data_to_api_and_from_api_roundtrip(self):
        data = {"CF_Token": "example", "CF_Account_ID": "example"}
        b64 = proxmox_acme_plugin_dns._data_to_api(data)
        raw = base64.b64decode(b64).decode("utf-8")
        assert acme_plugin_data_from_api(raw) == {
            "CF_Account_ID": "example",
            "CF_Token": "example",
        }


class TestProxmoxClusterAcmePluginDnsModule(ModuleTestCase):
    def setUp(self):
        super().setUp()
        self.module = proxmox_acme_plugin_dns
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
        mock_api.version.get.return_value = {"version": "8.0"}
        self.plugins_base = Mock()
        self.plugin_named = Mock()
        self.plugins_base.return_value = self.plugin_named
        mock_api.cluster.return_value.acme.return_value.plugins.return_value = self.plugins_base

    def tearDown(self):
        self.connect_mock.stop()
        self.mock_module_helper.stop()
        super().tearDown()

    def _run_module(self, args):
        with pytest.raises(SystemExit) as exc_info, set_module_args(args):
            self.module.main()
        return exc_info.value.args[0]

    def _check_mode_args(self, **kwargs):
        return {**build_module_args(**kwargs), "_ansible_check_mode": True}

    def test_present_creates_plugin(self):
        self.plugin_named.get.side_effect = [None, SAMPLE_PLUGIN]

        result = self._run_module(build_module_args())

        assert result["changed"] is True
        assert "successfully created" in result["msg"]
        assert result["name"] == PLUGIN_NAME
        assert result["plugin"] == "cf"
        assert result["disable"] is False
        assert result["validation_delay"] == int(SAMPLE_PLUGIN["validation-delay"])
        assert result["data"] == {"CF_Account_ID": "example", "CF_Token": "example"}
        self.plugins_base.post.assert_called_once()
        call_kw = self.plugins_base.post.call_args[1]
        assert call_kw["id"] == PLUGIN_NAME
        assert call_kw["type"] == "dns"
        assert call_kw["api"] == "cf"

    def test_present_idempotent(self):
        self.plugin_named.get.return_value = SAMPLE_PLUGIN

        result = self._run_module(
            build_module_args(
                data={"CF_Account_ID": "example", "CF_Token": "example"},
                disable=False,
                validation_delay=30,
            )
        )

        assert result["changed"] is False
        assert "already up to date" in result["msg"]
        assert self.plugins_base.post.call_count == 0
        assert self.plugin_named.put.call_count == 0

    def test_present_updates_plugin(self):
        updated = {
            **SAMPLE_PLUGIN,
            "validation-delay": 60,
            "data": "CF_Account_ID=example\nCF_Token=newsecret",
        }
        self.plugin_named.get.side_effect = [SAMPLE_PLUGIN, updated]

        result = self._run_module(
            build_module_args(
                data={"CF_Account_ID": "example", "CF_Token": "newsecret"},
                validation_delay=60,
            )
        )

        assert result["changed"] is True
        assert "successfully updated" in result["msg"]
        assert result["validation_delay"] == updated["validation-delay"]
        self.plugin_named.put.assert_called_once()

    def test_present_omit_data_does_not_trigger_update_for_remote_data(self):
        self.plugin_named.get.return_value = SAMPLE_PLUGIN

        result = self._run_module(build_module_args(name="cloudflare", plugin="cf"))

        assert result["changed"] is False
        assert self.plugin_named.put.call_count == 0

    def test_present_check_mode_create(self):
        self.plugin_named.get.return_value = None

        result = self._run_module(self._check_mode_args())

        assert result["changed"] is True
        assert "would be created" in result["msg"]
        assert self.plugins_base.post.call_count == 0

    def test_present_check_mode_update(self):
        self.plugin_named.get.return_value = SAMPLE_PLUGIN

        result = self._run_module(
            self._check_mode_args(
                data={"CF_Account_ID": "example", "CF_Token": "other"},
            )
        )

        assert result["changed"] is True
        assert "would be updated" in result["msg"]
        assert self.plugin_named.put.call_count == 0

    def test_absent_deletes(self):
        self.plugin_named.get.return_value = SAMPLE_PLUGIN

        result = self._run_module(build_module_args(state="absent"))

        assert result["changed"] is True
        assert "successfully deleted" in result["msg"]
        self.plugin_named.delete.assert_called_once()

    def test_absent_when_missing(self):
        self.plugin_named.get.return_value = None

        result = self._run_module(build_module_args(state="absent"))

        assert result["changed"] is False
        assert "does not exist" in result["msg"]
        assert self.plugin_named.delete.call_count == 0

    def test_absent_check_mode(self):
        self.plugin_named.get.return_value = SAMPLE_PLUGIN

        result = self._run_module(self._check_mode_args(state="absent"))

        assert result["changed"] is True
        assert "would be deleted" in result["msg"]
        assert self.plugin_named.delete.call_count == 0
