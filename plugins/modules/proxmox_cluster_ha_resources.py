#!/usr/bin/python

# Copyright (c) 2025, Markus Kötter <koetter@cispa.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

DOCUMENTATION = r"""
---
module: proxmox_cluster_ha_resources

short_description: Management of HA resources in Proxmox VE Cluster

version_added: "1.1.0"

description:
  - Manage Proxmox High Availability (HA) resources C(/cluster/ha/resources).

notes:
  - Proxmox 9.0+ deprecates HA groups. Use community.proxmox.proxmox_cluster_ha_rules instead of the legacy groups module for HA rule management.

attributes:
  check_mode:
    support: none
  diff_mode:
    support: none

options:
    name:
        description: |
            HA resource ID. Can be prefixed (e.g., V(vm:100), V(ct:100)) or just the ID (e.g., V(100)).
        required: true
        type: str
    state:
        description: Desired state of the resource configuration in the cluster.
        required: true
        choices: ['present', 'absent']
        type: str
    comment:
        description: Description/comment for the HA resource.
        type: str
        required: false
    max_relocate:
        description: Maximal number of relocation attempts.
        type: int
        default: 1
    max_restart:
        description: Maximal number of restart attempts.
        type: int
        default: 1
    hastate:
        description: |
            The requested state of the resource.
            V(started) means the resource will be started; V(stopped) means it will be stopped but stay in HA;
            V(disabled) is similar to stopped but the LRM will not touch it; V(ignored) removes it from HA management.
        type: str
        choices: ["started", "stopped", "disabled", "ignored"]
        default: "started"

extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes

author:
    - Tom Emming (@tinux-it)
"""

EXAMPLES = r"""
- name: Ensure VM 100 is managed by HA
  community.proxmox.proxmox_cluster_ha_resources:
    name: vm:100
    state: present
    hastate: started
    comment: "High priority web server"
  delegate_to: localhost

- name: Disable HA management for a container
  community.proxmox.proxmox_cluster_ha_resources:
    name: ct:101
    state: present
    hastate: disabled
  delegate_to: localhost

- name: Remove VM 100 from HA management
  community.proxmox.proxmox_cluster_ha_resources:
    name: vm:100
    state: absent
  delegate_to: localhost
"""

RETURN = r"""
resource:
  description: A representation of the HA resource.
  returned: success
  type: dict
  sample: {
      "sid": "vm:100",
      "state": "started",
      "comment": "webserver",
      "max_relocate": 1,
      "max_restart": 1,
  }
"""

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    ProxmoxAnsible,
    create_proxmox_module,
)


class ProxmoxClusterHAResourcesAnsible(ProxmoxAnsible):
    def _get(self, sid):
        try:
            return self.proxmox_api.cluster.ha.resources(sid).get()
        except Exception:
            return None

    def _post(self, data):
        return self.proxmox_api.cluster.ha.resources.post(**data)

    def _put(self, sid, data):
        return self.proxmox_api.cluster.ha.resources(sid).put(**data)

    def _delete(self, sid):
        return self.proxmox_api.cluster.ha.resources(sid).delete()

    def apply(self, existing):
        changed = False
        result_diff = {}
        sid = self.module.params["name"]

        desired_state = {
            "sid": sid,
            "state": self.module.params["hastate"],
            "comment": self.module.params["comment"] or "",
            "max_relocate": self.module.params["max_relocate"],
            "max_restart": self.module.params["max_restart"],
        }

        if existing:
            current_state = {
                "sid": existing.get("sid"),
                "state": str(existing.get("state")),
                "comment": str(existing.get("comment", "")),
                "max_relocate": int(existing.get("max_relocate", 1)),
                "max_restart": int(existing.get("max_restart", 1)),
            }

            needs_update = False
            for key in ["state", "comment", "max_relocate", "max_restart"]:
                if current_state.get(key) != desired_state.get(key):
                    needs_update = True
                    break

            if needs_update:
                changed = True
                result_diff = {"before": current_state, "after": desired_state}
                if not self.module.check_mode:
                    put_payload = {k: desired_state[k] for k in ["state", "comment", "max_relocate", "max_restart"]}
                    self._put(sid, put_payload)

                final_resource = desired_state
            else:
                final_resource = current_state
        else:
            changed = True
            result_diff = {"before": {}, "after": desired_state}
            if not self.module.check_mode:
                self._post(desired_state)

            final_resource = desired_state

        return {"changed": changed, "resource": final_resource, "diff": result_diff}

    def remove(self, existing):
        diff = {"before": {}, "after": {}}
        if existing:
            diff["before"] = existing
            if not self.module.check_mode:
                self._delete(self.module.params["name"])
            return {"changed": True, "diff": diff}
        return {"changed": False, "diff": diff}


def module_args():
    return dict(
        name=dict(type="str", required=True),
        state=dict(choices=["present", "absent"], required=True),
        comment=dict(type="str", required=False),
        max_relocate=dict(type="int", default=1),
        max_restart=dict(type="int", default=1),
        hastate=dict(
            choices=["started", "stopped", "disabled", "ignored"],
            default="started",
        ),
    )


def run_module():
    module = create_proxmox_module(module_args(), supports_check_mode=True)
    proxmox = ProxmoxClusterHAResourcesAnsible(module)

    name = module.params["name"]
    state = module.params["state"]

    try:
        # Check if exists
        existing = proxmox._get(name)

        if state == "present":
            result = proxmox.apply(existing)
        else:
            result = proxmox.remove(existing)

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=str(e))


def main():
    run_module()


if __name__ == "__main__":
    main()
