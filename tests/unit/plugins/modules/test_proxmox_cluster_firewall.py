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

from ansible_collections.community.proxmox.plugins.modules import proxmox_cluster_firewall
from ansible_collections.community.proxmox.plugins.modules.proxmox_cluster_firewall import (
    _build_log_ratelimit_string,
    _parse_log_ratelimit_string,
    _validate_log_ratelimit_rate,
)

# -- Fixtures

PROXMOX_OPTIONS_ENABLED = {
    "enable": 1,
    "ebtables": 1,
    "policy_in": "DROP",
    "policy_out": "ACCEPT",
    "policy_forward": "ACCEPT",
    "log_ratelimit": "enable=1,burst=5,rate=1/second",
}

PROXMOX_OPTIONS_DISABLED = {
    **PROXMOX_OPTIONS_ENABLED,
    "enable": 0,
}

# Expected Ansible-side representation of PROXMOX_OPTIONS_ENABLED
ANSIBLE_OPTIONS_ENABLED = {
    "enabled": True,
    "ebtables": True,
    "input_policy": "DROP",
    "output_policy": "ACCEPT",
    "forward_policy": "ACCEPT",
    "log_ratelimit": {"enabled": True, "burst": 5, "rate": "1/second"},
}

# Expected Ansible-side representation of PROXMOX_OPTIONS_DISABLED
ANSIBLE_OPTIONS_DISABLED = {
    **ANSIBLE_OPTIONS_ENABLED,
    "enabled": False,
}


# -- Helpers


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
        **overrides,
    }


# -- Unit tests for module helper function


class TestValidateLogRatelimitRate:
    @pytest.mark.parametrize("rate", [
        "1/second", "10/minute", "100/hour", "5/day", "99/second",
    ])  # fmt: skip
    def test_valid_rates(self, rate):
        assert _validate_log_ratelimit_rate(rate) is True

    @pytest.mark.parametrize("rate", [
        "0/second", "1/week", "1/Second", "1 /second", "second", "1/", "", "abc",
    ])  # fmt: skip
    def test_invalid_rates(self, rate):
        assert _validate_log_ratelimit_rate(rate) is False

    def test_none_rate_returns_true(self):
        assert _validate_log_ratelimit_rate(None) is True


class TestParseLogRatelimitString:
    def test_full_string(self):
        result = _parse_log_ratelimit_string("enable=1,burst=5,rate=1/second")
        assert result == {"enabled": True, "burst": 5, "rate": "1/second"}

    def test_partial_string_rate_only(self):
        assert _parse_log_ratelimit_string("rate=2/hour") == {"rate": "2/hour"}

    def test_empty_or_none_returns_none(self):
        assert _parse_log_ratelimit_string("") is None
        assert _parse_log_ratelimit_string(None) is None

    def test_invalid_burst_value_is_skipped(self):
        result = _parse_log_ratelimit_string("enable=1,burst=abc,rate=1/second")
        assert "burst" not in result
        assert result == {"enabled": True, "rate": "1/second"}


class TestBuildLogRatelimitString:
    def test_full_params(self):
        assert _build_log_ratelimit_string(enabled=True, burst=5, rate="1/second") == "enable=1,burst=5,rate=1/second"

    def test_none_param_excluded_from_output(self):
        assert _build_log_ratelimit_string(enabled=None, burst=5, rate="1/second") == "burst=5,rate=1/second"

    def test_all_none_returns_none(self):
        assert _build_log_ratelimit_string(None, None, None) is None

    def test_build_then_parse_returns_original_values(self):
        built = _build_log_ratelimit_string(enabled=True, burst=7, rate="3/hour")
        assert _parse_log_ratelimit_string(built) == {"enabled": True, "burst": 7, "rate": "3/hour"}


# -- Module tests


