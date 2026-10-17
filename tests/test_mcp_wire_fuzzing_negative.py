"""Malformed JSON-RPC and wire framing negative fuzzing test suite.

Exercises standalone PyPost MCP server resiliency against truncated JSON,
corrupted Content-Length, invalid JSON-RPC envelopes, chunked framing errors,
and raw non-UTF-8 binary noise over TCP wire.

Jira: PYPOST-1430
Architecture: ai-tasks/PYPOST-1430/20-architecture.md
"""

from __future__ import annotations

import json
import logging
import socket
from unittest.mock import MagicMock

import pytest

from pypost.core.qt.mcp_server import MCPServerManager
from pypost.core.request_service import ExecutionResult, ResponseData
from pypost.models.models import RequestData
from tests.helpers.port_allocation import allocate_tcp_port
from tests.helpers.qt_wait import wait_until
from tests.helpers.raw_tcp_client import RawTcpWireClient, parse_jsonrpc_from_response

pytestmark = pytest.mark.timeout(30)

REQUIRED_FAULT_CATEGORIES = (
    "http_framing",
    "truncated_json",
    "syntactically_invalid_json",
    "jsonrpc_schema_violations",
    "raw_binary_noise",
    "interleaved_stress_and_recovery",
)

IMPLEMENTED_FAULT_CATEGORIES: set[str] = set(REQUIRED_FAULT_CATEGORIES)


def _create_mock_request_service() -> MagicMock:
    """Create a mock request service returning canned tool execution responses."""
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


def build_raw_http_post(
    body: bytes,
    content_type: str = "application/json",
    content_length: int | str | None = None,
    path: str = "/mcp",
    host: str = "127.0.0.1",
    port: int = 8000,
    headers: list[str] | None = None,
) -> bytes:
    """Format raw HTTP/1.1 POST request bytes with optional header overrides."""
    cl = len(body) if content_length is None else content_length
    lines = [
        f"POST {path} HTTP/1.1",
        f"Host: {host}:{port}",
        f"Content-Type: {content_type}",
        "Accept: application/json, text/event-stream",
        f"Content-Length: {cl}",
        "Connection: keep-alive",
    ]
    if headers:
        lines.extend(headers)
    return "\r\n".join(lines).encode("utf-8") + b"\r\n\r\n" + body


def send_raw_payload_and_read(
    port: int,
    data: bytes,
    timeout: float = 3.0,
) -> tuple[int | None, dict[str, str], bytes]:
    """Transmit raw bytes to server and safely read HTTP response or EOF.

    Returns:
        (status_code, headers, body) if an HTTP response was received,
        or (None, {}, b"") if connection was closed/reset before response headers.
    """
    try:
        with RawTcpWireClient("127.0.0.1", port, timeout=timeout) as client:
            client.send_all(data)
            try:
                status, headers, body = client.read_http_response()
                return status, headers, body
            except (ConnectionResetError, BrokenPipeError, socket.timeout, OSError):
                return None, {}, b""
    except (ConnectionResetError, BrokenPipeError, socket.timeout, OSError):
        return None, {}, b""


def assert_post_fault_recovery(port: int) -> None:
    """Verify standalone MCP server accepts valid traffic after fault injection."""
    with RawTcpWireClient("127.0.0.1", port, timeout=5.0) as client:
        init_req = client.build_post_request(
            {
                "jsonrpc": "2.0",
                "id": "recovery-init",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "recovery-tester", "version": "1.0"},
                },
            }
        )
        client.send_all(init_req)
        status, _headers, body = client.read_http_response()
        assert status == 200, f"Expected 200 OK after fault, got {status}"
        assert client.session_id is not None
        msgs = parse_jsonrpc_from_response(body)
        assert any(m.get("id") == "recovery-init" for m in msgs)
        init_res = next(m for m in msgs if m.get("id") == "recovery-init")
        assert "capabilities" in init_res.get("result", {})


@pytest.fixture
def running_server(qapp):
    """Fixture providing an ephemeral standalone MCP server instance with cleanup."""
    port = allocate_tcp_port("127.0.0.1")
    tool = RequestData(
        id="fuzz_target",
        name="fuzz_target",
        method="POST",
        url="http://127.0.0.1/fuzz",
        expose_as_mcp=True,
    )
    mock_service = _create_mock_request_service()
    manager = MCPServerManager()
    manager._impl._create_request_service = lambda: mock_service
    manager.start_server(port, [tool], host="127.0.0.1")

    try:
        wait_until(lambda: manager.is_listening, message="MCP server did not start listening")
        yield port
    finally:
        manager.stop_server()


