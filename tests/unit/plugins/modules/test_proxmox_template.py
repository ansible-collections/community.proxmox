#
# Copyright (c) 2023, Sergei Antipov <greendayonfire at gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


import os
import tempfile
from unittest.mock import Mock, patch

import pytest
import requests

proxmoxer = pytest.importorskip("proxmoxer")

from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    ModuleTestCase,
    set_module_args,
)

import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
from ansible_collections.community.proxmox.plugins.modules import proxmox_template


class TestProxmoxTemplateModule(ModuleTestCase):
    def setUp(self):
        super().setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_template
        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect"
        )
        self.connect_mock.start()

    def tearDown(self):
        self.connect_mock.stop()
        super().tearDown()

    @patch("os.stat")
    @patch.multiple(os.path, exists=Mock(return_value=True), isfile=Mock(return_value=True))
    def test_module_fail_when_toolbelt_not_installed_and_file_size_is_big(self, mock_stat):
        self.module.HAS_REQUESTS_TOOLBELT = False
        mock_stat.return_value.st_size = 268435460
        with set_module_args(
            {
                "api_host": "host",
                "api_user": "user",
                "api_password": "password",
                "node": "pve",
                "src": "/tmp/mock.iso",
                "content_type": "iso",
            }
        ), pytest.raises(AnsibleFailJson) as exc_info:
            self.module.main()

        result = exc_info.value.args[0]
        assert result["failed"] is True
        assert "upload files larger than 256MB" in result["msg"]

    def _upload(self, extra_args):
        with tempfile.TemporaryDirectory() as tmp_dir:
            src = os.path.join(tmp_dir, "local-build.iso")
            with open(src, "wb") as f:
                f.write(b"iso-content")
            proxmox_api = Mock()
            storage_api = proxmox_api.nodes.return_value.storage.return_value
            storage_api.content.get.return_value = []
            storage_api.upload.post.return_value = "UPID:pve:upload"
            args = {
                "api_host": "host",
                "api_user": "user",
                "api_password": "password",
                "node": "pve",
                "src": src,
                "content_type": "iso",
            }
            args.update(extra_args)
            with patch.object(self.module.ProxmoxTemplateAnsible, "_connect", return_value=proxmox_api), patch.object(
                self.module.ProxmoxTemplateAnsible, "task_status", return_value=True
            ), set_module_args(args), pytest.raises(AnsibleExitJson) as exc_info:
                self.module.main()

            upload = storage_api.upload.post.call_args.kwargs["filename"]
            try:
                assert upload.read() == b"iso-content"
                # proxmoxer sends this as the multipart file name, and Proxmox VE stores the upload under it.
                return exc_info.value.args[0], requests.utils.guess_filename(upload)
            finally:
                upload.close()

    def test_upload_stores_file_under_template_name(self):
        result, upload_name = self._upload({"template": "debian-13.iso"})

        assert upload_name == "debian-13.iso"
        assert result["changed"] is True
        assert result["msg"] == "template with volid=local:iso/debian-13.iso uploaded"

    def test_upload_defaults_to_src_file_name(self):
        result, upload_name = self._upload({})

        assert upload_name == "local-build.iso"
        assert result["msg"] == "template with volid=local:iso/local-build.iso uploaded"

    def test_upload_skips_existing_template_name(self):
        proxmox_api = Mock()
        storage_api = proxmox_api.nodes.return_value.storage.return_value
        storage_api.content.get.return_value = [{"volid": "local:iso/debian-13.iso"}]
        with patch.object(self.module.ProxmoxTemplateAnsible, "_connect", return_value=proxmox_api), set_module_args(
            {
                "api_host": "host",
                "api_user": "user",
                "api_password": "password",
                "node": "pve",
                "src": "/tmp/local-build.iso",
                "template": "debian-13.iso",
                "content_type": "iso",
            }
        ), pytest.raises(AnsibleExitJson) as exc_info:
            self.module.main()

        assert exc_info.value.args[0]["changed"] is False
        storage_api.upload.post.assert_not_called()
