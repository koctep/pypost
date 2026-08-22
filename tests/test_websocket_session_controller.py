"""Integration and lifecycle unit tests for WebSocketSessionController with loopback
QWebSocketServer.
"""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtNetwork import QHostAddress
from PySide6.QtWebSockets import QWebSocket, QWebSocketServer
import pytest

from pypost.core.qt.websocket_session import WebSocketSessionController
from pypost.core.websocket_session_policy import (
    ReconnectConfig,
    SessionState,
)
from pypost.core.websocket_transport_protocol import (
    FrameDirection,
    FrameType,
    HandshakeTarget,
    RawFrame,
    WebSocketTransportListener,
)

pytestmark = pytest.mark.timeout(30)


@pytest.fixture
def echo_server():
    """Start a local hermetic QWebSocketServer fixture echoing frames."""
    server = QWebSocketServer("EchoServer", QWebSocketServer.SslMode.NonSecureMode)
    assert server.listen(QHostAddress.SpecialAddress.LocalHost, 0), "Failed to start server"
    clients: list[QWebSocket] = []

    def on_new_connection():
        socket = server.nextPendingConnection()
        if socket:
            clients.append(socket)
            socket.textMessageReceived.connect(lambda msg: socket.sendTextMessage(msg))
            socket.binaryMessageReceived.connect(lambda data: socket.sendBinaryMessage(data))

    server.newConnection.connect(on_new_connection)
    port = server.serverPort()
    url = f"ws://127.0.0.1:{port}"

    yield {"server": server, "url": url, "clients": clients}

    for c in clients:
        c.close()
    server.close()


def test_reconnection_exhaustion_lifecycle(qapp):
    """Verify session controller attempts reconnection and fails when max attempts are exceeded."""
    listener_ref: list[WebSocketTransportListener] = []

    class DummyTransport:
        def __init__(self):
            self.aborted = False

        def open(self, target: HandshakeTarget) -> None:
            pass

        def send_text(self, message: str) -> None:
            pass

        def send_binary(self, payload: bytes) -> None:
            pass

        def ping(self, payload: bytes = b"") -> None:
            pass

        def close(self, code: int = 1000, reason: str = "") -> None:
            pass

        def abort(self) -> None:
            self.aborted = True

        def negotiated_subprotocol(self) -> str:
            return ""

        def set_listener(self, listener: WebSocketTransportListener) -> None:
            listener_ref.append(listener)

    reconnects: list[tuple[int, int, int]] = []
    failures: list[tuple[str, str]] = []
    states: list[str] = []

    controller = WebSocketSessionController()
    controller.set_transport_factory(DummyTransport)
    controller.reconnect_scheduled.connect(lambda a, m, d: reconnects.append((a, m, d)))
    controller.session_failed.connect(lambda c, m: failures.append((c, m)))
    controller.state_changed.connect(lambda s, d: states.append(s))

    target = HandshakeTarget(url="wss://test.local/ws", headers={})
    reconnect_cfg = ReconnectConfig(
        enabled=True,
        initial_delay_seconds=0.01,
        max_attempts=2,
        jitter=False,
    )

    controller.open(target=target, reconnect=reconnect_cfg)
    listener = listener_ref[-1]
    listener.on_opened("")
    assert controller.state == SessionState.OPEN

    # 1. First abnormal drop
    listener.on_closed(1006, "Abnormal drop", peer_initiated=True)
    assert controller.state == SessionState.RECONNECTING
    assert len(reconnects) == 1
    assert reconnects[0][0] == 1  # attempt 1

    # Simulate timer firing and opening attempt 1
    controller._on_reconnect_timer()
    listener = listener_ref[-1]

    # 2. Second abnormal drop
    listener.on_closed(1006, "Drop 2", peer_initiated=True)
    assert controller.state == SessionState.RECONNECTING
    assert len(reconnects) == 2
    assert reconnects[1][0] == 2  # attempt 2

    # Simulate timer firing and opening attempt 2
    controller._on_reconnect_timer()
    listener = listener_ref[-1]

    # 3. Third drop -> max attempts (2) exhausted -> FAILED
    listener.on_closed(1006, "Drop 3", peer_initiated=True)
    assert controller.state == SessionState.FAILED
    assert len(failures) == 1
    assert failures[0][0] == "reconnect_exhausted"


