# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Ryan Smith <ryan.smith220@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest.mock import MagicMock, patch
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.proxmox.plugins.modules import proxmox
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import ProxmoxAnsible
from ansible.module_utils.compat.version import LooseVersion


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "version", return_value=LooseVersion("4.0"))
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
@patch.object(ProxmoxAnsible, "module", create=True)
def test_mount_formatting(mock_api, *_):
    """Test the process_mount_keys method correctly formats mounts."""
    lxc_ansible = proxmox.ProxmoxLxcAnsible(MagicMock(spec=AnsibleModule))
    mount_volumes = [{
        'host_path': '/mnt/dir',
        'mountpoint': 'mnt/dir',
        'id': 'mp0',
        'storage': None,
        'volume': None,
        'size': None,
        'options': None,
    }]
    mounts = lxc_ansible.process_mount_keys(
        100, "my-node", None, mount_volumes
    )
    assert mounts == {'mp0': '/mnt/dir,mp=mnt/dir'}
