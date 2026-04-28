# Copyright (c) 2025 Ian (@aph3rson)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from io import StringIO
from unittest.mock import MagicMock, mock_open, patch

import pytest
from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import connection_loader

proxmoxer = pytest.importorskip("proxmoxer")

MODULE = "ansible_collections.community.proxmox.plugins.connection.proxmox_qemu_api"

# Test constants
TEST_API_HOST = "pve.example.com"
TEST_API_PORT = 8006
TEST_NODE = "pve-1"
TEST_VMID = 100
TEST_CONNECT_TIMEOUT = 60


@pytest.fixture
def connection():
    """Create a connection instance with minimal required options."""
    play_context = PlayContext()
    in_stream = StringIO()
    conn = connection_loader.get("community.proxmox.proxmox_qemu_api", play_context, in_stream)
    conn.set_option("api_host", TEST_API_HOST)
    conn.set_option("api_port", TEST_API_PORT)
    conn.set_option("api_token_id", "user@pam!token")
    conn.set_option("api_token_secret", "secret-uuid")
    conn.set_option("node", TEST_NODE)
    conn.set_option("vmid", TEST_VMID)
    conn.set_option("validate_certs", True)
    conn.set_option("remote_tmp", "/tmp")
    conn.set_option("executable", "/bin/sh")
    conn.set_option("connect_timeout", TEST_CONNECT_TIMEOUT)
    return conn


def test_connection_options(connection):
    """Test that connection options are properly set."""
    assert connection.get_option("api_host") == "pve.example.com"
    assert connection.get_option("api_port") == TEST_API_PORT
    assert connection.get_option("node") == "pve-1"
    assert connection.get_option("vmid") == TEST_VMID
    assert connection.get_option("validate_certs") is True
    assert connection.get_option("remote_tmp") == "/tmp"
    assert connection.get_option("executable") == "/bin/sh"
    assert connection.get_option("connect_timeout") == TEST_CONNECT_TIMEOUT


def test_transport_name(connection):
    """Test that the transport name is correct."""
    assert connection.transport == "community.proxmox.proxmox_qemu_api"


def test_has_pipelining(connection):
    """Test that pipelining is disabled."""
    assert connection.has_pipelining is False


def test_has_tty(connection):
    """Test that TTY is disabled."""
    assert connection.has_tty is False


@patch(f"{MODULE}.ProxmoxAPI")
def test_get_proxmox_with_token(mock_api, connection):
    """Test ProxmoxAPI initialization with token authentication."""
    connection._get_proxmox()

    mock_api.assert_called_once_with(
        "pve.example.com",
        port=TEST_API_PORT,
        user="user@pam",
        token_name="token",
        token_value="secret-uuid",
        verify_ssl=True,
    )


@patch(f"{MODULE}.ProxmoxAPI")
def test_get_proxmox_with_password(mock_api, connection):
    """Test ProxmoxAPI initialization with password authentication."""
    connection.set_option("api_token_id", None)
    connection.set_option("api_token_secret", None)
    connection.set_option("api_user", "root@pam")
    connection.set_option("api_password", "password123")

    connection._get_proxmox()

    mock_api.assert_called_once_with(
        "pve.example.com",
        port=TEST_API_PORT,
        user="root@pam",
        password="password123",
        verify_ssl=True,
    )


def test_get_proxmox_no_auth(connection):
    """Test that missing authentication raises an error."""
    connection.set_option("api_token_id", None)
    connection.set_option("api_token_secret", None)
    connection.set_option("api_user", None)
    connection.set_option("api_password", None)

    with pytest.raises(AnsibleConnectionFailure, match="No authentication configured"):
        connection._get_proxmox()


@patch(f"{MODULE}.ProxmoxAPI")
def test_get_proxmox_caches_instance(mock_api, connection):
    """Test that ProxmoxAPI is only created once."""
    connection._get_proxmox()
    connection._get_proxmox()

    assert mock_api.call_count == 1


@patch(f"{MODULE}.HAS_PROXMOXER", False)
def test_get_proxmox_missing_library(connection):
    """Test that missing proxmoxer library raises an error."""
    connection._proxmox = None

    with pytest.raises(AnsibleError, match="requires the 'proxmoxer' library"):
        connection._get_proxmox()


