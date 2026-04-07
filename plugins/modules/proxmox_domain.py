#!/usr/bin/python
#
# Copyright (c) 2026, (@teslamania) <nicolas.vial@protonmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


DOCUMENTATION = r"""
module: proxmox_domain
version_added: 2.0.0
short_description: Manage authentication realms.
description:
  - Add, modify or delete domain authentication realms.
  - See L(Authentication Realms,https://pve.proxmox.com/pve-docs/chapter-pveum.html#user-realms-pam)
author: Vial Nicolas (@teslamania)
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none

options:
    openid_acr_values:
        description:
            - Defines the Authentication Context Class Reference values requested from the Authorization Server for the Authentication Request.
            - Supported for O(type=openid).
        type: str
    openid_autocreate:
        description:
            - Automatically create users if they do not exist.
            - Supported for O(type=openid).
        type: bool
    ldap_base_dn:
        description:
            - LDAP base domain name.
            - Required when O(type=ldap).
        type: str
    ldap_bind_dn:
        description:
            - LDAP user bind domain name.
            - Supported for O(type=ldap) and O(type=ad).
        type: str
        aliases: ["ad_bind_dn"]
    ad_case_sensitive:
        description:
            - Choose if username is case-sensitive or not.
            - Supported for O(type=ad).
        type: bool
        default: True
    comment:
        description: Description of the realm.
        type: str
    openid_client_id:
        description:
            - OpenID Client ID.
            - Required when O(type=openid).
        type: str
    openid_client_key:
        description:
            - OpenID Client key.
            - Supported for O(type=openid).
        type: str
    default:
        description: Use as default realm.
        type: bool
    ad_domain:
        description:
            - AD domain name.
            - Required when O(type=ad).
        type: str
    ldap_filter:
        description:
            - LDAP filter for user sync.
            - Supported for O(type=ldap) and O(type=ad).
        type: str
        aliases: ["ad_filter"]
    openid_issuer_url:
        description:
            - OpenID Issuer Url.
            - Required when O(type=openid).
        type: str
    openid_groups_autocreate:
        description:
            - Automatically create users if they do not exist.
            - Supported for O(type=openid).
        type: bool
    openid_groups_claim:
        description:
            - OpenID claim used to retrieve groups with.
            - Supported for O(type=openid).
        type: str
    openid_groups_overwrite:
        description:
            - All groups will be overwritten for the user on login.
            - Supported for O(type=openid).
        type: bool
    ldap_group_classes:
        description:
            - The object class for group (groupOfNames, group, univentionGroup, ipausergroup).
            - Supported for O(type=ldap) and O(type=ad).
        type: str
        aliases: ["ad_group_classes"]
    ldap_group_filter:
        description:
            - LDAP filter for group sync.
            - Supported for O(type=ldap) and O(type=ad).
        type: str
        aliases: ["ad_group_filter"]
    ldap_group_name_attr:
        description:
            - LDAP group attribute name.
            - Supported for O(type=ldap) and O(type=ad).
        type: str
        aliases: ["ad_group_name_attr"]
    ldap_mode:
        description:
            - LDAP protocol mode.
            - Supported for O(type=ldap) and O(type=ad).
        choices: ['ldap', 'ldaps', 'ldap+starttls']
        type: str
        aliases: ["ad_mode"]
    ldap_password:
        description:
            - LDAP bind password.
            - Supported for O(type=ldap) and O(type=ad).
        type: str
        aliases: ["ad_password"]
    ldap_port:
        description:
            - Server port.
            - Supported for O(type=ldap) and O(type=ad).
        type: int
        aliases: ["ad_port"]
    openid_prompt:
        description:
            - Specifies whether the Authorization Server prompts the End-User for reauthentication and consent.
            - Supported for with O(type=openid).
        type: str
    openid_query_userinfo:
        description:
            - Enables querying the userinfo endpoint for claims values.
            - Supported for with O(type=openid).
        type: bool
    realm:
        description: Arbitrary string used to identify the login realm in Proxmox.
        required: true
        type: str
    openid_scopes:
        description:
            - Specifies the scopes (user details) that should be authorized and returned, for example 'email' or 'profile'.
            - Supported for O(type=openid).
        type: str
    ldap_primary_server:
        description:
            - Server ip address or dns name.
            - Required when O(type=ldap) or O(type=ad).
        type: str
        aliases: ["ad_primary_server"]
    ldap_secondary_server:
        description:
            - Fallback server ip address or dns name.
            - Supported for O(type=ldap) and O(type=ad).
        type: str
        aliases: ["ad_secondary_server"]
    state:
        description:
            - Indicates if the realm should be present or absent.
        required: true
        choices: ['present', 'absent']
        type: str
    ldap_sync_defaults_options:
        description:
            - The defaults options for behavior of synchronizations.
            - Supported for O(type=ldap) and O(type=ad).
        type: dict
        aliases: ["ad_sync_defaults_options"]
        suboptions:
          scope:
            description: Select what to sync.
            choices: ['users', 'groups', 'both']
            type: str
          enable_new:
            description: Enable creation of new users.
            type: bool
          remove_vanished:
            description:
              - Semicolon-separated list of things to remove when they or the user vanishes during a sync.
              - The following values are possible
              - C(remove_vanished=acl) removes acls when the user/group is not returned from the sync.
              - C(remove_vanished=properties) removes the set properties on existing user/group that do not appear in the source (even custom ones).
              - C(remove_vanished=entry) removes the user/group when not returned from the sync.
              - Instead of a list it also can be C(remove_vanishe=none).
              - Example C(remove_vanished="acl;properties;entry").
            type: str
    type:
        description:
            - Realm type.
            - Required when O(state=present).
        choices: ['ad', 'ldap', 'openid']
        type: str
    openid_username_claim:
        description:
            - OpenID claim used to generate the unique username.
            - Supported for O(type=openid).
        type: str
    ldap_user_attr:
        description:
            - LDAP user attribute name.
            - Required when O(type=ldap).
        type: str
    ldap_user_classes:
        description:
            - The object class for user (inetorgperson, posixaccount, person, user).
            - Supported for O(type=ldap) and O(type=ad).
        type: str
        aliases: ["ad_user_classes"]
    ldap_validate_certs:
        description:
            - Verify the server's SSL certificate.
            - Supported for O(type=ldap) and O(type=ad).
        type: bool
        aliases: ["ad_validate_certs"]

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module
"""


