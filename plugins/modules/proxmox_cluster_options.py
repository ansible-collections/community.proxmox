#!/usr/bin/python

# Copyright (c) 2026, FingerlessGloves
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_cluster_options
short_description: Manage datacenter-wide options for a Proxmox VE cluster
version_added: "2.1.0"
author:
  - FingerlessGloves (@FingerlessGlov3s)
description:
  - Manage the datacenter-wide cluster options exposed by the Proxmox VE C(/cluster/options) API endpoint.
  - These are the settings found under B(Datacenter -> Options) in the Proxmox VE web interface.
  - All options are optional. Only the options you set are changed; any option you do not specify is left untouched.
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  keyboard:
    description:
      - Default keyboard layout for the VNC console.
    type: str
    choices:
      - de
      - de-ch
      - da
      - en-gb
      - en-us
      - es
      - fi
      - fr
      - fr-be
      - fr-ca
      - fr-ch
      - hu
      - is
      - it
      - ja
      - lt
      - mk
      - nl
      - "no"
      - pl
      - pt
      - pt-br
      - sv
      - sl
      - tr
  language:
    description:
      - Default language used in the web interface.
    type: str
    choices:
      - ar
      - ca
      - da
      - de
      - en
      - es
      - eu
      - fa
      - fr
      - hr
      - he
      - it
      - ja
      - ka
      - kr
      - nb
      - nl
      - nn
      - pl
      - pt_BR
      - ru
      - sl
      - sv
      - tr
      - ukr
      - zh_CN
      - zh_TW
  console:
    description:
      - Default console viewer to use.
    type: str
    choices:
      - applet
      - vv
      - html5
      - xtermjs
  mac_prefix:
    description:
      - Prefix for the automatically generated MAC addresses of virtual machine network interfaces.
      - Set to V(off) to let Proxmox VE use a fully random MAC address.
    type: str
  max_workers:
    description:
      - Defines the maximum number of workers that may run in parallel on a single cluster node during cluster-wide tasks, for example a bulk migration.
    type: int
  email_from:
    description:
      - Sender address used when Proxmox VE sends notification emails.
    type: str
  http_proxy:
    description:
      - HTTP proxy server used to download updates and subscription information, for example V(http://username:password@host:port/).
    type: str
  fencing:
    description:
      - Fencing mode used for the high availability stack.
    type: str
    choices:
      - watchdog
      - hardware
      - both
  description:
    description:
      - Datacenter description or notes. Shown in the web interface.
    type: str
  migration:
    description:
      - Cluster-wide migration settings.
    type: dict
    suboptions:
      type:
        description:
          - Whether the migration traffic is tunneled over an SSH connection (V(secure)) or sent unencrypted (V(insecure)).
        type: str
        choices:
          - secure
          - insecure
      network:
        description:
          - CIDR of the network used for migration traffic, for example V(10.0.0.0/24).
        type: str
  replication:
    description:
      - Cluster-wide storage replication settings.
    type: dict
    suboptions:
      type:
        description:
          - Whether replication traffic is tunneled over an SSH connection (V(secure)) or sent unencrypted (V(insecure)).
        type: str
        choices:
          - secure
          - insecure
      network:
        description:
          - CIDR of the network used for replication traffic, for example V(10.0.0.0/24).
        type: str
  bwlimit:
    description:
      - Default bandwidth limits, in KiB/s, for various cluster-wide operations.
      - A value of V(0) means unlimited.
    type: dict
    suboptions:
      clone:
        description:
          - Bandwidth limit, in KiB/s, for cloning disks.
        type: int
      default:
        description:
          - Default bandwidth limit, in KiB/s, applied when a more specific limit is not set.
        type: int
      migration:
        description:
          - Bandwidth limit, in KiB/s, for migrating virtual machines.
        type: int
      move:
        description:
          - Bandwidth limit, in KiB/s, for moving disks.
        type: int
      restore:
        description:
          - Bandwidth limit, in KiB/s, for restoring guests from backups.
        type: int
  ha:
    description:
      - Cluster-wide high availability settings.
    type: dict
    suboptions:
      shutdown_policy:
        description:
          - Cluster-wide policy applied to high availability services when a node shuts down.
        type: str
        choices:
          - freeze
          - failover
          - conditional
          - migrate
  crs:
    description:
      - Cluster resource scheduling settings.
    type: dict
    suboptions:
      ha:
        description:
          - Scheduler mode used for high availability.
        type: str
        choices:
          - basic
          - static
          - dynamic
      ha_auto_rebalance:
        description:
          - Enable automatic rebalancing of high availability services.
        type: bool
      ha_auto_rebalance_hold_duration:
        description:
          - Minimum number of minutes to wait between automatic rebalancing runs.
        type: int
      ha_auto_rebalance_margin:
        description:
          - Minimum improvement, as a percentage, required before a service is rebalanced.
        type: int
      ha_auto_rebalance_method:
        description:
          - Method used to score nodes for automatic rebalancing.
        type: str
        choices:
          - bruteforce
          - topsis
      ha_auto_rebalance_threshold:
        description:
          - Minimum node load, as a percentage, before automatic rebalancing is considered.
        type: int
      ha_rebalance_on_start:
        description:
          - Rebalance high availability services automatically when they are started.
        type: bool
  next_id:
    description:
      - Bounds for the next free VMID range offered by the web interface.
    type: dict
    suboptions:
      lower:
        description:
          - Lowest VMID that is automatically suggested.
        type: int
      upper:
        description:
          - Upper bound (exclusive) for automatically suggested VMIDs.
        type: int
  consent_text:
    description:
      - Consent text shown to the user before login.
      - Multi-line text and Markdown are supported; provide plain text (for example a YAML block scalar).
      - The module transparently base64-encodes this value for the API, matching the Proxmox VE web
        interface, which stores it base64-encoded.
    type: str
  location:
    description:
      - Geographic location of the datacenter, used by the web interface.
    type: dict
    suboptions:
      latitude:
        description:
          - Latitude of the datacenter location.
        type: float
      longitude:
        description:
          - Longitude of the datacenter location.
        type: float
      name:
        description:
          - Human-readable name of the location.
        type: str
  u2f:
    description:
      - U2F two-factor authentication settings.
    type: dict
    suboptions:
      appid:
        description:
          - U2F AppId URL override. Defaults to the origin.
        type: str
      origin:
        description:
          - U2F origin override. Defaults to the server URL.
        type: str
  webauthn:
    description:
      - WebAuthn two-factor authentication settings.
    type: dict
    suboptions:
      allow_subdomains:
        description:
          - Whether to allow the origin to be a subdomain of the relying party identifier.
        type: bool
      id:
        description:
          - Relying party identifier, usually the domain name of the Proxmox VE deployment.
        type: str
      origin:
        description:
          - The site origin that WebAuthn requests are expected to come from.
        type: str
      rp:
        description:
          - Relying party name, usually the company or deployment name.
        type: str
  notify:
    description:
      - Cluster-wide notification settings.
    type: dict
    suboptions:
      fencing:
        description:
          - When to send notifications about node fencing.
        type: str
        choices:
          - always
          - never
      package_updates:
        description:
          - When to send notifications about available package updates.
        type: str
        choices:
          - auto
          - always
          - never
      replication:
        description:
          - When to send notifications about replication failures.
        type: str
        choices:
          - always
          - never
      target_fencing:
        description:
          - Notification target (endpoint or group) used for fencing notifications.
        type: str
      target_package_updates:
        description:
          - Notification target used for package update notifications.
        type: str
      target_replication:
        description:
          - Notification target used for replication notifications.
        type: str
  tag_style:
    description:
      - Tag style overrides for the web interface.
    type: dict
    suboptions:
      case_sensitive:
        description:
          - Treat tags as case-sensitive when ordering and coloring them.
        type: bool
      color_map:
        description:
          - Manual color mapping for tags, for example V(tag1:0000ff;tag2:00ff00).
        type: str
      ordering:
        description:
          - How tags are ordered in the web interface.
        type: str
        choices:
          - config
          - alphabetical
      shape:
        description:
          - Shape used to render tags in the web interface.
        type: str
        choices:
          - full
          - circle
          - dense
          - none
  user_tag_access:
    description:
      - Controls which tags non-privileged users may set.
    type: dict
    suboptions:
      user_allow:
        description:
          - Policy controlling which tags users may set.
        type: str
        choices:
          - none
          - list
          - existing
          - free
      user_allow_list:
        description:
          - List of tags users are allowed to set when O(user_tag_access.user_allow=list).
        type: list
        elements: str
  registered_tags:
    description:
      - List of tags that require C(Sys.Modify) permission on C(/) to set and remove.
    type: list
    elements: str
  delete:
    description:
      - List of options to unset, returning them to their Proxmox VE defaults.
      - Each entry is the name of an option of this module, for example V(mac_prefix) or V(migration).
      - An option cannot be both set and listed in O(delete) in the same task.
    type: list
    elements: str

seealso:
  - module: community.proxmox.proxmox_cluster_options_info
    description: Retrieve the current datacenter-wide cluster options.
  - name: Proxmox VE datacenter configuration
    description: Reference for the Proxmox VE datacenter configuration file (datacenter.cfg).
    link: https://pve.proxmox.com/wiki/Manual:_datacenter.cfg

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Set the default keyboard layout and console viewer
  community.proxmox.proxmox_cluster_options:
    keyboard: en-gb
    console: xtermjs

- name: Configure secure migration over a dedicated network
  community.proxmox.proxmox_cluster_options:
    migration:
      type: secure
      network: 10.0.0.0/24

- name: Tune cluster resource scheduling
  community.proxmox.proxmox_cluster_options:
    crs:
      ha: static
      ha_rebalance_on_start: true

- name: Limit migration and restore bandwidth
  community.proxmox.proxmox_cluster_options:
    bwlimit:
      migration: 102400
      restore: 51200

- name: Clear the MAC prefix and HTTP proxy
  community.proxmox.proxmox_cluster_options:
    delete:
      - mac_prefix
      - http_proxy
"""

RETURN = r"""
cluster_options:
  description: The datacenter-wide cluster options after the module has run.
  returned: on success
  type: dict
  sample:
    keyboard: en-gb
    mac_prefix: "BC:24:11"
    migration:
      type: secure
      network: 10.0.0.0/24
msg:
  description: A short message describing what the module did.
  returned: always
  type: str
  sample: "Cluster options updated"
"""

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
)
from ansible_collections.community.proxmox.plugins.module_utils.proxmox_cluster_options import (
    ECHOED_DEFAULTS,
    LIST_FIELDS,
    PROPERTY_STRING_FIELDS,
    SCALAR_FIELDS,
    ansible_option_to_api,
    build_property_string,
    cluster_options_to_ansible_result,
    scalar_to_api,
)


def module_args():
    return dict(
        keyboard=dict(
            type="str",
            choices=[
                "de",
                "de-ch",
                "da",
                "en-gb",
                "en-us",
                "es",
                "fi",
                "fr",
                "fr-be",
                "fr-ca",
                "fr-ch",
                "hu",
                "is",
                "it",
                "ja",
                "lt",
                "mk",
                "nl",
                "no",
                "pl",
                "pt",
                "pt-br",
                "sv",
                "sl",
                "tr",
            ],
        ),
        language=dict(
            type="str",
            choices=[
                "ar",
                "ca",
                "da",
                "de",
                "en",
                "es",
                "eu",
                "fa",
                "fr",
                "hr",
                "he",
                "it",
                "ja",
                "ka",
                "kr",
                "nb",
                "nl",
                "nn",
                "pl",
                "pt_BR",
                "ru",
                "sl",
                "sv",
                "tr",
                "ukr",
                "zh_CN",
                "zh_TW",
            ],
        ),
        console=dict(type="str", choices=["applet", "vv", "html5", "xtermjs"]),
        mac_prefix=dict(type="str"),
        max_workers=dict(type="int"),
        email_from=dict(type="str"),
        http_proxy=dict(type="str"),
        fencing=dict(type="str", choices=["watchdog", "hardware", "both"]),
        description=dict(type="str"),
        migration=dict(
            type="dict",
            options=dict(
                type=dict(type="str", choices=["secure", "insecure"]),
                network=dict(type="str"),
            ),
        ),
        replication=dict(
            type="dict",
            options=dict(
                type=dict(type="str", choices=["secure", "insecure"]),
                network=dict(type="str"),
            ),
        ),
        bwlimit=dict(
            type="dict",
            options=dict(
                clone=dict(type="int"),
                default=dict(type="int"),
                migration=dict(type="int"),
                move=dict(type="int"),
                restore=dict(type="int"),
            ),
        ),
        ha=dict(
            type="dict",
            options=dict(
                shutdown_policy=dict(type="str", choices=["freeze", "failover", "conditional", "migrate"]),
            ),
        ),
        crs=dict(
            type="dict",
            options=dict(
                ha=dict(type="str", choices=["basic", "static", "dynamic"]),
                ha_auto_rebalance=dict(type="bool"),
                ha_auto_rebalance_hold_duration=dict(type="int"),
                ha_auto_rebalance_margin=dict(type="int"),
                ha_auto_rebalance_method=dict(type="str", choices=["bruteforce", "topsis"]),
                ha_auto_rebalance_threshold=dict(type="int"),
                ha_rebalance_on_start=dict(type="bool"),
            ),
        ),
        next_id=dict(
            type="dict",
            options=dict(
                lower=dict(type="int"),
                upper=dict(type="int"),
            ),
        ),
        consent_text=dict(type="str"),
        location=dict(
            type="dict",
            options=dict(
                latitude=dict(type="float"),
                longitude=dict(type="float"),
                name=dict(type="str"),
            ),
        ),
        u2f=dict(
            type="dict",
            options=dict(
                appid=dict(type="str"),
                origin=dict(type="str"),
            ),
        ),
        webauthn=dict(
            type="dict",
            options=dict(
                allow_subdomains=dict(type="bool"),
                id=dict(type="str"),
                origin=dict(type="str"),
                rp=dict(type="str"),
            ),
        ),
        notify=dict(
            type="dict",
            options=dict(
                fencing=dict(type="str", choices=["always", "never"]),
                package_updates=dict(type="str", choices=["auto", "always", "never"]),
                replication=dict(type="str", choices=["always", "never"]),
                target_fencing=dict(type="str"),
                target_package_updates=dict(type="str"),
                target_replication=dict(type="str"),
            ),
        ),
        tag_style=dict(
            type="dict",
            options=dict(
                case_sensitive=dict(type="bool"),
                color_map=dict(type="str"),
                ordering=dict(type="str", choices=["config", "alphabetical"]),
                shape=dict(type="str", choices=["full", "circle", "dense", "none"]),
            ),
        ),
        user_tag_access=dict(
            type="dict",
            options=dict(
                user_allow=dict(type="str", choices=["none", "list", "existing", "free"]),
                user_allow_list=dict(type="list", elements="str"),
            ),
        ),
        registered_tags=dict(type="list", elements="str"),
        delete=dict(type="list", elements="str"),
    )


def module_options():
    return {}


# All option names this module manages, excluding the meta option ``delete``.
MANAGED_FIELDS = tuple(SCALAR_FIELDS) + tuple(PROPERTY_STRING_FIELDS) + tuple(LIST_FIELDS)


class ProxmoxClusterOptionsAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def run(self):
        self._apply()

    def validate_params(self):
        delete = self.params.get("delete") or []
        unknown = [name for name in delete if name not in MANAGED_FIELDS]
        if unknown:
            self.module.fail_json(msg=f"Unknown option(s) in delete: {', '.join(sorted(unknown))}")

        clashing = [name for name in delete if self.params.get(name) is not None]
        if clashing:
            self.module.fail_json(
                msg=f"Option(s) cannot be both set and deleted in the same task: {', '.join(sorted(clashing))}"
            )

    def _get_options(self):
        try:
            return self.proxmox_api.cluster().options.get()
        except Exception as e:
            self.module.fail_json(msg=f"Failed to retrieve cluster options: {to_native(e)}")

    def _desired_ansible(self):
        """Build the desired state, including only the options the user actually set."""
        desired = {}
        for field in MANAGED_FIELDS:
            value = self.params.get(field)
            if value is not None:
                desired[field] = value
        return desired

    def _ansible_to_api_payload(self, desired, current_ansible):
        """Convert the desired Ansible state into the API payload for PUT."""
        payload = {}
        for field, value in desired.items():
            if field in PROPERTY_STRING_FIELDS:
                encoded = build_property_string(field, value)
                if encoded is not None:
                    payload[PROPERTY_STRING_FIELDS[field]["api"]] = encoded
            elif field in LIST_FIELDS:
                sep = LIST_FIELDS[field]["sep"]
                payload[LIST_FIELDS[field]["api"]] = sep.join(str(t) for t in value)
            else:
                # Scalar option; use the raw API name (e.g. consent_text -> consent-text)
                # and apply any required encoding (e.g. URL-encoding for consent_text).
                payload[ansible_option_to_api(field)] = scalar_to_api(field, value)

        to_delete = [ansible_option_to_api(name) for name in self._will_delete(current_ansible)]
        if to_delete:
            payload["delete"] = ",".join(to_delete)

        return payload

    def _options_differ(self, current_ansible, desired_ansible):
        for key, desired_value in desired_ansible.items():
            if key in PROPERTY_STRING_FIELDS:
                if self._dict_subset_differs(current_ansible.get(key), desired_value):
                    return True
            elif current_ansible.get(key) != desired_value:
                return True
        return False

    def _dict_subset_differs(self, current_sub, desired_sub):
        current_sub = current_sub or {}
        return any(current_sub.get(k) != v for k, v in desired_sub.items())

    def _will_delete(self, current_ansible):
        """Names that genuinely need deleting (present, and not already at an echoed default)."""
        names = []
        for name in self.params.get("delete") or []:
            if name not in current_ansible:
                continue
            # Some fields are always echoed with a default value even when unset; if the current
            # value equals that default, the option is effectively unset, so deleting is a no-op.
            if name in ECHOED_DEFAULTS and current_ansible[name] == ECHOED_DEFAULTS[name]:
                continue
            names.append(name)
        return names

    def _apply(self):
        current = self._get_options()
        current_ansible = cluster_options_to_ansible_result(current)
        desired = self._desired_ansible()

        differs = self._options_differ(current_ansible, desired)
        will_delete = self._will_delete(current_ansible)

        if not differs and not will_delete:
            self.module.exit_json(
                changed=False,
                msg="Cluster options already match the desired state",
                cluster_options=current_ansible,
            )

        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                msg="Cluster options would be updated",
                cluster_options=current_ansible,
            )

        payload = self._ansible_to_api_payload(desired, current_ansible)
        try:
            self.proxmox_api.cluster().options.put(**payload)
        except Exception as e:
            self.module.fail_json(msg=f"Failed to set cluster options: {to_native(e)}")

        updated = cluster_options_to_ansible_result(self._get_options())
        self.module.exit_json(changed=True, msg="Cluster options updated", cluster_options=updated)


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxClusterOptionsAnsible(module)
    proxmox.validate_params()

    try:
        proxmox.run()
    except Exception as e:
        module.fail_json(msg=f"An error occurred: {to_native(e)}")


if __name__ == "__main__":
    main()
