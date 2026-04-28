# Copyright (c) 2025 Ian Williams (@aph3rson)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
---
name: proxmox_qemu_api
short_description: Connect to QEMU VMs via the Proxmox guest agent API
description:
  - Execute commands and transfer files through the Proxmox VE QEMU Guest Agent API.
  - Does not require SSH or network connectivity to the VM.
  - Requires the QEMU Guest Agent (C(qemu-guest-agent)) to be installed and running inside the target VM.
  - Talks directly to the Proxmox REST API using C(proxmoxer), avoiding the overhead and limitations
    of shelling out to C(qm guest exec) over SSH.
  - Linux guests only. Windows guest support is not implemented.
author:
  - Ian Williams (@aph3rson)
version_added: "2.0.0"
requirements:
  - proxmoxer >= 2.3.0
  - requests
options:
  api_host:
    description: Proxmox VE API hostname or IP address.
    required: true
    type: str
    vars:
      - name: proxmox_api_host
    env:
      - name: PROXMOX_HOST
  api_port:
    description: Proxmox VE API port.
    default: 8006
    type: int
    vars:
      - name: proxmox_api_port
    env:
      - name: PROXMOX_PORT
  api_user:
    description:
      - Proxmox VE API user (for example V(root@pam)).
      - Used with O(api_password) to obtain an authentication ticket.
      - Mutually exclusive with O(api_token_id).
    type: str
    vars:
      - name: proxmox_api_user
    env:
      - name: PROXMOX_USER
  api_password:
    description:
      - Password for O(api_user).
      - Required when O(api_user) is set.
    type: str
    vars:
      - name: proxmox_api_password
    env:
      - name: PROXMOX_PASSWORD
  api_token_id:
    description:
      - API token ID (for example V(user@pam!token_name)).
      - Used with O(api_token_secret).
      - Mutually exclusive with O(api_user).
    type: str
    vars:
      - name: proxmox_api_token_id
    env:
      - name: PROXMOX_TOKEN_ID
  api_token_secret:
    description:
      - API token secret UUID.
      - Required when O(api_token_id) is set.
    type: str
    vars:
      - name: proxmox_api_token_secret
    env:
      - name: PROXMOX_TOKEN_SECRET
  node:
    description: Proxmox node name where the VM resides.
    required: true
    type: str
    vars:
      - name: proxmox_node
    env:
      - name: PROXMOX_NODE
  vmid:
    description: Target QEMU VM ID.
    required: true
    type: int
    vars:
      - name: proxmox_vmid
    env:
      - name: PROXMOX_VMID
  validate_certs:
    description: Validate PVE API TLS certificates.
    default: true
    type: bool
    vars:
      - name: proxmox_validate_certs
    env:
      - name: PROXMOX_VERIFY_SSL
  remote_tmp:
    description:
      - Temporary directory on the guest for staging chunked file transfers.
      - Must be writable by the guest agent process (typically root).
      - Only used when transferring files larger than 45000 bytes.
    default: /tmp
    type: str
    vars:
      - name: proxmox_remote_tmp
  executable:
    description: Shell executable for command execution on the guest.
    default: /bin/sh
    type: str
    vars:
      - name: ansible_executable
  connect_timeout:
    description:
      - Maximum number of seconds to wait for the guest agent to become responsive.
      - The plugin polls the agent every 5 seconds during connection.
    default: 60
    type: int
    vars:
      - name: proxmox_connect_timeout
notes:
  - The API user or token requires guest agent privileges on the target VM.
    On PVE 8, this is C(VM.Monitor). On PVE 9+, C(VM.Monitor) was replaced with
    fine-grained privileges -- C(VM.GuestAgent.Unrestricted) covers command execution,
    C(VM.GuestAgent.FileRead) and C(VM.GuestAgent.FileWrite) cover file transfers.
    Alternatively, C(VM.GuestAgent.Unrestricted) alone grants access to all guest agent operations.
  - This plugin requires the QEMU Guest Agent to be installed and running inside the VM.
    If the agent is not responsive, the connection will fail after O(connect_timeout) seconds.
  - File transfers use the PVE guest agent file-read/file-write API, which has a per-call
    size limit of approximately 45000 bytes. Files larger than this are automatically
    split into chunks using C(split) on the guest and reassembled on the controller or guest.
  - "Guest requirements: C(qemu-guest-agent) must be running. File transfers additionally
    require C(cat), C(split), C(ls), and C(rm) (coreutils)."
  - Works with the C(community.proxmox.proxmox) inventory plugin. Set
    C(ansible_connection=community.proxmox.proxmox_qemu_api) on discovered hosts.
