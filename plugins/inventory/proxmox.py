# Copyright (C) 2016 Guido Günther <agx@sigxcpu.org>, Daniel Lobato Garcia <dlobatog@redhat.com>
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

DOCUMENTATION = """
    name: proxmox
    short_description: Proxmox inventory source
    author:
        - Jeffrey van Pelt (@Thulium-Drake) <jeff@vanpelt.one>
    requirements:
        - requests >= 1.1
    description:
        - Get inventory hosts from a Proxmox PVE cluster.
        - "Uses a configuration file as an inventory source, it must end in C(.proxmox.yml) or C(.proxmox.yaml)"
        - Will retrieve the first network interface with an IP for Proxmox nodes.
        - Can retrieve LXC/QEMU configuration as facts.
    extends_documentation_fragment:
        - constructed
        - inventory_cache
    options:
      plugin:
        description: The name of this plugin, it should always be set to V(community.proxmox.proxmox) for this plugin to recognize it as its own.
        required: true
        choices: ['community.proxmox.proxmox']
        type: str
      url:
        description:
          - URL to Proxmox cluster.
          - If the value is not specified in the inventory configuration, the value of environment variable E(PROXMOX_URL) will be used instead.
          - You can use templating to specify the value of the O(url).
        default: 'http://localhost:8006'
        type: str
        env:
          - name: PROXMOX_URL
      user:
        description:
          - Proxmox authentication user.
          - If the value is not specified in the inventory configuration, the value of environment variable E(PROXMOX_USER) will be used instead.
          - You can use templating to specify the value of the O(user).
        required: true
        type: str
        env:
          - name: PROXMOX_USER
      password:
        description:
          - Proxmox authentication password.
          - If the value is not specified in the inventory configuration, the value of environment variable E(PROXMOX_PASSWORD) will be used instead.
          - You can use templating to specify the value of the O(password).
          - If you do not specify a password, you must set O(token_id) and O(token_secret) instead.
        type: str
        env:
          - name: PROXMOX_PASSWORD
      token_id:
        description:
          - Proxmox authentication token ID.
          - If the value is not specified in the inventory configuration, the value of environment variable E(PROXMOX_TOKEN_ID) will be used instead.
          - To use token authentication, you must also specify O(token_secret). If you do not specify O(token_id) and O(token_secret),
            you must set a password instead.
          - Make sure to grant explicit pve permissions to the token or disable 'privilege separation' to use the users' privileges instead.
        type: str
        env:
          - name: PROXMOX_TOKEN_ID
      token_secret:
        description:
          - Proxmox authentication token secret.
          - If the value is not specified in the inventory configuration, the value of environment variable E(PROXMOX_TOKEN_SECRET) will be used instead.
          - To use token authentication, you must also specify O(token_id). If you do not specify O(token_id) and O(token_secret),
            you must set a password instead.
        type: str
        env:
          - name: PROXMOX_TOKEN_SECRET
      validate_certs:
        description: Verify SSL certificate if using HTTPS.
        type: boolean
        default: true
      group_prefix:
        description: Prefix to apply to Proxmox groups.
        default: proxmox_
        type: str
      facts_prefix:
        description: Prefix to apply to LXC/QEMU config facts.
        default: proxmox_
        type: str
      want_facts:
        description:
          - Gather LXC/QEMU configuration facts.
          - When O(want_facts) is set to V(true) more details about QEMU VM status are possible, besides the running and stopped states.
            Currently if the VM is running and it is suspended, the status will be running and the machine will be in C(running) group,
            but its actual state will be paused. See O(qemu_extended_statuses) for how to retrieve the real status.
        default: false
        type: bool
      facts_concurrency:
        description:
          - Number of concurrent workers to use when gathering LXC/QEMU configuration facts.
          - Only applies when O(want_facts) is set to V(true).
          - Higher values can reduce inventory runtime over slow links, but will increase load on the Proxmox API.
          - Set to V(1) to gather facts serially.
        default: 1
        type: int
      api_timeout:
        description:
          - Timeout in seconds for Proxmox API requests.
          - The timeout is passed to the underlying HTTP client and applies to connection and socket read waits.
        default: 5
        type: int
      want_post_filter_facts:
        description:
        - Whether to collect facts after host filtering (in contrast to pull all facts of all hosts before filtering as with O(want_facts) set to V(true)).
        - This can be useful if you want to filter hosts based on some limited available criteria but still want to have access to all facts after filtering.
        - When O(want_facts) is set to V(true) facts are collected before filtering and this parameter is ignored.
        type: bool
        default: false
      qemu_extended_statuses:
        description:
          - Requires O(want_facts) to be set to V(true) to function. This will allow you to differentiate between C(paused) and C(prelaunch)
            statuses of the QEMU VMs.
          - This introduces multiple groups [prefixed with O(group_prefix)] C(prelaunch) and C(paused).
        default: false
        type: bool
      want_proxmox_nodes_ansible_host:
        description:
          - Whether to set C(ansible_host) for proxmox nodes.
          - When set to V(true) (default), will use the first available interface. This can be different from what you expect.
        type: bool
        default: false
      exclude_nodes:
        description: Exclude proxmox nodes and the nodes-group from the inventory output.
        type: bool
        default: false
      exclude_vms:
        description: Exclude LXC containers and QEMU virtual machines from the inventory output.
        type: bool
        default: false
      filters:
        description:
        - A list of Jinja templates that allow filtering hosts.
        - If strict mode is enabled, any error during host filter compositing will lead to an AnsibleError being raised, otherwise the host will be ignored.
        - Facts collected when O(want_facts) is set to V(true) can be used in the filters.
        - When O(want_facts) is set to V(false) full facts are not available and filters can only used on a limited set of facts
          proxmox_vmid, proxmox_name, proxmox_status, proxmox_vmtype, proxmox_tags, proxmox_template.
        type: list
        elements: str
        default: []
"""

