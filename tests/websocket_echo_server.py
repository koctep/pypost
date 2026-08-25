"""Scripted in-process WebSocket server for offline PyPost testing (PYPOST-1129 / WS-11).

Provides an ephemeral loopback QWebSocketServer with configurable scripted behaviors,
subprotocol negotiation, flood generation, close codes, and deterministic lifecycle.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional

from PySide6.QtCore import QByteArray, QObject
from PySide6.QtNetwork import QHostAddress, QSslConfiguration
from PySide6.QtWebSockets import (
    QWebSocket,
    QWebSocketCorsAuthenticator,
    QWebSocketProtocol,
    QWebSocketServer,
)

from pypost.agent.ui_wait import wait_until
from tests.tls_test_certs import TlsCertProfile, TlsTestCertificate, build_tls_test_certificate

logger = logging.getLogger(__name__)


class ServerBehavior(Enum):
    """Enumeration of supported scripted server behaviors."""

    ECHO = auto()
    REJECT_HANDSHAKE = auto()
    SUBPROTOCOL_NEGOTIATE = auto()
    SUBPROTOCOL_REFUSE = auto()
    CLOSE_WITH_CODE = auto()
    SILENT = auto()
    FLOOD = auto()
    OVERSIZE_MESSAGE = auto()
    DROP_CONNECTION = auto()
    CUSTOM_CALLBACK = auto()


@dataclass
class ServerBehaviorConfig:
    """Configuration options for scripted server behaviors."""

    behavior: ServerBehavior = ServerBehavior.ECHO
    supported_subprotocols: list[str] = field(default_factory=list)
    close_code: int = 1000
    close_reason: str = "Normal closure"
    close_on_connect: bool = True
    close_on_message_count: Optional[int] = None
    oversize_bytes: int = 10 * 1024 * 1024  # 10 MB default
    flood_count: int = 100
    flood_message_size: int = 1024
    custom_callback: Optional[
        Callable[[ScriptedWebSocketServer, QWebSocket, str | bytes], None]
    ] = None


class ScriptedWebSocketServer(QObject):
    """Local, in-process scripted WebSocket server for offline testing."""

    def __init__(
        self,
        server_name: str = "ScriptedWebSocketServer",
        config: Optional[ServerBehaviorConfig] = None,
        max_history: Optional[int] = None,
        tls_profile: Optional[TlsCertProfile] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        if max_history is not None and max_history < 1:
            raise ValueError("max_history must be None or a positive integer")
        self.server_name: str = server_name
        self.config: ServerBehaviorConfig = config or ServerBehaviorConfig()
        self._max_history: Optional[int] = max_history
        self._tls_profile: Optional[TlsCertProfile] = tls_profile
        self._tls_certificate: Optional[TlsTestCertificate] = None
        self._server: Optional[QWebSocketServer] = None
        self._clients: list[QWebSocket] = []
        self._received_messages: list[str | bytes] = []
        self._received_text_messages: list[str] = []
        self._received_binary_messages: list[bytes] = []
        self._sent_messages: list[str | bytes] = []
        self._sent_text_messages: list[str] = []
        self._sent_binary_messages: list[bytes] = []
        self._total_received_count: int = 0
        self._connection_count: int = 0
        self._disconnection_count: int = 0

    @property
    def max_history(self) -> Optional[int]:
        """Configured maximum message buffer entries; None means unbounded."""
        return self._max_history

    def _append_to_buffer(self, buffer: list, item: str | bytes) -> None:
        """Append to a message buffer and truncate oldest entries when capped."""
        buffer.append(item)
        if self._max_history is not None and len(buffer) > self._max_history:
            del buffer[: len(buffer) - self._max_history]

    @property
    def host(self) -> str:
        """Server loopback host IP."""
        return "127.0.0.1"

    @property
    def port(self) -> int:
        """Bound server port assigned by OS."""
        if self._server is None or not self._server.isListening():
            raise RuntimeError("Server is not listening")
        return self._server.serverPort()

    @property
    def url(self) -> str:
        """Complete WebSocket URL (ws:// or wss://127.0.0.1:<port>)."""
        scheme = "wss" if self.is_tls else "ws"
        return f"{scheme}://{self.host}:{self.port}"

    @property
    def is_tls(self) -> bool:
        """True when the server is configured for secure ``wss://`` transport."""
        return self._tls_profile is not None

    @property
    def tls_profile(self) -> Optional[TlsCertProfile]:
        """Active TLS certificate profile, if any."""
        return self._tls_profile

    @property
    def tls_certificate(self) -> Optional[TlsTestCertificate]:
        """Generated TLS certificate material for the active profile."""
        return self._tls_certificate

    @property
    def is_listening(self) -> bool:
        """True if server instance is active and listening."""
        return self._server is not None and self._server.isListening()

    @property
    def behavior(self) -> ServerBehavior:
        """Active server behavior."""
        return self.config.behavior

    @property
    def clients(self) -> list[QWebSocket]:
        """List of currently connected client sockets."""
        return list(self._clients)

    @property
    def connected_clients(self) -> list[QWebSocket]:
        """Alias for clients list."""
        return list(self._clients)

    @property
    def received_messages(self) -> list[str | bytes]:
        """List of all received messages (text and binary)."""
        return list(self._received_messages)

    @property
    def received_text_messages(self) -> list[str]:
        """List of received text messages."""
        return list(self._received_text_messages)

    @property
    def received_binary_messages(self) -> list[bytes]:
        """List of received binary messages."""
        return list(self._received_binary_messages)

    @property
    def sent_messages(self) -> list[str | bytes]:
        """List of all sent messages (text and binary)."""
        return list(self._sent_messages)

    @property
    def sent_text_messages(self) -> list[str]:
        """List of sent text messages."""
        return list(self._sent_text_messages)

    @property
    def sent_binary_messages(self) -> list[bytes]:
        """List of sent binary messages."""
        return list(self._sent_binary_messages)

    @property
    def connection_count(self) -> int:
        """Total number of accepted connections since start/reset."""
        return self._connection_count

    @property
    def disconnection_count(self) -> int:
        """Total number of client disconnections since start/reset."""
        return self._disconnection_count

    def _apply_subprotocol_config(self) -> None:
        """Configure supported subprotocols on internal QWebSocketServer."""
        if self._server is None:
            return
        if self.config.behavior == ServerBehavior.SUBPROTOCOL_REFUSE:
            self._server.setSupportedSubprotocols([])
        elif self.config.behavior == ServerBehavior.SUBPROTOCOL_NEGOTIATE:
            self._server.setSupportedSubprotocols(self.config.supported_subprotocols)
        elif self.config.supported_subprotocols:
            self._server.setSupportedSubprotocols(self.config.supported_subprotocols)
        else:
            self._server.setSupportedSubprotocols([])

    def _send_client_text(self, client: QWebSocket, message: str) -> None:
        """Send text frame to client and record in sent message buffer."""
        client.sendTextMessage(message)
        self._append_to_buffer(self._sent_messages, message)
        self._append_to_buffer(self._sent_text_messages, message)
        logger.debug(
            "ws_server_text_message_sent name=%s length=%d total_sent=%d",
            self.server_name,
            len(message),
            len(self._sent_messages),
        )

    def _send_client_binary(self, client: QWebSocket, message: bytes) -> None:
        """Send binary frame to client and record in sent message buffer."""
        client.sendBinaryMessage(QByteArray(message))
        self._append_to_buffer(self._sent_messages, message)
        self._append_to_buffer(self._sent_binary_messages, message)
        logger.debug(
            "ws_server_binary_message_sent name=%s length=%d total_sent=%d",
            self.server_name,
            len(message),
            len(self._sent_messages),
        )

    def start(self, timeout: float = 5.0) -> None:
        """Start listening on 127.0.0.1:0 and bounded-wait until ready."""
        if self._server is not None and self._server.isListening():
            return

        ssl_mode = (
            QWebSocketServer.SslMode.SecureMode
            if self._tls_profile is not None
            else QWebSocketServer.SslMode.NonSecureMode
        )
        self._server = QWebSocketServer(
            self.server_name,
            ssl_mode,
            self,
        )
        self._server.newConnection.connect(self._on_new_connection)
        self._server.originAuthenticationRequired.connect(self._on_origin_auth_required)
        self._apply_subprotocol_config()
        if self._tls_profile is not None:
            self._tls_certificate = build_tls_test_certificate(self._tls_profile)
            ssl_config = QSslConfiguration()
            ssl_config.setLocalCertificate(self._tls_certificate.certificate)
            ssl_config.setPrivateKey(self._tls_certificate.private_key)
            self._server.setSslConfiguration(ssl_config)
            logger.debug(
                "ws_server_tls_configured name=%s profile=%s",
                self.server_name,
                self._tls_profile.name,
            )

        success = self._server.listen(
            QHostAddress(QHostAddress.SpecialAddress.LocalHost),
            0,
        )
        if not success:
            raise RuntimeError(
                f"Failed to start QWebSocketServer: {self._server.errorString()}"
            )

        wait_until(
            lambda: self.is_listening,
            timeout=timeout,
            message="Server failed to start listening",
        )
        logger.debug(
            "ws_server_started name=%s host=%s port=%d url=%s tls=%s",
            self.server_name,
            self.host,
            self.port,
            self.url,
            str(self.is_tls).lower(),
        )

    def stop(self, timeout: float = 5.0) -> None:
        """Close all client connections, close the server, and settle events."""
        for client in list(self._clients):
            try:
                client.close()
                client.abort()
            except Exception:
                pass
        self._clients.clear()

        if self._server is not None:
            try:
                self._server.close()
            except Exception:
                pass
            self._server = None

        wait_until(
            lambda: not self.is_listening,
            timeout=timeout,
            message="Server failed to stop listening",
        )
        logger.debug("ws_server_stopped name=%s", self.server_name)

    def reset(self) -> None:
        """Reset received buffers and restore default configuration."""
        self._received_messages.clear()
        self._received_text_messages.clear()
        self._received_binary_messages.clear()
        self._sent_messages.clear()
        self._sent_text_messages.clear()
        self._sent_binary_messages.clear()
        self._total_received_count = 0
        self._connection_count = 0
        self._disconnection_count = 0
        self.config = ServerBehaviorConfig()
        logger.debug("ws_server_reset name=%s", self.server_name)

    def configure(self, config: ServerBehaviorConfig) -> None:
        """Update active server behavior configuration."""
        self.config = config
        self._apply_subprotocol_config()
        logger.debug(
            "ws_server_configured name=%s behavior=%s",
            self.server_name,
            self.config.behavior.name,
        )

    def send_to_all(self, message: str | bytes) -> None:
        """Broadcast a message to all connected clients."""
        for client in list(self._clients):
            if client.isValid():
                if isinstance(message, str):
                    self._send_client_text(client, message)
                else:
                    self._send_client_binary(client, message)

    def send_to_client(self, client: QWebSocket, message: str | bytes) -> None:
        """Send a message to a single connected client without broadcasting."""
        if client not in self._clients or not client.isValid():
            return
        if isinstance(message, str):
            self._send_client_text(client, message)
        else:
            self._send_client_binary(client, message)
        logger.debug(
            "ws_server_targeted_message_sent name=%s length=%d total_sent=%d",
            self.server_name,
            len(message),
            len(self._sent_messages),
        )

    def flood(self, count: int, size: int = 1024) -> None:
        """Emit a burst of messages to connected clients for stress testing."""
        logger.debug(
            "ws_server_flood_emitted name=%s count=%d size=%d",
            self.server_name,
            count,
            size,
        )
        payload = "A" * size
        for _ in range(count):
            self.send_to_all(payload)

    def drop_clients(self) -> None:
        """Abruptly abort all active client connections without sending close frame."""
        dropped_count = len(self._clients)
        for client in list(self._clients):
            try:
                client.abort()
            except Exception:
                pass
        self._clients.clear()
        logger.debug(
            "ws_server_clients_dropped name=%s count=%d",
            self.server_name,
            dropped_count,
        )

    def _on_origin_auth_required(
        self,
        authenticator: QWebSocketCorsAuthenticator,
    ) -> None:
        """Handle origin authentication / CORS negotiation."""
        allowed = self.config.behavior != ServerBehavior.REJECT_HANDSHAKE
        authenticator.setAllowed(allowed)
        logger.debug(
            "ws_server_origin_auth_evaluated name=%s allowed=%s behavior=%s",
            self.server_name,
            str(allowed).lower(),
            self.config.behavior.name,
        )

    def _on_new_connection(self) -> None:
        """Accept pending client connection and bind message listeners."""
        if self._server is None:
            return
        while self._server.hasPendingConnections():
            client = self._server.nextPendingConnection()
            if client is None:
                continue
            self._clients.append(client)
            self._connection_count += 1
            logger.debug(
                "ws_server_client_connected name=%s client_count=%d total_connections=%d",
                self.server_name,
                len(self._clients),
                self._connection_count,
            )

            client.textMessageReceived.connect(
                lambda msg, c=client: self._on_text_message_received(c, msg)
            )
            client.binaryMessageReceived.connect(
                lambda msg, c=client: self._on_binary_message_received(c, bytes(msg))
            )
            client.disconnected.connect(
                lambda c=client: self._on_client_disconnected(c)
            )

            if (
                self.config.behavior == ServerBehavior.CLOSE_WITH_CODE
                and self.config.close_on_connect
            ):
                client.close(
                    QWebSocketProtocol.CloseCode(self.config.close_code),
                    self.config.close_reason,
                )
            elif self.config.behavior == ServerBehavior.DROP_CONNECTION:
                client.abort()
                if client in self._clients:
                    self._clients.remove(client)

    def _on_text_message_received(self, client: QWebSocket, message: str) -> None:
        """Process incoming text message according to configured behavior."""
        self._append_to_buffer(self._received_messages, message)
        self._append_to_buffer(self._received_text_messages, message)
        self._total_received_count += 1
        logger.debug(
            "ws_server_text_message_received name=%s length=%d total_received=%d",
            self.server_name,
            len(message),
            len(self._received_messages),
        )

        if self.config.behavior == ServerBehavior.ECHO:
            self._send_client_text(client, message)
        elif self.config.behavior == ServerBehavior.CUSTOM_CALLBACK:
            if self.config.custom_callback is not None:
                self.config.custom_callback(self, client, message)
        elif self.config.behavior == ServerBehavior.CLOSE_WITH_CODE:
            if (
                self.config.close_on_message_count is not None
                and self._total_received_count >= self.config.close_on_message_count
            ):
                client.close(
                    QWebSocketProtocol.CloseCode(self.config.close_code),
                    self.config.close_reason,
                )

    def _on_binary_message_received(self, client: QWebSocket, message: bytes) -> None:
        """Process incoming binary message according to configured behavior."""
        self._append_to_buffer(self._received_messages, message)
        self._append_to_buffer(self._received_binary_messages, message)
        self._total_received_count += 1
        logger.debug(
            "ws_server_binary_message_received name=%s length=%d total_received=%d",
            self.server_name,
            len(message),
            len(self._received_messages),
        )

        if self.config.behavior == ServerBehavior.ECHO:
            self._send_client_binary(client, message)
        elif self.config.behavior == ServerBehavior.CUSTOM_CALLBACK:
            if self.config.custom_callback is not None:
                self.config.custom_callback(self, client, message)
        elif self.config.behavior == ServerBehavior.CLOSE_WITH_CODE:
            if (
                self.config.close_on_message_count is not None
                and self._total_received_count >= self.config.close_on_message_count
            ):
                client.close(
                    QWebSocketProtocol.CloseCode(self.config.close_code),
                    self.config.close_reason,
                )

    def _on_client_disconnected(self, client: QWebSocket) -> None:
        """Handle client socket disconnection."""
        if client in self._clients:
            self._clients.remove(client)
        self._disconnection_count += 1
        client.deleteLater()
        logger.debug(
            "ws_server_client_disconnected name=%s remaining_clients=%d total_disconnections=%d",
            self.server_name,
            len(self._clients),
            self._disconnection_count,
        )

    def __enter__(self) -> ScriptedWebSocketServer:
        """Context manager entry: start server."""
        self.start()
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> None:
        """Context manager exit: stop server and cleanup."""
        self.stop()
