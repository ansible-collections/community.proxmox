#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2026, (@teslamania) <nicolas.vial@protonmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
module: proxmox_domain
version_added: 1.6.0
short_description: Manage realms.
description:
  - Add, modify or delete domain realms.
author: Vial Nicolas (@teslamania)
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none

options:
    acr_values:
        description:
            - Specifies the Authentication Context Class Reference values that theAuthorization Server is being requested to use for the Auth Request.
            - Supported for O(type=openid).
        type: str
    autocreate:
        description:
            - Automatically create users if they do not exist.
            - Supported for O(type=openid).
        type: bool
    base_dn:
        description:
            - Ldap base domain name.
            - Required when O(type=ldap).
        type: str
    bind_dn:
        description:
            - Ldap user bind domain name.
            - Supported for O(type=ldap) and O(type=ad).
        type: str
    case_sensitive:
        description:
            - Username is case-sensitive.
            - Supported for O(type=ad).
        type: bool
        default: True
    comment:
        description: Description.
        type: str
    client_id:
        description:
            - OpenID Client ID.
            - Required when O(type=openid).
        type: str
    client_key:
        description:
            - OpenID Client ID.
            - Supported for O(type=openid).
        type: str
    default:
        description: Use as default realm.
        type: bool
    domain:
        description:
            - AD domain name.
            - Required when O(type=ad).
        type: str
    filter:
        description:
            - Ldap filter for user sync.
            - Supported for O(type=ldap) and O(type=ad).
        type: str
    issuer_url:
        description:
            - OpenID Issuer Url.
            - Required when O(type=openid).
        type: str
    groups_autocreate:
        description:
            - Automatically create users if they do not exist.
            - Supported for O(type=openid).
        type: bool
    groups_claim:
        description:
            - OpenID claim used to retrieve groups with.
            - Supported for O(type=openid).
        type: str
    groups_overwrite:
        description:
            - All groups will be overwritten for the user on login.
            - Supported for O(type=openid).
        type: bool
    group_classes:
        description:
            - The object class for group (groupOfNames, group, univentionGroup, ipausergroup).
            - Supported for O(type=ldap) and O(type=ad).
        type: str
    group_filter:
        description:
            - Ldap filter for group sync.
            - Supported for O(type=ldap) and O(type=ad).
        type: str
    group_name_attr:
        description:
            - Ldap group attribute name.
            - Supported for O(type=ldap) and O(type=ad).
        type: str
    mode:
        description:
            - Ldap protocol mode.
            - Supported for O(type=ldap) and O(type=ad).
        choices: ['ldap', 'ldaps', 'ldap+starttls']
        type: str
    password:
        description:
            - Ldap bind password.
            - Supported for O(type=ldap) and O(type=ad).
        type: str
    port:
        description:
            - Server port.
            - Supported for O(type=ldap) and O(type=ad).
        type: int
    prompt:
        description:
            - Specifies whether the Authorization Server prompts the End-User for reauthentication and consent.
            - Supported for with 0(type=openid).
        type: str
    query_userinfo:
        description:
            - Enables querying the userinfo endpoint for claims values.
            - Supported for with 0(type=openid).
        type: bool
    realm:
        description: Authentication domain ID.
        required: true
        type: str
    scopes:
        description:
            - Specifies the scopes (user details) that should be authorized and returned, for example 'email' or 'profile'.
            - Supported for O(type=openid).
        type: str
    server1:
        description:
            - Server ip address or dns name.
            - Required when O(type=ldap) or O(type=ad).
        type: str
    server2:
        description:
            - Fallback server ip address or dns name.
            - Supported for O(type=ldap) and O(type=ad).
        type: str
    state:
        description:
            - Indicates if the realm should be present or absent.
            - Run a sync.
        required: true
        choices: ['present', 'absent', 'sync']
        type: str
    sync_defaults_options:
        description:
            - The defaults options for behavior of synchronizations.
            - Supported for O(type=ldap) and O(type=ad).
        type: dict
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
              - A semicolon-separated list of things to remove when they or the user vanishes during a sync.
              - The following values are possible
              - entry removes the user/group when not returned from the sync.
              - properties removes the set properties on existing user/group that do not appear in the source (even custom ones).
              - acl removes acls when the user/group is not returned from the sync.
              - Instead of a list it also can be 'none' (the default).
            type: str
    type:
        description:
            - Realm type.
            - Required when O(state=present).
        choices: ['ad', 'ldap', 'openid']
        type: str
    username_claim:
        description:
            - OpenID claim used to generate the unique username.
            - Supported for 0(type=openid).
        type: str
    user_attr:
        description:
            - Ldap user attribute name.
            - Required when O(type=ldap).
        type: str
    user_classes:
        description:
            - The object class for user (inetorgperson, posixaccount, person, user).
            - Supported for O(type=ldap) and O(type=ad).
        type: str
    verify:
        description:
            - Verify the server's SSL certificate.
            - Supported for O(type=ldap) and O(type=ad).
        type: bool

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
  - community.proxmox.attributes.info_module
