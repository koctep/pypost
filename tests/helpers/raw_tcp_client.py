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


class RawTcpWireClient:
    """Raw TCP socket client for injecting fragmented frames, pipelining, and bursts.

    Designed for wire-level testing of HTTP/1.1 and MCP streamable transports.
    """

    def __init__(self, host: str, port: int, timeout: float = 10.0) -> None:
        """Initialize wire client with target host, port, and socket timeout.

        Args:
            host: Target hostname or IP address (typically '127.0.0.1').
            port: Target TCP port number.
            timeout: Socket timeout in seconds for connect and read operations.
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: socket.socket | None = None
        self.session_id: str | None = None
        self._unread_buffer = bytearray()

    def connect(self) -> None:
        """Establish physical TCP connection to (host, port).

        Creates socket.socket(socket.AF_INET, socket.SOCK_STREAM) with timeout.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))

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
            f"Host: {self.host}:{self.port}",
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
        - Decoding 'Transfer-Encoding: chunked' bodies.
        - Decoding 'Content-Length' bounded bodies.
        - Preserving remaining unread stream bytes in self._unread_buffer.

        Returns:
            Tuple of (status_code: int, headers: dict[str, str], body_bytes: bytes).

        Raises:
            ConnectionResetError: If connection is closed by peer during read.
            socket.timeout: If socket timeout expires before full response arrives.
        """
        assert self.sock is not None
        buf = self._unread_buffer

        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionResetError(
                    "Connection closed while waiting for HTTP header delimiter"
                )
            buf.extend(chunk)

        header_part, _, body_prefix = buf.partition(b"\r\n\r\n")
        header_lines = header_part.decode("utf-8", errors="replace").split("\r\n")
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

        body = bytearray(body_prefix)
        if "chunked" in transfer_encoding:
            decoded_chunks = bytearray()
            while True:
                crlf = body.find(b"\r\n")
                while crlf == -1:
                    more = self.sock.recv(4096)
                    if not more:
                        raise ConnectionResetError(
                            "Connection closed while reading chunk length"
                        )
                    body.extend(more)
                    crlf = body.find(b"\r\n")

                size_str = body[:crlf].decode("ascii", errors="replace").split(";")[0].strip()
                chunk_len = int(size_str, 16)
                if chunk_len == 0:
                    body = body[crlf + 2:]
                    while b"\r\n" not in body:
                        more = self.sock.recv(4096)
                        if not more:
                            break
                        body.extend(more)
                    end_crlf = body.find(b"\r\n")
                    if end_crlf != -1:
                        self._unread_buffer = body[end_crlf + 2:]
                    else:
                        self._unread_buffer = bytearray()
                    break

                needed = crlf + 2 + chunk_len + 2
                while len(body) < needed:
                    more = self.sock.recv(max(4096, needed - len(body)))
                    if not more:
                        raise ConnectionResetError(
                            "Connection closed while reading chunk data"
                        )
                    body.extend(more)

                chunk_content = body[crlf + 2:crlf + 2 + chunk_len]
                decoded_chunks.extend(chunk_content)
                body = body[crlf + 2 + chunk_len + 2:]

            return status_code, headers, bytes(decoded_chunks)

        elif content_length_str is not None:
            content_length = int(content_length_str)
            while len(body) < content_length:
                more = self.sock.recv(max(4096, content_length - len(body)))
                if not more:
                    break
                body.extend(more)
            self._unread_buffer = body[content_length:]
            return status_code, headers, bytes(body[:content_length])

        else:
            self._unread_buffer = bytearray()
            return status_code, headers, bytes(body)


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
