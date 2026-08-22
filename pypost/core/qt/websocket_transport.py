"""Qt-native WebSocket transport adapter wrapping PySide6.QtWebSockets.QWebSocket."""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import QByteArray, QObject, QUrl
from PySide6.QtNetwork import QNetworkRequest
from PySide6.QtWebSockets import (
    QWebSocket,
    QWebSocketHandshakeOptions,
    QWebSocketProtocol,
)

from pypost.core.websocket_transport_protocol import (
    HandshakeTarget,
    WebSocketTransport,
    WebSocketTransportListener,
)

logger = logging.getLogger(__name__)


class QtWebSocketTransport(WebSocketTransport):
    """Concrete WebSocketTransport adapter using PySide6.QtWebSockets.QWebSocket."""

    def __init__(self, parent: Optional[QObject] = None) -> None:
        self._listener: Optional[WebSocketTransportListener] = None
        self._local_close_requested: bool = False
        self._socket: QWebSocket = QWebSocket("", QWebSocketProtocol.VersionLatest, parent)
        self._connect_signals()

    def _connect_signals(self) -> None:
        self._socket.connected.connect(self._on_connected)
        self._socket.disconnected.connect(self._on_disconnected)
        self._socket.textMessageReceived.connect(self._on_text_message)
        self._socket.binaryMessageReceived.connect(self._on_binary_message)
        self._socket.pong.connect(self._on_pong)
        self._socket.errorOccurred.connect(self._on_error_occurred)
        self._socket.sslErrors.connect(self._on_ssl_errors)

    def _on_connected(self) -> None:
        if self._listener is not None:
            sub = self._socket.subprotocol() or ""
            self._listener.on_opened(sub)

    def _on_disconnected(self) -> None:
        if self._listener is not None:
            raw_code = self._socket.closeCode()
            code_val = raw_code.value if hasattr(raw_code, "value") else int(raw_code)
            reason = self._socket.closeReason() or ""
            peer_initiated = not self._local_close_requested
            self._listener.on_closed(code_val, reason, peer_initiated)

    def _on_text_message(self, message: str) -> None:
        if self._listener is not None:
            self._listener.on_text(message)

    def _on_binary_message(self, payload: QByteArray) -> None:
        if self._listener is not None:
            self._listener.on_binary(bytes(payload.data()))

    def _on_pong(self, elapsed_time: int, payload: QByteArray) -> None:
        if self._listener is not None:
            self._listener.on_pong(elapsed_time, bytes(payload.data()))

    def _on_error_occurred(self, error: object) -> None:
        if self._listener is not None:
            error_str = self._socket.errorString() or "WebSocket error"
            category = getattr(error, "name", "socket_error")
            logger.warning(
                "QtWebSocket error occurred: category=%s, message=%s",
                category,
                error_str,
            )
            self._listener.on_failed(category, error_str, str(error))

    def _on_ssl_errors(self, errors: list[object]) -> None:
        if self._listener is not None:
            err_strings = tuple(
                str(getattr(e, "errorString", lambda: str(e))())
                for e in errors
            )
            ignore = self._listener.on_tls_errors(err_strings)
            logger.warning(
                "QtWebSocket SSL errors encountered: count=%d, ignored=%s",
                len(err_strings),
                ignore,
            )
            if ignore:
                self._socket.ignoreSslErrors()

    def set_listener(self, listener: WebSocketTransportListener) -> None:
        """Register the listener receiving transport lifecycle callbacks."""
        self._listener = listener

    def open(self, target: HandshakeTarget) -> None:
        """Configure socket and open connection to target."""
        logger.debug(
            "QtWebSocketTransport opening connection to %s (max_bytes=%d, subprotocols=%s)",
            target.url,
            target.max_incoming_message_bytes,
            target.subprotocols,
        )
        self._local_close_requested = False
        self._socket.setMaxAllowedIncomingMessageSize(target.max_incoming_message_bytes)

        request = QNetworkRequest(QUrl(target.url))
        for header_name, header_val in target.headers.items():
            request.setRawHeader(
                QByteArray(header_name.encode("utf-8")),
                QByteArray(header_val.encode("utf-8")),
            )

        if target.subprotocols:
            options = QWebSocketHandshakeOptions()
            options.setSubprotocols(list(target.subprotocols))
            self._socket.open(request, options)
        else:
            self._socket.open(request)

    def send_text(self, message: str) -> None:
        """Send a UTF-8 text message frame."""
        byte_size = len(message.encode("utf-8"))
        logger.debug("QtWebSocketTransport sending text frame (%d bytes)", byte_size)
        self._socket.sendTextMessage(message)

    def send_binary(self, payload: bytes) -> None:
        """Send a binary message frame."""
        logger.debug("QtWebSocketTransport sending binary frame (%d bytes)", len(payload))
        self._socket.sendBinaryMessage(QByteArray(payload))

    def ping(self, payload: bytes = b"") -> None:
        """Send a WebSocket ping control frame."""
        logger.debug("QtWebSocketTransport sending ping frame (%d bytes)", len(payload))
        self._socket.ping(QByteArray(payload))

    def close(self, code: int = 1000, reason: str = "") -> None:
        """Initiate clean close handshake."""
        logger.debug("QtWebSocketTransport closing (code=%d, reason=%s)", code, reason)
        self._local_close_requested = True
        try:
            close_code = QWebSocketProtocol.CloseCode(code)
        except Exception:
            close_code = QWebSocketProtocol.CloseCode.CloseCodeNormal
        self._socket.close(close_code, reason)

    def abort(self) -> None:
        """Immediately terminate the socket."""
        logger.debug("QtWebSocketTransport aborting socket")
        self._socket.abort()

    def negotiated_subprotocol(self) -> str:
        """Return the negotiated subprotocol or empty string."""
        return self._socket.subprotocol() or ""
