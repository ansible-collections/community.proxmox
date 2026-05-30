#
# Copyright (c) 2026, FingerlessGloves
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

from ansible_collections.community.proxmox.plugins.module_utils.proxmox_cluster_options import (
    build_property_string,
    cluster_options_to_ansible_result,
    decode_property_value,
    parse_property_string,
    scalar_to_api,
)
from ansible_collections.community.proxmox.plugins.modules import proxmox_cluster_options

# -- Fixtures

# Mirrors a real (sparse) GET /cluster/options response from PVE 9.2.2. Note the API returns
# some property fields as already-decoded dicts (migration, crs) but others as raw strings
# (bwlimit), and numeric sub-values are inconsistently typed (int vs str).
PROXMOX_OPTIONS = {
    "allowed-tags": [],
    "description": "Production datacenter",
    "keyboard": "en-gb",
    "mac_prefix": "BC:24:11",
    "migration": {"type": "secure", "network": "10.0.0.0/24"},
    "crs": {"ha": "static", "ha-rebalance-on-start": 1},
    "bwlimit": "migration=102400,restore=51200",
}


# -- Helpers


def exit_json(*args, **kwargs):
    kwargs.setdefault("changed", False)
    raise SystemExit(kwargs)


def fail_json(*args, **kwargs):
    kwargs["failed"] = True
    raise SystemExit(kwargs)


def build_module_args(**overrides):
    return {
        "api_host": "host",
        "api_user": "user",
        "api_password": "password",
        **overrides,
    }


# -- Unit tests for property-string helpers


class TestParsePropertyString:
    def test_migration_full(self):
        assert parse_property_string("migration", "type=secure,network=10.0.0.0/24") == {
            "type": "secure",
            "network": "10.0.0.0/24",
        }

    def test_migration_bare_default_key(self):
        # Proxmox returns the default key ``type`` as a bare token.
        assert parse_property_string("migration", "secure") == {"type": "secure"}
        assert parse_property_string("migration", "secure,network=10.0.0.0/24") == {
            "type": "secure",
            "network": "10.0.0.0/24",
        }

    def test_bwlimit_casts_ints(self):
        assert parse_property_string("bwlimit", "migration=102400,restore=51200") == {
            "migration": 102400,
            "restore": 51200,
        }

    def test_crs_hyphen_to_underscore_and_bool(self):
        assert parse_property_string("crs", "ha=static,ha-rebalance-on-start=1,ha-auto-rebalance=0") == {
            "ha": "static",
            "ha_rebalance_on_start": True,
            "ha_auto_rebalance": False,
        }

    def test_next_id_ints(self):
        assert parse_property_string("next_id", "lower=100,upper=1000000") == {"lower": 100, "upper": 1000000}

    def test_empty_or_none_returns_none(self):
        assert parse_property_string("migration", "") is None
        assert parse_property_string("migration", None) is None

    def test_invalid_int_is_skipped(self):
        assert parse_property_string("bwlimit", "migration=abc,restore=10") == {"restore": 10}

    def test_unknown_subkey_ignored(self):
        assert parse_property_string("migration", "type=secure,bogus=1") == {"type": "secure"}