"""


EXAMPLES = r"""
- name: Add ldap domain
  community.proxmox.proxmox_domain:
    api_host: 192.168.1.21
    api_user: "root@pam"
    api_password: secret
    base_dn: "cn=accounts,dc=example,dc=test"
    bind_dn: "uid=sa-proxmox,cn=users,cn=accounts,dc=example,dc=test"
    default: True
    filter: "memberof=cn=admins-proxmox,cn=groups,cn=accounts,dc=example,dc=test"
    group_filter: "cn=admins-proxmox"
    group_name_attr: "cn"
    mode: "ldaps"
    password: XXXXX
    realm: "ipa.example.test"
    server1: "ipa.example.test"
    state: present
    type: "ldap"
    user_attr: "uid"
    verify: False
    sync_defaults_options:
      scope: "both"
      enable_new: True
      remove_vanished: "acl;properties;entry"

- name: Sync ldap domain
  community.proxmox.proxmox_domain:
    api_host: 192.168.1.21
    api_user: "root@pam"
    api_password: secret
    realm: "ipa.example.test"
    state: sync

- name: Add ad domain
  community.proxmox.proxmox_domain:
    api_host: 192.168.1.21
    api_user: "root@pam"
    api_password: secret
    domain: "ADDOMAIN"
    mode: "ldap"
    password: XXXXXXXX
    realm: "ad"
    server1: "ad.exemple.test"
    state: present
    type: "ad"
    comment: "AD"
    sync_defaults_options:
      scope: "both"
      enable_new: True
      remove_vanished: "acl;properties;entry"

- name: Add openid domain
  community.proxmox.proxmox_domain:
    api_host: 192.168.1.21
    api_user: "root@pam"
    api_password: secret
    realm: "openid"
    state: present
    type: "openid"
    client_id: idoftheclient
    client_key: keyoftheclient
    issuer_url: "https://example.test/openid-server"
"""

RETURN = r"""
msg:
    description: The output message that the module generates.
    type: str
    returned: always
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    proxmox_auth_argument_spec,
    ansible_to_proxmox_bool,
    ProxmoxAnsible,
)