"""

EXAMPLES = r"""
- name: Static inventory example
  # inventory.yml
  # all:
  #   hosts:
  #     my-vm:
  #       ansible_connection: community.proxmox.proxmox_qemu_api
  #       proxmox_vmid: 100
  #       ansible_host: my-vm.example.com
  #   vars:
  #     proxmox_api_host: pve-1.example.com
  #     proxmox_api_port: 8006
  #     proxmox_api_token_id: automation@pve!ansible
  #     proxmox_api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  #     proxmox_node: pve-1
  hosts: my-vm
  gather_facts: true
  tasks:
    - name: Install a package
      ansible.builtin.apt:
        name: curl
        state: present

    - name: Copy a configuration file
      ansible.builtin.copy:
        src: app.conf
        dest: /etc/app/app.conf

    - name: Run a command
      ansible.builtin.command:
        cmd: systemctl restart app
"""

import base64
import logging
import time

from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display

from ansible_collections.community.proxmox.plugins.module_utils.proxmox import HAS_PROXMOXER

if HAS_PROXMOXER:
    from proxmoxer import ProxmoxAPI

display = Display()


class _DisplayHandler(logging.Handler):
    """Route Python logging to Ansible Display."""

    _level_map = {
        logging.DEBUG: display.vvvv,
        logging.INFO: display.vvv,
        logging.WARNING: display.warning,
    }

    def emit(self, record):
        fn = self._level_map.get(record.levelno, display.warning)
        fn(self.format(record))


# Wire urllib3/requests logging through Display instead of stderr.
_handler = _DisplayHandler()
_handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
for _name in ("urllib3", "requests", "py.warnings"):
    _logger = logging.getLogger(_name)
    _logger.handlers.clear()
    _logger.addHandler(_handler)
    _logger.propagate = False

# PVE file-write content limit is 61440 bytes.
# base64 expands 3:4, so 45000 raw bytes -> 60000 base64 chars, safely under limit.
# TODO: Increase once Proxmox raises the QEMU guest agent file-write size limit.
# https://forum.proxmox.com/threads/maximum-file-upload-size-for-qemu-agent-file-write.166200/
FILE_WRITE_CHUNK = 45000
FILE_WRITE_RETRIES = 5


class Connection(ConnectionBase):
    """Connection plugin that uses the Proxmox QEMU Guest Agent API."""

    transport = "community.proxmox.proxmox_qemu_api"
    has_pipelining = False
    has_tty = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connected = False
        self._proxmox = None
        logging.captureWarnings(True)

    def _get_proxmox(self):
        if self._proxmox is not None:
            return self._proxmox

        if not HAS_PROXMOXER:
            msg = "This connection plugin requires the 'proxmoxer' library"
            raise AnsibleError(msg) from None

        host = self.get_option("api_host")
        port = self.get_option("api_port")
        verify_ssl = self.get_option("validate_certs")
        token_id = self.get_option("api_token_id")
        token_secret = self.get_option("api_token_secret")
        user = self.get_option("api_user")
        password = self.get_option("api_password")

        if token_id and token_secret:
            self._proxmox = ProxmoxAPI(
                host,
                port=port,
                user=token_id.split("!")[0],
                token_name=token_id.split("!")[-1],
                token_value=token_secret,
                verify_ssl=verify_ssl,
            )
        elif user and password:
            self._proxmox = ProxmoxAPI(
                host,
                port=port,
                user=user,
                password=password,
                verify_ssl=verify_ssl,
            )
        else:
            raise AnsibleConnectionFailure(
                "No authentication configured. Provide api_token_id + api_token_secret, or api_user + api_password."
            )

        return self._proxmox

    def _agent(self):
        proxmox = self._get_proxmox()
        node = self.get_option("node")
        vmid = self.get_option("vmid")
        return proxmox.nodes(node).qemu(vmid).agent

    def _connect(self):
        if self._connected:
            return self
        super()._connect()

        timeout = self.get_option("connect_timeout")
        interval = 5
        attempts = max(timeout // interval, 1)

        for attempt in range(attempts):
            try:
                self._agent().ping.post()
                self._connected = True
                display.vvv(f"QEMU guest agent responsive on VM {self.get_option('vmid')}")
                return self
            except Exception:
                if attempt < attempts - 1:
                    display.vvv(
                        f"Guest agent not ready on VM {self.get_option('vmid')}, "
                        f"retrying in {interval}s ({attempt + 1}/{attempts})"
                    )
                    time.sleep(interval)
                else:
                    raise AnsibleConnectionFailure(
                        f"QEMU guest agent is not responding on VM {self.get_option('vmid')} "
                        f"after {timeout}s. Is qemu-guest-agent installed and running?"
                    ) from None

    def exec_command(self, cmd, in_data=None, sudoable=True):
        super().exec_command(cmd, in_data=in_data, sudoable=sudoable)
        self._connect()

        shell = self.get_option("executable")
        display.vvv(f"EXEC via guest agent: {cmd}")

        try:
            data = self._agent().exec.post(command=[shell, "-c", cmd])
        except Exception as exc:
            raise AnsibleConnectionFailure(f"Failed to execute command on VM {self.get_option('vmid')}: {exc}") from exc

        pid = data["pid"]
        status = self._poll_exec_status(pid)

        rc = status.get("exitcode", -1)
        stdout = status.get("out-data", "")
        stderr = status.get("err-data", "")
        return rc, stdout, stderr

    def _poll_exec_status(self, pid):
        while True:
            time.sleep(0.5)
            status = self._agent()("exec-status").get(pid=pid)
            if status.get("exited"):
                return status

    def _file_write(self, guest_path, data_bytes):
        encoded = base64.b64encode(data_bytes).decode("ascii")
        for attempt in range(FILE_WRITE_RETRIES + 1):
            try:
                self._agent()("file-write").post(file=guest_path, content=encoded, encode=0)
                return
            except Exception:
                if attempt < FILE_WRITE_RETRIES:
                    time.sleep(5)
                else:
                    raise AnsibleConnectionFailure(
                        f"Failed to write file {guest_path} on VM {self.get_option('vmid')} "
                        f"after {FILE_WRITE_RETRIES + 1} attempts"
                    ) from None

    def put_file(self, in_path, out_path):
        super().put_file(in_path, out_path)
        self._connect()
        display.vvv(f"PUT {in_path} -> {out_path} via guest agent")

        with open(in_path, "rb") as f:
            raw = f.read()

        if len(raw) <= FILE_WRITE_CHUNK:
            self._file_write(out_path, raw)
            return

        self._put_file_chunked(raw, out_path)

    def _put_file_chunked(self, raw, out_path):
        remote_tmp = self.get_option("remote_tmp")
        parts = []
        for i in range(0, len(raw), FILE_WRITE_CHUNK):
            part_path = f"{remote_tmp}/.ansible_part_{i}"
            parts.append(part_path)
            self._file_write(part_path, raw[i : i + FILE_WRITE_CHUNK])

        cat_cmd = "cat " + " ".join(parts) + f" > {out_path} && rm -f " + " ".join(parts)
        rc, dummy_stdout, err = self.exec_command(cat_cmd)
        if rc != 0:
            raise AnsibleConnectionFailure(f"Failed to assemble chunked file on VM {self.get_option('vmid')}: {err}")

    def _file_read(self, guest_path):
        """Read a file from the guest via file-read API.

        PVE encodes raw file bytes as JSON unicode escapes (\\u00XX),
        which json.loads turns into a Python str with code points 0x00-0xFF.
        latin-1 is the exact inverse: U+00NN -> byte 0xNN, preserving binary content.
        """
        result = self._agent()("file-read").get(file=guest_path)
        content = result.get("content", "")
        return content.encode("latin-1")

    def fetch_file(self, in_path, out_path):
        super().fetch_file(in_path, out_path)
        self._connect()
        display.vvv(f"FETCH {in_path} -> {out_path} via guest agent")

        remote_tmp = self.get_option("remote_tmp")
        prefix = f"{remote_tmp}/.ansible_fetch_"

        # Split file into chunks on guest, read each chunk, append locally
        split_cmd = f"split -b {FILE_WRITE_CHUNK} -- {in_path} {prefix}"
        rc, dummy_stdout, err = self.exec_command(split_cmd)
        if rc != 0:
            raise AnsibleConnectionFailure(f"Failed to split file {in_path} on VM {self.get_option('vmid')}: {err}")

        # List the chunk files in order
        rc, stdout, err = self.exec_command(f"ls -1 {prefix}* 2>/dev/null")
        if rc != 0:
            raise AnsibleConnectionFailure(
                f"Failed to list chunks for {in_path} on VM {self.get_option('vmid')}: {err}"
            )

        parts = stdout.strip().split("\n") if stdout.strip() else []

        try:
            with open(out_path, "wb") as f:
                for part in parts:
                    chunk = self._file_read(part.strip())
                    f.write(chunk)
        finally:
            if parts:
                self.exec_command(f"rm -f {prefix}*")

    def close(self):
        self._proxmox = None
        self._connected = False
        super().close()

    def reset(self):
        self.close()
        self._connect()
