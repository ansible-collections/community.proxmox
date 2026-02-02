# Copyright (c) 2020, Tristan Le Guern <tleguern at bouledef.eu>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


import traceback
from time import sleep

PROXMOXER_IMP_ERR = None
try:
    from proxmoxer import ProxmoxAPI
    from proxmoxer import __version__ as proxmoxer_version

    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False
    PROXMOXER_IMP_ERR = traceback.format_exc()


from ansible.module_utils.basic import env_fallback, missing_required_lib
from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.proxmox.plugins.module_utils.version import LooseVersion


def proxmox_auth_argument_spec():
    """
    Returns the authentication argument specification for Proxmox API modules.

    Returns:
        dict[str, dict]: Parameter names mapped to their configuration dictionaries.
    """
    return dict(
        api_host=dict(type="str", required=True, fallback=(env_fallback, ["PROXMOX_HOST"])),
        api_port=dict(type="int", fallback=(env_fallback, ["PROXMOX_PORT"])),
        api_user=dict(type="str", required=True, fallback=(env_fallback, ["PROXMOX_USER"])),
        api_password=dict(type="str", no_log=True, fallback=(env_fallback, ["PROXMOX_PASSWORD"])),
        api_token_id=dict(type="str", no_log=False, fallback=(env_fallback, ["PROXMOX_TOKEN_ID"])),
        api_token_secret=dict(type="str", no_log=True, fallback=(env_fallback, ["PROXMOX_TOKEN_SECRET"])),
        ca_path=dict(type="path", fallback=(env_fallback, ["PROXMOX_CA_PATH"])),
        validate_certs=dict(type="bool", fallback=(env_fallback, ["PROXMOX_VALIDATE_CERTS"])),
        api_timeout=dict(type="int", default=5, fallback=(env_fallback, ["PROXMOX_API_TIMEOUT"])),
    )


def proxmox_to_ansible_bool(value):  # noqa: SIM210
    """Convert Proxmox representation of a boolean to be ansible-friendly.

    Args:
        value(int): The value which needs to be converted to a boolean.

    Returns:
        bool: True if value = `1`, False for everything else including non-integers.
    """
    return bool(isinstance(value, int) and value == 1)


def ansible_to_proxmox_bool(value):
    """
    Convert Ansible representation of a boolean to be proxmox-friendly.

    Returns:
        `None` when value is`None`, `1` for `True` and `0` for `False`
    """
    if value is None:
        return None

    if not isinstance(value, bool):
        raise ValueError(f"{value} must be of type bool not {type(value)}")

    return 1 if value else 0


def compare_list_of_dicts(existing_list, new_list, uid, params_to_ignore=None):
    """
    Compare two lists of dicts.

    Use case - for firewall rules we will be getting a list of rules from user.
    We want to filter out which rules needs to be updated and which rules are completely new and needs to be created.

    Args:
        existing_list(list): Existing values example - list of existing rules
        new_list(list): New values example - list of rules passed to module
        uid(str): unique identifier in dict.
            It should always be present in both lists - in case of firewall rules it's `pos`.
        params_to_ignore(list): list of params we want to ignore, which are present in existing_list's dict.
            In case of firewall rules we want to ignore `['digest', 'ipversion']`.

    Returns:
         tuple[list, list]: 2 lists: 1st is the list of items which are completely new and needs to be created
            2nd is a list of items which needs to be updated.
    """
    if params_to_ignore is None:
        params_to_ignore = list()
    items_to_update = []
    new_list = [{k: v for k, v in item.items() if v is not None and k not in params_to_ignore} for item in new_list]

    if existing_list is None:
        items_to_create = new_list
        items_to_update = list()
        return items_to_create, items_to_update

    existing_list = {x[uid]: x for x in existing_list}
    new_list = {x[uid]: x for x in new_list}

    common_uids = set(existing_list.keys()).intersection(set(new_list.keys()))
    missing_uids = set(new_list.keys()) - set(existing_list.keys())
    items_to_create = [new_list[uid] for uid in missing_uids]

    for c_uid in common_uids:
        # If new rule has a parameter that is not present in existing rule we need to update
        if set(new_list[c_uid].keys()) - set(existing_list[c_uid].keys()) != set():
            items_to_update.append(new_list[c_uid])
            continue

        # If existing rule param value doesn't match new rule param OR
        # If existing rule has a param that is not present in new rule except for params in params_to_ignore
        for existing_rule_param, existing_parm_value in existing_list[c_uid].items():
            if (
                existing_rule_param not in params_to_ignore
                and new_list[c_uid].get(existing_rule_param) != existing_parm_value
            ):
                items_to_update.append(new_list[c_uid])

    return items_to_create, items_to_update


