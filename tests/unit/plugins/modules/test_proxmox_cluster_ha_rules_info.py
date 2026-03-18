#
# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


from ansible_collections.community.proxmox.plugins.modules.proxmox_cluster_ha_rules_info import (
    _normalize_rules,
)


def test_normalize_node_affinity_rule():
    rules = [
        {
            "rule": "prefer-node-1",
            "type": "node-affinity",
            "resources": "vm:100,ct:101",
            "nodes": "pve-001:1,pve-002",
            "disable": 1,
            "strict": 0,
            "order": 1,
            "digest": "some-digest",
        }
    ]

    result = _normalize_rules(rules)

    assert isinstance(result, list)
    assert len(result) == 1

    rule = result[0]

    assert "digest" not in rule
    assert rule["resources"] == ["vm:100", "ct:101"]
    assert rule["nodes"] == ["pve-001:1", "pve-002"]
    assert rule["disable"] is True
    assert rule["strict"] is False


def test_normalize_resource_affinity_rule():
    rules = [
        {
            "rule": "resource-affinity-rule",
            "type": "resource-affinity",
            "resources": "vm:100,ct:101",
            "disable": 0,
            "order": 1,
            "digest": "another-digest",
        }
    ]

    result = _normalize_rules(rules)

    assert len(result) == 1
    rule = result[0]

    assert "digest" not in rule
    assert rule["resources"] == ["vm:100", "ct:101"]
    assert rule["disable"] is False
    assert "nodes" not in rule
    assert "strict" not in rule


def test_rules_sorted_by_order():
    rules = [
        {"rule": "second", "type": "resource-affinity", "resources": "vm:100", "order": 2},
        {"rule": "first", "type": "resource-affinity", "resources": "vm:101", "order": 1},
    ]

    result = _normalize_rules(rules)

    assert [r["rule"] for r in result] == ["first", "second"]
    assert [r["order"] for r in result] == [1, 2]
    assert result[0]["resources"] == ["vm:101"]
    assert result[1]["resources"] == ["vm:100"]


def test_normalize_with_missing_fields():
    # Proxmox API may omit optional fields; normalization must still work
    rules = [
        {
            "rule": "node-missing-fields",
            "type": "node-affinity",
            "order": 1,
        },
        {
            "rule": "resource-missing-fields",
            "type": "resource-affinity",
            "order": 2,
        },
    ]

    result = _normalize_rules(rules)

    node_rule, resource_rule = result

    assert node_rule["rule"] == "node-missing-fields"
    assert node_rule["resources"] == [""]
    assert node_rule["nodes"] == [""]
    assert isinstance(node_rule["disable"], bool)
    assert isinstance(node_rule["strict"], bool)

    assert resource_rule["rule"] == "resource-missing-fields"
    assert resource_rule["resources"] == [""]
    assert isinstance(resource_rule["disable"], bool)
    assert "nodes" not in resource_rule
    assert "strict" not in resource_rule
