#
# Copyright (c) 2026, Clément Cruau (@PendaGTP) <38917281+PendaGTP@users.noreply.github.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


from unittest.mock import Mock, patch

import pytest

proxmoxer = pytest.importorskip("proxmoxer")

from ansible.module_utils import basic
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    ModuleTestCase,
    set_module_args,
)

from ansible_collections.community.proxmox.plugins.module_utils.proxmox_acme_certificate import (
    cert_info_to_ansible_result,
    parse_acme_config,
)
from ansible_collections.community.proxmox.plugins.modules import proxmox_acme_certificate
from ansible_collections.community.proxmox.plugins.modules.proxmox_acme_certificate import (
    build_acme_property_string,
    build_acmedomain_property_string,
    find_acme_certificate,
    normalize_domain_list,
)

NODE_NAME = "pve-001"
UPID_ORDER = "UPID:pve-001:00180447:09B4EA04:69E1C426:acmenewcert::root@pam:"
UPID_REVOKE = "UPID:pve-001:0014714A:0979C6AF:69E12CC2:acmerevoke::root@pam:"
UPID_UNKNOWN = "UPID:unknown:unknown:unknown:unknown:unknown::root@pam:"

NODE_CONFIG_WITH_ACME = {
    "acme": "account=production",
    "acmedomain0": "domain=pve.example.com,plugin=cloudflare",
}

NODE_CONFIG_EMPTY = {}

SAMPLE_CERT_ACME = {
    "filename": "pveproxy-ssl.pem",
    "fingerprint": "12:34:56",
    "issuer": "...",
    "notafter": 1837175623,
    "notbefore": 1774103623,
    "pem": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
    "san": [],
    "subject": "CN = pve.example.com",
}

SAMPLE_CERT_PROXMOX = {
    "filename": "pve-ssl.pem",
    "fingerprint": "11:22:33",
    "issuer": "...",
    "pem": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
    "san": ["127.0.0.1"],
    "subject": "/OU=PVE Cluster Node/O=Proxmox Virtual Environment/CN=pve-001",
}


def exit_json(*args, **kwargs):
    kwargs.setdefault("changed", False)
    raise SystemExit(kwargs)


def fail_json(*args, **kwargs):
    kwargs["failed"] = True
    raise SystemExit(kwargs)


def build_module_args(state="present", **overrides):
    args = {
        "api_host": "host",
        "api_user": "user",
        "api_password": "password",
        "node_name": NODE_NAME,
        "state": state,
    }
    if state == "present":
        args.setdefault("account", "production")
        args.setdefault("domains", [{"domain": "pve.example.com", "plugin": "cloudflare"}])
    args.update(overrides)
    return args


