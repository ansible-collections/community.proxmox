# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Ryan Smith <ryan.smith220@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
from unittest.mock import MagicMock as MagicMike, patch

import pytest

# Skip tests if proxmoxer is not available
proxmoxer = pytest.importorskip('proxmoxer')

# Handle different import paths for different test environments
try:
    from ansible_collections.community.proxmox.plugins.modules import proxmox_user
    import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
except ImportError:
    sys.path.insert(0, 'plugins/modules')
    import proxmox
    sys.path.insert(0, 'plugins/module_utils')
    import proxmox as proxmox_utils


# Tests for internal methods and business logic
class TestProxmoxLxcInternals:
    """Test internal methods and business logic of ProxmoxLxcAnsible class."""

    @pytest.fixture
    def lxc_manager(self):
        """Create a ProxmoxLxcAnsible instance for internal testing."""
        module = MagicMike()
        module.check_mode = False
        module.exit_json = MagicMike()
        module.fail_json = MagicMike()

        with patch.object(proxmox_utils.ProxmoxAnsible, '__init__', return_value=None):
            manager = proxmox.ProxmoxLxcAnsible(module)
            manager.module = module
            manager.proxmox_api = MagicMike()
            return manager

    def test_mounts_formatting(self, lxc_manager):
        """Test the process_mount_keys method correctly formats mounts."""

        mount_volumes = [{
            'host_path': '/mnt/dir',
            'mountpoint': 'mnt/dir',
            'id': 'mp0',
            'storage': None,
            'volume': None,
            'size': None,
            'options': None,
        }]
        mounts = lxc_manager.process_mount_keys(
            100, "my-node", None, mount_volumes
        )
        assert mounts == {'mp0': '/mnt/dir,mp=mnt/dir'}