EXAMPLES = r"""
- name: Add LDAP domain
  community.proxmox.proxmox_domain:
    realm: "example.test"
    state: present
    type: "ldap"
    default: True
    ldap_base_dn: "cn=accounts,dc=example,dc=test"
    ldap_bind_dn: "uid=sa-proxmox,cn=users,cn=accounts,dc=example,dc=test"
    ldap_filter: "memberof=cn=admins-proxmox,cn=groups,cn=accounts,dc=example,dc=test"
    ldap_group_filter: "cn=admins-proxmox"
    ldap_group_name_attr: "cn"
    ldap_mode: "ldaps"
    ldap_password: XXXXX
    ldap_primary_server: "ipa.example.test"
    ldap_user_attr: "uid"
    ldap_validate_certs: False
    ldap_sync_defaults_options:
      scope: "both"
      enable_new: True
      remove_vanished: "acl;properties;entry"

- name: Add AD domain
  community.proxmox.proxmox_domain:
    ad_domain: "ADDOMAIN"
    realm: "ad"
    state: present
    type: "ad"
    comment: "AD"
    ad_mode: "ldap"
    ad_password: XXXXXXXX
    ad_primary_server: "ad.exemple.test"
    ad_sync_defaults_options:
      scope: "both"
      enable_new: True
      remove_vanished: "acl;properties;entry"

- name: Add OpenID domain
  community.proxmox.proxmox_domain:
    realm: "openid"
    state: present
    type: "openid"
    openid_client_id: idoftheclient
    openid_client_key: keyoftheclient
    openid_issuer_url: "https://example.test/openid-server"

- name: Remove domain
  community.proxmox.proxmox_domain:
    realm: "ipa.example.test"
    state: absent
"""

RETURN = r"""
msg:
    description: The output message that the module generates.
    type: str
    returned: always
"""


from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    ansible_to_proxmox_bool,
    create_proxmox_module,
)