class TestHelpers:
    def test_build_acme_property_string(self):
        assert build_acme_property_string("prod") == "account=prod"

    def test_build_acmedomain_property_string_full(self):
        result = build_acmedomain_property_string("pve.example.com", plugin="cloudflare", alias="alt.example.com")
        assert result == "domain=pve.example.com,plugin=cloudflare,alias=alt.example.com"

    def test_build_acmedomain_property_string_domain_only(self):
        result = build_acmedomain_property_string("pve.example.com")
        assert result == "domain=pve.example.com"

    def test_parse_acme_config_with_domains(self):
        result = parse_acme_config(NODE_CONFIG_WITH_ACME)
        assert result["account"] == "production"
        assert len(result["domains"]) == 1
        assert result["domains"][0]["domain"] == "pve.example.com"
        assert result["domains"][0]["plugin"] == "cloudflare"
        assert result["domains"][0]["alias"] is None

    def test_parse_acme_config_empty(self):
        result = parse_acme_config(NODE_CONFIG_EMPTY)
        assert result == {"account": None, "domains": []}

    def test_parse_acme_config_multiple_domains(self):
        config = {
            "acme": "account=staging",
            "acmedomain0": "domain=a.example.com,plugin=cf",
            "acmedomain1": "domain=b.example.com,plugin=cf,alias=val.example.com",
        }
        result = parse_acme_config(config)
        assert result["account"] == "staging"
        assert len(result["domains"]) == 2  # noqa: PLR2004
        assert result["domains"][1]["alias"] == "val.example.com"

    def test_find_acme_certificate_skips_proxmox(self):
        cert = find_acme_certificate([SAMPLE_CERT_PROXMOX, SAMPLE_CERT_ACME])
        assert cert is SAMPLE_CERT_ACME

    def test_find_acme_certificate_none_when_empty(self):
        assert find_acme_certificate([]) is None
        assert find_acme_certificate(None) is None

    def test_find_acme_certificate_none_when_only_proxmox(self):
        assert find_acme_certificate([SAMPLE_CERT_PROXMOX]) is None

    def test_normalize_domain_list_sorting(self):
        domains = [
            {"domain": "b.example.com", "plugin": "cf", "alias": None},
            {"domain": "a.example.com", "plugin": None, "alias": None},
        ]
        result = normalize_domain_list(domains)
        assert result[0]["domain"] == "a.example.com"
        assert result[1]["domain"] == "b.example.com"

    def test_normalize_domain_list_case_insensitive(self):
        domains = [{"domain": "PVE.Example.COM", "plugin": "CF"}]
        result = normalize_domain_list(domains)
        assert result[0]["domain"] == "pve.example.com"
        assert result[0]["plugin"] == "CF"

    def test_build_then_parse_roundtrip(self):
        built = build_acmedomain_property_string("pve.example.com", plugin="cf", alias="alt.example.com")
        config = {"acme": "account=test", "acmedomain0": built}
        parsed = parse_acme_config(config)
        assert parsed["account"] == "test"
        assert parsed["domains"][0] == {"domain": "pve.example.com", "plugin": "cf", "alias": "alt.example.com"}


