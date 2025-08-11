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

try:
    from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import set_module_args
except ImportError:
    from contextlib import contextmanager

    @contextmanager
    def set_module_args(args):
        with patch.object(sys, 'argv', ['test'] + [f'--{k}={v}' for k, v in args.items()]):
            yield


class TestProxmoxUser:
    """Test class for proxmox_user module"""

    # Test data constants
    SAMPLE_USER_DATA = {
        'userid': 'testuser@pam',
        'firstname': 'Test',
        'lastname': 'User',
        'email': 'test@example.com',
        'comment': 'Test user',
        'enable': 1,
        'expire': 0,
        'groups': ['admins'],
        'keys': ''
    }

    SAMPLE_MODULE_PARAMS = {
        'api_host': 'test.proxmox.com',
        'api_user': 'root@pam',
        'api_password': 'secret',
        'validate_certs': False
    }

    @pytest.fixture
    def mock_api(self, mocker):
        """Mock Proxmox API with common responses"""
        api = MagicMike()
        api.access.users.return_value.get.return_value = self.SAMPLE_USER_DATA
        api.access.users.post.return_value = None
        api.access.users.return_value.put.return_value = None
        api.access.users.return_value.delete.return_value = None
        api.access.password.put.return_value = None
        return api

    @pytest.fixture
    def user_manager(self, mock_api, mocker):
        """Create ProxmoxUserAnsible instance with mocked API"""
        module = MagicMike()
        module.params = self.SAMPLE_MODULE_PARAMS

        with patch.object(proxmox_utils.ProxmoxAnsible, '__init__', return_value=None):
            manager = proxmox_user.ProxmoxUserAnsible(module)
            manager.module = module
            manager.proxmox_api = mock_api
            return manager

    def test_user_exists(self, user_manager, mock_api):
        """Test successful user existence check"""
        result = user_manager.is_user_existing('testuser@pam')

        assert result is not False
        assert result['userid'] == 'testuser@pam'
        mock_api.access.users.assert_called_with('testuser@pam')

    def test_user_not_found(self, user_manager, mock_api):
        """Test user not found"""
        mock_api.access.users.return_value.get.side_effect = Exception("User does not exist")

        result = user_manager.is_user_existing('nonexistent@pam')

        assert result is False

    def test_user_api_error(self, user_manager, mock_api):
        """Test API error handling"""
        mock_api.access.users.return_value.get.side_effect = Exception("API Error")

        user_manager.is_user_existing('testuser@pam')

        user_manager.module.fail_json.assert_called_once()

    def test_no_update_needed(self, user_manager):
        """Test when no user update is needed"""
        result = user_manager._user_needs_update(
            self.SAMPLE_USER_DATA, 'Test user', 'test@example.com', 1, 0,
            'Test', 'User', 'admins', ''
        )
        assert result is False

    def test_update_needed(self, user_manager):
        """Test when user update is needed"""
        result = user_manager._user_needs_update(
            self.SAMPLE_USER_DATA, 'New comment', 'new@example.com', 1, 0,
            'Test', 'User', 'admins', ''
        )
        assert result is True

    def test_groups_format_matching(self, user_manager):
        """Test groups comparison with API list vs string format"""
        user_with_groups = {**self.SAMPLE_USER_DATA, 'groups': ['admins', 'users']}

        # Same groups should not need update
        result = user_manager._user_needs_update(
            user_with_groups, None, None, 1, None, None, None, 'admins,users', None
        )
        assert result is False

        # Different groups should need update
        result = user_manager._user_needs_update(
            user_with_groups, None, None, 1, None, None, None, 'admins', None
        )
        assert result is True

    def test_none_values_ignored(self, user_manager):
        """Test that None values are ignored in comparison"""
        result = user_manager._user_needs_update(
            self.SAMPLE_USER_DATA, None, None, 1, None, None, None, None, None
        )
        assert result is False

    def test_update_user_no_changes(self, user_manager):
        """Test user update when no changes needed"""
        with patch.object(user_manager, 'is_user_existing', return_value={'userid': 'testuser@pam'}), \
             patch.object(user_manager, '_user_needs_update', return_value=False):

            user_manager.create_update_user('testuser@pam')

            user_manager.module.exit_json.assert_called_once_with(
                changed=False, userid='testuser@pam',
                msg="User testuser@pam already up to date"
            )

    def test_update_user_with_changes(self, user_manager, mock_api):
        """Test user update when changes are needed"""
        with patch.object(user_manager, 'is_user_existing', return_value={'userid': 'testuser@pam'}), \
             patch.object(user_manager, '_user_needs_update', return_value=True):

            user_manager.create_update_user('testuser@pam', comment='New comment')

            mock_api.access.users.return_value.put.assert_called_once()
            user_manager.module.exit_json.assert_called_once_with(
                changed=True, userid='testuser@pam', msg="User testuser@pam updated"
            )

    def test_password_only_update(self, user_manager, mock_api):
        """Test user password update only"""
        with patch.object(user_manager, 'is_user_existing', return_value={'userid': 'testuser@pam'}), \
             patch.object(user_manager, '_user_needs_update', return_value=False):

            user_manager.create_update_user('testuser@pam', password='newpass')

            mock_api.access.password.put.assert_called_once_with(
                userid='testuser@pam', password='newpass'
            )

    def test_check_mode(self, user_manager):
        """Test check mode functionality"""
        user_manager.module.check_mode = True

        with patch.object(user_manager, 'is_user_existing', return_value={'userid': 'testuser@pam'}), \
             patch.object(user_manager, '_user_needs_update', return_value=True):

            user_manager.create_update_user('testuser@pam')

            user_manager.module.exit_json.assert_called_once_with(
                changed=True, userid='testuser@pam',
                msg="Would update testuser@pam (check mode)"
            )

    def test_create_new_user(self, user_manager, mock_api):
        """Test creating a new user"""
        with patch.object(user_manager, 'is_user_existing', return_value=False):

            user_manager.create_update_user('newuser@pam', comment='New user',
                                            groups=['users'])

            mock_api.access.users.post.assert_called_once()
            user_manager.module.exit_json.assert_called_once_with(
                changed=True, userid='newuser@pam', msg="Created user newuser@pam"
            )

    def test_delete_existing_user(self, user_manager, mock_api):
        """Test deleting existing user"""
        with patch.object(user_manager, 'is_user_existing', return_value={'userid': 'testuser@pam'}):

            user_manager.delete_user('testuser@pam')

            mock_api.access.users.return_value.delete.assert_called_once()
            user_manager.module.exit_json.assert_called_once_with(
                changed=True, userid='testuser@pam',
                msg="Deleted user with ID testuser@pam"
            )

    def test_delete_nonexistent_user(self, user_manager):
        """Test deleting non-existent user"""
        with patch.object(user_manager, 'is_user_existing', return_value=False):

            user_manager.delete_user('testuser@pam')

            user_manager.module.exit_json.assert_called_once_with(
                changed=False, userid='testuser@pam',
                msg="User testuser@pam doesn't exist"
            )

    def test_groups_normalization(self, user_manager):
        """Test groups list to string conversion"""
        with patch.object(user_manager, 'is_user_existing', return_value=False), \
             patch.object(user_manager, 'module') as mock_module:

            mock_module.check_mode = False
            mock_module.exit_json = MagicMike()

            user_manager.create_update_user('testuser@pam', groups=['admin', 'users'])

            # Verify groups were joined properly in the API call
            call_args = user_manager.proxmox_api.access.users.post.call_args
            assert call_args[1]['groups'] == 'admin,users'

    def test_api_error_handling(self, user_manager, mock_api):
        """Test API error handling during user operations"""
        mock_api.access.users.return_value.put.side_effect = Exception("API Error")

        with patch.object(user_manager, 'is_user_existing',
                          return_value={'userid': 'testuser@pam'}), \
             patch.object(user_manager, '_user_needs_update', return_value=True):

            user_manager.create_update_user('testuser@pam')

            user_manager.module.fail_json.assert_called_once()
            args = user_manager.module.fail_json.call_args[1]
            assert 'Failed to update user with ID testuser@pam' in args['msg']