def module_args():
    return dict(
        realm=dict(type="str", required=True),
        state=dict(choices=["present", "absent"], required=True),
        type=dict(choices=["ad", "ldap", "openid"]),
        comment=dict(type="str"),
        default=dict(type="bool"),
        ad_domain=dict(type="str"),
        ad_case_sensitive=dict(type="bool", default=True),
        ldap_base_dn=dict(type="str"),
        ldap_user_attr=dict(type="str"),
        ldap_bind_dn=dict(aliases=["ad_bind_dn"], type="str"),
        ldap_filter=dict(aliases=["ad_filter"], type="str"),
        ldap_group_filter=dict(aliases=["ad_group_filter"], type="str"),
        ldap_group_classes=dict(aliases=["ad_group_classes"], type="str"),
        ldap_group_name_attr=dict(aliases=["ad_group_name_attr"], type="str"),
        ldap_mode=dict(aliases=["ad_mode"], choices=["ldap", "ldaps", "ldap+starttls"]),
        ldap_password=dict(aliases=["ad_password"], type="str", no_log=True),
        ldap_port=dict(aliases=["ad_port"], type="int"),
        ldap_primary_server=dict(aliases=["ad_primary_server"], type="str"),
        ldap_secondary_server=dict(aliases=["ad_secondary_server"], type="str"),
        ldap_user_classes=dict(aliases=["ad_user_classes"], type="str"),
        ldap_validate_certs=dict(aliases=["ad_validate_certs"], type="bool"),
        ldap_sync_defaults_options=dict(
            aliases=["ad_sync_defaults_options"],
            type="dict",
            options={
                "enable_new": dict(type="bool"),
                "remove_vanished": dict(type="str"),
                "scope": dict(choices=["users", "groups", "both"]),
            },
        ),
        openid_acr_values=dict(type="str"),
        openid_autocreate=dict(type="bool"),
        openid_client_id=dict(type="str"),
        openid_client_key=dict(type="str", no_log=True),
        openid_groups_autocreate=dict(type="bool"),
        openid_groups_claim=dict(type="str"),
        openid_groups_overwrite=dict(type="bool"),
        openid_issuer_url=dict(type="str"),
        openid_prompt=dict(type="str"),
        openid_query_userinfo=dict(type="bool"),
        openid_scopes=dict(type="str"),
        openid_username_claim=dict(type="str"),
    )


def module_options():
    return dict(
        required_if=[
            ("type", "ldap", ["ldap_base_dn"]),
            ("type", "ldap", ["ldap_user_attr"]),
            ("type", "ldap", ["ldap_primary_server"]),
            ("type", "ad", ["ldap_primary_server"]),
            ("type", "ad", ["ad_domain"]),
            ("type", "openid", ["openid_issuer_url"]),
            ("type", "openid", ["openid_client_id"]),
            ("state", "present", ["type"]),
        ],
    )


class ProxmoxDomainAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super().__init__(module)
        self.params = module.params

    def check_domain(self, realm):
        domains = self.proxmox_api.access.domains.get()
        return realm in [item["realm"] for item in domains]

    def get_domain(self, realm):
        return self.proxmox_api.access.domains.get(realm)

    def is_equal(self, params, current):
        return all(params[k] == current.get(k) for k in params if k not in ("password", "realm"))

    def get_params_from_list(self, params_list):
        params = {
            k: ansible_to_proxmox_bool(v) if isinstance(v, bool) else v
            for k, v in self.params.items()
            if v is not None and k in params_list
        }
        return params

    def get_params_from_dict(self, params_dict):
        params = {
            params_dict[k]: ansible_to_proxmox_bool(v) if isinstance(v, bool) else v
            for k, v in self.params.items()
            if v is not None and k in params_dict
        }
        return params

    def get_domain_params(self):
        list_domain_params = [
            "comment",
            "default",
            "type",
            "realm",
        ]
        return self.get_params_from_list(list_domain_params)

    def get_ldap_params(self):
        ldap_params = {
            "base_dn": self.params["ldap_base_dn"],
            "user_attr": self.params["ldap_user_attr"],
        }
        return ldap_params

    def get_ad_params(self):
        ad_params = {
            "domain": self.params["ad_domain"],
            "case-sensitive": ansible_to_proxmox_bool(self.params["ad_case_sensitive"]),
        }
        return ad_params

    def get_sync_params(self):
        dict_sync_params = {
            "ldap_bind_dn": "bind_dn",
            "ldap_filter": "filter",
            "ldap_group_classes": "group_classes",
            "ldap_group_filter": "group_filter",
            "ldap_group_name_attr": "group_name_attr",
            "ldap_mode": "mode",
            "ldap_port": "port",
            "ldap_password": "password",
            "ldap_primary_server": "server1",
            "ldap_secondary_server": "server2",
            "ldap_user_classes": "user_classes",
            "ldap_validate_certs": "verify",
        }
        return self.get_params_from_dict(dict_sync_params)

    def get_sync_options_param(self):
        sync_option = self.params["ldap_sync_defaults_options"]
        if sync_option is not None:
            options = []
            if sync_option.get("enable_new"):
                options.append(f"enable-new={ansible_to_proxmox_bool(sync_option.get('enable_new'))}")
            if sync_option.get("remove_vanished") is not None:
                options.append(f"remove-vanished={sync_option.get('remove_vanished')}")
            if sync_option.get("scope") is not None:
                options.append(f"scope={sync_option.get('scope')}")
            param = {"sync-defaults-options": ",".join(options)}
        else:
            param = {}
        return param

    def get_openid_params(self):
        list_openid_params = [
            "openid_acr_values",
            "openid_autocreate",
            "openid_client_id",
            "openid_client_key",
            "openid_groups_autocreate",
            "openid_groups_claim",
            "openid_groups_overwrite",
            "openid_issuer_url",
            "openid_prompt",
            "openid_query_userinfo",
            "openid_scopes",
            "openid_username_claim",
        ]
        openid_param = self.get_params_from_list(list_openid_params)
        # Remove the openid_
        # On the api all the parameters are with a - and not a _
        openid_params = {k.replace("openid_", "").replace("_", "-"): v for k, v in openid_param.items()}
        return openid_params

    def add_domain(self):
        domain_params = self.get_domain_params()
        if self.params["type"] == "ldap":
            type_params = {
                **self.get_ldap_params(),
                **self.get_sync_params(),
                **self.get_sync_options_param(),
            }
        elif self.params["type"] == "ad":
            type_params = {
                **self.get_ad_params(),
                **self.get_sync_params(),
                **self.get_sync_options_param(),
            }
        elif self.params["type"] == "openid":
            type_params = self.get_openid_params()

        params = {**domain_params, **type_params}

        if self.check_domain(self.params["realm"]):
            current = self.get_domain(self.params["realm"])
            if self.is_equal(params, current):
                self.module.exit_json(
                    changed=False,
                    msg=f"Domain {self.params['realm']} already exists.",
                )
            else:
                if not self.module.check_mode:
                    params.pop("type")
                    self.proxmox_api.access.domains(self.params["realm"]).put(**params)
                    msg = f"Domain {self.params['realm']} edited."
                else:
                    msg = f"Domain {self.params['realm']} would be edited."
                self.module.exit_json(changed=True, msg=msg)
        else:
            if not self.module.check_mode:
                self.proxmox_api.access.domains.create(**params)
                msg = f"Domain {self.params['realm']} added."
            else:
                msg = f"Domain {self.params['realm']} would be added."
            self.module.exit_json(changed=True, msg=msg)

    def del_domain(self):
        if self.check_domain(self.params["realm"]):
            if not self.module.check_mode:
                self.proxmox_api.access.domains(self.params["realm"]).delete()
                msg = f"Domain {self.params['realm']} deleted."
            else:
                msg = f"Domain {self.params['realm']} would be deleted."

            self.module.exit_json(changed=True, msg=msg)
        else:
            self.module.exit_json(changed=False, msg=f"Domain {self.params['realm']} not present.")


def main():
    module = create_proxmox_module(module_args(), **module_options())
    proxmox = ProxmoxDomainAnsible(module)
    state = module.params["state"]

    if state == "present":
        proxmox.add_domain()

    elif state == "absent":
        proxmox.del_domain()


if __name__ == "__main__":
    main()