class TestProxmoxAcmeCertificateModule(ModuleTestCase):
    def setUp(self):
        super().setUp()
        self.module = proxmox_acme_certificate
        self.warn_mock = Mock()
        self.mock_module_helper = patch.multiple(
            basic.AnsibleModule,
            exit_json=exit_json,
            fail_json=fail_json,
            warn=self.warn_mock,
        )
        self.mock_module_helper.start()
        self.connect_mock = patch(
            "ansible_collections.community.proxmox.plugins.module_utils.proxmox.ProxmoxAnsible._connect",
        ).start()
        mock_api = self.connect_mock.return_value
        node_mock = mock_api.nodes.return_value
        self.node_config = node_mock.config
        self.cert_info = node_mock.certificates.info
        self.cert_acme = node_mock.certificates.acme.certificate
        self.cert_acme.post.return_value = UPID_ORDER
        self.wait_mock = patch.object(
            proxmox_acme_certificate.ProxmoxAcmeCertificateAnsible,
            "_wait_certificate_task",
        ).start()
        self.wait_revoke_mock = patch.object(
            proxmox_acme_certificate.ProxmoxAcmeCertificateAnsible,
            "_wait_revocation_task",
        ).start()

    def tearDown(self):
        self.wait_revoke_mock.stop()
        self.wait_mock.stop()
        self.connect_mock.stop()
        self.mock_module_helper.stop()
        super().tearDown()

    def _run_module(self, args):
        with pytest.raises(SystemExit) as exc_info, set_module_args(args):
            self.module.main()
        return exc_info.value.args[0]

    def _check_mode_args(self, **kwargs):
        return {**build_module_args(**kwargs), "_ansible_check_mode": True}

    # -- state=present

    def test_present_creates_certificate(self):
        self.node_config.get.return_value = NODE_CONFIG_EMPTY
        self.cert_info.get.return_value = [SAMPLE_CERT_ACME]

        result = self._run_module(build_module_args())

        assert result["changed"] is True
        assert "successfully ordered" in result["msg"]
        assert result["node_name"] == NODE_NAME
        assert result["account"] == "production"
        assert result["fingerprint"] == SAMPLE_CERT_ACME["fingerprint"]
        assert result["issuer"] == SAMPLE_CERT_ACME["issuer"]
        self.node_config.put.assert_called_once()
        put_kwargs = self.node_config.put.call_args[1]
        assert "acme" in put_kwargs
        assert "account=production" in put_kwargs["acme"]
        self.cert_acme.post.assert_called_once()

    def test_present_idempotent(self):
        self.node_config.get.return_value = NODE_CONFIG_WITH_ACME
        self.cert_info.get.return_value = [SAMPLE_CERT_PROXMOX, SAMPLE_CERT_ACME]

        result = self._run_module(build_module_args())

        assert result["changed"] is False
        assert "already up to date" in result["msg"]
        assert result["fingerprint"] == SAMPLE_CERT_ACME["fingerprint"]
        assert self.node_config.put.call_count == 0
        assert self.cert_acme.post.call_count == 0

    def test_present_updates_on_account_change(self):
        self.node_config.get.return_value = {
            "acme": "account=old-account",
            "acmedomain0": "domain=pve.example.com,plugin=cloudflare",
        }
        self.cert_info.get.return_value = [SAMPLE_CERT_ACME]

        result = self._run_module(build_module_args())

        assert result["changed"] is True
        assert "successfully ordered" in result["msg"]
        self.node_config.put.assert_called_once()
        self.cert_acme.post.assert_called_once()

    def test_present_updates_on_domain_change(self):
        self.node_config.get.return_value = {
            "acme": "account=production",
            "acmedomain0": "domain=old.example.com,plugin=cloudflare",
        }
        self.cert_info.get.return_value = [SAMPLE_CERT_ACME]

        result = self._run_module(build_module_args())

        assert result["changed"] is True
        self.node_config.put.assert_called_once()
        self.cert_acme.post.assert_called_once()

    def test_present_orders_when_no_cert_exists(self):
        self.node_config.get.return_value = NODE_CONFIG_WITH_ACME
        self.cert_info.get.side_effect = [
            [SAMPLE_CERT_PROXMOX],  # first read: only Proxmox cert
            [SAMPLE_CERT_ACME],  # after ordering
        ]

        result = self._run_module(build_module_args())

        assert result["changed"] is True
        assert "successfully ordered" in result["msg"]
        self.cert_acme.post.assert_called_once()

    def test_present_standalone_domain_without_plugin(self):
        self.node_config.get.return_value = NODE_CONFIG_EMPTY
        self.cert_info.get.return_value = [SAMPLE_CERT_ACME]

        result = self._run_module(
            build_module_args(
                domains=[{"domain": "pve.example.com"}],
            )
        )

        assert result["changed"] is True
        assert "successfully ordered" in result["msg"]
        put_kwargs = self.node_config.put.call_args[1]
        assert "acmedomain0" in put_kwargs
        assert "domain=pve.example.com" in put_kwargs["acmedomain0"]
        self.cert_acme.post.assert_called_once()

    def test_present_mixed_standalone_and_dns_domains(self):
        self.node_config.get.return_value = NODE_CONFIG_EMPTY
        self.cert_info.get.return_value = [SAMPLE_CERT_ACME]

        result = self._run_module(
            build_module_args(
                domains=[
                    {"domain": "standalone.example.com"},
                    {"domain": "dns.example.com", "plugin": "cloudflare"},
                ],
            )
        )

        assert result["changed"] is True
        put_kwargs = self.node_config.put.call_args[1]
        assert "acmedomain0" in put_kwargs
        assert "domain=standalone.example.com" in put_kwargs["acmedomain0"]
        assert "plugin" not in put_kwargs["acmedomain0"]
        assert "acmedomain1" in put_kwargs
        assert "domain=dns.example.com" in put_kwargs["acmedomain1"]
        assert "plugin=cloudflare" in put_kwargs["acmedomain1"]

    def test_present_check_mode_create(self):
        self.node_config.get.return_value = NODE_CONFIG_EMPTY

        result = self._run_module(self._check_mode_args())

        assert result["changed"] is True
        assert "would be ordered" in result["msg"]
        assert self.node_config.put.call_count == 0
        assert self.cert_acme.post.call_count == 0

    def test_present_check_mode_idempotent(self):
        self.node_config.get.return_value = NODE_CONFIG_WITH_ACME
        self.cert_info.get.return_value = [SAMPLE_CERT_ACME]

        result = self._run_module(self._check_mode_args())

        assert result["changed"] is False
        assert "already up to date" in result["msg"]

    def test_present_check_mode_force(self):
        self.node_config.get.return_value = NODE_CONFIG_WITH_ACME

        result = self._run_module(self._check_mode_args(force=True))

        assert result["changed"] is True
        assert "would be ordered" in result["msg"]
        assert self.cert_acme.post.call_count == 0

    # -- state=absent

    def test_absent_deletes(self):
        self.node_config.get.return_value = NODE_CONFIG_WITH_ACME

        result = self._run_module(build_module_args(state="absent"))

        assert result["changed"] is True
        assert "successfully removed" in result["msg"]
        self.cert_acme.delete.assert_called_once()
        cleanup_call = self.node_config.put.call_args
        assert "acme" in cleanup_call[1]["delete"]
        assert "acmedomain0" in cleanup_call[1]["delete"]

    def test_absent_when_no_config(self):
        self.node_config.get.return_value = NODE_CONFIG_EMPTY

        result = self._run_module(build_module_args(state="absent"))

        assert result["changed"] is False
        assert "No ACME configuration" in result["msg"]
        assert self.cert_acme.delete.call_count == 0
        assert self.node_config.put.call_count == 0

    def test_absent_check_mode(self):
        self.node_config.get.return_value = NODE_CONFIG_WITH_ACME

        result = self._run_module(self._check_mode_args(state="absent"))

        assert result["changed"] is True
        assert "would be removed" in result["msg"]
        assert self.cert_acme.delete.call_count == 0
        assert self.node_config.put.call_count == 0

    def test_absent_waits_for_revocation_task(self):
        self.node_config.get.return_value = NODE_CONFIG_WITH_ACME
        self.cert_acme.delete.return_value = UPID_REVOKE

        result = self._run_module(build_module_args(state="absent"))

        assert result["changed"] is True
        self.wait_revoke_mock.assert_called_once_with(NODE_NAME, UPID_REVOKE)

    # -- result

    def test_cert_info_to_ansible_result(self):
        result = cert_info_to_ansible_result(SAMPLE_CERT_ACME)
        assert result["certificate"] == SAMPLE_CERT_ACME["pem"]
        assert result["fingerprint"] == SAMPLE_CERT_ACME["fingerprint"]
        assert result["issuer"] == SAMPLE_CERT_ACME["issuer"]
        assert result["subject"] == SAMPLE_CERT_ACME["subject"]
        assert result["not_before"] == SAMPLE_CERT_ACME["notbefore"]
        assert result["not_after"] == SAMPLE_CERT_ACME["notafter"]
        assert result["subject_alternative_names"] == SAMPLE_CERT_ACME["san"]

    # -- Error handling

    def test_config_read_failure(self):
        self.node_config.get.side_effect = Exception()

        result = self._run_module(build_module_args())

        assert result.get("failed") is True
        assert "Failed to read node config" in result["msg"]

    def test_order_failure(self):
        self.node_config.get.return_value = NODE_CONFIG_EMPTY
        self.cert_acme.post.side_effect = Exception()

        result = self._run_module(build_module_args())

        assert result.get("failed") is True
        assert "Failed to order" in result["msg"]

    def test_order_failure_custom_cert_exists(self):
        self.node_config.get.return_value = NODE_CONFIG_EMPTY
        self.cert_acme.post.side_effect = Exception(
            "400 Bad Request: Parameter verification failed. "
            "- {'force': \"Custom certificate exists but 'force' is not set.\"}"
        )

        result = self._run_module(build_module_args(force=False))

        assert result.get("failed") is True
        assert "custom certificate already exists" in result["msg"].lower()
        assert "force=true" in result["msg"]

    def test_too_many_domains(self):
        domains = [{"domain": f"d{i}.example.com", "plugin": "cf"} for i in range(7)]

        result = self._run_module(build_module_args(domains=domains))

        assert result.get("failed") is True
        assert "maximum of 6" in result["msg"]

    def test_configure_node_failure(self):
        self.node_config.get.return_value = NODE_CONFIG_EMPTY
        self.node_config.put.side_effect = Exception()

        result = self._run_module(build_module_args())

        assert result.get("failed") is True
        assert "Failed to configure ACME settings" in result["msg"]

    def test_cert_info_read_failure(self):
        self.node_config.get.return_value = NODE_CONFIG_EMPTY
        self.cert_info.get.side_effect = Exception()

        result = self._run_module(build_module_args())

        assert result.get("failed") is True
        assert "Failed to read certificates info" in result["msg"]