def test_cancel_during_connecting_or_reconnecting(qapp):
    """Verify close() while connecting or reconnecting cleanly transitions to Closed."""
    controller = WebSocketSessionController()
    target = HandshakeTarget(url="wss://test.local/ws", headers={})
    controller.open(target=target)
    assert controller.state == SessionState.CONNECTING

    controller.close(1000, "User cancelled")
    assert controller.state == SessionState.CLOSED


def test_transport_failure_and_tls_error_handling(qapp):
    """Verify on_failed and on_tls_errors callbacks."""
    controller = WebSocketSessionController()
    failures: list[tuple[str, str]] = []
    tls_raised: list[tuple[str, ...]] = []

    controller.session_failed.connect(lambda c, m: failures.append((c, m)))
    controller.tls_errors_raised.connect(lambda errs: tls_raised.append(errs))

    target = HandshakeTarget(url="wss://test.local/ws", headers={}, verify_tls=False)
    controller.open(target=target)

    # on_tls_errors should return True when verify_tls is False
    assert controller.on_tls_errors(("Certificate expired",)) is True
    assert len(tls_raised) == 1

    # on_failed
    controller.on_failed("dns_error", "Host not found", "detail")
    assert controller.state == SessionState.FAILED
    assert len(failures) == 1
    assert failures[0] == ("dns_error", "Host not found")


def test_real_loopback_roundtrip(qapp, echo_server):
    """Verify real full-duplex text and binary round trip with QtWebSocketTransport."""
    controller = WebSocketSessionController()
    target = HandshakeTarget(url=echo_server["url"], headers={})

    received_frames: list[RawFrame] = []
    sent_frames: list[RawFrame] = []
    events: list[tuple[str, str]] = []

    controller.frame_received.connect(lambda f: received_frames.append(f))
    controller.frame_sent.connect(lambda f: sent_frames.append(f))
    controller.lifecycle_event.connect(lambda e, d: events.append((e, d)))

    controller.open(target=target)

    # Wait for connected
    for _ in range(50):
        QCoreApplication.processEvents()
        if controller.state == SessionState.OPEN:
            break
        QCoreApplication.processEvents()

    assert controller.state == SessionState.OPEN

    # Send text
    controller.send_text("Hello Real Server")
    for _ in range(50):
        QCoreApplication.processEvents()
        if len(received_frames) >= 1:
            break

    assert len(sent_frames) == 1
    assert sent_frames[0].payload == "Hello Real Server"
    assert len(received_frames) == 1
    assert received_frames[0].payload == "Hello Real Server"
    assert received_frames[0].direction == FrameDirection.IN
    assert received_frames[0].payload_format == FrameType.TEXT

    # Send binary
    controller.send_binary(b"\xde\xad\xbe\xef")
    for _ in range(50):
        QCoreApplication.processEvents()
        if len(received_frames) >= 2:
            break

    assert len(sent_frames) == 2
    assert sent_frames[1].payload == b"\xde\xad\xbe\xef"
    assert len(received_frames) == 2
    assert received_frames[1].payload == b"\xde\xad\xbe\xef"
    assert received_frames[1].payload_format == FrameType.BINARY

    # Close
    controller.close(1000, "Clean shutdown")
    for _ in range(50):
        QCoreApplication.processEvents()
        if controller.state == SessionState.CLOSED:
            break

    assert controller.state == SessionState.CLOSED


def test_websocket_structured_logging(qapp, caplog):
    """Verify standard library logging emits structured contextual logs without leaking payloads."""
    import logging
    controller = WebSocketSessionController()
    target = HandshakeTarget(url="wss://example.com/ws", headers={})

    with caplog.at_level(logging.DEBUG):
        controller.open(target=target)
        controller.on_opened("v1.proto")
        controller.send_text("secret_token_12345")
        controller.send_binary(b"binary_secret_payload")
        controller.close(1000, "Clean close")

    log_records = [
        r for r in caplog.records
        if r.name.startswith("pypost.core.qt.websocket_session")
    ]
    assert len(log_records) > 0
    messages = [r.getMessage() for r in log_records]

    # Verify structured attributes present
    assert any("Opening WebSocket session to wss://example.com/ws" in m for m in messages)
    assert any("Closing WebSocket session (code=1000" in m for m in messages)
    assert any(
        "WebSocket session opened successfully (subprotocol=v1.proto)" in m
        for m in messages
    )

    # Verify raw message contents are NOT leaked into logs
    assert not any("secret_token_12345" in m for m in messages)
    assert not any("binary_secret_payload" in m for m in messages)
    assert any("Sending WebSocket text frame (18 bytes)" in m for m in messages)
    assert any("Sending WebSocket binary frame (21 bytes)" in m for m in messages)
