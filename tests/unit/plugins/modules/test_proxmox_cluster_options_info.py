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

from ansible_collections.community.proxmox.plugins.modules import proxmox_cluster_options_info

# Mirrors a real (sparse) GET /cluster/options response from PVE 9.2.2.
PROXMOX_OPTIONS = {
    "allowed-tags": [],
    "description": "Production datacenter",
    "keyboard": "en-gb",
    "mac_prefix": "BC:24:11",
    "migration": "type=secure,network=10.0.0.0/24",
    "crs": "ha=static,ha-rebalance-on-start=1",
}


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


class TestProxmoxClusterOptionsInfoModule(ModuleTestCase):
    def setUp(self):
        super().setUp()
        self.module = proxmox_cluster_options_info

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

    def test_returns_decoded_options_including_unknown_keys(self):
        self.mock_api_options.get.return_value = dict(PROXMOX_OPTIONS)
        result = self._run_module(build_module_args())

        assert result["changed"] is False
        options = result["cluster_options"]
        assert options["keyboard"] == "en-gb"
        assert options["mac_prefix"] == "BC:24:11"
        assert options["migration"] == {"type": "secure", "network": "10.0.0.0/24"}
        assert options["crs"] == {"ha": "static", "ha_rebalance_on_start": True}
        # Unmodelled key is preserved untouched.
        assert options["allowed-tags"] == []

    def test_empty_options(self):
        self.mock_api_options.get.return_value = {}
        result = self._run_module(build_module_args())
        assert result["changed"] is False
        assert result["cluster_options"] == {}

    def test_api_failure(self):
        self.mock_api_options.get.side_effect = Exception()
        result = self._run_module(build_module_args())
        assert result["failed"] is True
        assert "Failed to retrieve cluster options" in result["msg"]
