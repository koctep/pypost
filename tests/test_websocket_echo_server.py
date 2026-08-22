"""Tests for ScriptedWebSocketServer and ws_test_server fixture (PYPOST-1129 / WS-11).

Asserts full lifecycle, ephemeral loopback binding, scripted behaviors,
subprotocol negotiation, clean teardown with no port leaks, and offscreen
responsiveness under load.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QByteArray, QCoreApplication, QUrl
from PySide6.QtNetwork import QNetworkRequest
from PySide6.QtWebSockets import QWebSocket

from pypost.agent.ui_wait import wait_until
from tests.websocket_echo_server import (
    ScriptedWebSocketServer,
    ServerBehavior,
    ServerBehaviorConfig,
)

pytestmark = pytest.mark.timeout(15)


@pytest.mark.timeout(10)
def test_server_startup_binding_and_properties(qapp) -> None:
    """Server starts, binds dynamically to 127.0.0.1:0, exposes properties, and stops cleanly."""
    server = ScriptedWebSocketServer("TestServer")
    assert not server.is_listening

    server.start()
    try:
        assert server.is_listening
        assert server.host == "127.0.0.1"
        assert isinstance(server.port, int)
        assert server.port > 0
        assert server.url == f"ws://127.0.0.1:{server.port}"
    finally:
        server.stop()

    assert not server.is_listening


@pytest.mark.timeout(10)
def test_server_context_manager(qapp) -> None:
    """Server supports context manager protocol with automatic start and stop."""
    with ScriptedWebSocketServer("ContextServer") as server:
        assert server.is_listening
        assert server.port > 0
        assert server.url.startswith("ws://127.0.0.1:")

    assert not server.is_listening


@pytest.mark.timeout(10)
def test_ws_test_server_fixture_lifecycle(ws_test_server) -> None:
    """pytest fixture ws_test_server yields an active, listening server bound to loopback."""
    assert ws_test_server.is_listening
    assert ws_test_server.host == "127.0.0.1"
    assert ws_test_server.port > 0
    assert ws_test_server.url.startswith("ws://127.0.0.1:")


@pytest.mark.timeout(10)
def test_behavior_echo_text_and_binary(qapp) -> None:
    """Server in ECHO mode echoes back text and binary frames and logs received messages."""
    server = ScriptedWebSocketServer(config=ServerBehaviorConfig(behavior=ServerBehavior.ECHO))
    server.start()

    client = QWebSocket()
    received_texts: list[str] = []
    received_binaries: list[bytes] = []

    client.textMessageReceived.connect(received_texts.append)
    client.binaryMessageReceived.connect(lambda b: received_binaries.append(bytes(b)))

    try:
        client.open(QUrl(server.url))
        wait_until(
            lambda: client.isValid() and len(server.clients) == 1,
            timeout=5.0,
            message="Client failed to connect to echo server",
        )

        # Test text echo
        client.sendTextMessage("Hello PyPost WebSocket!")
        wait_until(
            lambda: received_texts == ["Hello PyPost WebSocket!"],
            timeout=5.0,
            message="Echo server did not return text message",
        )

        # Test binary echo
        test_payload = b"\x00\x01\x02\xfe\xff\x42"
        client.sendBinaryMessage(QByteArray(test_payload))
        wait_until(
            lambda: received_binaries == [test_payload],
            timeout=5.0,
            message="Echo server did not return binary message",
        )

        assert server.received_text_messages == ["Hello PyPost WebSocket!"]
        assert server.received_binary_messages == [test_payload]
        assert len(server.received_messages) == 2
    finally:
        client.close()
        server.stop()


@pytest.mark.timeout(10)
def test_behavior_reject_handshake(qapp) -> None:
    """Server in REJECT_HANDSHAKE mode refuses client handshake with HTTP 403 / CORS denial."""
    server = ScriptedWebSocketServer(
        config=ServerBehaviorConfig(behavior=ServerBehavior.REJECT_HANDSHAKE)
    )
    server.start()

    client = QWebSocket()
    connected = [False]
    error_occurred = [False]

    client.connected.connect(lambda: connected.__setitem__(0, True))
    client.errorOccurred.connect(lambda _: error_occurred.__setitem__(0, True))

    try:
        client.open(QUrl(server.url))
        wait_until(
            lambda: error_occurred[0],
            timeout=3.0,
            message="Expected handshake rejection error",
        )
        assert not connected[0]
        assert len(server.clients) == 0
    finally:
        client.close()
        server.stop()


@pytest.mark.timeout(10)
def test_behavior_subprotocol_negotiation_and_refusal(qapp) -> None:
    """Server negotiates matching subprotocols and ignores unlisted subprotocols."""
    config = ServerBehaviorConfig(
        behavior=ServerBehavior.SUBPROTOCOL_NEGOTIATE,
        supported_subprotocols=["pypost.v1", "pypost.v2"],
    )
    server = ScriptedWebSocketServer(config=config)
    server.start()

    client = QWebSocket()
    unlisted_client = QWebSocket()
    try:
        # Request supported subprotocol
        request = QNetworkRequest(QUrl(server.url))
        request.setRawHeader(b"Sec-WebSocket-Protocol", b"pypost.v2")
        client.open(request)

        wait_until(
            lambda: client.isValid() and len(server.clients) == 1,
            timeout=5.0,
            message="Client failed to connect with supported subprotocol",
        )
        assert client.subprotocol() == "pypost.v2"

        # Request unlisted subprotocol
        unlisted_request = QNetworkRequest(QUrl(server.url))
        unlisted_request.setRawHeader(b"Sec-WebSocket-Protocol", b"unlisted.proto")
        unlisted_client.open(unlisted_request)

        wait_until(
            lambda: unlisted_client.isValid() and len(server.clients) == 2,
            timeout=5.0,
            message="Client with unlisted subprotocol failed to connect",
        )
        assert unlisted_client.subprotocol() == ""
    finally:
        client.close()
        unlisted_client.close()
        server.stop()


@pytest.mark.timeout(10)
def test_behavior_subprotocol_refuse(qapp) -> None:
    """Server in SUBPROTOCOL_REFUSE mode refuses requested subprotocols."""
    config = ServerBehaviorConfig(
        behavior=ServerBehavior.SUBPROTOCOL_REFUSE,
        supported_subprotocols=["pypost.v1"],
    )
    server = ScriptedWebSocketServer(config=config)
    server.start()

    client = QWebSocket()
    try:
        request = QNetworkRequest(QUrl(server.url))
        request.setRawHeader(b"Sec-WebSocket-Protocol", b"pypost.v1")
        client.open(request)

        wait_until(
            lambda: client.isValid() and len(server.clients) == 1,
            timeout=5.0,
            message="Client failed to connect to subprotocol-refusing server",
        )
        assert client.subprotocol() == ""
    finally:
        client.close()
        server.stop()


@pytest.mark.timeout(10)
def test_behavior_close_with_code_and_reason(qapp) -> None:
    """Server in CLOSE_WITH_CODE mode immediately closes connection with RFC code and reason."""
    config = ServerBehaviorConfig(
        behavior=ServerBehavior.CLOSE_WITH_CODE,
        close_code=1008,
        close_reason="Policy Violated: Test Reason",
        close_on_connect=True,
    )
    server = ScriptedWebSocketServer(config=config)
    server.start()

    client = QWebSocket()
    closed_events: list[tuple[int, str]] = []
    client.disconnected.connect(
        lambda: closed_events.append((client.closeCode().value, client.closeReason()))
    )

    try:
        client.open(QUrl(server.url))
        wait_until(
            lambda: len(closed_events) > 0,
            timeout=5.0,
            message="Server did not close client connection with code",
        )
        code, reason = closed_events[0]
        assert code == 1008
        assert reason == "Policy Violated: Test Reason"
    finally:
        client.close()
        server.stop()


@pytest.mark.timeout(10)
def test_behavior_silent_server_suppresses_replies(qapp) -> None:
    """Server in SILENT mode accepts connections and buffers messages without replying."""
    config = ServerBehaviorConfig(behavior=ServerBehavior.SILENT)
    server = ScriptedWebSocketServer(config=config)
    server.start()

    client = QWebSocket()
    received_texts: list[str] = []
    client.textMessageReceived.connect(received_texts.append)

    try:
        client.open(QUrl(server.url))
        wait_until(
            lambda: client.isValid() and len(server.clients) == 1,
            timeout=5.0,
            message="Client failed to connect to silent server",
        )

        client.sendTextMessage("Heartbeat Ping")
        wait_until(
            lambda: len(server.received_text_messages) == 1,
            timeout=5.0,
            message="Silent server did not record received message",
        )

        # Confirm no reply was sent
        deadline = time.monotonic() + 0.1
        while time.monotonic() < deadline:
            QCoreApplication.processEvents()
            time.sleep(0.01)
        assert len(received_texts) == 0
        assert server.received_text_messages == ["Heartbeat Ping"]
    finally:
        client.close()
        server.stop()


@pytest.mark.timeout(10)
def test_behavior_flood_burst(qapp) -> None:
    """Server flood method emits configured burst of messages to all connected clients."""
    server = ScriptedWebSocketServer()
    server.start()

    client = QWebSocket()
    received_texts: list[str] = []
    client.textMessageReceived.connect(received_texts.append)

    try:
        client.open(QUrl(server.url))
        wait_until(
            lambda: client.isValid() and len(server.clients) == 1,
            timeout=5.0,
            message="Client failed to connect for flood test",
        )

        server.flood(count=25, size=128)
        wait_until(
            lambda: len(received_texts) == 25,
            timeout=5.0,
            message="Client did not receive all 25 flood messages",
        )
        assert all(len(msg) == 128 for msg in received_texts)
    finally:
        client.close()
        server.stop()


@pytest.mark.timeout(10)
def test_behavior_oversize_message_delivery(qapp) -> None:
    """Server in OVERSIZE_MESSAGE mode sends large message frame to client."""
    oversize_payload = "X" * (64 * 1024)  # 64 KB test frame
    config = ServerBehaviorConfig(
        behavior=ServerBehavior.OVERSIZE_MESSAGE,
        oversize_bytes=64 * 1024,
    )
    server = ScriptedWebSocketServer(config=config)
    server.start()

    client = QWebSocket()
    received_texts: list[str] = []
    client.textMessageReceived.connect(received_texts.append)

    try:
        client.open(QUrl(server.url))
        wait_until(
            lambda: client.isValid() and len(server.clients) == 1,
            timeout=5.0,
            message="Client failed to connect for oversize message test",
        )

        # Trigger oversize send
        server.send_to_all(oversize_payload)
        wait_until(
            lambda: len(received_texts) == 1,
            timeout=5.0,
            message="Client did not receive oversize message",
        )
        assert len(received_texts[0]) == 64 * 1024
    finally:
        client.close()
        server.stop()


@pytest.mark.timeout(10)
def test_behavior_midstream_connection_drop(qapp) -> None:
    """Server drop_clients abruptly drops TCP connections without sending RFC 6455 close frame."""
    server = ScriptedWebSocketServer()
    server.start()

    client = QWebSocket()
    disconnected = [False]
    client.disconnected.connect(lambda: disconnected.__setitem__(0, True))

    try:
        client.open(QUrl(server.url))
        wait_until(
            lambda: client.isValid() and len(server.clients) == 1,
            timeout=5.0,
            message="Client failed to connect",
        )

        server.drop_clients()
        wait_until(
            lambda: disconnected[0],
            timeout=5.0,
            message="Client was not disconnected after drop_clients",
        )
    finally:
        client.close()
        server.stop()


@pytest.mark.timeout(10)
def test_behavior_custom_callback(qapp) -> None:
    """Server executes custom_callback when receiving client messages."""

    def custom_handler(
        srv: ScriptedWebSocketServer,
        sock: QWebSocket,
        message: str | bytes,
    ) -> None:
        if isinstance(message, str):
            sock.sendTextMessage(f"CUSTOM_REPLY:{message}")

    config = ServerBehaviorConfig(
        behavior=ServerBehavior.CUSTOM_CALLBACK,
        custom_callback=custom_handler,
    )
    server = ScriptedWebSocketServer(config=config)
    server.start()

    client = QWebSocket()
    received_texts: list[str] = []
    client.textMessageReceived.connect(received_texts.append)

    try:
        client.open(QUrl(server.url))
        wait_until(
            lambda: client.isValid() and len(server.clients) == 1,
            timeout=5.0,
            message="Client failed to connect for custom callback test",
        )

        client.sendTextMessage("ping_payload")
        wait_until(
            lambda: received_texts == ["CUSTOM_REPLY:ping_payload"],
            timeout=5.0,
            message="Custom callback handler did not produce expected reply",
        )
    finally:
        client.close()
        server.stop()


@pytest.mark.timeout(10)
def test_repeated_startup_teardown_leak_free(qapp) -> None:
    """Server can be repeatedly started and stopped without socket or port leaks."""
    for cycle in range(5):
        server = ScriptedWebSocketServer(f"LeakTest_{cycle}")
        server.start()
        assert server.is_listening
        port = server.port
        assert port > 0
        server.stop()
        assert not server.is_listening


@pytest.mark.timeout(10)
def test_offscreen_responsiveness_under_load(qapp) -> None:
    """Offscreen event processing remains responsive (< 50ms per tick) under load."""
    server = ScriptedWebSocketServer()
    server.start()

    client = QWebSocket()
    received_texts: list[str] = []
    client.textMessageReceived.connect(received_texts.append)

    max_tick_duration_ms: float = 0.0

    try:
        client.open(QUrl(server.url))
        wait_until(
            lambda: client.isValid() and len(server.clients) == 1,
            timeout=5.0,
            message="Client failed to connect",
        )

        # Flood 50 messages
        server.flood(count=50, size=256)

        # Measure responsiveness while polling
        deadline = time.monotonic() + 5.0
        while len(received_texts) < 50 and time.monotonic() < deadline:
            t0 = time.monotonic()
            QCoreApplication.processEvents()
            tick_duration_ms = (time.monotonic() - t0) * 1000
            if tick_duration_ms > max_tick_duration_ms:
                max_tick_duration_ms = tick_duration_ms
            time.sleep(0.01)

        assert len(received_texts) == 50
        # Assert responsiveness bound: no single event tick should block > 50ms
        assert max_tick_duration_ms < 50.0, f"Event loop lagged: {max_tick_duration_ms:.2f}ms"
    finally:
        client.close()
        server.stop()


@pytest.mark.timeout(10)
def test_observability_counters_and_buffers(qapp) -> None:
    """Server exposes accurate connection, disconnection, and message tracking counters."""
    server = ScriptedWebSocketServer("ObsServer")
    server.start()

    assert server.connection_count == 0
    assert server.disconnection_count == 0
    assert len(server.received_messages) == 0
    assert len(server.sent_messages) == 0

    client1 = QWebSocket()
    client2 = QWebSocket()
    try:
        client1.open(QUrl(server.url))
        wait_until(
            lambda: server.connection_count == 1 and len(server.clients) == 1,
            timeout=5.0,
            message="First client failed to connect",
        )

        client2.open(QUrl(server.url))
        wait_until(
            lambda: server.connection_count == 2 and len(server.clients) == 2,
            timeout=5.0,
            message="Second client failed to connect",
        )

        client1.sendTextMessage("hello-obs")
        wait_until(
            lambda: (
                len(server.received_text_messages) == 1
                and len(server.sent_text_messages) == 1
            ),
            timeout=5.0,
            message="Text message not recorded in observability buffers",
        )

        client2.sendBinaryMessage(QByteArray(b"\xaa\xbb"))
        wait_until(
            lambda: (
                len(server.received_binary_messages) == 1
                and len(server.sent_binary_messages) == 1
            ),
            timeout=5.0,
            message="Binary message not recorded in observability buffers",
        )

        assert server.received_text_messages == ["hello-obs"]
        assert server.received_binary_messages == [b"\xaa\xbb"]
        assert server.sent_text_messages == ["hello-obs"]
        assert server.sent_binary_messages == [b"\xaa\xbb"]
        assert len(server.received_messages) == 2
        assert len(server.sent_messages) == 2

        client1.close()
        wait_until(
            lambda: server.disconnection_count == 1 and len(server.clients) == 1,
            timeout=5.0,
            message="First client disconnection not counted",
        )

        client2.close()
        wait_until(
            lambda: server.disconnection_count == 2 and len(server.clients) == 0,
            timeout=5.0,
            message="Second client disconnection not counted",
        )

        # Verify reset clears all metrics
        server.reset()
        assert server.connection_count == 0
        assert server.disconnection_count == 0
        assert len(server.received_messages) == 0
        assert len(server.sent_messages) == 0
    finally:
        client1.close()
        client2.close()
        server.stop()


@pytest.mark.timeout(10)
def test_observability_structured_logging(qapp, caplog) -> None:
    """Server emits structured key=value debug logs for lifecycle and message events."""
    import logging

    server = ScriptedWebSocketServer("LoggingServer")
    with caplog.at_level(logging.DEBUG, logger="tests.websocket_echo_server"):
        server.start()
        client = QWebSocket()
        received_texts: list[str] = []
        client.textMessageReceived.connect(received_texts.append)
        try:
            client.open(QUrl(server.url))
            wait_until(
                lambda: client.isValid() and len(server.clients) == 1,
                timeout=5.0,
                message="Client failed to connect",
            )
            client.sendTextMessage("log-test-payload")
            wait_until(
                lambda: len(server.received_text_messages) == 1 and len(received_texts) == 1,
                timeout=5.0,
                message="Server did not receive or echo text message",
            )
            client.close()
            wait_until(
                lambda: server.disconnection_count == 1 and len(server.clients) == 0,
                timeout=5.0,
                message="Client disconnection was not recorded",
            )
        finally:
            client.close()
            server.stop()

    records = [r for r in caplog.records if r.name == "tests.websocket_echo_server"]
    messages = [r.getMessage() for r in records]

    assert any(msg.startswith("ws_server_started ") for msg in messages)
    assert any(msg.startswith("ws_server_client_connected ") for msg in messages)
    assert any(msg.startswith("ws_server_text_message_received ") for msg in messages)
    assert any(msg.startswith("ws_server_text_message_sent ") for msg in messages)
    assert any(msg.startswith("ws_server_client_disconnected ") for msg in messages)
    assert any(msg.startswith("ws_server_stopped ") for msg in messages)
