#
# Copyright (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


from unittest.mock import MagicMock, patch

import pytest

from ansible_collections.community.proxmox.plugins.module_utils import proxmox as proxmox_utils

CONNECT_PARAMS = {
    "api_host": "192.168.1.22",
    "api_port": None,
    "api_user": "root@pam",
    "api_password": "secret",
    "api_otp": None,
    "api_token_id": None,
    "api_token_secret": None,
    "ca_path": None,
    "validate_certs": False,
    "api_timeout": 5,
}


@pytest.fixture
def proxmox_ansible():
    """Return a ProxmoxAnsible object that has module parameters and no API connection."""
    instance = proxmox_utils.ProxmoxAnsible.__new__(proxmox_utils.ProxmoxAnsible)
    instance.module = MagicMock()
    instance.module.params = dict(CONNECT_PARAMS)
    instance.module.fail_json.side_effect = SystemExit
    return instance


@patch.object(proxmox_utils, "ProxmoxAPI", side_effect=ConnectionError("refused"), create=True)
def test_connect_fails_the_module_on_error(_mock_api, proxmox_ansible):
    """A connection error fails the module by default."""
    with pytest.raises(SystemExit):
        proxmox_ansible._connect()

    assert proxmox_ansible.module.fail_json.call_args[1]["msg"] == "refused"


@patch.object(proxmox_utils, "ProxmoxAPI", side_effect=ConnectionError("refused"), create=True)
def test_connect_raises_the_error_without_fail_on_error(_mock_api, proxmox_ansible):
    """With fail_on_error=False the caller gets the connection error and the module does not fail."""
    with pytest.raises(ConnectionError):
        proxmox_ansible._connect(fail_on_error=False)

    proxmox_ansible.module.fail_json.assert_not_called()