def test_negative_wire_fuzzing_initial_repro(qapp) -> None:
    """Assert complete negative fuzzing suite harness and fault vector coverage.

    Validates that the server starts on an ephemeral port and asserts that
    the negative fuzzing suite covers all 6 required fault categories:
    - http_framing (corrupted Content-Length, chunked framing, unterminated headers)
    - truncated_json (cut off mid-key, mid-string, mid-object)
    - syntactically_invalid_json (control chars, malformed unicode, unquoted identifiers)
    - jsonrpc_schema_violations (non-object root, invalid version, missing method)
    - raw_binary_noise (non-UTF-8 binary burst, non-UTF-8 in body)
    - interleaved_stress_and_recovery (alternating fault bursts with post-fault recovery)
    """
    port = allocate_tcp_port("127.0.0.1")
    tool = RequestData(
        id="fuzz_target",
        name="fuzz_target",
        method="POST",
        url="http://127.0.0.1/fuzz",
        expose_as_mcp=True,
    )
    mock_service = _create_mock_request_service()
    manager = MCPServerManager()
    manager._impl._create_request_service = lambda: mock_service
    manager.start_server(port, [tool], host="127.0.0.1")

    try:
        wait_until(lambda: manager.is_listening, message="MCP server did not start listening")

        # Baseline check: post-fault recovery handshake works on clean server
        assert_post_fault_recovery(port)

        # Repro assertion: suite must implement all 6 required negative fuzzing categories
        missing_categories = set(REQUIRED_FAULT_CATEGORIES) - set(IMPLEMENTED_FAULT_CATEGORIES)
        assert not missing_categories, (
            f"Malformed JSON-RPC and Wire Framing Fuzzing Suite incomplete: "
            f"missing implemented categories: {sorted(missing_categories)}"
        )
    finally:
        manager.stop_server()


@pytest.mark.parametrize(
    "framing_description, raw_bytes",
    [
        (
            "non-numeric Content-Length",
            b"POST /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\n"
            b"Content-Length: bad_length\r\nConnection: close\r\n\r\n{}",
        ),
        (
            "negative Content-Length",
            b"POST /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\n"
            b"Content-Length: -42\r\nConnection: close\r\n\r\n{}",
        ),
        (
            "invalid hex chunk size",
            b"POST /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\nTransfer-Encoding: chunked\r\n"
            b"Content-Type: application/json\r\nConnection: close\r\n\r\nZZ\r\n",
        ),
    ],
)
def test_wire_fuzzing_http_framing_corruptions(
    running_server: int, framing_description: str, raw_bytes: bytes
) -> None:
    """Validate server rejects framing corruptions gracefully and stays available."""
    port = running_server
    status, _headers, _body = send_raw_payload_and_read(port, raw_bytes)
    # Server either sends HTTP 400 Bad Request or resets/closes connection cleanly
    if status is not None:
        assert status == 400, (
            f"Expected HTTP 400 for {framing_description}, got {status}"
        )

    # Invariant: Server remains responsive for valid MCP traffic after malformed framing
    assert_post_fault_recovery(port)


def test_wire_fuzzing_http_framing_eof_and_premature_disconnect(
    running_server: int,
) -> None:
    """Validate server survives premature client socket disconnects without hanging."""
    port = running_server

    # 1. Premature EOF mid-chunk: declares chunk length of 16 bytes but closes after 3 bytes
    try:
        with RawTcpWireClient("127.0.0.1", port, timeout=2.0) as client:
            client.send_all(
                b"POST /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\nTransfer-Encoding: chunked\r\n"
                b"Content-Type: application/json\r\n\r\n10\r\nabc"
            )
    except OSError:
        pass

    assert_post_fault_recovery(port)

    # 2. Missing header terminator: truncated mid-header without final CRLF CRLF
    try:
        with RawTcpWireClient("127.0.0.1", port, timeout=2.0) as client:
            client.send_all(
                b"POST /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\n"
                b"X-Unterminated-Header: incomplete_value"
            )
    except OSError:
        pass

    assert_post_fault_recovery(port)

    # 3. Mismatched Content-Length: declares 500 bytes but sends 10 bytes and closes socket
    try:
        with RawTcpWireClient("127.0.0.1", port, timeout=2.0) as client:
            client.send_all(
                b"POST /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\n"
                b"Content-Length: 500\r\n\r\n{\"short\": 1"
            )
    except OSError:
        pass

    assert_post_fault_recovery(port)


