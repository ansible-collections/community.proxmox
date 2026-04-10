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

from ansible_collections.community.proxmox.plugins.modules import proxmox_node_firewall


def exit_json(*args, **kwargs):
    kwargs.setdefault("changed", False)
    raise SystemExit(kwargs)


def fail_json(*args, **kwargs):
    kwargs["failed"] = True
    raise SystemExit(kwargs)


def build_module_args(state="enabled", **overrides):
    return {
        "api_host": "host",
        "api_user": "user",
        "api_password": "password",
        "state": state,
        "node_name": "pve-001",
        **overrides,
    }


PROXMOX_OPTIONS_DEFAULTS = {
    "enable": 1,
    "log_level_in": "nolog",
    "log_level_out": "nolog",
    "log_level_forward": "nolog",
    "ndp": 1,
    "nftables": 0,
    "nosmurfs": 1,
    "smurf_log_level": "nolog",
    "tcp_flags_log_level": "nolog",
    "tcpflags": 0,
    "nf_conntrack_allow_invalid": 0,
    "nf_conntrack_helpers": None,
    "nf_conntrack_max": 262144,
    "nf_conntrack_tcp_timeout_established": 432000,
    "nf_conntrack_tcp_timeout_syn_recv": 60,
    "protection_synflood": 0,
    "protection_synflood_burst": 1000,
    "protection_synflood_rate": 200,
}


class TestProxmoxNodeFirewallModule(ModuleTestCase):
    def setUp(self):
        super().setUp()
        self.module = proxmox_node_firewall

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
        self.node_mock = mock_api.nodes.return_value
        mock_api.nodes.side_effect = lambda n: self.node_mock

        self.mock_api_fw_options = self.node_mock.firewall.return_value.options

    def tearDown(self):
        self.connect_mock.stop()
        self.mock_module_helper.stop()
        super().tearDown()

    def _run_module(self, args):
        with pytest.raises(SystemExit) as exc_info, set_module_args(args):
            self.module.main()
        return exc_info.value.args[0]

    def _check_mode(self, **kwargs):
        return {**build_module_args(**kwargs), "_ansible_check_mode": True}

    def test_validate_params_failure(self):
        cases = [
            ({"nf_conntrack_max": 1}, "nf_conntrack_max must be greater than 32768"),
            ({"nf_conntrack_tcp_timeout_syn_recv": 1}, "nf_conntrack_tcp_timeout_syn_recv must be between 30 and 60"),
            ({"nf_conntrack_tcp_timeout_syn_recv": 61}, "nf_conntrack_tcp_timeout_syn_recv must be between 30 and 60"),
            ({"protection_synflood_burst": 999}, "protection_synflood_burst must be greater than 1000"),
            ({"protection_synflood_rate": 199}, "protection_synflood_rate must be greater than 200"),
        ]
        for overrides, expected_substring in cases:
            result = self._run_module(build_module_args(**overrides))
            assert result["failed"] is True
            assert expected_substring in result["msg"]

    def test_idempotent_when_options_match(self):
        self.mock_api_fw_options.get.return_value = PROXMOX_OPTIONS_DEFAULTS

        result = self._run_module(build_module_args(state="enabled"))

        assert result["changed"] is False
        assert result["msg"] == "Node firewall options already match desired state"
        assert result["node_name"] == "pve-001"
        assert result["enabled"] is True
        assert result["ndp"] is True
        assert result["nftables"] is False
        assert not self.mock_api_fw_options.put.called

    def test_update_check_mode(self):
        self.mock_api_fw_options.get.return_value = {**PROXMOX_OPTIONS_DEFAULTS, "enable": 0}

        result = self._run_module(self._check_mode(state="enabled"))

        assert result["changed"] is True
        assert result["msg"] == "Node firewall options would be updated"
        assert result["enabled"] is True
        assert not self.mock_api_fw_options.put.called

    def test_update_success_sends_expected_payload(self):
        self.mock_api_fw_options.get.side_effect = [
            {**PROXMOX_OPTIONS_DEFAULTS, "enable": 0, "nftables": 0},
            {**PROXMOX_OPTIONS_DEFAULTS, "enable": 1, "nftables": 1},
        ]

        result = self._run_module(build_module_args(state="enabled", nftables=True))

        assert result["changed"] is True
        assert result["msg"] == "Node firewall options updated"
        assert result["enabled"] is True
        assert result["nftables"] is True

        assert self.mock_api_fw_options.put.called
        payload = self.mock_api_fw_options.put.call_args[1]
        assert payload["enable"] == 1
        assert payload["nftables"] == 1

    def test_disable_firewall_updates_enable_flag(self):
        self.mock_api_fw_options.get.side_effect = [
            PROXMOX_OPTIONS_DEFAULTS,
            {**PROXMOX_OPTIONS_DEFAULTS, "enable": 0},
        ]

        result = self._run_module(build_module_args(state="disabled"))

        assert result["changed"] is True
        assert result["msg"] == "Node firewall options updated"
        assert result["enabled"] is False

        payload = self.mock_api_fw_options.put.call_args[1]
        assert payload["enable"] == 0
