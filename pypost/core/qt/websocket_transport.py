"""Qt-native WebSocket transport adapter wrapping PySide6.QtWebSockets.QWebSocket."""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import QByteArray, QObject, QUrl
from PySide6.QtNetwork import QNetworkRequest, QSslConfiguration, QSslSocket
from PySide6.QtWebSockets import (
    QWebSocket,
    QWebSocketHandshakeOptions,
    QWebSocketProtocol,
)

from pypost.core.websocket_security_policy import TlsCertificateError
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
        self._socket: QWebSocket = QWebSocket(
            "",
            QWebSocketProtocol.Version.VersionLatest,
            parent,
        )
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
            code_val = (
                int(raw_code.value)
                if hasattr(raw_code, "value") and isinstance(raw_code.value, int)
                else 1000
            )
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
                "websocket_transport_socket_error category=%s message=%s",
                category,
                error_str,
            )
            self._listener.on_failed(category, error_str, str(error))

    def _on_ssl_errors(self, errors: list[object]) -> None:
        if self._listener is not None:
            parsed_errors: list[TlsCertificateError] = []
            for e in errors:
                if isinstance(e, TlsCertificateError):
                    parsed_errors.append(e)
                    continue

                msg = str(getattr(e, "errorString", lambda: str(e))())
                code = "ssl_error"
                if hasattr(e, "error"):
                    err_enum = e.error()
                    code = getattr(err_enum, "name", str(err_enum)).lower()
                elif "self-signed" in msg.lower():
                    code = "self_signed"
                elif "host" in msg.lower() and "match" in msg.lower():
                    code = "host_mismatch"
                elif "expired" in msg.lower():
                    code = "expired"

                subject = ""
                issuer = ""
                fingerprint = ""
                expiry_date = None

                cert = getattr(e, "certificate", lambda: None)()
                if cert is not None and getattr(cert, "isNull", lambda: True)() is False:
                    if hasattr(cert, "subjectDisplayName"):
                        subject = cert.subjectDisplayName()
                    if hasattr(cert, "issuerDisplayName"):
                        issuer = cert.issuerDisplayName()
                    if hasattr(cert, "digest"):
                        try:
                            digest_hex = cert.digest().toHex().data().decode("utf-8")
                            if digest_hex:
                                fingerprint = f"SHA256:{digest_hex}"
                        except Exception:
                            pass
                    if hasattr(cert, "expiryDate"):
                        try:
                            qdt = cert.expiryDate()
                            if hasattr(qdt, "toPython"):
                                expiry_date = qdt.toPython()
                        except Exception:
                            pass

                parsed_errors.append(
                    TlsCertificateError(
                        error_code=code,
                        message=msg,
                        certificate_subject=subject,
                        certificate_issuer=issuer,
                        certificate_fingerprint=fingerprint,
                        expiry_date=expiry_date,
                    )
                )

            logger.warning(
                "websocket_transport_ssl_errors_encountered count=%d errors=%s",
                len(parsed_errors),
                [e.message for e in parsed_errors],
            )
            self._listener.on_tls_errors(tuple(parsed_errors))

    def set_listener(self, listener: WebSocketTransportListener) -> None:
        """Register the listener receiving transport lifecycle callbacks."""
        self._listener = listener

    def open(self, target: HandshakeTarget) -> None:
        """Configure socket and open connection to target."""
        from pypost.core.sensitive_text_sanitizer import sanitize_text
        logger.debug(
            "websocket_transport_open_initiated url=%s max_bytes=%d subprotocols=%s verify_tls=%s",
            sanitize_text(target.url),
            target.max_incoming_message_bytes,
            target.subprotocols,
            target.verify_tls,
        )
        self._local_close_requested = False
        self._socket.setMaxAllowedIncomingMessageSize(target.max_incoming_message_bytes)

        if target.url.lower().startswith("wss://"):
            ssl_config = QSslConfiguration.defaultConfiguration()
            if target.verify_tls:
                ssl_config.setPeerVerifyMode(QSslSocket.PeerVerifyMode.VerifyPeer)
            else:
                ssl_config.setPeerVerifyMode(QSslSocket.PeerVerifyMode.VerifyNone)
            self._socket.setSslConfiguration(ssl_config)

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