EXAMPLES = """
---
# Minimal example which will not gather additional facts for QEMU/LXC guests
# By not specifying a URL the plugin will attempt to connect to the controller host on port 8006
# my.proxmox.yml
plugin: community.proxmox.proxmox
user: ansible@pve
password: secure
# Note that this can easily give you wrong values as ansible_host. See further below for
# an example where this is set to `false` and where ansible_host is set with `compose`.
want_proxmox_nodes_ansible_host: true

---
# Instead of login with password, proxmox supports api token authentication since release 6.2.
plugin: community.proxmox.proxmox
user: ci@pve
token_id: gitlab-1
token_secret: fa256e9c-26ab-41ec-82da-707a2c079829

# The secret can also be a vault string or passed via the environment variable TOKEN_SECRET.
token_secret: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          62353634333163633336343265623632626339313032653563653165313262343931643431656138
          6134333736323265656466646539663134306166666237630a653363623262636663333762316136
          34616361326263383766366663393837626437316462313332663736623066656237386531663731
          3037646432383064630a663165303564623338666131353366373630656661333437393937343331
          32643131386134396336623736393634373936356332623632306561356361323737313663633633
          6231313333666361656537343562333337323030623732323833

---
# More complete example demonstrating the use of 'want_facts' and the constructed options
# Note that using facts returned by 'want_facts' in constructed options requires 'want_facts=true'
# my.proxmox.yml
plugin: community.proxmox.proxmox
url: http://pve.domain.com:8006
user: ansible@pve
password: secure
want_facts: true
keyed_groups:
    # proxmox_tags_parsed is an example of a fact only returned when 'want_facts=true'
  - key: proxmox_tags_parsed
    separator: ""
    prefix: group
groups:
  webservers: "'web' in (proxmox_tags_parsed|list)"
  mailservers: "'mail' in (proxmox_tags_parsed|list)"
compose:
  ansible_port: 2222
# Note that this can easily give you wrong values as ansible_host. See further below for
# an example where this is set to `false` and where ansible_host is set with `compose`.
want_proxmox_nodes_ansible_host: true

---
# Using the inventory to allow ansible to connect via the first IP address of the VM / Container
# (Default is connection by name of QEMU/LXC guests)
# Note: my_inv_var demonstrates how to add a string variable to every host used by the inventory.
# my.proxmox.yml
plugin: community.proxmox.proxmox
url: http://192.168.1.2:8006
user: ansible@pve
password: secure
want_facts: true
want_proxmox_nodes_ansible_host: false
compose:
  ansible_host: proxmox_ipconfig0.ip | default(proxmox_net0.ip) | ipaddr('address')
  my_inv_var_1: "'my_var1_value'"
  my_inv_var_2: >
    "my_var_2_value"

---
# Specify the url, user and password using templating
# my.proxmox.yml
plugin: community.proxmox.proxmox
url: "{{ lookup('ansible.builtin.ini', 'url', section='proxmox', file='file.ini') }}"
user: "{{ lookup('ansible.builtin.env','PM_USER') | default('ansible@pve') }}"
password: "{{ lookup('community.proxmox.random_string', base64=True) }}"
# Note that this can easily give you wrong values as ansible_host. See further up for
# an example where this is set to `false` and where ansible_host is set with `compose`.
want_proxmox_nodes_ansible_host: true

"""