class TestBuildPropertyString:
    def test_migration_full(self):
        assert build_property_string("migration", {"type": "secure", "network": "10.0.0.0/24"}) == (
            "type=secure,network=10.0.0.0/24"
        )

    def test_partial_excludes_none(self):
        assert build_property_string("bwlimit", {"migration": 102400, "restore": None}) == "migration=102400"

    def test_crs_underscore_to_hyphen_and_bool(self):
        assert build_property_string("crs", {"ha": "static", "ha_rebalance_on_start": True}) == (
            "ha=static,ha-rebalance-on-start=1"
        )

    def test_empty_or_all_none_returns_none(self):
        assert build_property_string("migration", {}) is None
        assert build_property_string("migration", {"type": None, "network": None}) is None

    @pytest.mark.parametrize("field, data", [
        ("migration", {"type": "insecure", "network": "192.168.0.0/24"}),
        ("replication", {"type": "secure", "network": "172.16.0.0/16"}),
        ("bwlimit", {"clone": 1, "default": 2, "migration": 3, "move": 4, "restore": 5}),
        ("crs", {"ha": "dynamic", "ha_auto_rebalance": True, "ha_auto_rebalance_threshold": 30}),
        ("next_id", {"lower": 100, "upper": 999999}),
        ("location", {"latitude": 51.5074, "longitude": -0.1278, "name": "London"}),
        ("u2f", {"appid": "https://pve.example.com", "origin": "https://pve.example.com"}),
        ("webauthn", {"allow_subdomains": True, "id": "example.com", "rp": "Example"}),
        ("notify", {"fencing": "always", "package_updates": "never", "target_fencing": "mail"}),
        ("tag_style", {"case_sensitive": True, "ordering": "config", "shape": "dense"}),
        ("tag_style", {"color_map": "dev:ff0000:FFFFFF;test:000000:FFFFFF", "shape": "circle"}),
        ("user_tag_access", {"user_allow": "list", "user_allow_list": ["prod", "dev"]}),
    ])  # fmt: skip
    def test_build_then_parse_roundtrip(self, field, data):
        assert parse_property_string(field, build_property_string(field, data)) == data


class TestDecodePropertyValue:
    def test_decodes_string_form(self):
        # bwlimit is returned as a raw string by the API.
        assert decode_property_value("bwlimit", "migration=102400,restore=51200") == {
            "migration": 102400,
            "restore": 51200,
        }

    def test_decodes_dict_form_with_hyphen_keys(self):
        # crs is returned as a dict with hyphenated API keys and mixed int/str values.
        raw = {
            "ha": "static",
            "ha-rebalance-on-start": 1,
            "ha-auto-rebalance": 0,
            "ha-auto-rebalance-margin": "15",
        }
        assert decode_property_value("crs", raw) == {
            "ha": "static",
            "ha_rebalance_on_start": True,
            "ha_auto_rebalance": False,
            "ha_auto_rebalance_margin": 15,
        }

    def test_decodes_migration_dict(self):
        assert decode_property_value("migration", {"type": "insecure", "network": "10.0.0.0/24"}) == {
            "type": "insecure",
            "network": "10.0.0.0/24",
        }

    def test_none_returns_none(self):
        assert decode_property_value("migration", None) is None


class TestClusterOptionsToAnsibleResult:
    def test_translates_and_passes_through_unknown(self):
        result = cluster_options_to_ansible_result(PROXMOX_OPTIONS)
        assert result["keyboard"] == "en-gb"
        assert result["mac_prefix"] == "BC:24:11"
        # Dict-form property field.
        assert result["migration"] == {"type": "secure", "network": "10.0.0.0/24"}
        assert result["crs"] == {"ha": "static", "ha_rebalance_on_start": True}
        # String-form property field.
        assert result["bwlimit"] == {"migration": 102400, "restore": 51200}
        # Unmodelled key is preserved untouched.
        assert result["allowed-tags"] == []

    def test_empty(self):
        assert cluster_options_to_ansible_result({}) == {}

    def test_max_workers_cast_to_int(self):
        # Proxmox returns max_workers as a string; it must be normalised to int for idempotency.
        assert cluster_options_to_ansible_result({"max_workers": "4"}) == {"max_workers": 4}

    def test_description_trailing_newline_stripped(self):
        # Proxmox appends a trailing newline to description; strip it for idempotency.
        assert cluster_options_to_ansible_result({"description": "hello\n"})["description"] == "hello"

    def test_consent_text_hyphenated_api_name_and_base64_decoded(self):
        # The API key is consent-text (Ansible option consent_text), stored base64-encoded (as the UI does).
        raw = {"consent-text": "IyBNeSBvd24gdGVzdAoKc29tZXRoaW5nIGFib3V0IGJlaW5nIGNhcmVmdWwKCmBgYAp0ZXN0CmBgYA=="}
        assert cluster_options_to_ansible_result(raw) == {
            "consent_text": "# My own test\n\nsomething about being careful\n\n```\ntest\n```"
        }

    def test_location_floats_decoded(self):
        result = cluster_options_to_ansible_result({"location": {"latitude": "51.5074", "longitude": "-0.1278"}})
        assert result["location"] == {"latitude": 51.5074, "longitude": -0.1278}

    def test_registered_tags_list(self):
        # The API returns registered-tags as a list.
        assert cluster_options_to_ansible_result({"registered-tags": ["prod", "dev"]}) == {
            "registered_tags": ["prod", "dev"]
        }
        # ...but tolerate a separated string too.
        assert cluster_options_to_ansible_result({"registered-tags": "prod;dev"}) == {
            "registered_tags": ["prod", "dev"]
        }

    def test_user_tag_access_list_subvalue(self):
        # user-allow-list comes back as a list within the dict.
        raw = {"user-tag-access": {"user-allow": "list", "user-allow-list": ["prod", "dev"]}}
        assert cluster_options_to_ansible_result(raw) == {
            "user_tag_access": {"user_allow": "list", "user_allow_list": ["prod", "dev"]}
        }

    def test_consent_text_base64_encode_decode_roundtrip(self):
        text = "# Title\n\nSome **markdown** text.\n\n```\ncode block\n```"
        encoded = scalar_to_api("consent_text", text)
        # Encoded form is base64 (no raw newlines), and decodes back to the original text.
        assert "\n" not in encoded
        assert cluster_options_to_ansible_result({"consent-text": encoded}) == {"consent_text": text}