class TestProxmoxUserModule:
    """Integration tests for the complete module"""

    def test_module_args_validation(self):
        """Test module argument validation"""
        args = {
            'api_host': 'test.proxmox.com',
            'api_user': 'root@pam',
            'api_password': 'secret',
            'userid': 'testuser@pam',
            'state': 'present'
        }

        with set_module_args(args):
            patch_path = 'ansible_collections.community.proxmox.plugins.modules.proxmox_user.ProxmoxUserAnsible'
            with patch(patch_path):
                with pytest.raises(SystemExit):
                    proxmox_user.main()

    def test_module_missing_required_args(self):
        """Test module fails with missing required arguments"""
        with set_module_args({}):
            with pytest.raises(SystemExit) as result:
                proxmox_user.main()
            assert result.value.code != 0

    def test_main_present_state(self):
        """Test main function with present state"""
        args = {
            'api_host': 'test.proxmox.com',
            'api_user': 'root@pam',
            'api_password': 'secret',
            'userid': 'testuser@pam',
            'comment': 'Test User',
            'state': 'present'
        }

        with set_module_args(args):
            patch_path = 'ansible_collections.community.proxmox.plugins.modules.proxmox_user.ProxmoxUserAnsible'
            with patch(patch_path) as mock_class:
                mock_instance = mock_class.return_value
                mock_instance.create_update_user = MagicMike()

                with pytest.raises(SystemExit):
                    proxmox_user.main()

                mock_instance.create_update_user.assert_called_once()

    def test_main_absent_state(self):
        """Test main function with absent state"""
        args = {
            'api_host': 'test.proxmox.com',
            'api_user': 'root@pam',
            'api_password': 'secret',
            'userid': 'testuser@pam',
            'state': 'absent'
        }

        with set_module_args(args):
            patch_path = 'ansible_collections.community.proxmox.plugins.modules.proxmox_user.ProxmoxUserAnsible'
            with patch(patch_path) as mock_class:
                mock_instance = mock_class.return_value
                mock_instance.delete_user = MagicMike()

                with pytest.raises(SystemExit):
                    proxmox_user.main()

                mock_instance.delete_user.assert_called_once_with('testuser@pam')

    def test_empty_string_to_none_conversion(self):
        """Test that empty strings are converted to None"""
        args = {
            'api_host': 'test.proxmox.com',
            'api_user': 'root@pam',
            'api_password': 'secret',
            'userid': 'testuser@pam',
            'comment': '',
            'email': '',
            'firstname': '',
            'lastname': '',
            'keys': '',
            'state': 'present'
        }

        with set_module_args(args):
            patch_path = 'ansible_collections.community.proxmox.plugins.modules.proxmox_user.ProxmoxUserAnsible'
            with patch(patch_path) as mock_class:
                mock_instance = mock_class.return_value
                mock_instance.create_update_user = MagicMike()

                with pytest.raises(SystemExit):
                    proxmox_user.main()

                # Verify that create_update_user was called with None values
                call_args = mock_instance.create_update_user.call_args[0]
                assert call_args[1] is None  # comment
                assert call_args[2] is None  # email
                assert call_args[5] is None  # firstname
                assert call_args[8] is None  # keys
                assert call_args[9] is None  # lastname
