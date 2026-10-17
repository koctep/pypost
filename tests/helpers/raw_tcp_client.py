"""Raw TCP wire client and response parsing test helpers.

Provides low-level TCP socket injection and response decoding utilities
for testing HTTP/1.1 and MCP streamable transports.

Jira: PYPOST-1428
Architecture: ai-tasks/PYPOST-1428/20-architecture.md
"""

from __future__ import annotations

import json
import socket
import time
from typing import Any

from pypost.core.server_bind import detect_address_family


__all__ = [
    "RawTcpWireClient",
    "ZeroCopyStreamBuffer",
    "parse_jsonrpc_from_response",
]


class ZeroCopyStreamBuffer:
    """Zero-copy stream buffer with sliding read window and amortized compaction.

    Avoids O(N^2) memory copying during iterative stream framing and chunked payload parsing.
    """

    def __init__(
        self,
        initial: bytes | bytearray | None = None,
        compact_threshold: int = 64 * 1024,
    ) -> None:
        """Initialize buffer with optional initial content and compaction threshold.

        Args:
            initial: Optional initial byte sequence.
            compact_threshold: Number of consumed bytes before buffer compaction is triggered.
        """
        self._raw: bytearray = bytearray(initial) if initial else bytearray()
        self._read_offset: int = 0
        self.compact_threshold: int = compact_threshold

    @property
    def unread_len(self) -> int:
        """Return number of unconsumed bytes remaining in the active window."""
        return max(0, len(self._raw) - self._read_offset)

    @property
    def read_offset(self) -> int:
        """Return the current read window head offset."""
        return self._read_offset

    def unread_bytes(self) -> bytes:
        """Return all remaining unconsumed bytes as an immutable bytes object."""
        return bytes(self._raw[self._read_offset:])

    def unread_bytearray(self) -> bytearray:
        """Return all remaining unconsumed bytes as a bytearray for backward compatibility."""
        return bytearray(self._raw[self._read_offset:])

    def extend(self, data: bytes | bytearray | memoryview) -> None:
        """Append newly received socket bytes to the underlying buffer.

        Args:
            data: Incoming byte sequence from socket read.
        """
        self._raw.extend(data)

    def find(self, sub: bytes, start: int = 0) -> int:
        """Search for byte sequence starting from the current read offset.

        Args:
            sub: Target delimiter sequence to locate.
            start: Offset relative to the active window head (default 0).

        Returns:
            Index of the first match relative to active window head, or -1 if not found.
        """
        abs_start = self._read_offset + max(0, start)
        idx = self._raw.find(sub, abs_start)
        if idx == -1:
            return -1
        return idx - self._read_offset

    def read_bytes(self, length: int) -> bytes:
        """Extract a slice of bytes from the window and advance the read offset.

        Args:
            length: Number of bytes to consume and return.

        Returns:
            Extracted bytes object.
        """
        if length < 0:
            raise ValueError(f"length must be non-negative, got {length}")
        start = self._read_offset
        end = start + length
        result = bytes(self._raw[start:end])
        self.consume(length)
        return result

    def read_view(self, length: int) -> memoryview:
        """Return a non-copying memoryview slice and advance the read offset.

        Args:
            length: Number of bytes to slice.

        Returns:
            memoryview slice over the active window.
        """
        if length < 0:
            raise ValueError(f"length must be non-negative, got {length}")
        start = self._read_offset
        self._read_offset += length
        return memoryview(self._raw)[start:start + length]

    def consume(self, length: int) -> None:
        """Advance read offset without returning data (e.g. skipping CRLF delimiters).

        Args:
            length: Number of bytes to skip.
        """
        if length < 0:
            raise ValueError(f"length must be non-negative, got {length}")
        self._read_offset += length
        if self._read_offset >= len(self._raw):
            try:
                self._raw.clear()
                self._read_offset = 0
            except BufferError:
                pass

    def compact(self, force: bool = False) -> None:
        """Discard consumed bytes preceding read offset when threshold is exceeded.

        Args:
            force: If True, compacts immediately regardless of threshold.
        """
        if self._read_offset >= len(self._raw):
            try:
                self._raw.clear()
                self._read_offset = 0
            except BufferError:
                pass
        elif force or self._read_offset >= self.compact_threshold:
            try:
                del self._raw[:self._read_offset]
                self._read_offset = 0
            except BufferError:
                pass

    def clear(self) -> None:
        """Reset buffer and read offset to empty state."""
        self._raw.clear()
        self._read_offset = 0


