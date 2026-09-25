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
        _, put_kwargs = config.put.call_args
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
        _, put_kwargs = config.put.call_args
        assert put_kwargs["cmode"] == "tty"