class ProxmoxDomainAnsible(ProxmoxAnsible):
    def __init__(self, module):
        super(ProxmoxDomainAnsible, self).__init__(module)
        self.params = module.params

    def check_domain(self, realm):
        domains = self.proxmox_api.access.domains.get()
        return realm in [item["realm"] for item in domains]

    def get_domain(self, realm):
        return self.proxmox_api.access.domains.get(realm)

    # In params there is no None value
    def is_equal(self, params, current):
        for k, v in params.items():
            if k not in ["password", "realm"] and (k not in current.keys() or v != current[k]):
                return False
        return True

    def get_params_from_list(self, params_list):
        params = {
            k: ansible_to_proxmox_bool(v) if isinstance(v, bool) else v
            for k, v in self.params.items()
            if v is not None and k in params_list
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
        list_ldap_params = [
            "base_dn",
            "user_attr",
        ]
        return self.get_params_from_list(list_ldap_params)

    def get_ad_params(self):
        ad_params = {
            "domain": self.params["domain"],
            "case-sensitive": ansible_to_proxmox_bool(self.params["case_sensitive"]),
        }
        return ad_params

    def get_sync_params(self):
        list_sync_params = [
            "bind_dn",
            "filter",
            "group_classes",
            "group_filter",
            "group_name_attr",
            "mode",
            "port",
            "password",
            "server1",
            "server2",
            "user_classes",
            "verify",
        ]
        return self.get_params_from_list(list_sync_params)

    def get_sync_options_param(self):
        sync_option = self.params['sync_defaults_options']
        if sync_option is not None:
            options = []
            if sync_option.get('enable_new'):
                options.append(
                    f"enable-new={ansible_to_proxmox_bool(sync_option.get('enable_new'))}"
                )
            if sync_option.get('remove_vanished') is not None:
                options.append(f"remove-vanished={sync_option.get('remove_vanished')}")
            if sync_option.get('scope') is not None:
                options.append(f"scope={sync_option.get('scope')}")
            try:
                param = {"sync-defaults-options": ','.join(options)}
            except Exception as e:
                self.module.fail_json(msg=f"Failed : {options}")
        else:
            param = {}
        return param

    def get_openid_params(self):
        list_openid_params = [
            "acr_values",
            "autocreate",
            "client_id",
            "client_key",
            "groups_autocreate",
            "groups_claim",
            "groups_overwrite",
            "issuer_url",
            "query_userinfo",
            "username_claim",
        ]
        openid_param = self.get_params_from_list(list_openid_params)
        # On the api all the parameters are with a - and not a _
        openid_params = {k.replace('_', '-'): v for k, v in openid_param.items()}
        return openid_params

    def add_domain(self):
        domain_params = self.get_domain_params()
        if self.params['type'] == "ldap":
            type_params = {
                **self.get_ldap_params(),
                **self.get_sync_params(),
                **self.get_sync_options_param(),
            }
        elif self.params['type'] == "ad":
            type_params = {
                **self.get_ad_params(),
                **self.get_sync_params(),
                **self.get_sync_options_param(),
            }
        elif self.params['type'] == "openid":
            type_params = self.get_openid_params()

        params = {**domain_params, **type_params}

        if self.check_domain(self.params['realm']):
            current = self.get_domain(self.params['realm'])
            if self.is_equal(params, current):
                self.module.exit_json(
                    changed=False,
                    msg=f"Domain {self.params['realm']} already exists.",
                )
            else:
                if not self.module.check_mode:
                    params.pop('type')
                    self.proxmox_api.access.domains(self.params['realm']).put(**params)
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
            self.module.exit_json(
                changed=True,
                msg=msg,
            )

    def del_domain(self):
        if self.check_domain(self.params['realm']):
            if not self.module.check_mode:
                self.proxmox_api.access.domains(self.params['realm']).delete()
                msg = f"Domain {self.params['realm']} deleted."
            else:
                msg = f"Domain {self.params['realm']} would be deleted."

            self.module.exit_json(
                changed=True,
                msg=msg,
            )
        else:
            self.module.exit_json(
                changed=False,
                msg="Domain not present.",
            )

    def sync_domain(self):
        if self.check_domain(self.params['realm']):
            if not self.module.check_mode:
                self.proxmox_api.access.domains(self.params['realm']).sync.post()
                msg = f"Domain {self.params['realm']} synced."
            else:
                msg = f"Domain {self.params['realm']} would be synced."

            self.module.exit_json(changed=True, msg=msg)
        else:
            self.module.fail_json(msg=f"Domain {self.params['realm']} not present.")


def main():
    module_args = proxmox_auth_argument_spec()
    domain_args = dict(
        acr_values=dict(type='str'),
        autocreate=dict(type='bool'),
        base_dn=dict(type='str'),
        bind_dn=dict(type='str'),
        case_sensitive=dict(type='bool', default=True),
        comment=dict(type='str'),
        client_id=dict(type='str'),
        client_key=dict(type='str', no_log=True),
        default=dict(type='bool'),
        domain=dict(type='str'),
        filter=dict(type='str'),
        groups_autocreate=dict(type='bool'),
        groups_claim=dict(type='str'),
        groups_overwrite=dict(type='bool'),
        group_filter=dict(type='str'),
        group_classes=dict(type='str'),
        group_name_attr=dict(type='str'),
        issuer_url=dict(type='str'),
        mode=dict(choices=['ldap', 'ldaps', 'ldap+starttls']),
        password=dict(type='str', no_log=True),
        port=dict(type='int'),
        prompt=dict(type='str'),
        query_userinfo=dict(type='bool'),
        realm=dict(type='str', required=True),
        scopes=dict(type='str'),
        server1=dict(type='str'),
        server2=dict(type='str'),
        state=dict(choices=['present', 'absent', 'sync'], required=True),
        type=dict(choices=['ad', 'ldap', 'openid']),
        username_claim=dict(type='str'),
        user_attr=dict(type='str'),
        user_classes=dict(type='str'),
        verify=dict(type='bool'),
        sync_defaults_options=dict(type='dict', options={
            'enable_new': dict(type='bool'),
            'remove_vanished': dict(type='str'),
            'scope': dict(choices=['users', 'groups', 'both']),
        }),
    )

    module_args.update(domain_args)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[("api_password", "api_token_id")],
        required_together=[("api_token_id", "api_token_secret")],
        required_if=[
            ('type', 'ldap', ['base_dn']),
            ('type', 'ldap', ['user_attr']),
            ('type', 'ldap', ['server1']),
            ('type', 'ad', ['server1']),
            ('type', 'ad', ['domain']),
            ('type', 'openid', ['issuer_url']),
            ('type', 'openid', ['client_id']),
            ('state', 'present', ['type']),
        ],
    )

    proxmox = ProxmoxDomainAnsible(module)
    state = module.params['state']

    if state == 'present':
        proxmox.add_domain()

    elif state == 'absent':
        proxmox.del_domain()

    elif state == 'sync':
        proxmox.sync_domain()


if __name__ == "__main__":
    main()