@patch(f"{MODULE}.ProxmoxAPI")
def test_agent_returns_correct_path(mock_api, connection):
    """Test that _agent() builds the correct API path."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox

    connection._get_proxmox()
    connection._agent()

    mock_proxmox.nodes.assert_called_once_with("pve-1")
    mock_proxmox.nodes("pve-1").qemu.assert_called_once_with(100)


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_connect_success(mock_api, mock_sleep, connection):
    """Test successful connection to guest agent."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox

    connection._connect()

    assert connection._connected is True
    mock_sleep.assert_not_called()


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_connect_retries_on_failure(mock_api, mock_sleep, connection):
    """Test that connection retries when guest agent is not ready."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox

    agent = mock_proxmox.nodes("pve-1").qemu(TEST_VMID).agent
    agent.ping.post.side_effect = [Exception("not ready"), Exception("not ready"), None]

    connection.set_option("connect_timeout", 15)
    connection._connect()

    assert connection._connected is True
    assert mock_sleep.call_count == 2  # noqa: PLR2004


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_connect_timeout(mock_api, mock_sleep, connection):
    """Test that connection fails after timeout."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox

    agent = mock_proxmox.nodes("pve-1").qemu(TEST_VMID).agent
    agent.ping.post.side_effect = Exception("not ready")

    connection.set_option("connect_timeout", 10)

    with pytest.raises(AnsibleConnectionFailure, match="QEMU guest agent is not responding"):
        connection._connect()


def test_connect_already_connected(connection):
    """Test that _connect() is a no-op when already connected."""
    connection._connected = True
    result = connection._connect()
    assert result is connection


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_exec_command_success(mock_api, mock_sleep, connection):
    """Test successful command execution."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox

    agent = mock_proxmox.nodes("pve-1").qemu(TEST_VMID).agent
    agent.exec.post.return_value = {"pid": 42}
    agent("exec-status").get.return_value = {"exited": 1, "exitcode": 0, "out-data": "hello\n", "err-data": ""}

    connection._connected = True
    connection._proxmox = mock_proxmox

    rc, stdout, stderr = connection.exec_command("echo hello")

    assert rc == 0
    assert stdout == "hello\n"
    assert stderr == ""
    agent.exec.post.assert_called_once_with(command=["/bin/sh", "-c", "echo hello"])


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_exec_command_nonzero_exit(mock_api, mock_sleep, connection):
    """Test command execution with non-zero exit code."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox

    agent = mock_proxmox.nodes("pve-1").qemu(TEST_VMID).agent
    agent.exec.post.return_value = {"pid": 42}
    agent("exec-status").get.return_value = {"exited": 1, "exitcode": 1, "out-data": "", "err-data": "not found\n"}

    connection._connected = True
    connection._proxmox = mock_proxmox

    rc, stdout, stderr = connection.exec_command("false")

    assert rc == 1
    assert stderr == "not found\n"


