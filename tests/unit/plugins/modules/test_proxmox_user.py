# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Kevin Quick <kevin@overwrite.io>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
from unittest.mock import MagicMock as MagicMike, patch

import pytest
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleExitJson, AnsibleFailJson, set_module_args, ModuleTestCase)

# Skip tests if proxmoxer is not available
proxmoxer = pytest.importorskip('proxmoxer')

# Handle different import paths for different test environments
try:
    from ansible_collections.community.proxmox.plugins.modules import proxmox_user
    import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
except ImportError:
    sys.path.insert(0, 'plugins/modules')
    import proxmox_user
    sys.path.insert(0, 'plugins/module_utils')
    import proxmox as proxmox_utils


class TestProxmoxUserModule(ModuleTestCase):
    """Test cases for proxmox_user module using ModuleTestCase pattern."""

    # Common test data
    BASIC_MODULE_ARGS = {
        'api_host': 'test.proxmox.com',
        'api_user': 'root@pam',
        'api_password': 'secret',
    }

    SAMPLE_USER = {
        'userid': 'testuser@pam',
        'comment': 'Test User',
        'email': 'test@example.com',
        'enable': 1,
        'expire': 0,
        'firstname': 'John',
        'lastname': 'Doe',
        'groups': ['admins'],
        'keys': ''
    }

    def setUp(self):
        super(TestProxmoxUserModule, self).setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_user
        self.connect_mock = patch("ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect")
        self.connect_mock.start()

    def tearDown(self):
        self.connect_mock.stop()
        super(TestProxmoxUserModule, self).tearDown()

    def _create_module_args(self, **kwargs):
        """Helper to create module arguments with defaults."""
        args = self.BASIC_MODULE_ARGS.copy()
        args.update(kwargs)
        return args

    def test_module_fail_when_required_args_missing(self):
        """Test module fails with missing required arguments"""
        with set_module_args({}):
            with pytest.raises(AnsibleFailJson):
                proxmox_user.main()

    def test_user_creation_check_mode(self):
        """Test user creation in check mode"""
        module_args = self._create_module_args(userid='testuser@pam', comment='Test User', state='present', _ansible_check_mode=True)

        with set_module_args(module_args):
            with patch.object(proxmox_user.ProxmoxUserAnsible, 'is_user_existing', return_value=False):
                with pytest.raises(AnsibleExitJson) as exc_info:
                    proxmox_user.main()

                result = exc_info.value.args[0]
                assert result['changed'] is True
                assert 'check mode' in result['msg']

    def test_user_update_no_changes_needed(self):
        """Test user update when no changes needed"""
        module_args = self._create_module_args(userid='testuser@pam', comment='Test User', state='present')
        existing_user = {
            'userid': 'testuser@pam', 'comment': 'Test User', 'email': '', 'enable': 1, 'expire': 0,
            'firstname': '', 'lastname': '', 'groups': [], 'keys': ''
        }

        with set_module_args(module_args):
            mock_user_exists = patch.object(proxmox_user.ProxmoxUserAnsible, 'is_user_existing', return_value=existing_user)
            mock_needs_update = patch.object(proxmox_user.ProxmoxUserAnsible, '_user_needs_update', return_value=False)

            with mock_user_exists, mock_needs_update:
                with pytest.raises(AnsibleExitJson) as exc_info:
                    proxmox_user.main()

                result = exc_info.value.args[0]
                assert result['changed'] is False
                assert 'already up to date' in result['msg']


# Tests for internal methods and business logic
class TestProxmoxUserInternals:
    """Test internal methods and business logic of ProxmoxUserAnsible class."""

    # Test data for internal method testing
    SAMPLE_EXISTING_USER = {
        'userid': 'testuser@pam',
        'comment': 'Old comment',
        'email': 'old@example.com',
        'enable': 1,
        'expire': 0,
        'firstname': 'John',
        'lastname': 'Doe',
        'groups': ['admins'],
        'keys': ''
    }

    @pytest.fixture
    def user_manager(self):
        """Create a ProxmoxUserAnsible instance for internal testing."""
        module = MagicMike()
        module.check_mode = False
        module.exit_json = MagicMike()
        module.fail_json = MagicMike()

        with patch.object(proxmox_utils.ProxmoxAnsible, '__init__', return_value=None):
            manager = proxmox_user.ProxmoxUserAnsible(module)
            manager.module = module
            manager.proxmox_api = MagicMike()
            return manager

    def test_user_needs_update_logic(self, user_manager):
        """Test the _user_needs_update comparison logic for various scenarios."""
        existing_user = self.SAMPLE_EXISTING_USER.copy()

        # Test case: No update needed - identical data
        no_update_needed = user_manager._user_needs_update(
            existing_user, 'Old comment', 'old@example.com', 1, 0, 'John', 'Doe', 'admins', ''
        )
        assert no_update_needed is False

        # Test case: Update needed - different comment
        update_needed = user_manager._user_needs_update(
            existing_user, 'New comment', 'old@example.com', 1, 0, 'John', 'Doe', 'admins', ''
        )
        assert update_needed is True

    def test_groups_format_handling(self, user_manager):
        """Test groups comparison between API format (list) and module input format (string)."""
        existing_user_with_groups = {'userid': 'testuser@pam', 'groups': ['admins', 'users']}

        # Test case: Same groups in different formats - no update needed
        same_groups = user_manager._user_needs_update(
            existing_user_with_groups, None, None, 1, None, None, None, 'admins,users', None
        )
        assert same_groups is False

        # Test case: Different groups - update needed
        different_groups = user_manager._user_needs_update(
            existing_user_with_groups, None, None, 1, None, None, None, 'admins', None
        )
        assert different_groups is True