class RawTcpWireClient:
    """Raw TCP socket client for injecting fragmented frames, pipelining, and bursts.

    Designed for wire-level testing of HTTP/1.1 and MCP streamable transports.
    """

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 10.0,
        family: socket.AddressFamily | None = None,
    ) -> None:
        """Initialize wire client with target host, port, timeout, and address family.

        Args:
            host: Target hostname or IP address (e.g. '127.0.0.1', '::1', '[::1]').
            port: Target TCP port number.
            timeout: Socket timeout in seconds for connect and read operations.
            family: Optional socket address family override (AF_INET or AF_INET6).
                    If None, automatically detected from host.
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.family: socket.AddressFamily = (
            family if family is not None else detect_address_family(host)
        )
        self.clean_host = host.strip("[]")
        self.sock: socket.socket | None = None
        self.session_id: str | None = None
        self._stream_buffer = ZeroCopyStreamBuffer()

    @property
    def _unread_buffer(self) -> bytearray:
        """Backward-compatible access to unconsumed stream buffer."""
        return self._stream_buffer.unread_bytearray()

    @_unread_buffer.setter
    def _unread_buffer(self, data: bytes | bytearray) -> None:
        """Backward-compatible setter for unconsumed stream buffer."""
        self._stream_buffer = ZeroCopyStreamBuffer(data)

    @property
    def formatted_host(self) -> str:
        """Return bracketed host for IPv6 or clean host for IPv4."""
        if self.family == socket.AF_INET6:
            return f"[{self.clean_host}]"
        return self.clean_host

    @property
    def formatted_host_header(self) -> str:
        """Return RFC 3986 / RFC 7230 compliant Host header value."""
        return f"{self.formatted_host}:{self.port}"

    def connect(self) -> None:
        """Establish physical TCP connection to (clean_host, port).

        Creates socket.socket(self.family, socket.SOCK_STREAM) with timeout.
        """
        self.sock = socket.socket(self.family, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.clean_host, self.port))

    def close(self) -> None:
        """Gracefully shut down and close the underlying socket descriptor."""
        if self.sock is not None:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.sock.close()
            self.sock = None

    def __enter__(self) -> RawTcpWireClient:
        """Connect socket upon entering context block."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Close socket upon exiting context block."""
        self.close()

    def format_http_request(
        self,
        method: str = "GET",
        path: str = "/",
        headers: dict[str, str] | None = None,
        body: bytes | str | None = None,
    ) -> bytes:
        """Construct raw HTTP/1.1 request bytes.

        Args:
            method: HTTP method (e.g. 'GET', 'POST').
            path: Target endpoint URI path (default '/').
            headers: Optional additional headers dictionary.
            body: Optional request body bytes or string.

        Returns:
            Formatted raw HTTP/1.1 request bytes.
        """
        body_bytes = body.encode("utf-8") if isinstance(body, str) else (body or b"")
        req_headers = [
            f"{method} {path} HTTP/1.1",
            f"Host: {self.formatted_host_header}",
            "Connection: keep-alive",
        ]
        if body_bytes:
            req_headers.append(f"Content-Length: {len(body_bytes)}")
        if headers:
            for k, v in headers.items():
                req_headers.append(f"{k}: {v}")
        req_str = "\r\n".join(req_headers) + "\r\n\r\n"
        return req_str.encode("utf-8") + body_bytes

    def build_post_request(
        self,
        payload: dict[str, Any],
        path: str = "/mcp",
        session_id: str | None = None,
    ) -> bytes:
        """Construct raw HTTP/1.1 POST request bytes with JSON-RPC payload.

        Args:
            payload: JSON-serializable dictionary representing the JSON-RPC request.
            path: Target HTTP endpoint URI path (default '/mcp').
            session_id: Optional MCP session ID override; defaults to self.session_id.

        Returns:
            Formatted raw HTTP/1.1 request bytes including headers and body.
        """
        body = json.dumps(payload).encode("utf-8")
        headers = [
            f"POST {path} HTTP/1.1",
            f"Host: {self.formatted_host_header}",
            "Content-Type: application/json",
            "Accept: application/json, text/event-stream",
            f"Content-Length: {len(body)}",
            "Connection: keep-alive",
        ]
        sid = session_id or self.session_id
        if sid:
            headers.append(f"mcp-session-id: {sid}")
        req_header = "\r\n".join(headers) + "\r\n\r\n"
        return req_header.encode("utf-8") + body

    def send_fragmented(
        self,
        data: bytes,
        chunk_size: int = 7,
        delay: float = 0.0,
    ) -> None:
        """Transmit byte sequence in small fragmented chunks to simulate packet fragmentation.

        Args:
            data: Raw bytes to transmit over the socket.
            chunk_size: Maximum slice size per socket sendall call (default 7 bytes).
            delay: Optional sleep interval in seconds between slice transmissions.
        """
        assert self.sock is not None
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            self.sock.sendall(chunk)
            if delay > 0:
                time.sleep(delay)

    def send_all(self, data: bytes) -> None:
        """Transmit entire byte sequence in a single call for burst or pipelined requests.

        Args:
            data: Raw bytes to transmit.
        """
        assert self.sock is not None
        self.sock.sendall(data)

    def read_http_response(self) -> tuple[int, dict[str, str], bytes]:
        """Read a single complete HTTP/1.1 response from the persistent socket stream.

        Handles:
        - Header delimiter search (\\r\\n\\r\\n) across incoming socket reads.
        - Status line parsing and lowercase header map extraction.
        - Capturing 'mcp-session-id' header into self.session_id.
        - Decoding 'Transfer-Encoding: chunked' bodies using zero-copy slicing.
        - Decoding 'Content-Length' bounded bodies.
        - Preserving remaining unread stream bytes in self._stream_buffer.

        Returns:
            Tuple of (status_code: int, headers: dict[str, str], body_bytes: bytes).

        Raises:
            ConnectionResetError: If connection is closed by peer during read.
            socket.timeout: If socket timeout expires before full response arrives.
        """
        assert self.sock is not None

        while True:
            header_end = self._stream_buffer.find(b"\r\n\r\n")
            if header_end != -1:
                break
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionResetError(
                    "Connection closed while waiting for HTTP header delimiter"
                )
            self._stream_buffer.extend(chunk)

        header_bytes = self._stream_buffer.read_bytes(header_end)
        self._stream_buffer.consume(4)
        header_lines = header_bytes.decode("utf-8", errors="replace").split("\r\n")
        status_line = header_lines[0]
        tokens = status_line.split(" ", 2)
        status_code = int(tokens[1]) if len(tokens) > 1 else 0

        headers: dict[str, str] = {}
        for line in header_lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()

        if "mcp-session-id" in headers:
            self.session_id = headers["mcp-session-id"]

        transfer_encoding = headers.get("transfer-encoding", "").lower()
        content_length_str = headers.get("content-length")

        if "chunked" in transfer_encoding:
            decoded_chunks = bytearray()
            while True:
                crlf = self._stream_buffer.find(b"\r\n")
                while crlf == -1:
                    more = self.sock.recv(4096)
                    if not more:
                        raise ConnectionResetError(
                            "Connection closed while reading chunk length"
                        )
                    self._stream_buffer.extend(more)
                    crlf = self._stream_buffer.find(b"\r\n")

                size_str = (
                    self._stream_buffer.read_bytes(crlf)
                    .decode("ascii", errors="replace")
                    .split(";")[0]
                    .strip()
                )
                self._stream_buffer.consume(2)
                chunk_len = int(size_str, 16)
                if chunk_len == 0:
                    while self._stream_buffer.find(b"\r\n") == -1:
                        more = self.sock.recv(4096)
                        if not more:
                            break
                        self._stream_buffer.extend(more)
                    end_crlf = self._stream_buffer.find(b"\r\n")
                    if end_crlf != -1:
                        self._stream_buffer.consume(end_crlf + 2)
                    else:
                        self._stream_buffer.clear()
                    self._stream_buffer.compact()
                    break

                needed = chunk_len + 2
                while self._stream_buffer.unread_len < needed:
                    more = self.sock.recv(max(4096, needed - self._stream_buffer.unread_len))
                    if not more:
                        raise ConnectionResetError(
                            "Connection closed while reading chunk data"
                        )
                    self._stream_buffer.extend(more)

                with self._stream_buffer.read_view(chunk_len) as chunk_view:
                    decoded_chunks.extend(chunk_view)
                self._stream_buffer.consume(2)

            self._stream_buffer.compact()
            return status_code, headers, bytes(decoded_chunks)

        elif content_length_str is not None:
            content_length = int(content_length_str)
            while self._stream_buffer.unread_len < content_length:
                more = self.sock.recv(max(4096, content_length - self._stream_buffer.unread_len))
                if not more:
                    break
                self._stream_buffer.extend(more)
            body = self._stream_buffer.read_bytes(content_length)
            self._stream_buffer.compact()
            return status_code, headers, body

        else:
            body = self._stream_buffer.unread_bytes()
            self._stream_buffer.clear()
            return status_code, headers, body


def parse_jsonrpc_from_response(body_bytes: bytes) -> list[dict[str, Any]]:
    """Parse JSON-RPC messages from application/json body or text/event-stream SSE events.

    Args:
        body_bytes: Raw response body bytes received from the wire.

    Returns:
        List of parsed JSON-RPC message dictionaries. If no valid JSON-RPC
        payloads are present, returns an empty list.
    """
    if not body_bytes:
        return []
    text = body_bytes.decode("utf-8", errors="replace").strip()
    if text.startswith("{") and text.endswith("}"):
        try:
            return [json.loads(text)]
        except json.JSONDecodeError:
            pass

    messages = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            payload = line[5:].strip()
            if payload.startswith("{") and payload.endswith("}"):
                try:
                    messages.append(json.loads(payload))
                except json.JSONDecodeError:
                    pass
    return messages
