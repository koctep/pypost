"""Qt-free WebSocket transport abstractions and data structures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol, runtime_checkable


class FrameType(str, Enum):
    """Payload format type of a WebSocket frame."""

    TEXT = "text"
    BINARY = "binary"


class FrameDirection(str, Enum):
    """Direction of a WebSocket frame."""

    IN = "in"
    OUT = "out"


@dataclass(frozen=True)
class RawFrame:
    """Immutable representation of an unmasked raw WebSocket frame."""

    direction: FrameDirection
    payload_format: FrameType
    payload: str | bytes
    byte_size: int
    timestamp: datetime


@dataclass(frozen=True)
class HandshakeTarget:
    """Resolved parameters required to initiate a WebSocket handshake."""

    url: str
    headers: dict[str, str]
    subprotocols: tuple[str, ...] = ()
    max_incoming_message_bytes: int = 16 * 1024 * 1024
    verify_tls: bool = True


@runtime_checkable
class WebSocketTransportListener(Protocol):
    """Callback interface for asynchronous WebSocket transport events."""

    def on_opened(self, subprotocol: str) -> None:
        """Invoked when WebSocket handshake completes successfully."""
        ...

    def on_text(self, message: str) -> None:
        """Invoked when a text message frame is received."""
        ...

    def on_binary(self, payload: bytes) -> None:
        """Invoked when a binary frame is received."""
        ...

    def on_pong(self, elapsed_ms: int, payload: bytes) -> None:
        """Invoked when a pong response frame is received."""
        ...

    def on_closed(self, code: int, reason: str, peer_initiated: bool) -> None:
        """Invoked when the connection closes cleanly."""
        ...

    def on_failed(self, category: str, message: str, detail: str) -> None:
        """Invoked when an unrecoverable connection or protocol error occurs."""
        ...

    def on_tls_errors(self, errors: tuple[str, ...]) -> bool:
        """Invoked on TLS certificate validation failure. Returns True to ignore."""
        ...


@runtime_checkable
class WebSocketTransport(Protocol):
    """Low-level asynchronous WebSocket transport protocol."""

    def open(self, target: HandshakeTarget) -> None:
        """Initiate asynchronous handshake connection to target."""
        ...

    def send_text(self, message: str) -> None:
        """Send a UTF-8 text frame."""
        ...

    def send_binary(self, payload: bytes) -> None:
        """Send a binary frame."""
        ...

    def ping(self, payload: bytes = b"") -> None:
        """Send a WebSocket ping control frame."""
        ...

    def close(self, code: int = 1000, reason: str = "") -> None:
        """Initiate a clean WebSocket close handshake."""
        ...

    def abort(self) -> None:
        """Immediately abort and terminate the socket connection."""
        ...

    def negotiated_subprotocol(self) -> str:
        """Return the subprotocol negotiated during handshake, or empty string."""
        ...

    def set_listener(self, listener: WebSocketTransportListener) -> None:
        """Register the transport listener to receive events."""
        ...
