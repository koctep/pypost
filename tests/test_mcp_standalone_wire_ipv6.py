"""IPv6 socket transport tests for standalone MCP servers and RawTcpWireClient.

Validates RFC 3986 bracketed Host headers, AF_INET6 socket family negotiation,
and standalone MCP server wire protocol lifecycle over IPv6 loopback (::1).

Jira: PYPOST-1431
Architecture: ai-tasks/PYPOST-1431/20-architecture.md
"""

from __future__ import annotations

import json
import socket
from typing import Any
from unittest.mock import MagicMock

import pytest

from pypost.core.qt.mcp_server import MCPServerManager
from pypost.core.request_service import ExecutionResult, ResponseData
from pypost.models.models import RequestData
from tests.helpers.port_allocation import allocate_tcp_port
from tests.helpers.qt_wait import wait_until
from tests.helpers.raw_tcp_client import RawTcpWireClient, parse_jsonrpc_from_response


def is_ipv6_loopback_supported() -> bool:
    """Return True if the runtime environment allows binding to IPv6 loopback (::1)."""
    try:
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
            s.bind(("::1", 0))
            return True
    except OSError:
        return False


pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.skipif(
        not is_ipv6_loopback_supported(),
        reason="IPv6 loopback (::1) not supported in this environment",
    ),
]


def _create_mock_request_service() -> MagicMock:
    """Create a mock request service returning echo response data for tool calls."""
    mock_svc = MagicMock()
    mock_svc.execute.side_effect = lambda req, vars, **kw: ExecutionResult(
        response=ResponseData(
            status_code=200,
            headers={"content-type": "application/json"},
            body=json.dumps({"result": vars.get("mcp", {}).get("request", {})}),
            elapsed_time=0.001,
            size=len(
                json.dumps({"result": vars.get("mcp", {}).get("request", {})}).encode("utf-8")
            ),
        ),
        updated_variables={},
        script_logs=[],
        execution_error=None,
    )
    return mock_svc


def _allocate_ipv6_port() -> int:
    """Allocate an available TCP port on IPv6 loopback (::1).

    Attempts shared allocate_tcp_port, falling back to an ephemeral AF_INET6 socket
    if the allocator does not yet support IPv6.
    """
    try:
        return allocate_tcp_port("::1")
    except (OSError, socket.gaierror):
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind(("::1", 0))
            return int(probe.getsockname()[1])


def test_raw_tcp_wire_client_ipv6_connect_repro() -> None:
    """RawTcpWireClient must establish socket connection to IPv6 loopback (::1).

    In unpatched code, RawTcpWireClient hardcodes AF_INET in connect(),
    raising socket.gaierror ([Errno -9] Address family for hostname not supported)
    when connecting to ::1.
    """
    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("::1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]

        client = RawTcpWireClient(host="::1", port=port, timeout=5.0)
        try:
            client.connect()
            assert client.sock is not None
            assert client.sock.family == socket.AF_INET6
        finally:
            client.close()


def test_raw_tcp_wire_client_bracketed_ipv6_connect_repro() -> None:
    """RawTcpWireClient must establish socket connection when host is bracketed '[::1]'.

    In unpatched code, RawTcpWireClient does not strip brackets before calling
    connect(), raising socket.gaierror ([Errno -2] Name or service not known).
    """
    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("::1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]

        client = RawTcpWireClient(host="[::1]", port=port, timeout=5.0)
        try:
            client.connect()
            assert client.sock is not None
            assert client.sock.family == socket.AF_INET6
        finally:
            client.close()


def test_raw_tcp_wire_client_ipv6_host_header_rfc3986_repro() -> None:
    """RawTcpWireClient must format RFC 3986 compliant bracketed Host header for IPv6.

    In unpatched code, Host header is generated as 'Host: ::1:8000' (unbracketed),
    which violates RFC 3986 Section 3.2.2 and RFC 7230 Section 5.4.
    """
    client = RawTcpWireClient(host="::1", port=8000)
    if hasattr(client, "format_http_request"):
        raw_req = client.format_http_request("GET", "/")  # type: ignore[attr-defined]
    else:
        raw_req = client.build_post_request({"jsonrpc": "2.0"}, path="/")
    assert b"Host: [::1]:8000\r\n" in raw_req


def test_mcp_standalone_server_ipv6_lifecycle_handshake(qapp: Any) -> None:
    """Standalone MCP server starts on ::1 and completes protocol handshake over IPv6 wire."""
    port = _allocate_ipv6_port()
    tool = RequestData(
        id="ipv6_wire_handshake",
        name="ipv6_wire_handshake",
        method="POST",
        url="http://[::1]/handshake",
        expose_as_mcp=True,
    )
    mock_service = _create_mock_request_service()
    manager = MCPServerManager()
    manager._impl._create_request_service = lambda: mock_service
    manager.start_server(port, [tool], host="::1")

    try:
        wait_until(lambda: manager.is_listening, message="MCP server did not start listening")

        with RawTcpWireClient("::1", port, timeout=10.0) as client:
            # 1. Initialize request
            init_req = client.build_post_request(
                {
                    "jsonrpc": "2.0",
                    "id": "init-ipv6-1",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "wire-tester-ipv6", "version": "1.0"},
                    },
                }
            )
            client.send_fragmented(init_req, chunk_size=7)
            status, headers, body = client.read_http_response()
            assert status == 200
            assert client.session_id is not None
            msgs = parse_jsonrpc_from_response(body)
            assert any(m.get("id") == "init-ipv6-1" for m in msgs)
            init_res = next(m for m in msgs if m.get("id") == "init-ipv6-1")
            assert "capabilities" in init_res.get("result", {})

            # 2. Initialized notification
            notif_req = client.build_post_request(
                {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                }
            )
            client.send_fragmented(notif_req, chunk_size=7)
            status, headers, body = client.read_http_response()
            assert status == 202
    finally:
        manager.stop_server()