@patch(f"{MODULE}.ProxmoxAPI")
def test_exec_command_api_failure(mock_api, connection):
    """Test command execution when API call fails."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox

    agent = mock_proxmox.nodes("pve-1").qemu(TEST_VMID).agent
    agent.exec.post.side_effect = Exception("API error")

    connection._connected = True
    connection._proxmox = mock_proxmox

    with pytest.raises(AnsibleConnectionFailure, match="Failed to execute command"):
        connection.exec_command("echo hello")


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_poll_exec_status_waits(mock_api, mock_sleep, connection):
    """Test that exec status polling waits for completion."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox
    connection._proxmox = mock_proxmox

    agent = mock_proxmox.nodes("pve-1").qemu(TEST_VMID).agent
    agent("exec-status").get.side_effect = [
        {"exited": 0},
        {"exited": 0},
        {"exited": 1, "exitcode": 0, "out-data": "done"},
    ]

    status = connection._poll_exec_status(42)

    assert status["out-data"] == "done"
    assert mock_sleep.call_count == 3  # noqa: PLR2004


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_file_write_success(mock_api, mock_sleep, connection):
    """Test successful file write."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox
    connection._proxmox = mock_proxmox

    agent = mock_proxmox.nodes("pve-1").qemu(TEST_VMID).agent

    connection._file_write("/tmp/test", b"hello")

    agent("file-write").post.assert_called_once()
    call_kwargs = agent("file-write").post.call_args[1]
    assert call_kwargs["file"] == "/tmp/test"
    assert call_kwargs["encode"] == 0


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_file_write_retries(mock_api, mock_sleep, connection):
    """Test that file write retries on failure."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox
    connection._proxmox = mock_proxmox

    agent = mock_proxmox.nodes("pve-1").qemu(TEST_VMID).agent
    agent("file-write").post.side_effect = [Exception("busy"), Exception("busy"), None]

    connection._file_write("/tmp/test", b"hello")

    assert agent("file-write").post.call_count == 3  # noqa: PLR2004


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_file_write_exhausts_retries(mock_api, mock_sleep, connection):
    """Test that file write fails after exhausting retries."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox
    connection._proxmox = mock_proxmox

    agent = mock_proxmox.nodes("pve-1").qemu(TEST_VMID).agent
    agent("file-write").post.side_effect = Exception("busy")

    with pytest.raises(AnsibleConnectionFailure, match="Failed to write file"):
        connection._file_write("/tmp/test", b"hello")


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_put_file_small(mock_api, mock_sleep, connection):
    """Test putting a small file (under chunk size)."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox
    connection._connected = True
    connection._proxmox = mock_proxmox

    with patch("builtins.open", mock_open(read_data=b"small file")):
        connection.put_file("/local/path", "/remote/path")

    agent = mock_proxmox.nodes("pve-1").qemu(TEST_VMID).agent
    agent("file-write").post.assert_called_once()


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_put_file_chunked(mock_api, mock_sleep, connection):
    """Test putting a large file that requires chunking."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox
    connection._connected = True
    connection._proxmox = mock_proxmox

    agent = mock_proxmox.nodes("pve-1").qemu(TEST_VMID).agent
    agent.exec.post.return_value = {"pid": 1}
    agent("exec-status").get.return_value = {"exited": 1, "exitcode": 0, "out-data": "", "err-data": ""}

    large_data = b"x" * 100000
    with patch("builtins.open", mock_open(read_data=large_data)):
        connection.put_file("/local/path", "/remote/path")

    # Should have written 3 chunks (45000 + 45000 + 10000)
    assert agent("file-write").post.call_count == 3  # noqa: PLR2004
    # Should have run cat to assemble
    agent.exec.post.assert_called_once()


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_put_file_chunked_uses_remote_tmp(mock_api, mock_sleep, connection):
    """Test that chunked file transfer uses the configured remote_tmp."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox
    connection._connected = True
    connection._proxmox = mock_proxmox
    connection.set_option("remote_tmp", "/var/tmp")

    agent = mock_proxmox.nodes("pve-1").qemu(TEST_VMID).agent
    agent.exec.post.return_value = {"pid": 1}
    agent("exec-status").get.return_value = {"exited": 1, "exitcode": 0, "out-data": "", "err-data": ""}

    large_data = b"x" * 50000
    with patch("builtins.open", mock_open(read_data=large_data)):
        connection.put_file("/local/path", "/remote/path")

    # Check that the cat command references /var/tmp
    exec_call = agent.exec.post.call_args
    cmd = exec_call[1]["command"][2]
    assert "/var/tmp/.ansible_part_" in cmd


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_put_file_chunked_assemble_failure(mock_api, mock_sleep, connection):
    """Test that chunked file transfer fails if assembly fails."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox
    connection._connected = True
    connection._proxmox = mock_proxmox

    agent = mock_proxmox.nodes("pve-1").qemu(TEST_VMID).agent
    agent.exec.post.return_value = {"pid": 1}
    agent("exec-status").get.return_value = {"exited": 1, "exitcode": 1, "out-data": "", "err-data": "disk full"}

    large_data = b"x" * 50000
    with pytest.raises(AnsibleConnectionFailure, match="Failed to assemble chunked file"), patch(
        "builtins.open", mock_open(read_data=large_data)
    ):
        connection.put_file("/local/path", "/remote/path")


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_fetch_file_small(mock_api, mock_sleep, connection):
    """Test fetching a small file (single chunk)."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox
    connection._connected = True
    connection._proxmox = mock_proxmox

    agent = mock_proxmox.nodes("pve-1").qemu(TEST_VMID).agent
    agent("file-read").get.return_value = {"content": "hello world"}

    with patch.object(connection, "exec_command") as mock_exec:
        mock_exec.side_effect = [
            (0, "", ""),  # split
            (0, "/tmp/.ansible_fetch_aa\n", ""),  # ls
            (0, "", ""),  # rm
        ]
        m = mock_open()
        with patch("builtins.open", m):
            connection.fetch_file("/remote/path", "/local/path")

    m.assert_called_with("/local/path", "wb")
    m().write.assert_called_once_with(b"hello world")


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_fetch_file_chunked(mock_api, mock_sleep, connection):
    """Test fetching a large file that requires multiple chunks."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox
    connection._connected = True
    connection._proxmox = mock_proxmox

    chunk_a = "a" * 45000
    chunk_b = "b" * 45000
    chunk_c = "c" * 10000
    agent = mock_proxmox.nodes("pve-1").qemu(TEST_VMID).agent
    agent("file-read").get.side_effect = [
        {"content": chunk_a},
        {"content": chunk_b},
        {"content": chunk_c},
    ]

    with patch.object(connection, "exec_command") as mock_exec:
        mock_exec.side_effect = [
            (0, "", ""),  # split
            (0, "/tmp/.ansible_fetch_aa\n/tmp/.ansible_fetch_ab\n/tmp/.ansible_fetch_ac\n", ""),  # ls
            (0, "", ""),  # rm
        ]
        m = mock_open()
        with patch("builtins.open", m):
            connection.fetch_file("/remote/path", "/local/path")

    assert agent("file-read").get.call_count == 3  # noqa: PLR2004
    calls = m().write.call_args_list
    assert len(calls) == 3  # noqa: PLR2004
    assert calls[0][0][0] == chunk_a.encode("latin-1")
    assert calls[1][0][0] == chunk_b.encode("latin-1")
    assert calls[2][0][0] == chunk_c.encode("latin-1")


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_fetch_file_binary(mock_api, mock_sleep, connection):
    """Test fetching a binary file preserves bytes via latin-1 encoding."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox
    connection._connected = True
    connection._proxmox = mock_proxmox

    binary_as_str = "".join(chr(i) for i in range(256))
    agent = mock_proxmox.nodes("pve-1").qemu(TEST_VMID).agent
    agent("file-read").get.return_value = {"content": binary_as_str}

    with patch.object(connection, "exec_command") as mock_exec:
        mock_exec.side_effect = [
            (0, "", ""),  # split
            (0, "/tmp/.ansible_fetch_aa\n", ""),  # ls
            (0, "", ""),  # rm
        ]
        m = mock_open()
        with patch("builtins.open", m):
            connection.fetch_file("/remote/path", "/local/path")

    written = m().write.call_args[0][0]
    assert written == bytes(range(256))


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_fetch_file_split_failure(mock_api, mock_sleep, connection):
    """Test that fetch fails if split command fails."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox
    connection._connected = True
    connection._proxmox = mock_proxmox

    with patch.object(connection, "exec_command") as mock_exec:
        mock_exec.return_value = (1, "", "No such file")
        with pytest.raises(AnsibleConnectionFailure, match="Failed to split file"):
            connection.fetch_file("/remote/path", "/local/path")


def test_close(connection):
    """Test connection close."""
    connection._connected = True
    connection._proxmox = MagicMock()

    connection.close()

    assert connection._connected is False
    assert connection._proxmox is None


@patch(f"{MODULE}.time.sleep")
@patch(f"{MODULE}.ProxmoxAPI")
def test_reset(mock_api, mock_sleep, connection):
    """Test connection reset closes and reconnects."""
    mock_proxmox = MagicMock()
    mock_api.return_value = mock_proxmox
    connection._connected = True
    connection._proxmox = mock_proxmox

    connection.reset()

    # After reset, should be connected again
    assert connection._connected is True