class ProxmoxAnsible:
    """Base class for Proxmox modules."""

    TASK_TIMED_OUT = "timeout expired"

    def __init__(self, module):
        if not HAS_PROXMOXER:
            module.fail_json(msg=missing_required_lib("proxmoxer"), exception=PROXMOXER_IMP_ERR)
        if proxmoxer_version < LooseVersion("2.0"):
            module.fail_json(f"Requires proxmoxer 2.0 or newer; found version {proxmoxer_version}")

        self.module = module
        self.proxmoxer_version = proxmoxer_version
        self.proxmox_api = self._connect()
        # Test token validity
        try:
            self.proxmox_api.version.get()
        except Exception as e:
            module.fail_json(msg=f"{e}", exception=traceback.format_exc())

    def _connect(self):
        api_host = self.module.params["api_host"]
        api_port = self.module.params["api_port"]
        api_user = self.module.params["api_user"]
        api_password = self.module.params["api_password"]
        api_token_id = self.module.params["api_token_id"]
        api_token_secret = self.module.params["api_token_secret"]
        if self.module.params["validate_certs"] is None:
            self.module.deprecate(
                "The connection setting `validate_certs` was not provided and "
                "defaults to `false`. This default will change to `true` in"
                "in community.proxmox 2.0.0.",
                version="2.0.0",
                collection_name="community.proxmox",
            )
            self.module.params["validate_certs"] = False
        # Only push the cert path as a string to proxmoxer, if validation is required
        # verify_ssl supports True, False or Path as values
        if self.module.params["ca_path"] and self.module.params["validate_certs"]:
            validate_certs = self.module.params["ca_path"]
        else:
            validate_certs = self.module.params["validate_certs"]
        validate_certs = self.module.params["validate_certs"]
        api_timeout = self.module.params["api_timeout"]
        auth_args = {"user": api_user}

        if api_port:
            auth_args["port"] = api_port

        if api_password:
            auth_args["password"] = api_password
        else:
            auth_args["token_name"] = api_token_id
            auth_args["token_value"] = api_token_secret

        try:
            return ProxmoxAPI(api_host, timeout=api_timeout, verify_ssl=validate_certs, **auth_args)
        except Exception as e:
            self.module.fail_json(msg=f"{e}", exception=traceback.format_exc())

    def version(self):
        """
        Queries the proxmox api for its current version.

        Returns:
            int: Major release of the Proxmox VE host.
        """
        try:
            apiversion = self.proxmox_api.version.get()
            return LooseVersion(apiversion["version"])
        except Exception as e:
            self.module.fail_json(msg=f"Unable to retrieve Proxmox VE version: {e}")

    def get_node(self, node):
        """
        Filters all known PVE nodes for the given node name.

        Args:
            node(str): The name of the node.

        Returns:
            dict | None: The node information provided by the api path GET /nodes.
        """
        try:
            nodes = [n for n in self.proxmox_api.nodes.get() if n["node"] == node]
        except Exception as e:
            self.module.fail_json(msg=f"Unable to retrieve Proxmox VE node: {e}")
        return nodes[0] if nodes else None

    def get_nextvmid(self):
        """
        Queries the PVE api for the next vmid.

        Returns:
            int: The next vmid.
        """
        try:
            return self.proxmox_api.cluster.nextid.get()
        except Exception as e:
            self.module.fail_json(msg=f"Unable to retrieve next free vmid: {e}")

    def get_vmid(self, name, ignore_missing=False, choose_first_if_multiple=False):
        """
        Searches the PVE VMs for a VM with the given name.

        Args:
            name(str): The name to filter the api output to.
            ignore_missing (bool): Don't fail the task if no vm could be found.
            choose_first_if_multiple (bool): Don't fail the task if several names match.

        Returns:
            int | None : The matching vmid or None, when no name matched.
        """
        try:
            vms = [vm["vmid"] for vm in self.proxmox_api.cluster.resources.get(type="vm") if vm.get("name") == name]
        except Exception as e:
            self.module.fail_json(msg=f"Unable to retrieve list of VMs filtered by name {name}: {e}")

        if not vms:
            if ignore_missing:
                return None

            self.module.fail_json(msg=f"No VM with name {name}f found")
        elif len(vms) > 1 and not choose_first_if_multiple:
            self.module.fail_json(msg=f"Multiple VMs with name {name} found, provide vmid instead")

        return vms[0]

    def get_vm(self, vmid, ignore_missing=False):
        """
        Retrieve VM information based on the given VMID.

        Args:
            vmid(int): VMID to query.
            ignore_missing: Skip failing the task if no VM was found.

        Returns:
            dict | None: VM attributes or None, if no VM was found.

        """
        try:
            vms = [vm for vm in self.proxmox_api.cluster.resources.get(type="vm") if vm["vmid"] == int(vmid)]
        except Exception as e:
            self.module.fail_json(msg=f"Unable to retrieve list of VMs filtered by vmid {vmid}: {e}")

        if vms:
            return vms[0]
        else:
            if ignore_missing:
                return None

            self.module.fail_json(msg=f"VM with vmid {vmid} does not exist in cluster")

    def api_task_ok(self, node, taskid):
        """
        Verify the success of a finished task.

        Args:
            node(str): Node, which task log should be queried.
            taskid(str): Unique task identifier.

        Returns:
            bool: Task status.

        """
        try:
            status = self.proxmox_api.nodes(node).tasks(taskid).status.get()
            exitstatus = to_native(status.get("exitstatus") or "")
            return status["status"] == "stopped" and (exitstatus == "OK" or exitstatus.startswith("WARN"))
        except Exception as e:
            self.module.fail_json(msg=f"Unable to retrieve API task ID from node {node}: {e}")

    def api_task_failed(self, node, taskid):
        """
        Verify the failure of a finished task.

        Args:
            node(str): Node, which task log should be queried.
            taskid(str): Unique task identifier.

        Returns:
            bool: Task status.

        """
        try:
            status = self.proxmox_api.nodes(node).tasks(taskid).status.get()
            return status["status"] == "stopped" and status["exitstatus"] != "OK"
        except Exception as e:
            self.module.fail_json(msg=f"Unable to retrieve API task ID from node {node}: {e}")

    def api_task_complete(self, node_name, task_id, timeout):
        """
        Wait until the task stops or times out.

        Args:
            node_name(str): Proxmox node name where the task is running.
            task_id(str): ID of the running task.
            timeout(int): Timeout in seconds to wait for the task to complete.

        Returns:
            tuple[bool, str]: Task completion status and `exitstatus` message when status=False.
        """
        status = {}
        while timeout:
            try:
                status = self.proxmox_api.nodes(node_name).tasks(task_id).status.get()
            except Exception as e:
                self.module.fail_json(msg=f"Unable to retrieve API task ID from node {node_name}: {e}")

            if status["status"] == "stopped":
                if status["exitstatus"] == "OK":
                    return True, None
                else:
                    return False, status["exitstatus"]
            else:
                timeout -= 1
                if timeout <= 0:
                    return False, ProxmoxAnsible.TASK_TIMED_OUT
                sleep(1)

    def get_pool(self, poolid):
        """
        Retrieve pool information.

        Args:
            poolid(str): Name of the pool.

        Returns:
            dict: Pool information.
        """
        try:
            return self.proxmox_api.pools(poolid).get()
        except Exception as e:
            self.module.fail_json(msg=f"Unable to retrieve pool {poolid} information: {e}")

    def get_storages(self, storagetype):
        """
        Retrieve storages information.

        Args:
            storagetype(str): Type of storages to filter to.

        Returns:
            list[dict]: List of configured storages.
        """
        try:
            return self.proxmox_api.storage.get(type=storagetype)
        except Exception as e:
            self.module.fail_json(msg=f"Unable to retrieve storages information with type {storagetype}: {e}")

    def get_storage_content(self, node, storage, content=None, vmid=None):
        """
        Retrieve a list of storage contents.

        Args:
            storage(str): Storage to check.
            node(str): Node to query.
            content(str): Limit the file list to the following content type.
            vmid(int): Limit the file list to this vmid.

        Returns:
            list[dict]: List of configured files.
        """
        try:
            return self.proxmox_api.nodes(node).storage(storage).content().get(content=content, vmid=vmid)
        except Exception as e:
            self.module.fail_json(msg=f"Unable to list content on {node}, {storage} for {content} and {vmid}: {e}")
