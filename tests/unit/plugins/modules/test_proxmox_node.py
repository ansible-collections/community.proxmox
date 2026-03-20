# Copyright (c) 2025, Florian Paul Azim Hoberg (@gyptazy) <florian.hoberg@credativ.de>
#
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest.mock import MagicMock, patch

import pytest

proxmoxer = pytest.importorskip("proxmoxer")

from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    ModuleTestCase,
    set_module_args,
)

import ansible_collections.community.proxmox.plugins.module_utils.proxmox as proxmox_utils
from ansible_collections.community.proxmox.plugins.modules import proxmox_node

# Minimal valid PEM certificate for fingerprint tests
SAMPLE_PEM_CERT = """-----BEGIN CERTIFICATE-----
MFAwRgIBADADBgEAMAAwHhcNNTAwMTAxMDAwMDAwWhcNNDkxMjMxMjM1OTU5WjAAMBgwCwYJKoZIhvcNAQEBAwkAMAYCAQACAQAwAwYBAAMBAA==
-----END CERTIFICATE-----"""


def get_certificate_module_args(  # noqa:PLR0913
    cert=None,
    certificate=None,
    key=None,
    private_key=None,
    state="present",
    restart=False,
    force=False,
    check_mode=False,
):
    """Build module args for certificate management."""
    args = {
        "api_host": "localhost",
        "api_user": "root@pam",
        "api_password": "secret",
        "node_name": "test-node",
        "certificates": {
            "cert": cert,
            "certificate": certificate,
            "key": key,
            "private_key": private_key,
            "state": state,
            "restart": restart,
            "force": force,
        },
    }
    if check_mode:
        args["_ansible_check_mode"] = True
    return args


# --- Legacy tests (power_state, subscription) - use MagicMock style ---

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import ProxmoxAnsible


