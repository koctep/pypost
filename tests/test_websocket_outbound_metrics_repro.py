"""Outbound WebSocket metrics acceptance boundary (PYPOST-1288, real loopback PYPOST-1297)."""

from __future__ import annotations

import logging
from unittest.mock import Mock

from PySide6.QtNetwork import QAbstractSocket
from PySide6.QtWidgets import QApplication
from prometheus_client import generate_latest
import pytest

from pypost.agent.ui_wait import wait_until
from pypost.core.metrics_registry import MetricsRegistry
from pypost.core.qt.websocket_session import WebSocketSessionController
from pypost.core.qt.websocket_transport import QtWebSocketTransport
from pypost.core.websocket_session_policy import HeartbeatConfig, SessionState
from pypost.core.websocket_transport_protocol import (
    HandshakeTarget,
    RawFrame,
    WebSocketTransportListener,
)
from pypost.models.websocket import WebSocketConnection
from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
from tests.websocket_echo_server import (
    ScriptedWebSocketServer,
    ServerBehavior,
    ServerBehaviorConfig,
)

pytestmark = pytest.mark.timeout(30)

_LOOPBACK_TEXT = "héllo 💡 мир"
_LOOPBACK_BINARY = b"\x00\x01\x7f\x80\xfe\xff"
_LOOPBACK_ROWS: tuple[str | bytes, ...] = (_LOOPBACK_TEXT, _LOOPBACK_BINARY, "", b"")


class FakeTransport:
    """A synchronous handoff result without a socket or event loop callbacks."""

    def __init__(self, accepted: bool = True) -> None:
        self.accepted = accepted
        self.sent_text: list[str] = []
        self.sent_binary: list[bytes] = []
        self.listener: WebSocketTransportListener | None = None

    def set_listener(self, listener: WebSocketTransportListener) -> None:
        self.listener = listener

    def open(self, target: HandshakeTarget) -> None:
        self.target = target

    def send_text(self, message: str) -> bool:
        self.sent_text.append(message)
        return self.accepted

    def send_binary(self, payload: bytes) -> bool:
        self.sent_binary.append(payload)
        return self.accepted

    def ping(self, payload: bytes = b"") -> None:
        pass

    def close(self, code: int = 1000, reason: str = "") -> None:
        pass

    def abort(self) -> None:
        pass

    def negotiated_subprotocol(self) -> str:
        return ""


def _open_session(
    accepted: bool = True,
) -> tuple[WebSocketPresenter, WebSocketSessionController, FakeTransport, MetricsRegistry]:
    metrics = MetricsRegistry()
    controller = WebSocketSessionController()
    transport = FakeTransport(accepted=accepted)
    controller.set_transport_factory(lambda: transport)
    presenter = WebSocketPresenter(
        connection=WebSocketConnection(url="ws://example.test/socket"),
        session_controller=controller,
        metrics=metrics,
    )
    controller.open(
        HandshakeTarget(url="ws://example.test/socket"),
        heartbeat=HeartbeatConfig(interval_seconds=0),
    )
    controller.on_opened("")
    assert controller.state == SessionState.OPEN
    return presenter, controller, transport, metrics


def _scrape(metrics: MetricsRegistry) -> str:
    return generate_latest(metrics.registry).decode("utf-8")


def test_accepted_text_and_binary_send_record_outbound_counts_and_payload_bytes(
    qapp: QApplication,
    caplog: pytest.LogCaptureFixture,
) -> None:
    presenter, controller, transport, metrics = _open_session()
    frames: list[RawFrame] = []
    controller.frame_sent.connect(frames.append)
    try:
        with caplog.at_level(logging.DEBUG, logger="pypost.core.qt.websocket_session"):
            controller.send_text("é💡")
            controller.send_binary(b"\x00\xff\x7f")

        assert transport.sent_text == ["é💡"]
        assert transport.sent_binary == [b"\x00\xff\x7f"]
        assert len(frames) == 2
        assert [frame.byte_size for frame in frames] == [6, 3]

        scrape = _scrape(metrics)
        assert 'websocket_messages_total{direction="outbound",kind="text"} 1.0' in scrape
        assert 'websocket_messages_total{direction="outbound",kind="binary"} 1.0' in scrape
        assert 'websocket_message_bytes_total{direction="outbound"} 9.0' in scrape
        assert "websocket_send_accepted kind=text bytes=6" in caplog.text
        assert "websocket_send_accepted kind=binary bytes=3" in caplog.text
        assert "é💡" not in caplog.text

    finally:
        presenter.teardown()


def test_blocked_send_does_not_emit_frame_or_change_outbound_metrics(
    qapp: QApplication,
) -> None:
    presenter, controller, transport, metrics = _open_session()
    frames: list[RawFrame] = []
    controller.frame_sent.connect(frames.append)
    try:
        controller.close()
        assert controller.state == SessionState.CLOSING
        scrape = _scrape(metrics)

        controller.send_text("blocked")
        controller.send_binary(b"blocked")

        assert frames == []
        assert transport.sent_text == []
        assert transport.sent_binary == []
        assert _scrape(metrics) == scrape
    finally:
        presenter.teardown()


