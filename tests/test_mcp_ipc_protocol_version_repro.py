"""Red acceptance repro tests for MCP IPC protocol versioning (PYPOST-1467).

Architecture: ai-tasks/PYPOST-1467/20-architecture.md § Mandatory — Failing Repro

Covers:
1. IPC envelope version contracts, error types, and validation helpers.
2. Worker start rejection and exit on incompatible envelope version.
3. Worker runtime command rejection on mismatched envelope version without crashing.
4. Supervisor ingress rejection marking worker failed on mismatched version during startup.
5. Supervisor ingress rejection discarding invalid version envelopes while running.
6. Worker ingress rejection logging on mismatched START envelope version.
7. Worker ingress rejection logging on mismatched runtime command envelope version.
"""

from __future__ import annotations

import logging
import multiprocessing
from unittest.mock import MagicMock

import pytest

import pypost.core.mcp_worker_ipc as ipc
from pypost.core.mcp_process_supervisor import McpProcessSupervisor, _WorkerRecord
from pypost.core.mcp_worker_process import worker_main
from tests.helpers.port_allocation import reserve_ephemeral_ports

pytestmark = pytest.mark.timeout(30)


@pytest.mark.timeout(20)
def test_ipc_envelope_version_contracts() -> None:
    """Validate protocol version contracts, errors, and envelope validation."""
    assert hasattr(ipc, "SUPPORTED_MSG_VERSIONS"), (
        "SUPPORTED_MSG_VERSIONS must be defined in pypost.core.mcp_worker_ipc"
    )
    supported_versions = getattr(ipc, "SUPPORTED_MSG_VERSIONS")
    assert isinstance(supported_versions, frozenset), (
        "SUPPORTED_MSG_VERSIONS must be a frozenset"
    )
    assert 1 in supported_versions, (
        "Version 1 must be supported in SUPPORTED_MSG_VERSIONS"
    )

    assert hasattr(ipc, "McpProtocolVersionError"), (
        "McpProtocolVersionError must be defined in pypost.core.mcp_worker_ipc"
    )
    err_cls = getattr(ipc, "McpProtocolVersionError")
    assert issubclass(err_cls, ValueError), (
        "McpProtocolVersionError must inherit from ValueError"
    )

    # Validate error attributes
    sample_err = err_cls(
        "mismatch", received_v=99, supported_versions=supported_versions
    )
    assert getattr(sample_err, "received_v", None) == 99
    assert getattr(sample_err, "supported_versions", None) == supported_versions

    assert hasattr(ipc, "validate_message_version"), (
        "validate_message_version must be defined in pypost.core.mcp_worker_ipc"
    )
    validate_fn = getattr(ipc, "validate_message_version")

    # Valid version 1
    assert validate_fn({"v": 1, "type": "START"}) == 1

    # Missing version field
    with pytest.raises(err_cls) as missing_info:
        validate_fn({"type": "START"})
    assert getattr(missing_info.value, "received_v", None) is None

    # Non-integer types (bool is an int subclass and must be explicitly rejected)
    for bad_v in ["1", True, False, 1.5, None, [], {}]:
        with pytest.raises(err_cls):
            validate_fn({"v": bad_v, "type": "START"})

    # Unsupported integer versions
    for unsupported_v in [0, 2, 99, -1]:
        with pytest.raises(err_cls):
            validate_fn({"v": unsupported_v, "type": "START"})

    # Envelope constructor default version
    envelope = ipc.make_message("START")
    assert envelope.get("v") == 1
    assert envelope.get("type") == "START"

    # Explicit version parameter override
    v_override = ipc.make_message("START", v=2)
    assert v_override.get("v") == 2