import re
from collections.abc import MutableMapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from sys import version as python_version
from threading import Lock, local
from urllib.parse import urlencode

from ansible.errors import AnsibleError
from ansible.module_utils.ansible_release import __version__ as ansible_version
from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable, Constructable
from ansible.utils.display import Display

from ansible_collections.community.proxmox.plugins.module_utils.version import LooseVersion
from ansible_collections.community.proxmox.plugins.plugin_utils.unsafe import make_unsafe

# 3rd party imports
try:
    import requests
    import urllib3

    if LooseVersion(requests.__version__) < LooseVersion("1.1.0"):
        raise ImportError
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

display = Display()


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    """Host inventory parser for ansible using Proxmox as source."""

    NAME = "community.proxmox.proxmox"

    def __init__(self):
        super().__init__()

        # from config
        self.proxmox_url = None

        self._thread_local = local()
        self._results_lock = Lock()
        self.cache_key = None
        self.use_cache = None
        self.facts_concurrency = 1
        self.api_timeout = 5

    def verify_file(self, path):
        valid = False
        if super().verify_file(path):
            if path.endswith(("proxmox.yaml", "proxmox.yml")):
                valid = True
            else:
                self.display.vvv('Skipping due to inventory source not ending in "proxmox.yaml" nor "proxmox.yml"')
        return valid

    def _get_session(self):
        session = getattr(self._thread_local, "session", None)
        if session is None:
            session = requests.session()
            session.headers.update(
                {"User-Agent": f"ansible {ansible_version} Python {python_version.split(' ', 1)[0]}"}
            )
            session.verify = self.get_option("validate_certs")
            if not session.verify:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            self._thread_local.session = session
        return session

    def _get_auth(self):
        if self.proxmox_password:
            credentials = urlencode({"username": self.proxmox_user, "password": self.proxmox_password})
            a = self._get_session()
            ret = a.post(
                f"{self.proxmox_url}/api2/json/access/ticket",
                data=credentials,
                timeout=self.api_timeout,
            )
            json = ret.json()
            self.headers = {
                # only required for POST/PUT/DELETE methods, which we are not using currently
                # 'CSRFPreventionToken': json['data']['CSRFPreventionToken'],
                "Cookie": f"PVEAuthCookie={json['data']['ticket']}"
            }
        else:
            # Clean and format token components
            user = self.proxmox_user.strip()
            token_id = self.proxmox_token_id.strip()
            token_secret = self.proxmox_token_secret.strip()

            # Build token string without newlines
            token = f"{user}!{token_id}={token_secret}"

            # Set headers with clean token
            self.headers = {"Authorization": f"PVEAPIToken={token}"}

    def _get_json(self, url, ignore_errors=None):
        data = []
        has_data = False

        if self.use_cache:
            try:
                data = self._cache[self.cache_key][url]
                has_data = True
            except KeyError:
                self.update_cache = True

        if not has_data:
            s = self._get_session()
            while True:
                ret = s.get(url, headers=self.headers, timeout=self.api_timeout)
                if ignore_errors and ret.status_code in ignore_errors:
                    break
                ret.raise_for_status()
                json = ret.json()

                # process results
                # FIXME: This assumes 'return type' matches a specific query,
                #        it will break if we expand the queries and they dont have different types
                if "data" not in json:
                    # /hosts/:id does not have a 'data' key
                    data = json
                    break
                elif isinstance(json["data"], MutableMapping):
                    # /facts are returned as dict in 'data'
                    data = json["data"]
                    break
                else:
                    if json["data"]:
                        # /hosts 's 'results' is a list of all hosts, returned is paginated
                        data = data + json["data"]
                    break

        with self._results_lock:
            self._results[url] = data
        return make_unsafe(data)

    def _get_nodes(self):
        display.vvv("Fetching Proxmox cluster status")
        cluster_status = self._get_json(f"{self.proxmox_url}/api2/json/cluster/status")
        nodes = [item for item in cluster_status if item["type"] == "node"]
        display.vvv(f"Fetched {len(nodes)} Proxmox nodes")
        return nodes

    def _get_pools(self):
        display.vvv("Fetching Proxmox pools")
        pools = self._get_json(f"{self.proxmox_url}/api2/json/pools")
        display.vvv(f"Fetched {len(pools)} Proxmox pools")
        return pools

    def _get_vms(self):
        display.vvv("Fetching Proxmox VM resources")
        vms = self._get_json(f"{self.proxmox_url}/api2/json/cluster/resources?type=vm")
        display.vvv(f"Fetched {len(vms)} Proxmox VM resources")
        return vms

    def _get_vms_by_node(self):
        vms_by_node = {"qemu": {}, "lxc": {}}

        if self.exclude_vms:
            return vms_by_node

        for item in self._get_vms():
            ittype = item.get("type")
            if ittype not in vms_by_node or "node" not in item:
                continue

            node_items = vms_by_node[ittype].setdefault(item["node"], [])
            node_items.append(item)

        display.vvv(
            "Grouped Proxmox VM resources into "
            f"{sum(len(items) for items in vms_by_node['qemu'].values())} QEMU guests and "
            f"{sum(len(items) for items in vms_by_node['lxc'].values())} LXC guests"
        )
        return vms_by_node

    def _get_members_per_pool(self, pool):
        display.vvv(f"Fetching Proxmox pool members for {pool}")
        ret = self._get_json(f"{self.proxmox_url}/api2/json/pools/{pool}")
        members = ret["members"]
        display.vvv(f"Fetched {len(members)} Proxmox pool members for {pool}")
        return members

    def _get_lxc_interfaces(self, properties, node, vmid):
        status_key = self._fact("status")

        if status_key not in properties or properties[status_key] != "running":
            return

        ret = self._get_json(f"{self.proxmox_url}/api2/json/nodes/{node}/lxc/{vmid}/interfaces", ignore_errors=[501])
        if not ret:
            return

        result = []

        for iface in ret:
            result_iface = {"name": iface["name"], "hwaddr": iface["hwaddr"]}

            if "inet" in iface:
                result_iface["inet"] = iface["inet"]

            if "inet6" in iface:
                result_iface["inet6"] = iface["inet6"]

            result.append(result_iface)

        properties[self._fact("lxc_interfaces")] = result

    def _get_agent_network_interfaces(self, node, vmid, vmtype):
        result = []

        try:
            ifaces = self._get_json(
                f"{self.proxmox_url}/api2/json/nodes/{node}/{vmtype}/{vmid}/agent/network-get-interfaces"
            )["result"]

            if "error" in ifaces:
                if "class" in ifaces["error"]:
                    # This happens on Windows, even though qemu agent is running, the IP address
                    # cannot be fetched, as it is unsupported, also a command disabled can happen.
                    errorClass = ifaces["error"]["class"]
                    if errorClass in ["Unsupported"]:
                        self.display.v(
                            "Retrieving network interfaces from guest agents on windows with older qemu-guest-agents is not supported"
                        )
                    elif errorClass in ["CommandDisabled"]:
                        self.display.v("Retrieving network interfaces from guest agents has been disabled")
                return result

            for iface in ifaces:
                result.append(
                    {
                        "name": iface["name"],
                        "mac-address": iface.get("hardware-address", ""),
                        "ip-addresses": [f"{ip['ip-address']}/{ip['prefix']}" for ip in iface["ip-addresses"]]
                        if "ip-addresses" in iface
                        else [],
                    }
                )
        except requests.HTTPError:
            pass

        return result

    def _get_vm_config(self, properties, node, vmid, vmtype, name):  # noqa: PLR0912
        ret = self._get_json(f"{self.proxmox_url}/api2/json/nodes/{node}/{vmtype}/{vmid}/config")

        plaintext_configs = [
            "description",
        ]

        for config in ret:
            key = self._fact(config)
            value = ret[config]
            try:
                # fixup disk images as they have no key
                if config == "rootfs" or config.startswith(("virtio", "sata", "ide", "scsi")):
                    value = f"disk_image={value}"

                # Additional field containing parsed tags as list
                if config == "tags":
                    stripped_value = value.strip()
                    if stripped_value:
                        parsed_key = f"{key}_parsed"
                        properties[parsed_key] = [tag.strip() for tag in stripped_value.replace(",", ";").split(";")]

                # The first field in the agent string tells you whether the agent is enabled
                # the rest of the comma separated string is extra config for the agent.
                # In some (newer versions of proxmox) instances it can be 'enabled=1'.
                if config == "agent":
                    agent_enabled = 0
                    try:
                        agent_enabled = int(value.split(",")[0])
                    except ValueError:
                        if value.split(",")[0] == "enabled=1":
                            agent_enabled = 1
                    if agent_enabled:
                        agent_iface_value = self._get_agent_network_interfaces(node, vmid, vmtype)
                        if agent_iface_value:
                            agent_iface_key = self.to_safe(f"{key}_interfaces")
                            properties[agent_iface_key] = agent_iface_value

                if config == "lxc":
                    out_val = {}
                    for k, v in value:
                        out_key = k[len("lxc.") :] if k.startswith("lxc.") else k
                        out_val[out_key] = v
                    value = out_val

                if (
                    config not in plaintext_configs
                    and isinstance(value, (str, bytes))
                    and all("=" in v for v in value.split(","))
                ):
                    # split off strings with commas to a dict
                    # skip over any keys that cannot be processed
                    try:
                        value = dict(key.split("=", 1) for key in value.split(","))
                    except Exception:
                        continue

                properties[key] = value
            except NameError:
                return None

    def _get_vm_status(self, properties, node, vmid, vmtype, name):
        ret = self._get_json(f"{self.proxmox_url}/api2/json/nodes/{node}/{vmtype}/{vmid}/status/current")
        properties[self._fact("status")] = ret["status"]
        if vmtype == "qemu":
            properties[self._fact("qmpstatus")] = ret["qmpstatus"]

    def _get_vm_snapshots(self, properties, node, vmid, vmtype, name):
        ret = self._get_json(f"{self.proxmox_url}/api2/json/nodes/{node}/{vmtype}/{vmid}/snapshot")
        snapshots = [snapshot["name"] for snapshot in ret if snapshot["name"] != "current"]
        properties[self._fact("snapshots")] = snapshots

    def _get_guest_facts(self, properties, node, vmid, ittype, name):
        self._get_vm_status(properties, node, vmid, ittype, name)
        self._get_vm_config(properties, node, vmid, ittype, name)
        self._get_vm_snapshots(properties, node, vmid, ittype, name)

        if ittype == "lxc":
            self._get_lxc_interfaces(properties, node, vmid)

    def _safe_get_guest_facts(self, properties, node, vmid, ittype, name):
        try:
            self._get_guest_facts(properties, node, vmid, ittype, name)
        except Exception as e:  # pylint: disable=broad-except
            properties[self._fact("fact_gathering_failed")] = True
            properties[self._fact("fact_gathering_error")] = str(e)
            display.warning(f"Could not gather Proxmox guest facts for {node}/{ittype}/{vmid} ({name}) - {e}")

    def _get_guest_facts_for_item(self, node, ittype, item):
        properties = {}
        self._safe_get_guest_facts(properties, node, item["vmid"], ittype, item["name"])
        display.vvvv(f"Gathered Proxmox guest facts for {node}/{ittype}/{item['vmid']} ({item['name']})")
        return node, ittype, item["vmid"], properties

    def _get_guest_facts_by_item(self, items):
        guest_facts_by_item = {}

        if not self.get_option("want_facts") or not items:
            return guest_facts_by_item

        display.vvv(f"Gathering Proxmox guest facts for {len(items)} guests with {self.facts_concurrency} workers")

        if self.facts_concurrency == 1:
            for node, ittype, item in items:
                result_node, result_ittype, vmid, properties = self._get_guest_facts_for_item(node, ittype, item)
                guest_facts_by_item[(result_node, result_ittype, vmid)] = properties
            return guest_facts_by_item

        executor = ThreadPoolExecutor(max_workers=self.facts_concurrency)
        try:
            futures = [
                executor.submit(self._get_guest_facts_for_item, node, ittype, item) for node, ittype, item in items
            ]
            for future in as_completed(futures):
                node, ittype, vmid, properties = future.result()
                guest_facts_by_item[(node, ittype, vmid)] = properties
        except KeyboardInterrupt:
            pending_futures = sum(1 for future in futures if not future.done())
            running_futures = sum(1 for future in futures if future.running())
            display.warning(
                "Interrupted Proxmox guest fact gathering with "
                f"{pending_futures} pending tasks, {running_futures} running"
            )
            executor.shutdown(wait=False, cancel_futures=True)
            raise
        else:
            executor.shutdown(wait=True)

        return guest_facts_by_item

    def to_safe(self, word):
        """Converts 'bad' characters in a string to underscores so they can be used as Ansible groups
        #> ProxmoxInventory.to_safe("foo-bar baz")
        'foo_barbaz'
        """
        regex = r"[^A-Za-z0-9\_]"
        return re.sub(regex, "_", word.replace(" ", ""))

    def _fact(self, name):
        """Generate a fact's full name from the common prefix and a name."""
        return self.to_safe(f"{self.facts_prefix}{name.lower()}")

    def _group(self, name):
        """Generate a group's full name from the common prefix and a name."""
        return self.to_safe(f"{self.group_prefix}{name.lower()}")

    def _can_add_host(self, name, properties):
        """Ensure that a host satisfies all defined hosts filters. If strict mode is
        enabled, any error during host filter compositing will lead to an AnsibleError
        being raised, otherwise the filter will be ignored.
        """
        for host_filter in self.host_filters:
            try:
                if not self._compose(host_filter, properties):
                    return False
            except Exception as e:  # pylint: disable=broad-except
                message = f"Could not evaluate host filter {host_filter} for host {name} - {e}"
                if self.strict:
                    raise AnsibleError(message) from e
                display.warning(message)
        return True

    def _add_host(self, name, variables):
        self.inventory.add_host(name)
        for k, v in variables.items():
            self.inventory.set_variable(name, k, v)
        variables = self.inventory.get_host(name).get_vars()
        self._set_composite_vars(self.get_option("compose"), variables, name, strict=self.strict)
        self._add_host_to_composed_groups(self.get_option("groups"), variables, name, strict=self.strict)
        self._add_host_to_keyed_groups(self.get_option("keyed_groups"), variables, name, strict=self.strict)

    def _handle_item(self, node, ittype, item, guest_facts=None):
        """Handle an item from the list of LXC containers and Qemu VM. The
        return value will be either None if the item was skipped or the name of
        the item if it was added to the inventory."""
        properties = dict()
        name, vmid, status = item["name"], item["vmid"], item["status"]
        is_template = bool(item.get("template", 0))

        properties[self._fact("node")] = node
        properties[self._fact("vmid")] = vmid
        properties[self._fact("vmtype")] = ittype
        properties[self._fact("name")] = name
        properties[self._fact("status")] = status
        properties[self._fact("template")] = is_template

        tags = item.get("tags")
        if tags:
            properties[self._fact("tags")] = tags

        # get status, config and snapshots if want_facts == True
        want_facts = self.get_option("want_facts")
        if want_facts:
            if guest_facts is not None:
                properties.update(guest_facts)
            else:
                self._safe_get_guest_facts(properties, node, vmid, ittype, name)

        # ensure the host satisfies filters
        if not self._can_add_host(name, properties):
            return None

        # get status, config and snapshots if we want_post_filter_facts only
        want_post_filter_facts = self.get_option("want_post_filter_facts")
        if not want_facts and want_post_filter_facts:
            self._safe_get_guest_facts(properties, node, vmid, ittype, name)

        # add the host to the inventory
        self._add_host(name, properties)
        if is_template:
            self.inventory.add_child(self._group("all_templates"), name)
            return name

        node_type_group = self._group(f"{node}_{ittype}")
        self.inventory.add_child(self._group(f"all_{ittype}"), name)
        self.inventory.add_child(node_type_group, name)

        item_status = item["status"]
        if item_status == "running" and want_facts and ittype == "qemu" and self.get_option("qemu_extended_statuses"):
            # get more details about the status of the qemu VM
            item_status = properties.get(self._fact("qmpstatus"), item_status)
        self.inventory.add_group(self._group(f"all_{item_status}"))
        self.inventory.add_child(self._group(f"all_{item_status}"), name)

        return name

    def _populate_pool_groups(self, added_hosts):
        """Generate groups from Proxmox resource pools, ignoring VMs and
        containers that were skipped."""
        for pool in self._get_pools():
            poolid = pool.get("poolid")
            if not poolid:
                continue
            pool_group = self._group(f"pool_{poolid}")
            self.inventory.add_group(pool_group)

            for member in self._get_members_per_pool(poolid):
                name = member.get("name")
                if name and name in added_hosts:
                    self.inventory.add_child(pool_group, name)

    def _populate(self):  # noqa: PLR0912
        # create common groups
        default_groups = ["lxc", "qemu", "running", "stopped", "templates"]

        if self.get_option("qemu_extended_statuses"):
            default_groups.extend(["prelaunch", "paused"])

        for group in default_groups:
            self.inventory.add_group(self._group(f"all_{group}"))
        nodes_group = self._group("nodes")
        if not self.exclude_nodes:
            self.inventory.add_group(nodes_group)

        want_proxmox_nodes_ansible_host = self.get_option("want_proxmox_nodes_ansible_host")

        # gather VMs on nodes
        self._get_auth()
        hosts = []
        vms_by_node = self._get_vms_by_node()
        vm_items = []
        for node in self._get_nodes():
            if not self.exclude_nodes:
                self.inventory.add_host(node["name"])
                self.inventory.add_child(nodes_group, node["name"])
                if want_proxmox_nodes_ansible_host:
                    self.inventory.set_variable(node["name"], "ansible_host", node["ip"])

            if node["online"] != 1:
                continue

            # Setting composite variables
            if not self.exclude_nodes:
                variables = self.inventory.get_host(node["name"]).get_vars()
                self._set_composite_vars(self.get_option("compose"), variables, node["name"], strict=self.strict)

            # add Qemu and LXC VMs for the node
            if not self.exclude_vms:
                for ittype in ("qemu", "lxc"):
                    node_type_group = self._group(f"{node['name']}_{ittype}")
                    self.inventory.add_group(node_type_group)
                    for item in vms_by_node[ittype].get(node["name"], []):
                        vm_items.append((node["name"], ittype, item))

        guest_facts_by_item = self._get_guest_facts_by_item(vm_items)
        for node, ittype, item in vm_items:
            guest_facts = guest_facts_by_item.get((node, ittype, item["vmid"]))
            name = self._handle_item(node, ittype, item, guest_facts=guest_facts)
            if name is not None:
                hosts.append(name)

        # gather vm's in pools
        if not self.exclude_vms:
            self._populate_pool_groups(hosts)

    def parse(self, inventory, loader, path, cache=True):
        if not HAS_REQUESTS:
            raise AnsibleError("This module requires Python Requests 1.1.0 or higher: https://github.com/psf/requests.")

        super().parse(inventory, loader, path)

        # read config from file, this sets 'options'
        self._read_config_data(path)

        # read and template auth options
        for o in ("url", "user", "password", "token_id", "token_secret"):
            v = self.get_option(o)
            if self.templar.is_template(v):
                v = self.templar.template(v)
            setattr(self, f"proxmox_{o}", v)

        # some more cleanup and validation
        self.proxmox_url = self.proxmox_url.rstrip("/")

        if self.proxmox_password is None and (self.proxmox_token_id is None or self.proxmox_token_secret is None):
            raise AnsibleError("You must specify either a password or both token_id and token_secret.")

        if self.get_option("qemu_extended_statuses") and not self.get_option("want_facts"):
            raise AnsibleError("You must set want_facts to True if you want to use qemu_extended_statuses.")
        if self.get_option("facts_concurrency") < 1:
            raise AnsibleError("You must set facts_concurrency to 1 or greater.")
        if self.get_option("api_timeout") < 1:
            raise AnsibleError("You must set api_timeout to 1 or greater.")
        # read rest of options
        self.exclude_nodes = self.get_option("exclude_nodes")
        self.exclude_vms = self.get_option("exclude_vms")
        self.facts_concurrency = self.get_option("facts_concurrency")
        self.api_timeout = self.get_option("api_timeout")
        self.cache_key = self.get_cache_key(path)
        self.use_cache = cache and self.get_option("cache")
        self.update_cache = not cache and self.get_option("cache")
        self.host_filters = self.get_option("filters")
        self.group_prefix = self.get_option("group_prefix")
        self.facts_prefix = self.get_option("facts_prefix")
        self.strict = self.get_option("strict")
        self.want_post_filter_facts = self.get_option("want_post_filter_facts")

        # actually populate inventory
        self._results = {}
        self._populate()
        if self.update_cache:
            self._cache[self.cache_key] = self._results