@pytest.mark.parametrize("payload", ["rejected", b"\x00\xff"])
def test_rejected_handoff_emits_no_sent_frame_or_outbound_metrics(
    qapp: QApplication, payload: str | bytes, caplog: pytest.LogCaptureFixture
) -> None:
    presenter, controller, transport, metrics = _open_session(accepted=False)
    frames: list[RawFrame] = []
    controller.frame_sent.connect(frames.append)
    try:
        if isinstance(payload, str):
            controller.send_text(payload)
            assert transport.sent_text == [payload]
        else:
            controller.send_binary(payload)
            assert transport.sent_binary == [payload]

        assert frames == []
        text_count = metrics.websocket_messages.labels(direction="outbound", kind="text")
        binary_count = metrics.websocket_messages.labels(direction="outbound", kind="binary")
        assert text_count._value.get() == 0
        assert binary_count._value.get() == 0
        assert metrics.websocket_message_bytes.labels(direction="outbound")._value.get() == 0
        kind = "text" if isinstance(payload, str) else "binary"
        byte_size = len(payload.encode("utf-8")) if isinstance(payload, str) else len(payload)
        assert (
            f"websocket_send_rejected kind={kind} bytes={byte_size} state=Open"
            in [record.message for record in caplog.records]
        )
    finally:
        presenter.teardown()


@pytest.mark.parametrize(
    ("payload", "accepted_bytes", "connected", "accepted"),
    [
        ("é", 2, True, True),
        ("é", 1, True, False),
        ("", 0, True, True),
        ("é", 0, False, False),
        (b"\x00\xff", 2, True, True),
        (b"\x00\xff", 1, True, False),
        (b"", 0, True, True),
        (b"\x00\xff", 0, False, False),
    ],
)
def test_qt_transport_reports_complete_handoff_only(
    qapp: QApplication,
    payload: str | bytes,
    accepted_bytes: int,
    connected: bool,
    accepted: bool,
) -> None:
    transport = QtWebSocketTransport()
    socket = Mock()
    socket.state.return_value = (
        QAbstractSocket.SocketState.ConnectedState
        if connected
        else QAbstractSocket.SocketState.UnconnectedState
    )
    socket.sendTextMessage.return_value = accepted_bytes
    socket.sendBinaryMessage.return_value = accepted_bytes
    transport._socket = socket

    if isinstance(payload, str):
        result = transport.send_text(payload)
        assert socket.sendTextMessage.call_count == int(connected)
    else:
        result = transport.send_binary(payload)
        assert socket.sendBinaryMessage.call_count == int(connected)

    assert result is accepted


def _outbound(metrics: MetricsRegistry) -> tuple[float, float, float]:
    """Return outbound (text count, binary count, bytes) via the public sample API."""

    def sample(name: str, labels: dict[str, str]) -> float:
        value = metrics.registry.get_sample_value(name, labels)
        return 0.0 if value is None else value

    return (
        sample("websocket_messages_total", {"direction": "outbound", "kind": "text"}),
        sample("websocket_messages_total", {"direction": "outbound", "kind": "binary"}),
        sample("websocket_message_bytes_total", {"direction": "outbound"}),
    )


def _run_loopback_send_table(server: ScriptedWebSocketServer) -> None:
    """Send the PYPOST-1297 table through the real Qt adapter and assert metrics and receipt.

    Metric deltas are asserted right after each send (``frame_sent`` is delivered
    directly), then peer receipt is awaited with a bounded wait.
    """
    # Guard the fixture: the text row must have UTF-8 bytes != characters.
    assert len(_LOOPBACK_TEXT.encode("utf-8")) == 18 != len(_LOOPBACK_TEXT) == 11
    server.configure(ServerBehaviorConfig(behavior=ServerBehavior.SILENT))
    metrics = MetricsRegistry()
    controller = WebSocketSessionController()
    presenter = WebSocketPresenter(
        connection=WebSocketConnection(url=server.url),
        session_controller=controller,
        metrics=metrics,
    )
    try:
        controller.open(
            HandshakeTarget(url=server.url),
            heartbeat=HeartbeatConfig(interval_seconds=0),
        )
        wait_until(
            lambda: controller.state == SessionState.OPEN and len(server.clients) == 1,
            timeout=5.0,
            message="real loopback session did not open",
        )

        for row, payload in enumerate(_LOOPBACK_ROWS):
            if isinstance(payload, str):
                kind, size = "text", len(payload.encode("utf-8"))
            else:
                kind, size = "binary", len(payload)
            exp_text, exp_binary = (1, 0) if kind == "text" else (0, 1)
            label = f"row {row} {kind} ({size} bytes)"

            before = _outbound(metrics)
            if isinstance(payload, str):
                controller.send_text(payload)
            else:
                controller.send_binary(payload)
            after = _outbound(metrics)

            d_text, d_binary, d_bytes = (a - b for a, b in zip(after, before))
            assert (d_text, d_binary) == (exp_text, exp_binary), (
                f"{label} count delta: expected text=+{exp_text} binary=+{exp_binary}, "
                f"got text=+{d_text:g} binary=+{d_binary:g}"
            )
            assert d_bytes == size, f"{label} bytes delta: expected +{size}, got +{d_bytes:g}"

            received_count = row + 1
            wait_until(
                lambda: len(server.received_messages) == received_count,
                timeout=5.0,
                message=f"{label} not received by peer",
            )
            received = server.received_messages[-1]
            assert type(received) is type(payload), f"{label} peer kind mismatch"
            assert received == payload, f"{label} peer payload mismatch"

        assert server.received_text_messages == [_LOOPBACK_TEXT, ""]
        assert server.received_binary_messages == [_LOOPBACK_BINARY, b""]
    finally:
        presenter.teardown()


@pytest.mark.timeout(60)
def test_real_loopback_send_records_outbound_metrics_and_reaches_peer(
    qapp: QApplication,
    ws_test_server: ScriptedWebSocketServer,
) -> None:
    _run_loopback_send_table(ws_test_server)