# -- Module tests


class TestProxmoxClusterOptionsModule(ModuleTestCase):
    def setUp(self):
        super().setUp()
        self.module = proxmox_cluster_options

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
        self.mock_api_options = mock_api.cluster.return_value.options

    def tearDown(self):
        self.connect_mock.stop()
        self.mock_module_helper.stop()
        super().tearDown()

    def _run_module(self, args):
        with pytest.raises(SystemExit) as exc_info, set_module_args(args):
            self.module.main()
        return exc_info.value.args[0]

    # -- API errors

    def test_get_options_api_failure(self):
        self.mock_api_options.get.side_effect = Exception()
        result = self._run_module(build_module_args(keyboard="en-us"))
        assert result["failed"] is True
        assert "Failed to retrieve cluster options" in result["msg"]

    def test_put_options_api_failure(self):
        self.mock_api_options.get.return_value = dict(PROXMOX_OPTIONS)
        self.mock_api_options.put.side_effect = Exception()
        result = self._run_module(build_module_args(keyboard="en-us"))
        assert result["failed"] is True
        assert "Failed to set cluster options" in result["msg"]

    # -- Idempotency

    def test_idempotent_scalar_and_property_string(self):
        self.mock_api_options.get.return_value = dict(PROXMOX_OPTIONS)
        result = self._run_module(
            build_module_args(
                keyboard="en-gb",
                migration={"type": "secure", "network": "10.0.0.0/24"},
            )
        )
        assert result["changed"] is False
        assert result["msg"] == "Cluster options already match the desired state"
        assert not self.mock_api_options.put.called

    def test_partial_no_touch(self):
        # User only sets description; the payload must not include other options.
        self.mock_api_options.get.side_effect = [
            dict(PROXMOX_OPTIONS),
            {**PROXMOX_OPTIONS, "description": "New notes"},
        ]
        result = self._run_module(build_module_args(description="New notes"))
        assert result["changed"] is True
        payload = self.mock_api_options.put.call_args.kwargs
        assert payload == {"description": "New notes"}

    # -- Updates

    def test_update_scalar(self):
        self.mock_api_options.get.side_effect = [
            dict(PROXMOX_OPTIONS),
            {**PROXMOX_OPTIONS, "keyboard": "en-us"},
        ]
        result = self._run_module(build_module_args(keyboard="en-us"))
        assert result["changed"] is True
        assert result["msg"] == "Cluster options updated"
        assert result["cluster_options"]["keyboard"] == "en-us"
        assert self.mock_api_options.put.call_args.kwargs == {"keyboard": "en-us"}

    def test_update_migration_property_string(self):
        self.mock_api_options.get.side_effect = [
            {"keyboard": "en-gb"},
            {"keyboard": "en-gb", "migration": "type=insecure,network=192.168.0.0/24"},
        ]
        result = self._run_module(build_module_args(migration={"type": "insecure", "network": "192.168.0.0/24"}))
        assert result["changed"] is True
        assert self.mock_api_options.put.call_args.kwargs == {"migration": "type=insecure,network=192.168.0.0/24"}

    def test_update_crs_property_string(self):
        self.mock_api_options.get.side_effect = [
            {"keyboard": "en-gb"},
            {"keyboard": "en-gb", "crs": "ha=dynamic,ha-rebalance-on-start=1"},
        ]
        result = self._run_module(build_module_args(crs={"ha": "dynamic", "ha_rebalance_on_start": True}))
        assert result["changed"] is True
        assert self.mock_api_options.put.call_args.kwargs == {"crs": "ha=dynamic,ha-rebalance-on-start=1"}

    def test_update_bwlimit_property_string(self):
        self.mock_api_options.get.side_effect = [
            {"keyboard": "en-gb"},
            {"keyboard": "en-gb", "bwlimit": "migration=102400,restore=51200"},
        ]
        result = self._run_module(build_module_args(bwlimit={"migration": 102400, "restore": 51200}))
        assert result["changed"] is True
        assert self.mock_api_options.put.call_args.kwargs == {"bwlimit": "migration=102400,restore=51200"}

    # -- Check mode

    def test_check_mode(self):
        self.mock_api_options.get.return_value = dict(PROXMOX_OPTIONS)
        result = self._run_module({**build_module_args(keyboard="en-us"), "_ansible_check_mode": True})
        assert result["changed"] is True
        assert result["msg"] == "Cluster options would be updated"
        assert not self.mock_api_options.put.called

    # -- delete / unset

    def test_delete_option(self):
        self.mock_api_options.get.side_effect = [
            dict(PROXMOX_OPTIONS),
            {k: v for k, v in PROXMOX_OPTIONS.items() if k != "keyboard"},
        ]
        result = self._run_module(build_module_args(delete=["keyboard"]))
        assert result["changed"] is True
        assert self.mock_api_options.put.call_args.kwargs == {"delete": "keyboard"}

    def test_delete_property_string_uses_api_key(self):
        # next_id maps to the hyphenated API key "next-id"; deleting must use the API key.
        current = {**PROXMOX_OPTIONS, "next-id": "lower=100,upper=1000000"}
        self.mock_api_options.get.side_effect = [
            current,
            {k: v for k, v in current.items() if k != "next-id"},
        ]
        result = self._run_module(build_module_args(delete=["next_id"]))
        assert result["changed"] is True
        assert self.mock_api_options.put.call_args.kwargs == {"delete": "next-id"}

    def test_delete_already_absent_idempotent(self):
        self.mock_api_options.get.return_value = {"keyboard": "en-gb"}
        result = self._run_module(build_module_args(delete=["language"]))
        assert result["changed"] is False
        assert not self.mock_api_options.put.called

    def test_delete_echoed_default_is_idempotent(self):
        # Proxmox always echoes mac_prefix (default BC:24:11) and description (""), even when unset.
        # Deleting them when they equal the default must be a no-op.
        self.mock_api_options.get.return_value = {"mac_prefix": "BC:24:11", "description": ""}
        result = self._run_module(build_module_args(delete=["mac_prefix", "description"]))
        assert result["changed"] is False
        assert not self.mock_api_options.put.called

    def test_delete_mac_prefix_when_non_default_changes(self):
        # If mac_prefix is set to a non-default value, deleting it does change.
        self.mock_api_options.get.side_effect = [
            {"mac_prefix": "AA:BB:CC"},
            {"mac_prefix": "BC:24:11"},
        ]
        result = self._run_module(build_module_args(delete=["mac_prefix"]))
        assert result["changed"] is True
        assert self.mock_api_options.put.call_args.kwargs == {"delete": "mac_prefix"}

    def test_delete_and_set_same_option_fails(self):
        result = self._run_module(build_module_args(mac_prefix="AA:BB:CC", delete=["mac_prefix"]))
        assert result["failed"] is True
        assert "both set and deleted" in result["msg"]

    def test_delete_unknown_option_fails(self):
        result = self._run_module(build_module_args(delete=["not_a_real_option"]))
        assert result["failed"] is True
        assert "Unknown option" in result["msg"]