class TestProxmoxClusterFirewallModule(ModuleTestCase):
    def setUp(self):
        super().setUp()
        self.module = proxmox_cluster_firewall

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
        self.mock_api_fw_options = mock_api.cluster.return_value.firewall.return_value.options

    def tearDown(self):
        self.connect_mock.stop()
        self.mock_module_helper.stop()
        super().tearDown()

    def _run_module(self, args):
        with pytest.raises(SystemExit) as exc_info, set_module_args(args):
            self.module.main()
        return exc_info.value.args[0]

    # -- Helpers

    def _run_module(self, args):
        with pytest.raises(SystemExit) as exc_info, set_module_args(args):
            self.module.main()
        return exc_info.value.args[0]

    def _check_mode(self, **kwargs):
        return {**build_module_args(**kwargs), "_ansible_check_mode": True}

    def _assert_ansible_options(self, result, expected):
        for key, value in expected.items():
            assert result[key] == value, f"Mismatch on '{key}': {result[key]!r} != {value!r}"

    def _run_disabled_update(self, initial_state):
        final_state = {
            "enable": 0,
            "ebtables": 1,
            "policy_in": "DROP",
            "policy_out": "ACCEPT",
            "policy_forward": "ACCEPT",
            "log_ratelimit": "enable=0,burst=10,rate=5/minute",
        }
        self.mock_api_fw_options.get.side_effect = [initial_state, final_state]

        result = self._run_module(
            build_module_args(
                state="disabled",
                log_ratelimit={"enabled": False, "burst": 10, "rate": "5/minute"},
            )
        )

        assert result["changed"] is True
        assert result["msg"] == "Cluster firewall options updated"
        assert result["enabled"] is False
        assert result["log_ratelimit"] == {"enabled": False, "burst": 10, "rate": "5/minute"}
        assert self.mock_api_fw_options.put.called

    # -- API error

    def test_get_options_api_failure(self):
        self.mock_api_fw_options.get.side_effect = Exception()

        result = self._run_module(build_module_args(state="enabled"))

        assert result["failed"] is True
        assert "Failed to retrieve cluster firewall options" in result["msg"]

    def test_put_options_api_failure(self):
        self.mock_api_fw_options.get.return_value = PROXMOX_OPTIONS_DISABLED
        self.mock_api_fw_options.put.side_effect = Exception()
        result = self._run_module(build_module_args(state="enabled"))
        assert result["failed"] is True
        assert "Failed to set cluster firewall options" in result["msg"]

        self.mock_api_fw_options.get.return_value = PROXMOX_OPTIONS_ENABLED
        self.mock_api_fw_options.put.side_effect = Exception()
        result = self._run_module(build_module_args(state="disabled"))
        assert result["failed"] is True
        assert "Failed to set cluster firewall options" in result["msg"]

    # -- state=enabled

    def test_enabled_idempotent(self):
        self.mock_api_fw_options.get.return_value = PROXMOX_OPTIONS_ENABLED

        result = self._run_module(
            build_module_args(
                state="enabled",
                ebtables=True,
                input_policy="DROP",
                output_policy="ACCEPT",
                forward_policy="ACCEPT",
                log_ratelimit={"enabled": True, "burst": 5, "rate": "1/second"},
            )
        )

        assert result["changed"] is False
        assert result["msg"] == "Cluster firewall options already match desired state"
        assert ANSIBLE_OPTIONS_ENABLED.items() <= result.items()
        assert not self.mock_api_fw_options.put.called

    def test_enabled_update(self):
        self.mock_api_fw_options.get.side_effect = [
            # First call, differs from desired
            {
                "enable": 0,
                "ebtables": 0,
                "policy_in": "ACCEPT",
                "policy_out": "ACCEPT",
                "policy_forward": "DROP",
                "log_ratelimit": "enable=0,burst=5,rate=1/second",
            },
            # Re-call after PUT
            PROXMOX_OPTIONS_ENABLED,
        ]

        result = self._run_module(
            build_module_args(
                state="enabled",
                ebtables=True,
                input_policy="DROP",
                output_policy="ACCEPT",
                forward_policy="ACCEPT",
                log_ratelimit={"enabled": True, "burst": 5, "rate": "1/second"},
            )
        )

        assert result["changed"] is True
        assert result["msg"] == "Cluster firewall options updated"
        assert ANSIBLE_OPTIONS_ENABLED.items() <= result.items()
        assert self.mock_api_fw_options.put.called

    def test_enabled_update_check_mode(self):
        self.mock_api_fw_options.get.return_value = {
            "enable": 0,
            "ebtables": 1,
            "policy_in": "ACCEPT",
            "policy_out": "ACCEPT",
            "policy_forward": "DROP",
            "log_ratelimit": "enable=0,burst=5,rate=1/second",
        }

        result = self._run_module(
            {
                **build_module_args(
                    state="enabled",
                    ebtables=True,
                    input_policy="DROP",
                    output_policy="ACCEPT",
                    forward_policy="ACCEPT",
                    log_ratelimit={"enabled": True, "burst": 5, "rate": "1/second"},
                ),
                "_ansible_check_mode": True,
            }
        )

        assert result["changed"] is True
        assert result["msg"] == "Cluster firewall options would be updated"
        assert ANSIBLE_OPTIONS_ENABLED.items() <= result.items()
        assert not self.mock_api_fw_options.put.called

    def test_enabled_idempotent_without_log_ratelimit(self):
        self.mock_api_fw_options.get.return_value = {
            "enable": 1,
            "ebtables": 1,
            "policy_in": "DROP",
            "policy_out": "ACCEPT",
            "policy_forward": "ACCEPT",
            # no log_ratelimit key
        }

        result = self._run_module(
            build_module_args(
                state="enabled",
                ebtables=True,
                input_policy="DROP",
                output_policy="ACCEPT",
                forward_policy="ACCEPT",
            )
        )

        assert result["changed"] is False
        assert "log_ratelimit" not in result
        assert not self.mock_api_fw_options.put.called

    # -- state=disabled

    def test_disabled_idempotent(self):
        self.mock_api_fw_options.get.return_value = {
            "enable": 0,
            "ebtables": 0,
            "policy_in": "ACCEPT",
            "policy_out": "REJECT",
            "policy_forward": "DROP",
            "log_ratelimit": "enable=0,burst=10,rate=5/minute",
        }

        result = self._run_module(
            build_module_args(
                state="disabled",
                ebtables=False,
                input_policy="ACCEPT",
                output_policy="REJECT",
                forward_policy="DROP",
                log_ratelimit={"enabled": False, "burst": 10, "rate": "5/minute"},
            )
        )

        assert result["changed"] is False
        assert result["msg"] == "Cluster firewall options already match desired state"
        assert result["enabled"] is False
        assert result["log_ratelimit"] == {"enabled": False, "burst": 10, "rate": "5/minute"}
        assert not self.mock_api_fw_options.put.called

    def test_disabled_update_when_previously_enabled(self):
        self._run_disabled_update(PROXMOX_OPTIONS_ENABLED)

    def test_disabled_update_when_already_disabled_with_different_ratelimit(self):
        self._run_disabled_update(PROXMOX_OPTIONS_DISABLED)

    def test_disabled_update_check_mode(self):
        self.mock_api_fw_options.get.return_value = PROXMOX_OPTIONS_ENABLED

        result = self._run_module(self._check_mode(state="disabled"))

        assert result["changed"] is True
        assert result["msg"] == "Cluster firewall options would be updated"
        assert not self.mock_api_fw_options.put.called
