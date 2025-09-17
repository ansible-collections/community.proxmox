# -*- coding: utf-8 -*-
# Copyright (c) 2025, Reto Kupferschmid (@rekup) <kupferschmid@puzzle.ch>
#
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

from unittest.mock import patch

import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
from ansible_collections.community.proxmox.plugins.modules import (
    proxmox_cluster_ha_rules,
)
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    set_module_args,
    ModuleTestCase,
)

__metaclass__ = type

import pytest

proxmoxer = pytest.importorskip("proxmoxer")


class TestProxmoxClusterHARules(ModuleTestCase):
    def setUp(self):
        super(TestProxmoxClusterHARules, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_cluster_ha_rules
        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()
        self.mock_get = patch.object(
            proxmox_cluster_ha_rules.ProxmoxClusterHARuleAnsible, "get"
        ).start()
        self.mock_post = patch.object(
            proxmox_cluster_ha_rules.ProxmoxClusterHARuleAnsible, "_post"
        ).start()
        self.mock_put = patch.object(
            proxmox_cluster_ha_rules.ProxmoxClusterHARuleAnsible, "_put"
        ).start()
        self.mock_delete = patch.object(
            proxmox_cluster_ha_rules.ProxmoxClusterHARuleAnsible, "_delete"
        ).start()

    def tearDown(self):
        self.connect_mock.stop()
        self.mock_get.stop()
        self.mock_post.stop()
        self.mock_put.stop()
        self.mock_delete.stop()
        super(TestProxmoxClusterHARules, self).tearDown()

    @staticmethod
    def build_module_params(params):
        auth_params = {
            "api_user": "root@pam",
            "api_password": "secret",
            "api_host": "127.0.0.1",
        }
        return {**auth_params, **params}

    def test_proxmox_cluster_ha_rules_without_argument(self):
        with set_module_args({}):
            with pytest.raises(AnsibleFailJson):
                proxmox_cluster_ha_rules.main()

    # affinity param is required for new rules of type resource-affinity
    def test_create_ha_rule_nodes_missing_resource(self):
        module_params = {
            "comment": "My rule",
            "name": "my-rule",
            "state": "present",
            "type": "resource-affinity",
        }

        with set_module_args(self.build_module_params(module_params)):
            with pytest.raises(AnsibleFailJson):
                proxmox_cluster_ha_rules.main()

    # node param is required for new rules of type node-affinity
    def test_create_ha_rule_nodes_missing_node(self):
        module_params = {
            "comment": "My rule",
            "name": "my-rule",
            "resources": "vm:100,vm:101",
            "state": "present",
            "type": "node-affinity",
        }

        with set_module_args(self.build_module_params(module_params)):
            with pytest.raises(AnsibleFailJson):
                proxmox_cluster_ha_rules.main()

    def test_create_ha_rule_check(self):
        self.mock_get.side_effect = lambda: []

        module_params = {
            "affinity": "positive",
            "comment": "My rule",
            "name": "my-rule",
            "nodes": "pve01:10",
            "resources": "vm:100",
            "state": "present",
            "type": "node-affinity",
            "_ansible_check_mode": True,
        }

        with set_module_args(self.build_module_params(module_params)):
            with pytest.raises(AnsibleExitJson) as exc_info:
                proxmox_cluster_ha_rules.main()

        result = exc_info.value.args[0]

        assert result.get("changed") is True
        assert self.mock_get.call_count == 1
        assert self.mock_post.call_count == 0
        assert self.mock_put.call_count == 0
        assert self.mock_delete.call_count == 0

    # new node-affinity rule with minimal parameters
    def test_create_ha_rule_minimal_node(self):
        self.mock_get.side_effect = [
            [],  # first call to get does return an empty list (rule does not exist yet)
            [{"rule": "my-rule"}],
        ]

        module_params = {
            "comment": "My rule",
            "name": "my-rule",
            "nodes": "pve01:10,pve02:10",
            "resources": "vm:100,vm:101",
            "state": "present",
            "type": "node-affinity",
        }

        with set_module_args(self.build_module_params(module_params)):
            with pytest.raises(AnsibleExitJson) as exc_info:
                proxmox_cluster_ha_rules.main()

        result = exc_info.value.args[0]

        assert result.get("changed") is True
        assert result.get("rule", {}).get("rule") == "my-rule"
        assert self.mock_get.call_count == 2
        assert self.mock_put.call_count == 0
        assert self.mock_delete.call_count == 0
        self.mock_post.assert_called_once_with(
            {
                "comment": "My rule",
                "nodes": "pve01:10,pve02:10",
                "resources": "vm:100,vm:101",
                "rule": "my-rule",
                "type": "node-affinity",
            }
        )

    def test_update_ha_rule_idempotence(self):
        self.mock_get.side_effect = [
            [{"rule": "my-rule", "nodes": "pve02:20,pve01:10", "resources": "vm:101,vm:100", "type": "node-affinity", "comment": "new comment"}]
        ]

        module_params = {
            "comment": "new comment",
            "name": "my-rule",
            "nodes": ["pve01:10", "pve02:20"],
            "resources": ["vm:100", "vm:101"],
            "state": "present",
            "type": "node-affinity",
        }

        with set_module_args(self.build_module_params(module_params)):
            with pytest.raises(AnsibleExitJson) as exc_info:
                proxmox_cluster_ha_rules.main()

        result = exc_info.value.args[0]

        assert result.get("changed") is False
        assert self.mock_get.call_count == 1
        assert self.mock_post.call_count == 0
        assert self.mock_put.call_count == 0
        assert self.mock_delete.call_count == 0

    # new resource-affinity rule with minimal parameters
    def test_create_ha_rule_minimal_resource(self):
        self.mock_get.side_effect = [
            [],  # first call to get does return an empty list (rule does not exist yet)
            [{"rule": "my-rule"}],
        ]

        module_params = {
            "comment": "My rule",
            "name": "my-rule",
            "affinity": "positive",
            "resources": "vm:100,vm:101",
            "state": "present",
            "type": "resource-affinity",
        }

        with set_module_args(self.build_module_params(module_params)):
            with pytest.raises(AnsibleExitJson) as exc_info:
                proxmox_cluster_ha_rules.main()

        result = exc_info.value.args[0]

        assert result.get("changed") is True
        assert result.get("rule", {}).get("rule") == "my-rule"
        assert self.mock_get.call_count == 2
        assert self.mock_put.call_count == 0
        assert self.mock_delete.call_count == 0
        self.mock_post.assert_called_once_with(
            {
                "affinity": "positive",
                "comment": "My rule",
                "resources": "vm:100,vm:101",
                "rule": "my-rule",
                "type": "resource-affinity",
            }
        )

    # new node-affinity rule with minimal parameters, nodes and resources as list
    def test_create_ha_rule_minimal_list(self):
        self.mock_get.side_effect = [
            [],  # first call to get does return an empty list (rule does not exist yet)
            [{"rule": "my-rule"}],
        ]

        module_params = {
            "comment": "My rule",
            "name": "my-rule",
            "nodes": ["pve01:10", "pve02:10"],
            "resources": ["vm:100", "vm:101"],
            "state": "present",
            "type": "node-affinity",
        }

        with set_module_args(self.build_module_params(module_params)):
            with pytest.raises(AnsibleExitJson) as exc_info:
                proxmox_cluster_ha_rules.main()

        result = exc_info.value.args[0]

        assert result.get("changed") is True
        assert result.get("rule", {}).get("rule") == "my-rule"
        assert self.mock_get.call_count == 2
        assert self.mock_put.call_count == 0
        assert self.mock_delete.call_count == 0
        self.mock_post.assert_called_once_with(
            {
                "comment": "My rule",
                "nodes": "pve01:10,pve02:10",
                "resources": "vm:100,vm:101",
                "rule": "my-rule",
                "type": "node-affinity",
            }
        )

    # new node-affinity rule with all parameters
    def test_create_ha_rule_all(self):
        self.mock_get.side_effect = [
            [],  # first call to get does return an empty list (rule does not exist yet)
            [{"rule": "my-rule"}],
        ]

        module_params = {
            "comment": "My rule",
            "name": "my-rule",
            "nodes": ["pve01:10", "pve02:20"],
            "resources": ["vm:100", "vm:101"],
            "state": "present",
            "type": "node-affinity",
            "disable": False,
            "strict": True,
        }

        with set_module_args(self.build_module_params(module_params)):
            with pytest.raises(AnsibleExitJson) as exc_info:
                proxmox_cluster_ha_rules.main()

        result = exc_info.value.args[0]

        assert result.get("changed") is True
        assert result.get("rule", {}).get("rule") == "my-rule"
        assert self.mock_get.call_count == 2
        assert self.mock_put.call_count == 0
        assert self.mock_delete.call_count == 0
        self.mock_post.assert_called_once_with(
            {
                "comment": "My rule",
                "disable": 0,
                "nodes": "pve01:10,pve02:20",
                "resources": "vm:100,vm:101",
                "rule": "my-rule",
                "strict": 1,
                "type": "node-affinity",
            }
        )

    def test_update_ha_rule(self):
        self.mock_get.side_effect = [
            [{"rule": "my-rule", "resources": "vm:100,vm:101", "type": "node-affinity", "comment": "old comment", "nodes": "pve01:10,pve02:20"}]
        ]

        module_params = {
            "comment": "new comment",
            "name": "my-rule",
            "nodes": ["pve01:10", "pve02:20"],
            "resources": ["vm:100", "vm:101"],
            "state": "present",
            "type": "node-affinity",
        }

        with set_module_args(self.build_module_params(module_params)):
            with pytest.raises(AnsibleExitJson) as exc_info:
                proxmox_cluster_ha_rules.main()

        result = exc_info.value.args[0]

        assert result.get("changed") is True
        assert result.get("rule", {}).get("comment") == "new comment"
        assert self.mock_get.call_count == 1
        assert self.mock_post.call_count == 0
        assert self.mock_put.call_count == 1
        assert self.mock_delete.call_count == 0
        self.mock_put.assert_called_once_with(
            "my-rule",
            {"comment": "new comment", "nodes": "pve01:10,pve02:20", "resources": "vm:100,vm:101", "rule": "my-rule", "type": "node-affinity"},
        )

    def test_update_ha_rule_no_change(self):
        self.mock_get.side_effect = [
            [{"rule": "my-rule", "nodes": "pve01:10,pve02:20", "resources": "vm:100,vm:101", "type": "node-affinity", "comment": "new comment"}]
        ]

        module_params = {
            "comment": "new comment",
            "name": "my-rule",
            "nodes": ["pve01:10", "pve02:20"],
            "resources": ["vm:100", "vm:101"],
            "state": "present",
            "type": "node-affinity",
        }

        with set_module_args(self.build_module_params(module_params)):
            with pytest.raises(AnsibleExitJson) as exc_info:
                proxmox_cluster_ha_rules.main()

        result = exc_info.value.args[0]

        assert result.get("changed") is False
        assert self.mock_get.call_count == 1
        assert self.mock_post.call_count == 0
        assert self.mock_put.call_count == 0
        assert self.mock_delete.call_count == 0

    def test_delete_ha_rule_check(self):
        self.mock_get.side_effect = [[{"rule": "my-rule", "type": "node-affinity"}]]

        module_params = {
            "name": "my-rule",
            "state": "absent",
            "_ansible_check_mode": True,
        }

        with set_module_args(self.build_module_params(module_params)):
            with pytest.raises(AnsibleExitJson) as exc_info:
                proxmox_cluster_ha_rules.main()

        result = exc_info.value.args[0]

        assert result.get("changed") is True
        assert self.mock_get.call_count == 1
        assert self.mock_post.call_count == 0
        assert self.mock_put.call_count == 0
        assert self.mock_delete.call_count == 0

    def test_delete_ha_rule_not_existing(self):
        self.mock_get.side_effect = [[{"rule": "my-rule", "type": "node-affinity"}]]

        module_params = {
            "name": "my-absent-rule",
            "state": "absent",
        }

        with set_module_args(self.build_module_params(module_params)):
            with pytest.raises(AnsibleExitJson) as exc_info:
                proxmox_cluster_ha_rules.main()

        result = exc_info.value.args[0]

        assert result.get("changed") is False
        assert self.mock_get.call_count == 1
        assert self.mock_post.call_count == 0
        assert self.mock_put.call_count == 0
        assert self.mock_delete.call_count == 0

    def test_update_ha_rule_change_type_no_force(self):
        self.mock_get.side_effect = [
            [
                {"rule": "my-rule", "type": "resource-affinity"}
            ],  # first call to get does return an empty list (rule does not exist yet)
            [{"rule": "my-rule"}],
        ]

        module_params = {
            "comment": "My rule",
            "name": "my-rule",
            "nodes": ["pve01:10", "pve02:20"],
            "resources": ["vm:100", "vm:101"],
            "state": "present",
            "type": "node-affinity",
            "disable": False,
            "strict": True,
        }

        with set_module_args(self.build_module_params(module_params)):
            with pytest.raises(AnsibleFailJson):
                proxmox_cluster_ha_rules.main()

    def test_update_ha_rule_change_type_force_check(self):
        self.mock_get.side_effect = [
            [
                {"rule": "my-rule", "type": "resource-affinity"}
            ],  # first call to get does return an empty list (rule does not exist yet)
            [{"rule": "my-rule"}],
        ]

        module_params = {
            "comment": "My rule",
            "force": True,
            "name": "my-rule",
            "nodes": ["pve01:10", "pve02:20"],
            "resources": ["vm:100", "vm:101"],
            "state": "present",
            "type": "node-affinity",
            "disable": False,
            "strict": True,
            "_ansible_check_mode": True,
        }

        with set_module_args(self.build_module_params(module_params)):
            with pytest.raises(AnsibleExitJson) as exc_info:
                proxmox_cluster_ha_rules.main()

        result = exc_info.value.args[0]

        assert result.get("changed") is True
        assert result.get("rule", {}).get("rule") == "my-rule"
        assert self.mock_get.call_count == 1
        assert self.mock_put.call_count == 0
        assert self.mock_post.call_count == 0
        assert self.mock_delete.call_count == 0

    def test_update_ha_rule_change_type_force(self):
        self.mock_get.side_effect = [
            [
                {"rule": "my-rule", "type": "resource-affinity"}
            ],  # first call to get does return an empty list (rule does not exist yet)
            [{"rule": "my-rule"}],
        ]

        module_params = {
            "comment": "My rule",
            "force": True,
            "name": "my-rule",
            "nodes": ["pve01:10", "pve02:20"],
            "resources": ["vm:100", "vm:101"],
            "state": "present",
            "type": "node-affinity",
            "disable": False,
            "strict": True,
        }

        with set_module_args(self.build_module_params(module_params)):
            with pytest.raises(AnsibleExitJson) as exc_info:
                proxmox_cluster_ha_rules.main()

        result = exc_info.value.args[0]

        assert result.get("changed") is True
        assert result.get("rule", {}).get("rule") == "my-rule"
        assert self.mock_get.call_count == 2
        assert self.mock_put.call_count == 0
        assert self.mock_delete.call_count == 1
        self.mock_post.assert_called_once_with(
            {
                "comment": "My rule",
                "disable": 0,
                "nodes": "pve01:10,pve02:20",
                "resources": "vm:100,vm:101",
                "rule": "my-rule",
                "strict": 1,
                "type": "node-affinity",
            }
        )