@pytest.mark.timeout(30)
def test_worker_start_rejection_on_mismatched_version() -> None:
    """Worker process must reject invalid START envelope version and abort cleanly."""
    with reserve_ephemeral_ports(1) as ports:
        port = ports[0]
        ctx = multiprocessing.get_context("spawn")
        parent_conn, child_conn = ctx.Pipe(duplex=True)
        proc = ctx.Process(target=worker_main, args=(child_conn,), daemon=True)
        ports.release()
        proc.start()
        child_conn.close()

        try:
            # Send START envelope with unsupported protocol version v=99
            bad_start = {
                "v": 99,
                "type": "START",
                "host": "127.0.0.1",
                "port": port,
                "tools": [],
                "variables": {},
                "hidden_keys": [],
                "overridable_keys": [],
                "name": "test-version-worker",
                "server_type": "local",
            }
            parent_conn.send(bad_start)

            # Worker must reply with START_FAILED and not START
            assert parent_conn.poll(5.0), "Worker did not respond within 5s to invalid START"
            reply = parent_conn.recv()
            assert isinstance(reply, dict), f"Expected dict reply, got {type(reply)}"
            assert reply.get("type") == "START_FAILED", (
                f"Expected START_FAILED on version mismatch, got {reply.get('type')!r}: {reply}"
            )
            assert "version" in str(reply.get("message", "")).lower(), (
                f"Expected version failure message, got: {reply.get('message')}"
            )

            # Worker process should terminate after rejecting START
            proc.join(timeout=3.0)
            assert not proc.is_alive(), "Worker process should terminate after START_FAILED"
        finally:
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=1.0)
                if proc.is_alive():
                    proc.kill()
                    proc.join(timeout=1.0)
            parent_conn.close()


@pytest.mark.timeout(30)
def test_worker_runtime_command_rejection_on_mismatched_version() -> None:
    """Worker must reject runtime commands with invalid version without crashing."""
    with reserve_ephemeral_ports(1) as ports:
        port = ports[0]
        ctx = multiprocessing.get_context("spawn")
        parent_conn, child_conn = ctx.Pipe(duplex=True)
        proc = ctx.Process(target=worker_main, args=(child_conn,), daemon=True)
        ports.release()
        proc.start()
        child_conn.close()

        try:
            # Start worker with valid protocol version 1
            valid_start = ipc.make_message(
                "START",
                host="127.0.0.1",
                port=port,
                tools=[],
                variables={},
                hidden_keys=[],
                overridable_keys=[],
                name="test-version-worker-runtime",
                server_type="local",
            )
            parent_conn.send(valid_start)

            assert parent_conn.poll(5.0), "Worker did not report STARTED within 5s"
            start_ack = parent_conn.recv()
            assert start_ack.get("type") == "STARTED", f"Worker failed to start: {start_ack}"

            # Send UPDATE_TOOLS command with invalid protocol version v=99
            bad_update = {
                "v": 99,
                "type": "UPDATE_TOOLS",
                "tools": [],
            }
            parent_conn.send(bad_update)

            assert parent_conn.poll(5.0), "Worker did not respond to invalid UPDATE_TOOLS"
            err_reply = parent_conn.recv()
            assert err_reply.get("type") in ("WORKER_ERROR", "VERSION_MISMATCH"), (
                f"Expected WORKER_ERROR or VERSION_MISMATCH, "
                f"got {err_reply.get('type')!r}: {err_reply}"
            )
            assert "version" in str(err_reply.get("message", "")).lower(), (
                f"Expected version failure details in message, got: {err_reply.get('message')}"
            )

            # Worker must remain alive and responsive to valid messages
            parent_conn.send(ipc.make_message("HEARTBEAT", nonce="probe-after-rejection"))
            assert parent_conn.poll(5.0), "Worker did not respond to HEARTBEAT after error"
            pong = parent_conn.recv()
            assert pong.get("type") == "HEARTBEAT_PONG"
            assert pong.get("nonce") == "probe-after-rejection"

            # Clean shutdown
            parent_conn.send(ipc.make_message("STOP"))
            proc.join(timeout=3.0)
        finally:
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=1.0)
                if proc.is_alive():
                    proc.kill()
                    proc.join(timeout=1.0)
            parent_conn.close()


