#
# Copyright (c) 2026, Jens Timmerman <github@caret.be>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
import unittest
from unittest.mock import MagicMock, patch

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.compat.version import LooseVersion

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import ProxmoxAnsible
from ansible_collections.community.proxmox.plugins.modules import proxmox


class TestUpdateLxcCmode(unittest.TestCase):
    @patch.object(ProxmoxAnsible, "__init__", return_value=None)
    @patch.object(ProxmoxAnsible, "version", return_value=LooseVersion("9.0"))
    @patch.object(ProxmoxAnsible, "proxmox_api", create=True)
    @patch.object(ProxmoxAnsible, "module", create=True)
    def test_update_strips_cmode_default_sentinel(self, mock_module, mock_api, mock_version, mock_init):
        """cmode='default' must never be PUT to PVE (it rejects the literal value)."""
        lxc_ansible = proxmox.ProxmoxLxcAnsible(MagicMock(spec=AnsibleModule))
        config = lxc_ansible.proxmox_api.nodes("node1").lxc(100).config
        config.get.return_value = {"hostname": "c1", "memory": "512", "cmode": "shell"}
        lxc_ansible.update_lxc_instance(100, "node1", cmode="default", memory="1024")
        put_kwargs = config.put.call_args[1]
        assert "cmode" not in put_kwargs
        assert put_kwargs["memory"] == "1024"

    @patch.object(ProxmoxAnsible, "__init__", return_value=None)
    @patch.object(ProxmoxAnsible, "version", return_value=LooseVersion("9.0"))
    @patch.object(ProxmoxAnsible, "proxmox_api", create=True)
    @patch.object(ProxmoxAnsible, "module", create=True)
    def test_update_keeps_explicit_cmode(self, mock_module, mock_api, mock_version, mock_init):
        """An explicit cmode must still pass through to PVE."""
        lxc_ansible = proxmox.ProxmoxLxcAnsible(MagicMock(spec=AnsibleModule))
        config = lxc_ansible.proxmox_api.nodes("node1").lxc(100).config
        config.get.return_value = {"hostname": "c1", "memory": "512", "cmode": "shell"}
        lxc_ansible.update_lxc_instance(100, "node1", cmode="tty", memory="1024")
        put_kwargs = config.put.call_args[1]
        assert put_kwargs["cmode"] == "tty"


class TestLxcResourceWithoutName(unittest.TestCase):
    """PVE leaves out 'name' in /cluster/resources for a container created in the last stats cycle."""

    NAMELESS_ROW = {"id": "lxc/100", "vmid": 100, "node": "node1", "type": "lxc"}

    @patch.object(ProxmoxAnsible, "__init__", return_value=None)
    @patch.object(ProxmoxAnsible, "version", return_value=LooseVersion("9.0"))
    @patch.object(ProxmoxAnsible, "proxmox_api", create=True)
    @patch.object(ProxmoxAnsible, "module", create=True)
    def test_lxc_present_without_update_reports_existing_by_vmid(self, mock_module, mock_api, mock_version, mock_init):
        lxc_ansible = proxmox.ProxmoxLxcAnsible(MagicMock(spec=AnsibleModule))
        lxc_ansible.params = {"clone": None}
        lxc_ansible.module.exit_json.side_effect = SystemExit
        lxc_ansible.proxmox_api.cluster.resources.get.return_value = [dict(self.NAMELESS_ROW)]

        with self.assertRaises(SystemExit):
            lxc_ansible.lxc_present(100, None, None, update=False, force=False)

        lxc_ansible.module.exit_json.assert_called_once_with(changed=False, vmid=100, msg="VM 100 already exists.")

    @patch.object(ProxmoxAnsible, "__init__", return_value=None)
    @patch.object(ProxmoxAnsible, "version", return_value=LooseVersion("9.0"))
    @patch.object(ProxmoxAnsible, "proxmox_api", create=True)
    @patch.object(ProxmoxAnsible, "module", create=True)
    def test_lookup_by_hostname_skips_rows_without_name(self, mock_module, mock_api, mock_version, mock_init):
        lxc_ansible = proxmox.ProxmoxLxcAnsible(MagicMock(spec=AnsibleModule))
        named = {"id": "lxc/101", "vmid": 101, "node": "node1", "type": "lxc", "name": "c1"}
        lxc_ansible.proxmox_api.cluster.resources.get.return_value = [dict(self.NAMELESS_ROW), named]

        assert lxc_ansible.get_lxc_resource_by_hostname("c1") == named

    @patch.object(ProxmoxAnsible, "__init__", return_value=None)
    @patch.object(ProxmoxAnsible, "version", return_value=LooseVersion("9.0"))
    @patch.object(ProxmoxAnsible, "proxmox_api", create=True)
    @patch.object(ProxmoxAnsible, "module", create=True)
    def test_lxc_started_without_name_uses_vmid(self, mock_module, mock_api, mock_version, mock_init):
        lxc_ansible = proxmox.ProxmoxLxcAnsible(MagicMock(spec=AnsibleModule))
        lxc_ansible.module.exit_json.side_effect = SystemExit
        lxc_ansible.proxmox_api.cluster.resources.get.return_value = [dict(self.NAMELESS_ROW)]
        lxc_ansible.proxmox_api.nodes("node1").lxc(100).status.current.get.return_value = {"status": "running"}

        with self.assertRaises(SystemExit):
            lxc_ansible.lxc_started(100, None, None, timeout=30)

        lxc_ansible.module.exit_json.assert_called_once_with(changed=False, vmid=100, msg="VM 100 is already running.")
