#
# Copyright (c) 2025, Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


from unittest.mock import MagicMock

import pytest

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    compare_list_of_dicts,
    task_exitstatus_ok,
)

EXISTING_RULES = [
    {"pos": 0, "type": "out", "action": "ACCEPT", "source": "1.1.1.1", "log": "nolog", "digest": "abc"},
    {"pos": 1, "type": "in", "action": "DROP", "source": "2.2.2.2", "digest": "abc"},
]


def test_compare_list_of_dicts_queues_item_with_multiple_changed_params_once():
    """An item is queued once for update, no matter how many of its params differ."""
    new_list = [{"pos": 0, "type": "out", "action": "ACCEPT", "source": "9.9.9.9", "log": "info"}]

    items_to_create, items_to_update = compare_list_of_dicts(
        existing_list=EXISTING_RULES, new_list=new_list, uid="pos", params_to_ignore=["digest"]
    )

    assert items_to_create == []
    assert [item["pos"] for item in items_to_update] == [0]


def test_compare_list_of_dicts_queues_item_with_added_param_once():
    """An item with an additional param is queued once and an identical item is not queued."""
    new_list = [
        {"pos": 0, "type": "out", "action": "ACCEPT", "source": "1.1.1.1", "log": "nolog", "comment": "added"},
        {"pos": 1, "type": "in", "action": "DROP", "source": "2.2.2.2"},
    ]

    items_to_create, items_to_update = compare_list_of_dicts(
        existing_list=EXISTING_RULES, new_list=new_list, uid="pos", params_to_ignore=["digest"]
    )

    assert items_to_create == []
    # Only the item with the added param is queued, the identical one is left alone
    assert [item["pos"] for item in items_to_update] == [0]


@pytest.mark.parametrize(
    ("exitstatus", "expected"),
    [
        ("OK", True),
        ("WARNINGS: 1", True),
        ("WARNINGS: 12", True),
        ("job errors", False),
        ("unexpected status", False),
        ("", False),
        (None, False),
    ],
)
def test_task_exitstatus_ok(exitstatus, expected):
    """OK and WARNINGS: <count> are successful exit statuses, anything else is an error."""
    assert task_exitstatus_ok(exitstatus) is expected


def _proxmox_with_task_status(status):
    proxmox = ProxmoxAnsible.__new__(ProxmoxAnsible)
    proxmox.module = MagicMock()
    proxmox.proxmox_api = MagicMock()
    proxmox.proxmox_api.nodes.return_value.tasks.return_value.status.get.return_value = status
    return proxmox


def test_task_with_warnings_is_ok_and_not_failed():
    """A task that ended with warnings counts as a success in every task helper."""
    proxmox = _proxmox_with_task_status({"status": "stopped", "exitstatus": "WARNINGS: 2"})

    assert proxmox.api_task_ok("pve", "UPID:pve:1") is True
    assert proxmox.api_task_failed("pve", "UPID:pve:1") is False
    assert proxmox.api_task_complete("pve", "UPID:pve:1", 1) == (True, None)


def test_task_with_error_is_failed():
    """A task that ended with an error counts as a failure in every task helper."""
    proxmox = _proxmox_with_task_status({"status": "stopped", "exitstatus": "command failed"})

    assert proxmox.api_task_ok("pve", "UPID:pve:1") is False
    assert proxmox.api_task_failed("pve", "UPID:pve:1") is True
    assert proxmox.api_task_complete("pve", "UPID:pve:1", 1) == (False, "command failed")