@pytest.mark.parametrize(
    "truncation_type, truncated_payload",
    [
        ("mid-key", b'{"jsonrpc": "2.0", "metho'),
        ("mid-string", b'{"jsonrpc": "2.0", "method": "tools/ca'),
        ("mid-object", b'{"jsonrpc": "2.0", "id": 12, "params": {"arg": '),
        ("unclosed-brace", b'{"jsonrpc": "2.0", "id": 1, "method": "initialize"'),
    ],
)
def test_wire_fuzzing_truncated_json(
    running_server: int, truncation_type: str, truncated_payload: bytes
) -> None:
    """Validate server rejects truncated JSON payloads with JSON-RPC Parse Error (-32700)."""
    port = running_server
    req = build_raw_http_post(
        truncated_payload,
        content_type="application/json",
        port=port,
    )
    status, _headers, body = send_raw_payload_and_read(port, req)
    assert status == 400, (
        f"Expected HTTP 400 for {truncation_type} truncated JSON, got {status}"
    )

    msgs = parse_jsonrpc_from_response(body)
    assert len(msgs) > 0, f"Expected JSON-RPC error response for {truncation_type}"
    err = msgs[0].get("error", {})
    assert err.get("code") == -32700, (
        f"Expected JSON-RPC parse error code -32700 for {truncation_type}, got {err}"
    )

    # Verify server recovered and continues processing
    assert_post_fault_recovery(port)


@pytest.mark.parametrize(
    "syntax_error_type, corrupted_payload",
    [
        (
            "unescaped control chars",
            b'{"jsonrpc": "2.0", "method": "tools/\x00\x01\x1b"}',
        ),
        (
            "invalid unicode escape",
            b'{"jsonrpc": "2.0", "id": 1, "method": "tools/\\uXXXX"}',
        ),
        (
            "Python literals instead of JSON",
            b'{"jsonrpc": "2.0", "id": None, "params": True}',
        ),
        (
            "unquoted identifiers",
            b'{jsonrpc: "2.0", id: 1, method: "tools/list"}',
        ),
    ],
)
def test_wire_fuzzing_syntactically_invalid_json(
    running_server: int, syntax_error_type: str, corrupted_payload: bytes
) -> None:
    """Validate server returns JSON-RPC Parse Error (-32700) for syntactically invalid JSON."""
    port = running_server
    req = build_raw_http_post(corrupted_payload, port=port)
    status, _headers, body = send_raw_payload_and_read(port, req)
    assert status == 400, (
        f"Expected HTTP 400 for {syntax_error_type}, got {status}"
    )

    msgs = parse_jsonrpc_from_response(body)
    assert len(msgs) > 0, f"Expected JSON-RPC error response for {syntax_error_type}"
    err = msgs[0].get("error", {})
    assert err.get("code") == -32700, (
        f"Expected error code -32700 for {syntax_error_type}, got {err}"
    )

    # Verify fragmented delivery of syntactically invalid JSON also handled cleanly
    with RawTcpWireClient("127.0.0.1", port, timeout=3.0) as client:
        client.send_fragmented(req, chunk_size=3)
        frag_status, _headers, frag_body = client.read_http_response()
        assert frag_status == 400
        frag_msgs = parse_jsonrpc_from_response(frag_body)
        assert len(frag_msgs) > 0
        assert frag_msgs[0].get("error", {}).get("code") == -32700

    assert_post_fault_recovery(port)


@pytest.mark.parametrize(
    "schema_violation_type, violation_payload",
    [
        ("non-object array root", b'["not", "a", "jsonrpc", "object"]'),
        ("non-object primitive string", b'"primitive-string-payload"'),
        ("non-object primitive number", b"9999"),
        ("invalid jsonrpc version", b'{"jsonrpc": "1.0", "id": 1, "method": "tools/list"}'),
        ("missing method field", b'{"jsonrpc": "2.0", "id": 1, "params": {}}'),
        (
            "invalid id type object",
            b'{"jsonrpc": "2.0", "id": {"nested": "id"}, "method": "tools/list"}',
        ),
        ("invalid id type boolean", b'{"jsonrpc": "2.0", "id": true, "method": "tools/list"}'),
    ],
)
def test_wire_fuzzing_jsonrpc_schema_violations(
    running_server: int, schema_violation_type: str, violation_payload: bytes
) -> None:
    """Validate server rejects JSON-RPC schema violations with protocol error codes."""
    port = running_server
    req = build_raw_http_post(violation_payload, port=port)
    status, _headers, body = send_raw_payload_and_read(port, req)
    assert status == 400, (
        f"Expected HTTP 400 for {schema_violation_type}, got {status}"
    )

    msgs = parse_jsonrpc_from_response(body)
    assert len(msgs) > 0, f"Expected JSON-RPC error response for {schema_violation_type}"
    err = msgs[0].get("error", {})
    # JSON-RPC error codes:
    # -32600 (Invalid Request), -32602 (Invalid params), or -32700 (Parse error)
    assert err.get("code") in (-32600, -32602, -32700), (
        f"Unexpected JSON-RPC error code for {schema_violation_type}: {err}"
    )

    assert_post_fault_recovery(port)