@pytest.mark.timeout(20)
def test_supervisor_ingress_start_rejection_on_mismatched_version(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Supervisor receiving invalid version during worker startup marks worker failed."""
    supervisor = McpProcessSupervisor()
    try:
        mock_proc = MagicMock(pid=8888, is_alive=MagicMock(return_value=True))
        record = _WorkerRecord(
            instance_id="sup-start-reject",
            process=mock_proc,
            parent_conn=MagicMock(),
            state="starting",
        )
        with supervisor._lock:
            supervisor._workers["sup-start-reject"] = record

        caplog.clear()
        with caplog.at_level(logging.ERROR, logger="pypost.core.mcp_process_supervisor"):
            supervisor._apply_ipc_message(
                "sup-start-reject",
                {
                    "v": 99,
                    "type": "STARTED",
                    "pid": 8888,
                    "host": "127.0.0.1",
                    "port": 9000,
                },
            )

        # State must transition to failed with started_event signaled
        assert record.state == "failed", f"Expected state 'failed', got {record.state!r}"
        assert record.started_event.is_set(), "started_event must be signaled"
        assert "version" in str(record.last_error or "").lower(), (
            f"Expected version rejection in last_error, got {record.last_error!r}"
        )
        assert "mcp_supervisor_ipc_version_rejected" in caplog.text
        assert "received_v=99" in caplog.text
    finally:
        supervisor.shutdown()


@pytest.mark.timeout(20)
def test_supervisor_ingress_running_rejection_on_mismatched_version(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Supervisor receiving invalid version while worker is running logs and discards."""
    supervisor = McpProcessSupervisor()
    try:
        mock_proc = MagicMock(pid=8889, is_alive=MagicMock(return_value=True))
        record = _WorkerRecord(
            instance_id="sup-run-reject",
            process=mock_proc,
            parent_conn=MagicMock(),
            state="running",
        )
        with supervisor._lock:
            supervisor._workers["sup-run-reject"] = record

        caplog.clear()
        with caplog.at_level(logging.ERROR, logger="pypost.core.mcp_process_supervisor"):
            # Invalid envelope that would otherwise mutate state if not version-checked
            supervisor._apply_ipc_message(
                "sup-run-reject",
                {"v": 99, "type": "START_FAILED", "message": "untrusted-start-failed"},
            )

        # State must not be mutated to 'failed' because envelope version was rejected
        assert record.state == "running", (
            f"Expected state to remain 'running', got {record.state!r}"
        )
        assert record.last_error is None
        assert "mcp_supervisor_ipc_version_rejected" in caplog.text
        assert "received_v=99" in caplog.text
    finally:
        supervisor.shutdown()


@pytest.mark.timeout(20)
def test_worker_ingress_start_rejection_logs_version_mismatch(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Worker logs mcp_worker_ipc_version_rejected when START has mismatched version."""
    mock_conn = MagicMock()
    mock_conn.poll.return_value = True
    mock_conn.recv.return_value = {"v": 99, "type": "START"}

    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="pypost.core.mcp_worker_process"):
        worker_main(mock_conn)

    assert "mcp_worker_ipc_version_rejected" in caplog.text
    assert "received_v=99" in caplog.text
    assert "supported=" in caplog.text
    assert mock_conn.send.call_count == 1
    reply = mock_conn.send.call_args[0][0]
    assert reply.get("type") == "START_FAILED"


@pytest.mark.timeout(20)
def test_worker_ingress_runtime_rejection_logs_version_mismatch(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Worker logs mcp_worker_ipc_version_rejected when runtime message has bad version."""
    monkeypatch.setattr(
        "pypost.core.mcp_worker_process._run_uvicorn",
        lambda *args, **kwargs: None,
    )
    mock_conn = MagicMock()
    mock_conn.poll.return_value = True
    mock_conn.recv.side_effect = [
        ipc.make_message(
            "START",
            tools=[],
            variables={},
            hidden_keys=[],
            overridable_keys=[],
        ),
        {"v": 99, "type": "UPDATE_TOOLS", "tools": []},
        EOFError(),
    ]

    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="pypost.core.mcp_worker_process"):
        worker_main(mock_conn)

    assert "mcp_worker_ipc_version_rejected" in caplog.text
    assert "received_v=99" in caplog.text
    assert mock_conn.send.call_count == 1
    reply = mock_conn.send.call_args[0][0]
    assert reply.get("type") == "WORKER_ERROR"