@pytest.fixture
def module_args_power_on():
    return {
        "api_host": "proxmoxhost",
        "api_user": "root@pam",
        "api_password": "secret",
        "validate_certs": False,
        "node_name": "test-node",
        "power_state": "online",
    }


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_power_state_present(mock_api, mock_init, module_args_power_on):
    module = MagicMock(spec=AnsibleModule)
    module.params = module_args_power_on
    module.check_mode = False

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance

    nodes = {"nodes": {"test-node": {"name": "test-node", "status": "offline"}}}

    module.exit_json = lambda **kwargs: (x for x in ()).throw(SystemExit(kwargs))
    module.fail_json = lambda **kwargs: (x for x in ()).throw(SystemExit(kwargs))

    proxmox = proxmox_node.ProxmoxNodeAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    with patch.object(mock_api_instance.nodes("test-node").wakeonlan, "post") as mock_post:
        changed, msg = proxmox.power_state(nodes)

    assert changed is True
    assert "powered on" in msg
    mock_post.assert_called_once_with(node_name="test-node")


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_power_state_already_online(mock_api, mock_init, module_args_power_on):
    module = MagicMock(spec=AnsibleModule)
    module.params = module_args_power_on
    module.check_mode = False

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance

    nodes = {"nodes": {"test-node": {"name": "test-node", "status": "online"}}}

    proxmox = proxmox_node.ProxmoxNodeAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    changed, msg = proxmox.power_state(nodes)

    assert changed is False
    assert "already online" in msg


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_subscription_present_new_key(mock_api, mock_init):
    module = MagicMock(spec=AnsibleModule)
    module.params = {"node_name": "test-node", "subscription": {"state": "present", "key": "ABCD-1234"}}
    module.check_mode = False

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance
    mock_api_instance.nodes("test-node").subscription.get.return_value = {"key": "OLD-KEY"}

    module.exit_json = lambda **kwargs: (x for x in ()).throw(SystemExit(kwargs))
    module.fail_json = lambda **kwargs: (x for x in ()).throw(SystemExit(kwargs))

    proxmox = proxmox_node.ProxmoxNodeAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    changed, msg = proxmox.subscription()

    assert changed is True
    assert "uploaded" in msg
    mock_api_instance.nodes("test-node").subscription.put.assert_called_once_with(key="ABCD-1234")


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
@patch.object(ProxmoxAnsible, "proxmox_api", create=True)
def test_subscription_already_present(mock_api, mock_init):
    module = MagicMock(spec=AnsibleModule)
    module.params = {"node_name": "test-node", "subscription": {"state": "present", "key": "ABCD-1234"}}
    module.check_mode = False

    mock_api_instance = MagicMock()
    mock_api.return_value = mock_api_instance
    mock_api_instance.nodes("test-node").subscription.get.return_value = {"key": "ABCD-1234"}

    proxmox = proxmox_node.ProxmoxNodeAnsible(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api_instance

    changed, msg = proxmox.subscription()

    assert changed is False
    assert msg == "Unchanged"
    mock_api_instance.nodes("test-node").subscription.put.assert_not_called()


class TestProxmoxNodeCertificate(ModuleTestCase):
    def setUp(self):
        super().setUp()
        proxmox_utils.HAS_PROXMOXER = True
        self.module = proxmox_node

        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()

        mock_api = self.connect_mock.return_value
        mock_api.version.get.return_value = {}
        mock_api.nodes.get.return_value = [{"node": "test-node", "status": "online"}]

        node_mock = mock_api.nodes.return_value
        mock_api.nodes.side_effect = lambda n: node_mock
        node_mock.certificates.info.get.return_value = []
        node_mock.certificates.custom.post.return_value = None
        node_mock.certificates.custom.delete.return_value = None

        self.mock_read_file = patch.object(
            proxmox_node.ProxmoxNodeAnsible, "read_file", return_value=SAMPLE_PEM_CERT
        ).start()
        self.mock_get_fingerprints_file = patch.object(
            proxmox_node.ProxmoxNodeAnsible,
            "get_leaf_certificate_fingerprint",
            return_value="AA:BB:CC:DD",
        ).start()
        self.mock_get_fingerprints_api = patch.object(
            proxmox_node.ProxmoxNodeAnsible,
            "get_certificate_fingerprints_api",
            return_value=[],
        ).start()
        self.mock_get_custom_certs = patch.object(
            proxmox_node.ProxmoxNodeAnsible, "_get_custom_certificates", return_value=[]
        ).start()

    def tearDown(self):
        self.mock_get_custom_certs.stop()
        self.mock_get_fingerprints_api.stop()
        self.mock_get_fingerprints_file.stop()
        self.mock_read_file.stop()
        self.connect_mock.stop()
        super().tearDown()

    def _run_module(self, args):
        with pytest.raises(AnsibleExitJson) as exc_info, set_module_args(args):
            self.module.main()
        return exc_info.value.args[0]

    def _run_module_fail(self, args):
        with pytest.raises(AnsibleFailJson) as exc_info, set_module_args(args):
            self.module.main()
        return exc_info.value.args[0]

    def test_certificate_present_new_upload(self):
        self.mock_get_fingerprints_api.return_value = []
        result = self._run_module(get_certificate_module_args(cert="/path/to/cert.pem"))

        assert result["changed"] is True
        assert "updated" in result["certificates"]
        node_mock = self.connect_mock.return_value.nodes.return_value
        node_mock.certificates.custom.post.assert_called_once()

    def test_certificate_present_already_present_no_force(self):
        self.mock_get_fingerprints_api.return_value = ["AA:BB:CC:DD"]
        result = self._run_module(get_certificate_module_args(cert="/path/to/cert.pem", force=False))

        assert result["changed"] is False
        assert "already present" in result["certificates"]
        node_mock = self.connect_mock.return_value.nodes.return_value
        node_mock.certificates.custom.post.assert_not_called()

    def test_certificate_present_force_overwrite(self):
        self.mock_get_fingerprints_api.return_value = ["AA:BB:CC:DD"]
        result = self._run_module(get_certificate_module_args(cert="/path/to/cert.pem", force=True))

        assert result["changed"] is True
        assert "overwritten" in result["certificates"]
        node_mock = self.connect_mock.return_value.nodes.return_value
        node_mock.certificates.custom.post.assert_called_once()

    def test_certificate_present_with_raw_certificate_no_file_read(self):
        self.mock_read_file.reset_mock()
        result = self._run_module(get_certificate_module_args(certificate=SAMPLE_PEM_CERT))

        self.mock_read_file.assert_not_called()
        assert result["changed"] is True

    def test_certificate_present_includes_private_key_when_provided(self):
        self.mock_read_file.side_effect = [
            SAMPLE_PEM_CERT,
            "-----BEGIN PRIVATE KEY-----\nxxx\n-----END PRIVATE KEY-----",
        ]
        result = self._run_module(get_certificate_module_args(cert="/path/cert.pem", key="/path/key.pem"))

        assert result["changed"] is True

    def test_certificate_present_check_mode_no_post(self):
        result = self._run_module(get_certificate_module_args(cert="/path/to/cert.pem", check_mode=True))

        assert result["changed"] is True
        assert "would be" in result["certificates"]
        node_mock = self.connect_mock.return_value.nodes.return_value
        node_mock.certificates.custom.post.assert_not_called()

    def test_certificate_present_fail_when_both_cert_and_certificate(self):
        result = self._run_module_fail(get_certificate_module_args(cert="/path/cert.pem", certificate=SAMPLE_PEM_CERT))

        assert result["failed"] is True
        assert "Cannot specify both cert" in result["msg"]

    def test_certificate_present_fail_when_both_key_and_private_key(self):
        result = self._run_module_fail(
            get_certificate_module_args(
                cert="/path/cert.pem",
                key="/path/key.pem",
                private_key="-----BEGIN PRIVATE KEY-----\nxxx\n-----END PRIVATE KEY-----",
            )
        )

        assert result["failed"] is True
        assert "Cannot specify both key" in result["msg"]

    def test_certificate_present_fail_when_neither_cert_nor_certificate(self):
        args = get_certificate_module_args()
        args["certificates"]["cert"] = None
        args["certificates"]["certificate"] = None

        result = self._run_module_fail(args)

        assert result["failed"] is True
        assert "certificate" in result["msg"].lower()

    def test_certificate_restart_only(self):
        args = get_certificate_module_args(restart=True)
        del args["certificates"]["state"]

        result = self._run_module(args)

        assert result["changed"] is True
        assert "restarted" in result["certificates"].lower()
        node_mock = self.connect_mock.return_value.nodes.return_value
        node_mock.certificates.custom.post.assert_not_called()
        node_mock.certificates.custom.delete.assert_not_called()
        node_mock.service.assert_called_with("pveproxy")

    def test_certificate_absent_deletes_when_custom_certs_exist(self):
        self.mock_get_custom_certs.return_value = [{"filename": "custom.pem", "fingerprint": "AA:BB:CC:DD"}]
        result = self._run_module(get_certificate_module_args(state="absent"))

        assert result["changed"] is True
        assert "deleted" in result["certificates"]
        node_mock = self.connect_mock.return_value.nodes.return_value
        node_mock.certificates.custom.delete.assert_called_once_with(restart=False)

    def test_certificate_absent_already_absent(self):
        self.mock_get_custom_certs.return_value = []
        result = self._run_module(get_certificate_module_args(state="absent"))

        assert result["changed"] is False
        assert "already absent" in result["certificates"]
        node_mock = self.connect_mock.return_value.nodes.return_value
        node_mock.certificates.custom.delete.assert_not_called()

    def test_certificate_absent_check_mode(self):
        self.mock_get_custom_certs.return_value = [{"filename": "custom.pem"}]
        result = self._run_module(get_certificate_module_args(state="absent", check_mode=True))

        assert result["changed"] is True
        assert "would be deleted" in result["certificates"]
        node_mock = self.connect_mock.return_value.nodes.return_value
        node_mock.certificates.custom.delete.assert_not_called()


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
def test_get_leaf_certificate_fingerprint_single_cert(mock_init):
    module = MagicMock(spec=AnsibleModule)
    module.params = {}

    proxmox = proxmox_node.ProxmoxNodeAnsible(module)

    fingerprint = proxmox.get_leaf_certificate_fingerprint(SAMPLE_PEM_CERT)

    assert fingerprint is not None
    assert ":" in fingerprint

    parts = fingerprint.split(":")
    assert all(len(p) == 2 for p in parts)  # noqa: PLR2004


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
def test_get_leaf_certificate_fingerprint_multiple_certs(mock_init):
    module = MagicMock(spec=AnsibleModule)
    module.params = {}

    proxmox = proxmox_node.ProxmoxNodeAnsible(module)

    pem_chain = SAMPLE_PEM_CERT + "\n" + SAMPLE_PEM_CERT

    fingerprint = proxmox.get_leaf_certificate_fingerprint(pem_chain)

    assert fingerprint is not None
    assert ":" in fingerprint


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
def test_get_leaf_certificate_fingerprint_invalid_pem(mock_init):
    module = MagicMock(spec=AnsibleModule)
    module.params = {}

    proxmox = proxmox_node.ProxmoxNodeAnsible(module)

    fingerprint = proxmox.get_leaf_certificate_fingerprint("invalid cert")

    assert fingerprint is None
