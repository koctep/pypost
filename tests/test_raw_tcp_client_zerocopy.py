"""Automated tests for ZeroCopyStreamBuffer and RawTcpWireClient zero-copy optimization.

Jira: PYPOST-1432
Architecture: ai-tasks/PYPOST-1432/20-architecture.md
"""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from tests.helpers.raw_tcp_client import RawTcpWireClient, ZeroCopyStreamBuffer

pytestmark = pytest.mark.timeout(30)


def test_zero_copy_stream_buffer_initialization() -> None:
    """ZeroCopyStreamBuffer initializes with default or provided parameters."""
    buf = ZeroCopyStreamBuffer()
    assert buf.unread_len == 0
    assert buf.read_offset == 0
    assert buf.unread_bytes() == b""
    assert buf.unread_bytearray() == bytearray()

    buf_with_data = ZeroCopyStreamBuffer(b"initial payload", compact_threshold=1024)
    assert buf_with_data.unread_len == 15
    assert buf_with_data.read_offset == 0
    assert buf_with_data.unread_bytes() == b"initial payload"


def test_zero_copy_read_view_returns_memoryview() -> None:
    """read_view returns a zero-copy memoryview slice and advances read offset."""
    raw_payload = b"HEADER\r\n\r\nPAYLOAD_CHUNK_12345"
    buf = ZeroCopyStreamBuffer(raw_payload)

    view = buf.read_view(6)
    assert isinstance(view, memoryview)
    assert bytes(view) == b"HEADER"
    assert buf.read_offset == 6
    assert buf.unread_len == len(raw_payload) - 6
    view.release()


def test_zero_copy_offset_windowing_and_consume() -> None:
    """consume advances read_offset without mutating or reallocating underlying buffer."""
    buf = ZeroCopyStreamBuffer(b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello")
    underlying_id = id(buf._raw)
    initial_raw_len = len(buf._raw)

    delim_idx = buf.find(b"\r\n\r\n")
    assert delim_idx == 34

    # Consuming the header advances offset without modifying the underlying raw buffer
    buf.consume(delim_idx + 4)
    assert buf.read_offset == 38
    assert buf.unread_len == 5
    assert id(buf._raw) == underlying_id
    assert len(buf._raw) == initial_raw_len
    assert buf.read_bytes(5) == b"hello"
    assert buf.unread_len == 0


def test_zero_copy_amortized_compaction_threshold() -> None:
    """compact() only mutates underlying buffer when read_offset >= compaction_threshold."""
    threshold = 64
    buf = ZeroCopyStreamBuffer(compact_threshold=threshold)
    buf.extend(b"x" * 100)

    # Consume 40 bytes (below threshold)
    buf.consume(40)
    assert buf.read_offset == 40
    underlying_id = id(buf._raw)

    # Compact should be a no-op since offset < threshold
    buf.compact()
    assert buf.read_offset == 40
    assert id(buf._raw) == underlying_id
    assert len(buf._raw) == 100

    # Consume 30 more bytes (total 70 >= threshold)
    buf.consume(30)
    assert buf.read_offset == 70

    # Compaction triggers: shifts remaining 30 bytes to head and resets offset
    buf.compact()
    assert buf.read_offset == 0
    assert buf.unread_len == 30
    assert len(buf._raw) == 30
    assert buf.unread_bytes() == b"x" * 30


def test_zero_copy_buffer_error_safety_during_mutations() -> None:
    """Buffer mutations (extend, compact) do not encounter active export BufferError."""
    buf = ZeroCopyStreamBuffer(compact_threshold=32)
    buf.extend(b"0123456789abcdef0123456789abcdef")  # 32 bytes

    # Read slice via memoryview
    view = buf.read_view(16)
    assert bytes(view) == b"0123456789abcdef"
    # Releasing view ensures export count drops to 0
    view.release()

    # Extending after view release must not raise BufferError
    buf.extend(b"additional_bytes")
    assert buf.unread_len == 32  # 16 unread from initial + 16 additional

    # Compact after view release must not raise BufferError
    buf.consume(20)  # offset now 36 >= threshold 32
    buf.compact()
    assert buf.read_offset == 0
    assert buf.unread_len == 12


def test_raw_tcp_wire_client_unread_buffer_property_backward_compatibility() -> None:
    """_unread_buffer property on RawTcpWireClient maintains backward compatibility."""
    client = RawTcpWireClient("127.0.0.1", 8080)
    assert isinstance(client._unread_buffer, bytearray)
    assert client._unread_buffer == bytearray()

    # Setter compatibility: assigns new unread buffer
    client._unread_buffer = bytearray(b"EXTRA_TRAILING_BYTES")
    assert client._unread_buffer == bytearray(b"EXTRA_TRAILING_BYTES")
    assert isinstance(client._unread_buffer, bytearray)


def test_raw_tcp_wire_client_chunked_http_decoding_with_stream_buffer() -> None:
    """RawTcpWireClient decodes chunked response using ZeroCopyStreamBuffer."""
    client = RawTcpWireClient("127.0.0.1", 8080)
    mock_sock = MagicMock()
    raw_response = (
        b"HTTP/1.1 200 OK\r\n"
        b"Transfer-Encoding: chunked\r\n"
        b"\r\n"
        b"4\r\nWiki\r\n"
        b"5\r\npedia\r\n"
        b"E\r\n in\r\n\r\nchunks.\r\n"
        b"0\r\n\r\n"
        b"TRAILING_PIPELINED_DATA"
    )
    mock_sock.recv.side_effect = [raw_response]
    client.sock = mock_sock

    status, headers, body = client.read_http_response()
    assert status == 200
    assert headers["transfer-encoding"] == "chunked"
    assert body == b"Wikipedia in\r\n\r\nchunks."
    assert client._unread_buffer == bytearray(b"TRAILING_PIPELINED_DATA")


def test_raw_tcp_wire_client_pipelined_responses_residual_integrity() -> None:
    """Consecutive read_http_response calls preserve residual stream bytes."""
    client = RawTcpWireClient("127.0.0.1", 8080)
    mock_sock = MagicMock()
    response_1 = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Length: 5\r\n"
        b"\r\n"
        b"first"
    )
    response_2 = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Length: 6\r\n"
        b"\r\n"
        b"second"
    )
    # Both responses sent in single TCP burst
    mock_sock.recv.side_effect = [response_1 + response_2]
    client.sock = mock_sock

    status_1, _, body_1 = client.read_http_response()
    assert status_1 == 200
    assert body_1 == b"first"

    status_2, _, body_2 = client.read_http_response()
    assert status_2 == 200
    assert body_2 == b"second"
    assert client._unread_buffer == bytearray()