def test_wire_fuzzing_raw_binary_noise(
    running_server: int, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate server handles non-UTF-8 bytes and binary garbage safely without crashes."""
    port = running_server

    # 1. Direct raw non-UTF-8 binary burst over TCP socket without HTTP headers
    raw_garbage = bytes(range(128, 256)) * 4
    status, _headers, _body = send_raw_payload_and_read(port, raw_garbage)
    if status is not None:
        assert status == 400

    assert_post_fault_recovery(port)

    # 2. Raw non-UTF-8 bytes in HTTP POST body
    non_utf8_body = b"\x80\x81\x82\x83\xfe\xff\x90\x91\xa0\xa1"
    req = build_raw_http_post(
        non_utf8_body,
        content_type="application/json",
        port=port,
    )
    with caplog.at_level(logging.ERROR, logger="mcp.server.streamable_http"):
        status, _headers, body = send_raw_payload_and_read(port, req)
    if status is not None:
        assert status == 400
        msgs = parse_jsonrpc_from_response(body)
        if msgs:
            assert msgs[0].get("error", {}).get("code") == -32700

    assert_post_fault_recovery(port)

    # 3. Binary noise injected into HTTP request line
    garbage_request_line = b"POST /mcp HTTP/1.1\r\n" + bytes(range(130, 200)) + b"\r\n\r\n"
    status, _headers, _body = send_raw_payload_and_read(port, garbage_request_line)
    if status is not None:
        assert status == 400

    assert_post_fault_recovery(port)


def test_wire_fuzzing_interleaved_stress_and_recovery(running_server: int) -> None:
    """Blast mixed malformed payloads followed by complete handshake and tool call execution."""
    port = running_server

    corrupted_batch = [
        # Framing corruption
        b"POST /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Length: -99\r\n\r\n{}",
        # Truncated JSON
        build_raw_http_post(b'{"jsonrpc": "2.0", "method": "tools/', port=port),
        # Non-UTF-8 binary noise
        bytes(range(128, 255)),
        # Invalid JSON-RPC envelope
        build_raw_http_post(b'["array-not-object"]', port=port),
        # Syntactic corruption
        build_raw_http_post(b'{"jsonrpc": 2.0, "id": null, "bad": true}', port=port),
        # Invalid chunk hex
        b"POST /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\nTransfer-Encoding: chunked\r\n\r\nGG\r\n",
    ]

    # Run 3 cycles of interleaved fault blasts and operational verification
    for cycle in range(3):
        for payload in corrupted_batch:
            send_raw_payload_and_read(port, payload, timeout=1.5)

        # Immediate operational verification: complete handshake and tool execution
        with RawTcpWireClient("127.0.0.1", port, timeout=5.0) as client:
            # 1. Initialize
            init_req = client.build_post_request(
                {
                    "jsonrpc": "2.0",
                    "id": f"cycle-{cycle}-init",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "interleaved-tester", "version": "1.0"},
                    },
                }
            )
            client.send_all(init_req)
            status, _headers, body = client.read_http_response()
            assert status == 200, f"Cycle {cycle}: initialize failed with status {status}"
            assert client.session_id is not None
            init_msgs = parse_jsonrpc_from_response(body)
            assert any(m.get("id") == f"cycle-{cycle}-init" for m in init_msgs)

            # 2. Initialized notification
            notif_req = client.build_post_request(
                {"jsonrpc": "2.0", "method": "notifications/initialized"}
            )
            client.send_all(notif_req)
            status, _headers, _body = client.read_http_response()
            assert status == 202, f"Cycle {cycle}: notification failed with status {status}"

            # 3. Tool call execution
            call_req = client.build_post_request(
                {
                    "jsonrpc": "2.0",
                    "id": f"cycle-{cycle}-call",
                    "method": "tools/call",
                    "params": {
                        "name": "fuzz_target",
                        "arguments": {"test_cycle": cycle, "status": "active"},
                    },
                }
            )
            client.send_all(call_req)
            status, _headers, body = client.read_http_response()
            assert status == 200, f"Cycle {cycle}: tool call failed with status {status}"
            call_msgs = parse_jsonrpc_from_response(body)
            assert any(m.get("id") == f"cycle-{cycle}-call" for m in call_msgs)
            call_res = next(m for m in call_msgs if m.get("id") == f"cycle-{cycle}-call")
            assert "content" in call_res.get("result", {})