def test_mcp_standalone_server_ipv6_tool_discovery_and_call(qapp: Any) -> None:
    """Standalone MCP server executes tool discovery and tool execution over IPv6 wire."""
    port = _allocate_ipv6_port()
    tool = RequestData(
        id="ipv6_calc",
        name="ipv6_calc",
        method="POST",
        url="http://[::1]/calc",
        expose_as_mcp=True,
    )
    mock_service = _create_mock_request_service()
    manager = MCPServerManager()
    manager._impl._create_request_service = lambda: mock_service
    manager.start_server(port, [tool], host="::1")

    try:
        wait_until(lambda: manager.is_listening, message="MCP server did not start listening")

        with RawTcpWireClient("::1", port, timeout=10.0) as client:
            # 1. Initialize session
            init_req = client.build_post_request(
                {
                    "jsonrpc": "2.0",
                    "id": "init-call",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "wire-tester-ipv6", "version": "1.0"},
                    },
                }
            )
            client.send_all(init_req)
            status, headers, body = client.read_http_response()
            assert status == 200

            # 2. Initialized notification
            notif_req = client.build_post_request(
                {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                }
            )
            client.send_all(notif_req)
            status, headers, body = client.read_http_response()
            assert status == 202

            # 3. tools/list discovery
            list_req = client.build_post_request(
                {
                    "jsonrpc": "2.0",
                    "id": "list-ipv6",
                    "method": "tools/list",
                    "params": {},
                }
            )
            client.send_all(list_req)
            status, headers, body = client.read_http_response()
            assert status == 200
            msgs = parse_jsonrpc_from_response(body)
            assert any(m.get("id") == "list-ipv6" for m in msgs)
            list_res = next(m for m in msgs if m.get("id") == "list-ipv6")
            tools = list_res.get("result", {}).get("tools", [])
            assert any(t.get("name") == "ipv6_calc" for t in tools)

            # 4. tools/call execution
            call_req = client.build_post_request(
                {
                    "jsonrpc": "2.0",
                    "id": "call-ipv6",
                    "method": "tools/call",
                    "params": {
                        "name": "ipv6_calc",
                        "arguments": {"operand_a": 10, "operand_b": 32},
                    },
                }
            )
            client.send_all(call_req)
            status, headers, body = client.read_http_response()
            assert status == 200
            msgs = parse_jsonrpc_from_response(body)
            assert any(m.get("id") == "call-ipv6" for m in msgs)
            call_res = next(m for m in msgs if m.get("id") == "call-ipv6")
            content = call_res.get("result", {}).get("content", [])
            assert len(content) > 0
            tool_payload = json.loads(content[0]["text"])
            assert tool_payload["status"] == 200
            assert json.loads(tool_payload["body"]) == {
                "result": {"operand_a": 10, "operand_b": 32}
            }
    finally:
        manager.stop_server()


def test_mcp_standalone_server_ipv6_teardown_and_rebind(qapp: Any) -> None:
    """Standalone MCP server handles client communication, tears down, and frees IPv6 port."""
    port = _allocate_ipv6_port()
    tool = RequestData(
        id="rebind_tool",
        name="rebind_tool",
        method="GET",
        url="http://[::1]/rebind",
        expose_as_mcp=True,
    )
    mock_service = _create_mock_request_service()
    manager = MCPServerManager()
    manager._impl._create_request_service = lambda: mock_service
    manager.start_server(port, [tool], host="::1")

    try:
        wait_until(lambda: manager.is_listening, message="MCP server did not start listening")
        with RawTcpWireClient("::1", port, timeout=5.0) as client:
            req = client.build_post_request(
                {
                    "jsonrpc": "2.0",
                    "id": "init-rebind",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "wire-tester-ipv6", "version": "1.0"},
                    },
                }
            )
            client.send_all(req)
            status, _, _ = client.read_http_response()
            assert status == 200
    finally:
        manager.stop_server()

    wait_until(lambda: not manager.is_running(), message="MCP server did not stop")
    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("::1", port))
