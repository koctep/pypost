"""Failing repro tests for WebSocket transport seam and Qt session engine (PYPOST-1127).

Asserts the contract and behavior specified in:
- `ai-tasks/PYPOST-1127/10-requirements.md`
- `ai-tasks/PYPOST-1127/20-architecture.md`

Covers:
1. Pure Qt-free transport protocol abstractions and data structures
   (`pypost.core.websocket_transport_protocol`).
2. Pure Qt-free session state machine, backoff calculation, and reconnect policy
   (`pypost.core.websocket_session_policy`).
3. Qt-native transport adapter interface conformance
   (`pypost.core.qt.websocket_transport`).
4. Headless Qt session controller lifecycle, timers, and signal emissions
   (`pypost.core.qt.websocket_session`).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pytest

pytestmark = pytest.mark.timeout(30)


# =============================================================================
# 1. Transport Protocol & Data Structures (Qt-Free Seam)
# =============================================================================


def test_websocket_transport_protocol_enums_and_dataclasses():
    """Verify FrameType, FrameDirection, RawFrame, and HandshakeTarget definitions."""
    from pypost.core.websocket_transport_protocol import (
        FrameDirection,
        FrameType,
        HandshakeTarget,
        RawFrame,
    )

    # FrameType enum
    assert FrameType.TEXT.value == "text"
    assert FrameType.BINARY.value == "binary"

    # FrameDirection enum
    assert FrameDirection.IN.value == "in"
    assert FrameDirection.OUT.value == "out"

    # RawFrame frozen dataclass
    now = datetime.now(timezone.utc)
    frame = RawFrame(
        direction=FrameDirection.IN,
        payload_format=FrameType.TEXT,
        payload="Hello WebSocket",
        byte_size=15,
        timestamp=now,
    )
    assert frame.direction == FrameDirection.IN
    assert frame.payload_format == FrameType.TEXT
    assert frame.payload == "Hello WebSocket"
    assert frame.byte_size == 15
    assert frame.timestamp == now

    with pytest.raises((AttributeError, TypeError)):
        # Immutability check
        frame.payload = "Mutated"  # type: ignore[misc]

    # HandshakeTarget frozen dataclass with defaults
    target = HandshakeTarget(
        url="wss://echo.example.com/ws",
        headers={"Authorization": "Bearer token123", "X-Custom": "HeaderVal"},
        subprotocols=("graphql-ws", "chat"),
    )
    assert target.url == "wss://echo.example.com/ws"
    assert target.headers["Authorization"] == "Bearer token123"
    assert target.subprotocols == ("graphql-ws", "chat")
    assert target.max_incoming_message_bytes == 16 * 1024 * 1024
    assert target.verify_tls is True

    with pytest.raises((AttributeError, TypeError)):
        # Immutability check
        target.url = "wss://mutated.com"  # type: ignore[misc]


def test_websocket_transport_and_listener_protocols():
    """Verify WebSocketTransport and WebSocketTransportListener runtime checkable protocols."""
    from pypost.core.websocket_transport_protocol import (
        HandshakeTarget,
        WebSocketTransport,
        WebSocketTransportListener,
    )

    class DummyListener:
        def on_opened(self, subprotocol: str) -> None:
            pass

        def on_text(self, message: str) -> None:
            pass

        def on_binary(self, payload: bytes) -> None:
            pass

        def on_pong(self, elapsed_ms: int, payload: bytes) -> None:
            pass

        def on_closed(self, code: int, reason: str, peer_initiated: bool) -> None:
            pass

        def on_failed(self, category: str, message: str, detail: str) -> None:
            pass

        def on_tls_errors(self, errors: tuple[str, ...]) -> bool:
            return False

    listener = DummyListener()
    assert isinstance(listener, WebSocketTransportListener)

    class IncompleteListener:
        def on_opened(self, subprotocol: str) -> None:
            pass

    assert not isinstance(IncompleteListener(), WebSocketTransportListener)

    class DummyTransport:
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
            pass

        def negotiated_subprotocol(self) -> str:
            return ""

        def set_listener(self, listener: WebSocketTransportListener) -> None:
            pass

    transport = DummyTransport()
    assert isinstance(transport, WebSocketTransport)


# =============================================================================
# 2. Session Policy & Pure State Machine
# =============================================================================


def test_websocket_session_policy_state_enum_and_configs():
    """Verify SessionState enum values and policy configuration dataclasses."""
    from pypost.core.websocket_session_policy import (
        HeartbeatConfig,
        ReconnectConfig,
        SessionState,
        StateDetail,
    )

    assert SessionState.IDLE.value == "Idle"
    assert SessionState.CONNECTING.value == "Connecting"
    assert SessionState.OPEN.value == "Open"
    assert SessionState.CLOSING.value == "Closing"
    assert SessionState.CLOSED.value == "Closed"
    assert SessionState.RECONNECTING.value == "Reconnecting"
    assert SessionState.FAILED.value == "Failed"

    detail = StateDetail(
        message="Socket error",
        error_category="handshake_rejected",
        close_code=1002,
        reason="Protocol error",
    )
    assert detail.message == "Socket error"
    assert detail.error_category == "handshake_rejected"
    assert detail.close_code == 1002
    assert detail.reason == "Protocol error"

    hb = HeartbeatConfig()
    assert hb.interval_seconds == 30.0
    assert hb.timeout_seconds == 10.0
    assert hb.ping_payload == b""

    rc = ReconnectConfig()
    assert rc.enabled is False
    assert rc.initial_delay_seconds == 1.0
    assert rc.multiplier == 2.0
    assert rc.max_delay_seconds == 60.0
    assert rc.max_attempts == 5
    assert rc.jitter is True


def test_websocket_session_policy_transition_rules():
    """Verify valid and invalid state transitions in WebSocketSessionPolicy."""
    from pypost.core.websocket_session_policy import (
        SessionState,
        WebSocketSessionPolicy,
    )

    policy = WebSocketSessionPolicy()

    # Valid transitions
    assert policy.can_transition(SessionState.IDLE, SessionState.CONNECTING) is True
    assert policy.can_transition(SessionState.CONNECTING, SessionState.OPEN) is True
    assert policy.can_transition(SessionState.CONNECTING, SessionState.FAILED) is True
    assert policy.can_transition(SessionState.CONNECTING, SessionState.IDLE) is True
    assert policy.can_transition(SessionState.OPEN, SessionState.CLOSING) is True
    assert policy.can_transition(SessionState.OPEN, SessionState.CLOSED) is True
    assert policy.can_transition(SessionState.OPEN, SessionState.RECONNECTING) is True
    assert policy.can_transition(SessionState.OPEN, SessionState.FAILED) is True
    assert policy.can_transition(SessionState.CLOSING, SessionState.CLOSED) is True
    assert policy.can_transition(SessionState.RECONNECTING, SessionState.OPEN) is True
    assert policy.can_transition(SessionState.RECONNECTING, SessionState.RECONNECTING) is True
    assert policy.can_transition(SessionState.RECONNECTING, SessionState.FAILED) is True
    assert policy.can_transition(SessionState.RECONNECTING, SessionState.IDLE) is True
    assert policy.can_transition(SessionState.FAILED, SessionState.CONNECTING) is True
    assert policy.can_transition(SessionState.CLOSED, SessionState.CONNECTING) is True

    # Invalid transitions
    assert policy.can_transition(SessionState.IDLE, SessionState.OPEN) is False
    assert policy.can_transition(SessionState.IDLE, SessionState.CLOSING) is False
    assert policy.can_transition(SessionState.CLOSED, SessionState.OPEN) is False
    assert policy.can_transition(SessionState.FAILED, SessionState.OPEN) is False
    assert policy.can_transition(SessionState.CLOSING, SessionState.OPEN) is False


def test_websocket_session_policy_backoff_and_reconnect_evaluation():
    """Verify backoff calculation and reconnect decision logic in WebSocketSessionPolicy."""
    from pypost.core.websocket_session_policy import (
        ReconnectConfig,
        WebSocketSessionPolicy,
    )

    policy = WebSocketSessionPolicy()

    # Backoff calculation with jitter disabled
    cfg = ReconnectConfig(
        enabled=True,
        initial_delay_seconds=1.0,
        multiplier=2.0,
        max_delay_seconds=10.0,
        max_attempts=3,
        jitter=False,
    )
    assert policy.calculate_backoff_delay(attempt=1, config=cfg) == 1.0
    assert policy.calculate_backoff_delay(attempt=2, config=cfg) == 2.0
    assert policy.calculate_backoff_delay(attempt=3, config=cfg) == 4.0
    assert policy.calculate_backoff_delay(attempt=4, config=cfg) == 8.0
    # Clamped at max_delay_seconds
    assert policy.calculate_backoff_delay(attempt=5, config=cfg) == 10.0

    # Backoff with jitter enabled stays within expected bounds [0.75, 1.25] of base
    cfg_jitter = ReconnectConfig(
        enabled=True,
        initial_delay_seconds=2.0,
        multiplier=2.0,
        max_delay_seconds=30.0,
        max_attempts=5,
        jitter=True,
    )
    delay_1 = policy.calculate_backoff_delay(attempt=1, config=cfg_jitter)
    assert 1.0 <= delay_1 <= 3.0

    # Reconnect evaluation: unexpected drop (code 1006) when enabled
    assert policy.should_reconnect(
        close_code=1006, peer_initiated=True, config=cfg, attempts_made=0
    ) is True
    assert policy.should_reconnect(
        close_code=1006, peer_initiated=True, config=cfg, attempts_made=2
    ) is True
    # Reconnect exhausted: attempts_made >= max_attempts
    assert policy.should_reconnect(
        close_code=1006, peer_initiated=True, config=cfg, attempts_made=3
    ) is False

    # Normal close (1000) does not trigger reconnection
    assert policy.should_reconnect(
        close_code=1000, peer_initiated=True, config=cfg, attempts_made=0
    ) is False
    assert policy.should_reconnect(
        close_code=1000, peer_initiated=False, config=cfg, attempts_made=0
    ) is False

    # Disabled config never reconnects
    cfg_disabled = ReconnectConfig(enabled=False)
    assert policy.should_reconnect(
        close_code=1006, peer_initiated=True, config=cfg_disabled, attempts_made=0
    ) is False


# =============================================================================
# 3. Qt Transport Adapter Conformance
# =============================================================================


def test_qt_websocket_transport_implements_protocol(qapp):
    """Verify QtWebSocketTransport implements WebSocketTransport protocol."""
    from pypost.core.qt.websocket_transport import QtWebSocketTransport
    from pypost.core.websocket_transport_protocol import WebSocketTransport

    adapter = QtWebSocketTransport()
    assert isinstance(adapter, WebSocketTransport)
    assert hasattr(adapter, "open")
    assert hasattr(adapter, "send_text")
    assert hasattr(adapter, "send_binary")
    assert hasattr(adapter, "ping")
    assert hasattr(adapter, "close")
    assert hasattr(adapter, "abort")
    assert hasattr(adapter, "negotiated_subprotocol")
    assert hasattr(adapter, "set_listener")


# =============================================================================
# 4. Qt Session Controller Lifecycle, Signals, & Coordination
# =============================================================================


def test_websocket_session_controller_signal_surface(qapp):
    """Verify Qt signal signatures and initialization state of WebSocketSessionController."""
    from pypost.core.qt.websocket_session import WebSocketSessionController
    from pypost.core.websocket_session_policy import SessionState

    controller = WebSocketSessionController()

    # Initial state
    assert controller.state == SessionState.IDLE

    # Signal existence
    assert hasattr(controller, "state_changed")
    assert hasattr(controller, "frame_received")
    assert hasattr(controller, "frame_sent")
    assert hasattr(controller, "lifecycle_event")
    assert hasattr(controller, "reconnect_scheduled")
    assert hasattr(controller, "subprotocol_negotiated")
    assert hasattr(controller, "session_failed")
    assert hasattr(controller, "tls_errors_raised")


def test_websocket_session_controller_lifecycle_with_mock_transport(qapp):
    """Verify state transitions, frame emission, and signals via mock transport."""
    from pypost.core.qt.websocket_session import WebSocketSessionController
    from pypost.core.websocket_session_policy import (
        HeartbeatConfig,
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

    # Track signals emitted by controller
    state_changes: list[tuple[str, object]] = []
    frames_sent: list[RawFrame] = []
    frames_received: list[RawFrame] = []
    lifecycle_events: list[tuple[str, str]] = []
    subprotocols: list[str] = []
    failures: list[tuple[str, str]] = []
    reconnects: list[tuple[int, int, int]] = []

    controller = WebSocketSessionController()
    controller.state_changed.connect(lambda state, detail: state_changes.append((state, detail)))
    controller.frame_sent.connect(lambda frame: frames_sent.append(frame))
    controller.frame_received.connect(lambda frame: frames_received.append(frame))
    controller.lifecycle_event.connect(lambda evt, det: lifecycle_events.append((evt, det)))
    controller.subprotocol_negotiated.connect(lambda sub: subprotocols.append(sub))
    controller.session_failed.connect(lambda cat, msg: failures.append((cat, msg)))
    controller.reconnect_scheduled.connect(
        lambda att, max_att, delay: reconnects.append((att, max_att, delay))
    )

    # Mock transport capturing listener
    captured_listener: Optional[WebSocketTransportListener] = None

    class MockTransport:
        def __init__(self):
            self.opened_target: Optional[HandshakeTarget] = None
            self.sent_texts: list[str] = []
            self.sent_bins: list[bytes] = []
            self.pings: list[bytes] = []
            self.closed_with: Optional[tuple[int, str]] = None
            self.aborted = False

        def open(self, target: HandshakeTarget) -> None:
            self.opened_target = target

        def send_text(self, message: str) -> None:
            self.sent_texts.append(message)

        def send_binary(self, payload: bytes) -> None:
            self.sent_bins.append(payload)

        def ping(self, payload: bytes = b"") -> None:
            self.pings.append(payload)

        def close(self, code: int = 1000, reason: str = "") -> None:
            self.closed_with = (code, reason)

        def abort(self) -> None:
            self.aborted = True

        def negotiated_subprotocol(self) -> str:
            return "chat-v1"

        def set_listener(self, listener: WebSocketTransportListener) -> None:
            nonlocal captured_listener
            captured_listener = listener

    mock_transport = MockTransport()
    controller.set_transport_factory(lambda: mock_transport)

    target = HandshakeTarget(
        url="wss://example.com/ws",
        headers={"X-Test": "1"},
        subprotocols=("chat-v1",),
    )

    # 1. Open -> Connecting
    controller.open(
        target=target,
        heartbeat=HeartbeatConfig(interval_seconds=60.0, timeout_seconds=5.0),
        reconnect=ReconnectConfig(enabled=True, max_attempts=3),
    )
    assert controller.state == SessionState.CONNECTING
    assert state_changes[-1][0] == SessionState.CONNECTING.value
    assert mock_transport.opened_target == target
    assert captured_listener is not None

    # 2. Transport handshake success -> Open
    captured_listener.on_opened("chat-v1")
    assert controller.state == SessionState.OPEN
    assert state_changes[-1][0] == SessionState.OPEN.value
    assert subprotocols[-1] == "chat-v1"

    # 3. Send and Receive Text Frame
    controller.send_text("Ping message")
    assert mock_transport.sent_texts == ["Ping message"]
    assert len(frames_sent) == 1
    assert frames_sent[-1].direction == FrameDirection.OUT
    assert frames_sent[-1].payload_format == FrameType.TEXT
    assert frames_sent[-1].payload == "Ping message"

    captured_listener.on_text("Pong reply")
    assert len(frames_received) == 1
    assert frames_received[-1].direction == FrameDirection.IN
    assert frames_received[-1].payload_format == FrameType.TEXT
    assert frames_received[-1].payload == "Pong reply"

    # 4. Send and Receive Binary Frame
    controller.send_binary(b"\x00\x01\x02")
    assert mock_transport.sent_bins == [b"\x00\x01\x02"]
    assert len(frames_sent) == 2
    assert frames_sent[-1].direction == FrameDirection.OUT
    assert frames_sent[-1].payload_format == FrameType.BINARY
    assert frames_sent[-1].payload == b"\x00\x01\x02"

    captured_listener.on_binary(b"\x03\x04\x05")
    assert len(frames_received) == 2
    assert frames_received[-1].direction == FrameDirection.IN
    assert frames_received[-1].payload_format == FrameType.BINARY
    assert frames_received[-1].payload == b"\x03\x04\x05"

    # 5. Clean close
    controller.close(code=1000, reason="Normal Shutdown")
    assert controller.state == SessionState.CLOSING
    assert mock_transport.closed_with == (1000, "Normal Shutdown")

    captured_listener.on_closed(1000, "Normal Shutdown", peer_initiated=False)
    assert controller.state == SessionState.CLOSED
    assert state_changes[-1][0] == SessionState.CLOSED.value
    assert lifecycle_events[-1][0] == "closed"


def test_websocket_session_controller_heartbeat_timeout(qapp):
    """Verify heartbeat timeout triggers abort and transitions session to Failed."""
    from pypost.core.qt.websocket_session import WebSocketSessionController
    from pypost.core.websocket_session_policy import (
        HeartbeatConfig,
        SessionState,
    )
    from pypost.core.websocket_transport_protocol import (
        HandshakeTarget,
        WebSocketTransportListener,
    )

    listener_ref: list[WebSocketTransportListener] = []

    class MockTransport:
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

    mock_transport = MockTransport()
    controller = WebSocketSessionController()
    controller.set_transport_factory(lambda: mock_transport)

    failures: list[tuple[str, str]] = []
    controller.session_failed.connect(lambda cat, msg: failures.append((cat, msg)))

    # Short heartbeat interval and timeout
    controller.open(
        target=HandshakeTarget(url="wss://test.local/ws", headers={}),
        heartbeat=HeartbeatConfig(interval_seconds=0.05, timeout_seconds=0.05),
    )
    listener_ref[0].on_opened("")
    assert controller.state == SessionState.OPEN

    # Trigger heartbeat ping check directly or via timeout
    controller._on_heartbeat_timeout()

    assert mock_transport.aborted is True
    assert controller.state == SessionState.FAILED
    assert len(failures) == 1
    assert failures[0][0] == "heartbeat_timeout"
