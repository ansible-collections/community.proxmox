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

from ansible_collections.community.proxmox.plugins.modules import proxmox_cluster_firewall_security_group
from ansible_collections.community.proxmox.plugins.modules.proxmox_cluster_firewall_security_group import (
    _api_rule_to_ansible,
    _build_create_rule_payload,
    _build_update_rule_payload,
    _normalize_for_compare,
    _normalize_for_return,
    _put_rule_payload,
    _rules_content_equal,
    _sort_rules,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

GROUP_NAME = "webserver"

SAMPLE_GROUP = {
    "group": GROUP_NAME,
    "comment": "Managed by Ansible",
    "digest": "abc123",
}

SAMPLE_RULE_0 = {
    "pos": 0,
    "type": "in",
    "action": "ACCEPT",
    "enable": 1,
    "comment": "Allow HTTP",
    "dest": "192.168.1.100",
    "dport": "80",
    "proto": "tcp",
    "digest": "rule-digest-0",
}

SAMPLE_RULE_1 = {
    "pos": 1,
    "type": "in",
    "action": "ACCEPT",
    "enable": 1,
    "comment": "Allow HTTPS",
    "dest": "192.168.1.100",
    "dport": "443",
    "proto": "tcp",
    "digest": "rule-digest-1",
}

# Ansible-side representation of SAMPLE_RULE_0 / SAMPLE_RULE_1
DESIRED_RULE_0 = {
    "action": "ACCEPT",
    "type": "in",
    "enabled": True,
    "comment": "Allow HTTP",
    "dest": "192.168.1.100",
    "dport": "80",
    "proto": "tcp",
}

DESIRED_RULE_1 = {
    "action": "ACCEPT",
    "type": "in",
    "enabled": True,
    "comment": "Allow HTTPS",
    "dest": "192.168.1.100",
    "dport": "443",
    "proto": "tcp",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
        "name": GROUP_NAME,
        "state": state,
    }
    args.update(overrides)
    return args


# ---------------------------------------------------------------------------
# Unit tests — standalone helper functions
# ---------------------------------------------------------------------------


class TestApiRuleToAnsible:
    def test_renames_enable_to_enabled_bool(self):
        """Ensure API `enable` is converted to Ansible `enabled` for stable return values."""
        result = _api_rule_to_ansible({"action": "ACCEPT", "type": "in", "enable": 1})
        assert result["enabled"] is True
        assert "enable" not in result

    def test_disabled_rule(self):
        """Guard disabled rule conversion so state comparisons handle disabled rules correctly."""
        result = _api_rule_to_ansible({"action": "ACCEPT", "type": "in", "enable": 0})
        assert result["enabled"] is False

    def test_renames_icmp_type_hyphen_to_underscore(self):
        """Verify API `icmp-type` maps to `icmp_type` expected by module args/results."""
        result = _api_rule_to_ansible({"action": "ACCEPT", "type": "in", "enable": 1, "icmp-type": "echo-request"})
        assert result["icmp_type"] == "echo-request"
        assert "icmp-type" not in result

    def test_other_fields_pass_through(self):
        """Prevent accidental dropping of unrelated rule fields during API->Ansible conversion."""
        result = _api_rule_to_ansible(
            {"action": "ACCEPT", "type": "in", "enable": 1, "pos": 2, "dport": "80", "digest": "abc"}
        )
        assert result["pos"] == 2  # noqa: PLR2004
        assert result["dport"] == "80"
        assert result["digest"] == "abc"

    def test_empty_dict_returns_empty(self):
        """Keep empty payload handling predictable and avoid injecting synthetic defaults."""
        assert _api_rule_to_ansible({}) == {}

    def test_falsy_input_returns_as_is(self):
        """Preserve `None` passthrough to avoid masking missing-rule conditions upstream."""
        assert _api_rule_to_ansible(None) is None


class TestNormalizeForCompare:
    def test_required_fields(self):
        """Confirm normalization always compares the required identity fields and enabled flag."""
        result = _normalize_for_compare({"action": "ACCEPT", "type": "in", "enable": 1})
        assert result == {"action": "ACCEPT", "type": "in", "enabled": True}

    def test_empty_string_optional_excluded(self):
        """Ignore empty/None optional values so harmless API noise does not trigger drift."""
        result = _normalize_for_compare({"action": "DROP", "type": "out", "enable": 1, "comment": "", "dport": None})
        assert "comment" not in result
        assert "dport" not in result

    def test_non_empty_optional_included(self):
        """Ensure meaningful optional fields participate in rule drift detection."""
        result = _normalize_for_compare({"action": "ACCEPT", "type": "in", "enable": 1, "dport": "80", "proto": "tcp"})
        assert result["dport"] == "80"
        assert result["proto"] == "tcp"

    def test_dport_int_normalized_to_str(self):
        """Normalize integer ports to strings to prevent false-positive updates."""
        result = _normalize_for_compare({"action": "ACCEPT", "type": "in", "enable": 1, "dport": 80})
        assert result["dport"] == "80"

    def test_icmp_type_key_renamed(self):
        """Use canonical `icmp_type` key during compare so API/user key styles match."""
        result = _normalize_for_compare({"action": "ACCEPT", "type": "in", "enable": 1, "icmp-type": "echo-request"})
        assert result["icmp_type"] == "echo-request"
        assert "icmp-type" not in result

    def test_none_input_returns_none(self):
        """Allow callers to treat missing rules distinctly from normalized rule dicts."""
        assert _normalize_for_compare(None) is None


class TestRulesContentEqual:
    def test_identical_rules_equal(self):
        """Baseline equality check proving compare function is stable for unchanged rules."""
        assert _rules_content_equal(SAMPLE_RULE_0, SAMPLE_RULE_0) is True

    def test_different_action_not_equal(self):
        """Catch action changes so ACCEPT/DROP drift is never ignored."""
        assert _rules_content_equal(SAMPLE_RULE_0, {**SAMPLE_RULE_0, "action": "DROP"}) is False

    def test_different_dport_not_equal(self):
        """Catch port changes so traffic policy updates are applied."""
        assert _rules_content_equal(SAMPLE_RULE_0, {**SAMPLE_RULE_0, "dport": "443"}) is False

    def test_different_enable_not_equal(self):
        """Catch enabled/disabled flips so rule activation drift is reconciled."""
        assert _rules_content_equal({**SAMPLE_RULE_0, "enable": 1}, {**SAMPLE_RULE_0, "enable": 0}) is False

    def test_digest_and_pos_ignored(self):
        """Confirm metadata-only differences do not force unnecessary updates."""
        a = {**SAMPLE_RULE_0, "digest": "aaa", "pos": 0}
        b = {**SAMPLE_RULE_0, "digest": "bbb", "pos": 5}
        assert _rules_content_equal(a, b) is True


class TestBuildCreateRulePayload:
    def test_required_and_positional_fields(self):
        """Ensure create payload includes required rule fields plus ordering/group placement."""
        payload = _build_create_rule_payload({"action": "ACCEPT", "type": "in", "enabled": True}, 2, GROUP_NAME)
        assert payload["action"] == "ACCEPT"
        assert payload["type"] == "in"
        assert payload["enable"] == 1
        assert payload["pos"] == 2  # noqa: PLR2004
        assert payload["group"] == GROUP_NAME

    def test_optional_fields_included_when_set(self):
        """Verify user-provided optional attributes are sent to API on create."""
        rule = {"action": "ACCEPT", "type": "in", "dport": "80", "proto": "tcp", "comment": "test"}
        payload = _build_create_rule_payload(rule, 0, GROUP_NAME)
        assert payload["dport"] == "80"
        assert payload["proto"] == "tcp"
        assert payload["comment"] == "test"

    def test_optional_fields_excluded_when_none(self):
        """Avoid sending explicit null optional fields that can clobber API defaults."""
        rule = {"action": "ACCEPT", "type": "in", "dport": None, "comment": None}
        payload = _build_create_rule_payload(rule, 0, GROUP_NAME)
        assert "dport" not in payload
        assert "comment" not in payload

    def test_enabled_false_maps_to_zero(self):
        """Proxmox expects numeric booleans; this prevents wrong enabled state on create."""
        payload = _build_create_rule_payload({"action": "DROP", "type": "in", "enabled": False}, 0, GROUP_NAME)
        assert payload["enable"] == 0

    def test_icmp_type_key_converted(self):
        """Validate Ansible `icmp_type` is translated to API `icmp-type` key."""
        rule = {"action": "ACCEPT", "type": "in", "icmp_type": "echo-request"}
        payload = _build_create_rule_payload(rule, 0, GROUP_NAME)
        assert payload["icmp-type"] == "echo-request"
        assert "icmp_type" not in payload


class TestBuildUpdateRulePayload:
    def test_seeds_optional_fields_from_current(self):
        """Update payload must preserve omitted optional fields from current rule."""
        desired = {"action": "ACCEPT", "type": "in"}
        current = {"action": "DROP", "type": "in", "enable": 1, "proto": "tcp", "dport": "80"}
        payload = _build_update_rule_payload(desired, current)
        assert payload["proto"] == "tcp"  # preserved from current
        assert payload["dport"] == "80"  # preserved from current

    def test_desired_overrides_current_action(self):
        """Requested action must win over existing value during updates."""
        desired = {"action": "DROP", "type": "in"}
        current = {"action": "ACCEPT", "type": "in", "enable": 1}
        payload = _build_update_rule_payload(desired, current)
        assert payload["action"] == "DROP"

    def test_desired_overrides_optional_field(self):
        """Explicit optional fields from desired state must replace current values."""
        desired = {"action": "ACCEPT", "type": "in", "dport": "443"}
        current = {"action": "ACCEPT", "type": "in", "enable": 1, "dport": "80"}
        payload = _build_update_rule_payload(desired, current)
        assert payload["dport"] == "443"

    def test_no_current_rule(self):
        """Handle update payload creation when current rule is absent (defensive path)."""
        desired = {"action": "ACCEPT", "type": "in", "dport": "80"}
        payload = _build_update_rule_payload(desired, None)
        assert payload["action"] == "ACCEPT"
        assert payload["type"] == "in"
        assert payload["dport"] == "80"


class TestNormalizeForReturn:
    def test_adds_enabled_default_when_absent(self):
        """Check-mode return should include default enabled value for consistency."""
        result = _normalize_for_return({"action": "ACCEPT", "type": "in"})
        assert result["enabled"] is True

    def test_preserves_explicit_enabled_false(self):
        """Do not overwrite explicit disabled state while normalizing output."""
        result = _normalize_for_return({"action": "ACCEPT", "type": "in", "enabled": False})
        assert result["enabled"] is False

    def test_preserves_other_fields(self):
        """Normalization must not drop unrelated user-provided rule fields."""
        result = _normalize_for_return({"action": "DROP", "type": "out", "dport": "80", "proto": "tcp"})
        assert result["action"] == "DROP"
        assert result["dport"] == "80"
        assert result["proto"] == "tcp"

    def test_does_not_mutate_input(self):
        """Protect callers from side effects when normalizing return structures."""
        rule = {"action": "ACCEPT", "type": "in"}
        _normalize_for_return(rule)
        assert "enabled" not in rule


class TestPutRulePayload:
    def test_strips_pos_ipversion_digest_group(self):
        """PUT payload must omit immutable/unsupported fields rejected by Proxmox API."""
        merged = {
            "action": "ACCEPT",
            "type": "in",
            "enable": 1,
            "pos": 2,
            "ipversion": 4,
            "digest": "abc123",
            "group": "webserver",
            "dport": "80",
        }
        result = _put_rule_payload(merged)
        assert "pos" not in result
        assert "ipversion" not in result
        assert "digest" not in result
        assert "group" not in result
        assert result["action"] == "ACCEPT"
        assert result["dport"] == "80"

    def test_empty_dict(self):
        """Empty payload handling should remain a safe no-op transformation."""
        assert _put_rule_payload({}) == {}

    def test_keeps_all_other_fields(self):
        """Ensure sanitization only removes forbidden keys and preserves valid fields."""
        merged = {"action": "DROP", "type": "out", "enable": 0, "proto": "tcp", "comment": "test"}
        result = _put_rule_payload(merged)
        assert result == merged


class TestSortRules:
    def test_sorts_ascending_by_pos(self):
        """Rule fetch order must be deterministic for positional reconciliation logic."""
        rules = [
            {"pos": 2, "action": "DROP"},
            {"pos": 0, "action": "ACCEPT"},
            {"pos": 1, "action": "REJECT"},
        ]
        sorted_rules = _sort_rules(rules)
        assert [r["pos"] for r in sorted_rules] == [0, 1, 2]

    def test_already_sorted_unchanged(self):
        """Sorting helper should be idempotent for already ordered API responses."""
        rules = [{"pos": 0, "action": "ACCEPT"}, {"pos": 1, "action": "DROP"}]
        assert _sort_rules(rules) == rules

    def test_single_rule(self):
        """Single-entry rule lists should remain unchanged by sorting helper."""
        rules = [{"pos": 5, "action": "ACCEPT"}]
        assert _sort_rules(rules) == rules


# ---------------------------------------------------------------------------
# Module integration tests
# ---------------------------------------------------------------------------


class TestProxmoxClusterFirewallSecurityGroupModule(ModuleTestCase):
    def setUp(self):
        super().setUp()
        self.module = proxmox_cluster_firewall_security_group
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
        fw = mock_api.cluster.return_value.firewall.return_value

        self.groups_base = Mock()
        self.groups_named = Mock()
        self.rule_at_pos = Mock()
        self.groups_named.return_value = self.rule_at_pos

        fw.groups.side_effect = lambda *args: self.groups_named if args else self.groups_base

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

    # -- state=absent ---------------------------------------------------------

    def test_absent_when_group_not_found(self):
        """Deleting a missing group must be idempotent and avoid delete API calls."""
        self.groups_base.get.return_value = []

        result = self._run_module(build_module_args(state="absent"))

        assert result["changed"] is False
        assert "does not exist" in result["msg"]
        self.groups_named.delete.assert_not_called()

    def test_absent_deletes_rules_then_group(self):
        """Ensure delete flow removes rules first, then group, for API compatibility."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        self.groups_named.get.side_effect = [
            [SAMPLE_RULE_0],  # initial fetch in _delete_rules
            [],  # re-fetch after deletion → exits loop
        ]

        result = self._run_module(build_module_args(state="absent"))

        assert result["changed"] is True
        assert "successfully deleted" in result["msg"]
        self.rule_at_pos.delete.assert_called_once()
        self.groups_named.delete.assert_called_once()

    def test_absent_deletes_multiple_rules_in_reverse_order(self):
        """Verify repeated deletion loop handles multiple rules safely until empty."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        self.groups_named.get.side_effect = [
            [SAMPLE_RULE_0, SAMPLE_RULE_1],  # initial fetch
            [SAMPLE_RULE_0],  # re-fetch after deleting pos=1
            [],  # re-fetch after deleting pos=0
        ]

        self._run_module(build_module_args(state="absent"))

        assert self.rule_at_pos.delete.call_count == 2  # noqa: PLR2004
        self.groups_named.delete.assert_called_once()

    def test_absent_deletes_group_with_no_rules(self):
        """Delete path should still remove group when no child rules exist."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        self.groups_named.get.return_value = []

        result = self._run_module(build_module_args(state="absent"))

        assert result["changed"] is True
        self.rule_at_pos.delete.assert_not_called()
        self.groups_named.delete.assert_called_once()

    def test_absent_check_mode(self):
        """Check mode should report deletion without performing destructive operations."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]

        result = self._run_module(self._check_mode(state="absent"))

        assert result["changed"] is True
        assert "would be deleted" in result["msg"]
        self.groups_named.delete.assert_not_called()
        self.groups_base.post.assert_not_called()

    # -- state=present, group does not exist ----------------------------------

    def test_present_creates_group_without_rules(self):
        """Create path without `rules` must manage only group/comment and skip rules."""
        self.groups_base.get.return_value = []

        result = self._run_module(build_module_args(comment="Managed by Ansible"))

        assert result["changed"] is True
        assert "successfully created" in result["msg"]
        assert result["name"] == GROUP_NAME
        assert result["comment"] == "Managed by Ansible"
        assert "rules" not in result  # rules param was omitted
        self.groups_base.post.assert_called_once()
        self.groups_named.post.assert_not_called()

    def test_present_creates_group_with_rules(self):
        """Create path with rules should create both group and initial rules."""
        self.groups_base.get.return_value = []
        self.groups_named.get.return_value = [SAMPLE_RULE_0]

        result = self._run_module(build_module_args(rules=[DESIRED_RULE_0]))

        assert result["changed"] is True
        assert "successfully created" in result["msg"]
        assert "rules" in result
        assert len(result["rules"]) == 1
        assert result["rules"][0]["action"] == "ACCEPT"
        assert result["rules"][0]["enabled"] is True
        self.groups_base.post.assert_called_once()
        self.groups_named.post.assert_called_once()

    def test_present_creates_group_with_multiple_rules(self):
        """Multiple desired rules must produce one create call per rule."""
        self.groups_base.get.return_value = []
        self.groups_named.get.return_value = [SAMPLE_RULE_0, SAMPLE_RULE_1]

        self._run_module(build_module_args(rules=[DESIRED_RULE_0, DESIRED_RULE_1]))

        assert self.groups_named.post.call_count == 2  # noqa: PLR2004

    def test_present_check_mode_create(self):
        """Check mode create should preview resulting object while avoiding API writes."""
        self.groups_base.get.return_value = []

        result = self._run_module(self._check_mode(comment="Managed by Ansible", rules=[DESIRED_RULE_0]))

        assert result["changed"] is True
        assert "would be created" in result["msg"]
        assert result["comment"] == "Managed by Ansible"
        assert len(result["rules"]) == 1
        assert result["rules"][0]["action"] == "ACCEPT"
        assert result["rules"][0]["enabled"] is True
        self.groups_base.post.assert_not_called()
        self.groups_named.post.assert_not_called()

    def test_present_check_mode_create_without_rules(self):
        """Check mode should preserve omitted-rules semantics (no synthetic rules list)."""
        self.groups_base.get.return_value = []

        result = self._run_module(self._check_mode())

        assert result["changed"] is True
        assert result.get("rules") is None
        self.groups_base.post.assert_not_called()

    # -- state=present, group exists ------------------------------------------

    def test_present_idempotent_no_params(self):
        """Existing group with no desired changes should return unchanged and no writes."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]

        result = self._run_module(build_module_args())

        assert result["changed"] is False
        assert "already in desired state" in result["msg"]
        assert result["comment"] == SAMPLE_GROUP["comment"]
        assert "rules" not in result
        self.groups_base.post.assert_not_called()
        self.groups_named.post.assert_not_called()

    def test_present_idempotent_comment_matches(self):
        """Matching comment should not trigger needless group update call."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]

        result = self._run_module(build_module_args(comment="Managed by Ansible"))

        assert result["changed"] is False
        self.groups_base.post.assert_not_called()

    def test_present_updates_comment(self):
        """Comment drift must trigger update and return new comment value."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]

        result = self._run_module(build_module_args(comment="New comment"))

        assert result["changed"] is True
        assert "successfully updated" in result["msg"]
        assert result["comment"] == "New comment"
        self.groups_base.post.assert_called_once()

    def test_present_idempotent_rules_match(self):
        """Matching rules should not trigger post/put/delete reconciliation actions."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        self.groups_named.get.side_effect = [
            [SAMPLE_RULE_0],  # _rules_would_change
            [SAMPLE_RULE_0],  # _prune_excess_rules
            [SAMPLE_RULE_0],  # final fetch
        ]

        result = self._run_module(build_module_args(rules=[DESIRED_RULE_0]))

        assert result["changed"] is False
        assert "rules" in result
        assert result["rules"][0]["pos"] == 0
        self.groups_named.post.assert_not_called()
        self.rule_at_pos.put.assert_not_called()
        self.rule_at_pos.delete.assert_not_called()

    def test_present_prunes_excess_rules(self):
        """When desired list is shorter, extra existing rules must be pruned."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        self.groups_named.get.side_effect = [
            [SAMPLE_RULE_0, SAMPLE_RULE_1],  # _rules_would_change (count differs)
            [SAMPLE_RULE_0, SAMPLE_RULE_1],  # _prune_excess_rules initial fetch
            [SAMPLE_RULE_0],  # _prune_excess_rules after deletion
            [SAMPLE_RULE_0],  # final fetch
        ]

        result = self._run_module(build_module_args(rules=[DESIRED_RULE_0]))

        assert result["changed"] is True
        self.rule_at_pos.delete.assert_called_once()
        assert len(result["rules"]) == 1

    def test_present_updates_rule_in_place(self):
        """Rule content drift in shared prefix should trigger PUT, not recreate."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        updated_rule = {**SAMPLE_RULE_0, "dport": "8080"}
        self.groups_named.get.side_effect = [
            [SAMPLE_RULE_0],  # _rules_would_change (content differs)
            [SAMPLE_RULE_0],  # _prune_excess_rules
            [updated_rule],  # final fetch
        ]

        result = self._run_module(build_module_args(rules=[{**DESIRED_RULE_0, "dport": "8080"}]))

        assert result["changed"] is True
        self.rule_at_pos.put.assert_called_once()
        self.rule_at_pos.delete.assert_not_called()
        assert result["rules"][0]["dport"] == "8080"

    def test_present_creates_trailing_rule(self):
        """When desired list grows, missing trailing rules must be created."""
        # Start with no rules, add one.
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        self.groups_named.get.side_effect = [
            [],  # _rules_would_change (count differs)
            [],  # _prune_excess_rules
            [SAMPLE_RULE_0],  # _create_missing_trailing_rules after POST
            [SAMPLE_RULE_0],  # final fetch
        ]

        result = self._run_module(build_module_args(rules=[DESIRED_RULE_0]))

        assert result["changed"] is True
        self.groups_named.post.assert_called_once()
        assert len(result["rules"]) == 1

    def test_present_updates_comment_and_rules(self):
        """Combined drift should update both group metadata and rule set in one run."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        self.groups_named.get.side_effect = [
            [],  # _rules_would_change
            [],  # _prune_excess_rules
            [SAMPLE_RULE_0],  # _create_missing_trailing_rules after POST
            [SAMPLE_RULE_0],  # final fetch
        ]

        result = self._run_module(build_module_args(comment="New comment", rules=[DESIRED_RULE_0]))

        assert result["changed"] is True
        assert result["comment"] == "New comment"
        assert len(result["rules"]) == 1
        self.groups_base.post.assert_called_once()  # comment update
        self.groups_named.post.assert_called_once()  # rule create

    def test_present_check_mode_no_change(self):
        """No-op check mode should return current normalized rules without side effects."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        self.groups_named.get.side_effect = [
            [SAMPLE_RULE_0],  # _rules_would_change
            [SAMPLE_RULE_0],  # check mode result fetch
        ]

        result = self._run_module(self._check_mode(comment="Managed by Ansible", rules=[DESIRED_RULE_0]))

        assert result["changed"] is False
        assert "already in desired state" in result["msg"]
        assert result["comment"] == SAMPLE_GROUP["comment"]
        assert result["rules"][0]["pos"] == 0  # API fields present
        assert result["rules"][0]["enabled"] is True  # enable→enabled conversion
        self.groups_base.post.assert_not_called()
        self.groups_named.post.assert_not_called()

    def test_present_check_mode_would_update_comment(self):
        """Check mode must flag pending comment update without API mutation."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]

        result = self._run_module(self._check_mode(comment="New comment"))

        assert result["changed"] is True
        assert "would be updated" in result["msg"]
        assert result["comment"] == "New comment"
        self.groups_base.post.assert_not_called()

    def test_present_check_mode_would_update_rules(self):
        """Check mode must flag pending rule reconciliation and preview desired rules."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        self.groups_named.get.return_value = []  # empty → count differs

        result = self._run_module(self._check_mode(rules=[DESIRED_RULE_0]))

        assert result["changed"] is True
        assert "would be updated" in result["msg"]
        assert len(result["rules"]) == 1
        assert result["rules"][0]["enabled"] is True
        self.groups_named.post.assert_not_called()

    # -- API error handling ---------------------------------------------------

    def test_fetch_groups_api_error(self):
        """Surface group read failures with module-specific, actionable error message."""
        self.groups_base.get.side_effect = Exception("connection refused")

        result = self._run_module(build_module_args())

        assert result.get("failed") is True
        assert "Failed to read firewall security groups" in result["msg"]

    def test_create_group_api_error(self):
        """Surface group create failures instead of silently continuing."""
        self.groups_base.get.return_value = []
        self.groups_base.post.side_effect = Exception("unauthorized")

        result = self._run_module(build_module_args())

        assert result.get("failed") is True
        assert "Failed to create firewall security group" in result["msg"]

    def test_create_rule_api_error(self):
        """Surface rule create failures from create workflow with clear context."""
        self.groups_base.get.return_value = []
        self.groups_named.post.side_effect = Exception("rule rejected")

        result = self._run_module(build_module_args(rules=[DESIRED_RULE_0]))

        assert result.get("failed") is True
        assert "Failed to create firewall rule" in result["msg"]

    def test_fetch_rules_api_error(self):
        """Surface rule read failures during reconcile to stop unsafe updates."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        self.groups_named.get.side_effect = Exception("timeout")

        result = self._run_module(build_module_args(rules=[DESIRED_RULE_0]))

        assert result.get("failed") is True
        assert "Failed to read firewall rules" in result["msg"]

    def test_update_group_comment_api_error(self):
        """Surface comment update failures so partial updates are visible."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        self.groups_base.post.side_effect = Exception("unauthorized")

        result = self._run_module(build_module_args(comment="New comment"))

        assert result.get("failed") is True
        assert "Failed to update firewall security group" in result["msg"]

    def test_delete_group_api_error(self):
        """Surface group delete failures for absent workflow reliability."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        self.groups_named.get.return_value = []
        self.groups_named.delete.side_effect = Exception("forbidden")

        result = self._run_module(build_module_args(state="absent"))

        assert result.get("failed") is True
        assert "Failed to delete firewall security group" in result["msg"]

    def test_delete_rules_api_error(self):
        """Surface individual rule delete failures instead of looping indefinitely."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        self.groups_named.get.return_value = [SAMPLE_RULE_0]
        self.rule_at_pos.delete.side_effect = Exception("server error")

        result = self._run_module(build_module_args(state="absent"))

        assert result.get("failed") is True
        assert "Failed to delete firewall rule" in result["msg"]

    def test_prune_excess_rules_api_error(self):
        """Surface failures while pruning extra rules during reconcile."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        self.groups_named.get.side_effect = [
            [SAMPLE_RULE_0, SAMPLE_RULE_1],  # _rules_would_change (count differs)
            [SAMPLE_RULE_0, SAMPLE_RULE_1],  # _prune_excess_rules initial fetch
        ]
        self.rule_at_pos.delete.side_effect = Exception("conflict")

        result = self._run_module(build_module_args(rules=[DESIRED_RULE_0]))

        assert result.get("failed") is True
        assert "Failed to delete firewall rule" in result["msg"]

    def test_update_rule_in_prefix_api_error(self):
        """Surface failures when updating existing prefix rules via PUT."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        self.groups_named.get.side_effect = [
            [SAMPLE_RULE_0],  # _rules_would_change (content differs)
            [SAMPLE_RULE_0],  # _prune_excess_rules
        ]
        self.rule_at_pos.put.side_effect = Exception("conflict")

        result = self._run_module(build_module_args(rules=[{**DESIRED_RULE_0, "dport": "8080"}]))

        assert result.get("failed") is True
        assert "Failed to update firewall rule" in result["msg"]

    # -- missing behavioural scenarios ----------------------------------------

    def test_absent_check_mode_when_group_not_found(self):
        """Check-mode delete of missing group should stay unchanged and side-effect free."""
        self.groups_base.get.return_value = []

        result = self._run_module(self._check_mode(state="absent"))

        assert result["changed"] is False
        assert "does not exist" in result["msg"]
        self.groups_named.delete.assert_not_called()
        self.groups_base.post.assert_not_called()

    def test_present_check_mode_update_rule_in_place(self):
        """Check mode when count is unchanged but rule content differs."""
        self.groups_base.get.return_value = [SAMPLE_GROUP]
        self.groups_named.get.return_value = [SAMPLE_RULE_0]  # current: dport=80

        result = self._run_module(self._check_mode(rules=[{**DESIRED_RULE_0, "dport": "8080"}]))

        assert result["changed"] is True
        assert "would be updated" in result["msg"]
        assert result["rules"][0]["dport"] == "8080"
        self.rule_at_pos.put.assert_not_called()
        self.groups_named.post.assert_not_called()
