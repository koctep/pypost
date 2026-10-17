"""Unit tests for shared RawTcpWireClient and parse_jsonrpc_from_response helper.

Jira: PYPOST-1428
Architecture: ai-tasks/PYPOST-1428/20-architecture.md
"""

from __future__ import annotations

import json
import socket
from unittest.mock import MagicMock, patch

import pytest

from tests.helpers.raw_tcp_client import RawTcpWireClient, parse_jsonrpc_from_response

pytestmark = pytest.mark.timeout(30)


def test_parse_jsonrpc_empty_and_invalid_payloads() -> None:
    """Empty or non-JSON response bodies return an empty list without raising exceptions."""
    assert parse_jsonrpc_from_response(b"") == []
    assert parse_jsonrpc_from_response(b"   ") == []
    assert parse_jsonrpc_from_response(b"not json payload") == []
    assert parse_jsonrpc_from_response(b"{broken json:") == []


def test_parse_jsonrpc_standard_json_body() -> None:
    """Standard application/json bodies are parsed into a single-element list."""
    body = b'{"jsonrpc": "2.0", "result": {"status": "ok"}, "id": 1}'
    messages = parse_jsonrpc_from_response(body)
    assert len(messages) == 1
    assert messages[0] == {"jsonrpc": "2.0", "result": {"status": "ok"}, "id": 1}


def test_parse_jsonrpc_sse_stream() -> None:
    """Server-Sent Event (SSE) streams extract JSON-RPC envelopes from data lines."""
    body = (
        b": keepalive\n\n"
        b"data: {\"jsonrpc\": \"2.0\", \"method\": \"notifications/message\", \"params\": {}}\n\n"
        b"data: not json\n\n"
        b"data: {\"jsonrpc\": \"2.0\", \"id\": 2, \"result\": {\"tools\": []}}\n\n"
    )
    messages = parse_jsonrpc_from_response(body)
    assert len(messages) == 2
    assert messages[0]["method"] == "notifications/message"
    assert messages[1]["id"] == 2


def test_raw_tcp_wire_client_init_and_defaults() -> None:
    """Client initializes with supplied host, port, timeout, and clean initial state."""
    client = RawTcpWireClient("127.0.0.1", 9000, timeout=5.0)
    assert client.host == "127.0.0.1"
    assert client.port == 9000
    assert client.timeout == 5.0
    assert client.session_id is None
    assert client.sock is None
    assert client._unread_buffer == bytearray()


def test_raw_tcp_wire_client_build_post_request_defaults() -> None:
    """build_post_request formats standard HTTP/1.1 POST headers and JSON body."""
    client = RawTcpWireClient("127.0.0.1", 9000)
    payload = {"jsonrpc": "2.0", "method": "initialize", "id": 1}
    req = client.build_post_request(payload)

    assert req.startswith(b"POST /mcp HTTP/1.1\r\n")
    assert b"Host: 127.0.0.1:9000\r\n" in req
    assert b"Content-Type: application/json\r\n" in req
    assert b"Accept: application/json, text/event-stream\r\n" in req
    assert b"Connection: keep-alive\r\n" in req
    expected_body = json.dumps(payload).encode("utf-8")
    assert f"Content-Length: {len(expected_body)}\r\n".encode("utf-8") in req
    assert b"mcp-session-id:" not in req
    assert req.endswith(b"\r\n\r\n" + expected_body)


def test_raw_tcp_wire_client_build_post_request_with_session_and_custom_path() -> None:
    """build_post_request respects custom endpoint path and session tracking headers."""
    client = RawTcpWireClient("127.0.0.1", 9000)
    client.session_id = "default-session-id"

    # Uses client.session_id and custom path
    req1 = client.build_post_request({"id": 1}, path="/custom-rpc")
    assert req1.startswith(b"POST /custom-rpc HTTP/1.1\r\n")
    assert b"mcp-session-id: default-session-id\r\n" in req1

    # Overrides session_id when parameter is explicitly provided
    req2 = client.build_post_request({"id": 2}, session_id="override-id")
    assert b"mcp-session-id: override-id\r\n" in req2


def test_raw_tcp_wire_client_context_manager_lifecycle() -> None:
    """Context manager connects on enter and closes cleanly on exit."""
    with patch("socket.socket") as mock_sock_cls:
        mock_sock = MagicMock()
        mock_sock_cls.return_value = mock_sock

        with RawTcpWireClient("127.0.0.1", 8080, timeout=3.5) as client:
            mock_sock_cls.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
            mock_sock.settimeout.assert_called_once_with(3.5)
            mock_sock.connect.assert_called_once_with(("127.0.0.1", 8080))
            assert client.sock is mock_sock

        mock_sock.shutdown.assert_called_once_with(socket.SHUT_RDWR)
        mock_sock.close.assert_called_once()
        assert client.sock is None


def test_raw_tcp_wire_client_close_handles_oserror() -> None:
    """close() suppresses OSError if socket is already disconnected by peer."""
    with patch("socket.socket") as mock_sock_cls:
        mock_sock = MagicMock()
        mock_sock.shutdown.side_effect = OSError("Socket not connected")
        mock_sock_cls.return_value = mock_sock

        client = RawTcpWireClient("127.0.0.1", 8080)
        client.connect()
        client.close()

        mock_sock.close.assert_called_once()
        assert client.sock is None


def test_raw_tcp_wire_client_send_methods() -> None:
    """send_all transmits full burst; send_fragmented slices transmission into chunks."""
    client = RawTcpWireClient("127.0.0.1", 8080)
    mock_sock = MagicMock()
    client.sock = mock_sock

    client.send_all(b"payload-burst")
    mock_sock.sendall.assert_called_once_with(b"payload-burst")

    mock_sock.reset_mock()
    client.send_fragmented(b"abcdefgh", chunk_size=3)
    assert mock_sock.sendall.call_count == 3
    sent_chunks = [call.args[0] for call in mock_sock.sendall.call_args_list]
    assert sent_chunks == [b"abc", b"def", b"gh"]


def test_raw_tcp_wire_client_read_http_response_content_length() -> None:
    """read_http_response parses Content-Length responses and preserves unread buffer."""
    client = RawTcpWireClient("127.0.0.1", 8080)
    mock_sock = MagicMock()
    raw_http = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: application/json\r\n"
        b"mcp-session-id: test-session-uuid\r\n"
        b"Content-Length: 13\r\n"
        b"\r\n"
        b"{\"status\": 1}"
        b"EXTRA_BUFFER"
    )
    mock_sock.recv.side_effect = [raw_http]
    client.sock = mock_sock

    status, headers, body = client.read_http_response()
    assert status == 200
    assert headers["content-type"] == "application/json"
    assert headers["mcp-session-id"] == "test-session-uuid"
    assert client.session_id == "test-session-uuid"
    assert body == b'{"status": 1}'
    assert client._unread_buffer == bytearray(b"EXTRA_BUFFER")


def test_raw_tcp_wire_client_read_http_response_chunked() -> None:
    """read_http_response properly decodes RFC 9112 Transfer-Encoding: chunked streams."""
    client = RawTcpWireClient("127.0.0.1", 8080)
    mock_sock = MagicMock()
    raw_chunked = (
        b"HTTP/1.1 200 OK\r\n"
        b"Transfer-Encoding: chunked\r\n"
        b"\r\n"
        b"5\r\nhello\r\n"
        b"6\r\n world\r\n"
        b"0\r\n\r\n"
    )
    mock_sock.recv.side_effect = [raw_chunked]
    client.sock = mock_sock

    status, headers, body = client.read_http_response()
    assert status == 200
    assert body == b"hello world"
