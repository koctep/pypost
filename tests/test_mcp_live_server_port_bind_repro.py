"""Deterministic repro for MCP live-server ephemeral port TOCTOU (PYPOST-1541)."""

from __future__ import annotations

import socket

import pytest

from pypost.core.request_service import ExecutionResult
from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from tests.helpers import mcp_live_server as live_mod
from tests.helpers.mcp_live_server import LiveMCPServer
from tests.helpers.port_allocation import allocate_bound_tcp_socket


pytestmark = pytest.mark.timeout(60)


def _exec_ok() -> ExecutionResult:
    body = "ok"
    return ExecutionResult(
        response=ResponseData(
            status_code=200,
            headers={},
            body=body,
            elapsed_time=0.01,
            size=len(body.encode("utf-8")),
        ),
        updated_variables={},
        script_logs=[],
        execution_error=None,
    )


@pytest.mark.timeout(30)
def test_allocate_bound_tcp_socket_holds_port_until_closed() -> None:
    """Held bind must exclude a peer exclusive bind until the socket is closed."""
    sock = allocate_bound_tcp_socket("127.0.0.1")
    port = int(sock.getsockname()[1])
    peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(OSError):
            peer.bind(("127.0.0.1", port))
    finally:
        peer.close()
        sock.close()

    rebound = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        rebound.bind(("127.0.0.1", port))
    finally:
        rebound.close()


@pytest.mark.timeout(60)
def test_live_mcp_server_starts_when_allocated_port_stolen_before_listen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the first reserved listen socket is unusable, start() retries and listens."""
    holders: list[socket.socket] = []
    calls = {"n": 0}
    real_alloc = live_mod.allocate_bound_tcp_socket

    def alloc_steal_first(host: str = "127.0.0.1") -> socket.socket:
        calls["n"] += 1
        sock = real_alloc(host)
        if calls["n"] != 1:
            return sock
        port = int(sock.getsockname()[1])
        sock.close()
        holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        holder.bind((host, port))
        holders.append(holder)

        class _DeadSocket:
            """Closed reservation that still reports the stolen port for wait_for_port."""

            def getsockname(self) -> tuple[str, int]:
                return (host, port)

            def close(self) -> None:
                return None

            def fileno(self) -> int:
                return -1

        return _DeadSocket()  # type: ignore[return-value]

    monkeypatch.setattr(live_mod, "allocate_bound_tcp_socket", alloc_steal_first)

    tool = RequestData(
        name="Port Hold Probe",
        expose_as_mcp=True,
        method="GET",
        url="http://example.com/probe",
    )
    server = LiveMCPServer([tool], execute_result=_exec_ok())
    try:
        server.start()
        probe = socket.create_connection((server.host, server.port), timeout=1.0)
        probe.close()
    finally:
        server.stop()
        for holder in holders:
            holder.close()

    assert calls["n"] >= 2, "expected bind retry after the stolen first reservation"
