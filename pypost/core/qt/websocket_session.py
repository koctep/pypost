"""Headless WebSocket session controller and coordinator using Qt signals and timers."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Callable, Optional

from PySide6.QtCore import QObject, QTimer, Signal

from pypost.core.qt.websocket_transport import QtWebSocketTransport
from pypost.core.websocket_security_policy import (
    TlsCertificateError,
    classify_endpoint_security,
)
from pypost.core.websocket_session_policy import (
    HeartbeatConfig,
    ReconnectConfig,
    SessionState,
    StateDetail,
    WebSocketSessionPolicy,
)
from pypost.core.websocket_transport_protocol import (
    FrameDirection,
    FrameType,
    HandshakeTarget,
    RawFrame,
    WebSocketTransport,
)

logger = logging.getLogger(__name__)


class WebSocketSessionController(QObject):
    """Headless coordinator managing WebSocket transport lifecycle, state, and signals."""

    state_changed = Signal(str, object)
    security_classification_changed = Signal(str)
    frame_received = Signal(object)
    frame_sent = Signal(object)
    lifecycle_event = Signal(str, str)
    reconnect_scheduled = Signal(int, int, int)
    subprotocol_negotiated = Signal(str)
    session_failed = Signal(str, str)
    tls_errors_raised = Signal(object)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._state: SessionState = SessionState.IDLE
        self._policy = WebSocketSessionPolicy()
        self._target: Optional[HandshakeTarget] = None
        self._ephemeral_trust_granted: bool = False
        self._heartbeat_config: HeartbeatConfig = HeartbeatConfig()
        self._reconnect_config: ReconnectConfig = ReconnectConfig()
        self._reconnect_attempts_made: int = 0
        self._transport: Optional[WebSocketTransport] = None
        self._transport_factory: Callable[[], WebSocketTransport] = (
            lambda: QtWebSocketTransport(parent=self)
        )

        self._heartbeat_interval_timer = QTimer(self)
        self._heartbeat_interval_timer.timeout.connect(self._on_heartbeat_interval)

        self._heartbeat_timeout_timer = QTimer(self)
        self._heartbeat_timeout_timer.setSingleShot(True)
        self._heartbeat_timeout_timer.timeout.connect(self._on_heartbeat_timeout)

        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setSingleShot(True)
        self._reconnect_timer.timeout.connect(self._on_reconnect_timer)

    @property
    def state(self) -> SessionState:
        """Current session lifecycle state."""
        return self._state

    def grant_ephemeral_tls_exception(self) -> None:
        """Grant in-memory ephemeral TLS verification bypass for active/next connection."""
        logger.warning(
            "websocket_ephemeral_tls_exception_granted session_state=%s",
            self._state.value,
        )
        self._ephemeral_trust_granted = True

    def has_ephemeral_tls_exception(self) -> bool:
        """Return True if ephemeral TLS exception is active in memory."""
        return self._ephemeral_trust_granted

    def revoke_ephemeral_tls_exception(self) -> None:
        """Revoke active ephemeral TLS exception."""
        logger.info(
            "websocket_ephemeral_tls_exception_revoked session_state=%s",
            self._state.value,
        )
        self._ephemeral_trust_granted = False

    def set_transport_factory(self, factory: Callable[[], WebSocketTransport]) -> None:
        """Override transport instantiation factory (useful for tests and mock adapters)."""
        self._transport_factory = factory

    def open(
        self,
        target: HandshakeTarget,
        heartbeat: Optional[HeartbeatConfig] = None,
        reconnect: Optional[ReconnectConfig] = None,
    ) -> None:
        """Initiate connection handshake to target endpoint."""
        if self._ephemeral_trust_granted and target.url.lower().startswith("wss://"):
            effective_target = HandshakeTarget(
                url=target.url,
                headers=target.headers,
                subprotocols=target.subprotocols,
                max_incoming_message_bytes=target.max_incoming_message_bytes,
                verify_tls=False,
            )
        else:
            effective_target = target

        self._target = effective_target
        if heartbeat is not None:
            self._heartbeat_config = heartbeat
        if reconnect is not None:
            self._reconnect_config = reconnect
        self._reconnect_attempts_made = 0

        classification = classify_endpoint_security(
            effective_target.url,
            verify_tls=effective_target.verify_tls,
        )
        self.security_classification_changed.emit(classification.value)

        logger.info(
            "Opening WebSocket session to %s (verify_tls=%s, security=%s, "
            "heartbeat=%.1fs, reconnect=%s, ephemeral_trust=%s)",
            effective_target.url,
            effective_target.verify_tls,
            classification.value,
            self._heartbeat_config.interval_seconds,
            self._reconnect_config.enabled,
            self._ephemeral_trust_granted,
        )

        self._stop_all_timers()
        if self._transport is not None:
            self._transport.abort()
            self._transport = None

        self._transition_to(
            SessionState.CONNECTING,
            StateDetail(message=f"Connecting to {effective_target.url}"),
        )

        self._transport = self._transport_factory()
        self._transport.set_listener(self)
        self._transport.open(effective_target)

    def send_text(self, message: str) -> None:
        """Send UTF-8 text message frame and emit frame_sent."""
        if self._transport is not None and self._state == SessionState.OPEN:
            byte_size = len(message.encode("utf-8"))
            logger.debug("Sending WebSocket text frame (%d bytes)", byte_size)
            self._transport.send_text(message)
            frame = RawFrame(
                direction=FrameDirection.OUT,
                payload_format=FrameType.TEXT,
                payload=message,
                byte_size=byte_size,
                timestamp=datetime.now(timezone.utc),
            )
            self.frame_sent.emit(frame)

    def send_binary(self, payload: bytes) -> None:
        """Send raw binary frame and emit frame_sent."""
        if self._transport is not None and self._state == SessionState.OPEN:
            byte_size = len(payload)
            logger.debug("Sending WebSocket binary frame (%d bytes)", byte_size)
            self._transport.send_binary(payload)
            frame = RawFrame(
                direction=FrameDirection.OUT,
                payload_format=FrameType.BINARY,
                payload=payload,
                byte_size=byte_size,
                timestamp=datetime.now(timezone.utc),
            )
            self.frame_sent.emit(frame)

    def close(self, code: int = 1000, reason: str = "") -> None:
        """Initiate clean close handshake or terminate in-progress connect/reconnect."""
        logger.info(
            "Closing WebSocket session (code=%d, reason=%s, current_state=%s)",
            code,
            reason,
            self._state.value,
        )
        self._ephemeral_trust_granted = False
        self._stop_all_timers()

        if self._state in (SessionState.CONNECTING, SessionState.RECONNECTING):
            if self._transport is not None:
                self._transport.abort()
                self._transport = None
            detail = StateDetail(
                message="Closed by user",
                close_code=code,
                reason=reason,
            )
            self._transition_to(SessionState.CLOSED, detail)
            self.lifecycle_event.emit("closed", f"{code} {reason}".strip())
            return

        if self._state == SessionState.OPEN:
            detail = StateDetail(
                message="Closing session",
                close_code=code,
                reason=reason,
            )
            self._transition_to(SessionState.CLOSING, detail)
            if self._transport is not None:
                self._transport.close(code, reason)

    def abort(self) -> None:
        """Immediately abort transport and transition to Failed."""
        logger.warning(
            "Aborting WebSocket session immediately (current_state=%s)",
            self._state.value,
        )
        self._ephemeral_trust_granted = False
        self._stop_all_timers()
        if self._transport is not None:
            self._transport.abort()
        detail = StateDetail(
            message="Session aborted",
            error_category="aborted",
        )
        self._transition_to(SessionState.FAILED, detail)

    def on_opened(self, subprotocol: str) -> None:
        """Transport listener callback on successful handshake."""
        self._reconnect_attempts_made = 0
        logger.info(
            "WebSocket session opened successfully (subprotocol=%s)",
            subprotocol or "none",
        )
        if self._policy.can_transition(self._state, SessionState.OPEN):
            self._transition_to(SessionState.OPEN, None)
            if subprotocol:
                self.subprotocol_negotiated.emit(subprotocol)
            self._start_heartbeat()
            msg = f"Subprotocol: {subprotocol}" if subprotocol else "Connected"
            self.lifecycle_event.emit("opened", msg)

    def on_text(self, message: str) -> None:
        """Transport listener callback on incoming text frame."""
        byte_size = len(message.encode("utf-8"))
        logger.debug("Received WebSocket text frame (%d bytes)", byte_size)
        frame = RawFrame(
            direction=FrameDirection.IN,
            payload_format=FrameType.TEXT,
            payload=message,
            byte_size=byte_size,
            timestamp=datetime.now(timezone.utc),
        )
        self.frame_received.emit(frame)

    def on_binary(self, payload: bytes) -> None:
        """Transport listener callback on incoming binary frame."""
        byte_size = len(payload)
        logger.debug("Received WebSocket binary frame (%d bytes)", byte_size)
        frame = RawFrame(
            direction=FrameDirection.IN,
            payload_format=FrameType.BINARY,
            payload=payload,
            byte_size=byte_size,
            timestamp=datetime.now(timezone.utc),
        )
        self.frame_received.emit(frame)

    def on_pong(self, elapsed_ms: int, payload: bytes) -> None:
        """Transport listener callback on incoming pong frame."""
        logger.debug(
            "Received WebSocket pong (latency=%dms, payload_size=%d)",
            elapsed_ms,
            len(payload),
        )
        self._heartbeat_timeout_timer.stop()
        self.lifecycle_event.emit("pong", f"{elapsed_ms}ms latency")

    def on_closed(self, code: int, reason: str, peer_initiated: bool) -> None:
        """Transport listener callback on connection closure."""
        logger.info(
            "WebSocket connection closed (code=%d, reason=%s, peer=%s, state=%s)",
            code,
            reason,
            peer_initiated,
            self._state.value,
        )
        self._stop_heartbeat_timers()

        if (
            self._policy.should_reconnect(
                code,
                peer_initiated,
                self._reconnect_config,
                self._reconnect_attempts_made,
            )
            and self._target is not None
        ):
            self._reconnect_attempts_made += 1
            delay_s = self._policy.calculate_backoff_delay(
                self._reconnect_attempts_made,
                self._reconnect_config,
            )
            delay_ms = int(delay_s * 1000)
            logger.info(
                "Scheduling WebSocket reconnect attempt %d/%d in %.1fs",
                self._reconnect_attempts_made,
                self._reconnect_config.max_attempts,
                delay_s,
            )
            detail = StateDetail(
                message=f"Reconnecting in {delay_s:.1f}s",
                close_code=code,
                reason=reason,
            )
            self._transition_to(SessionState.RECONNECTING, detail)
            self.reconnect_scheduled.emit(
                self._reconnect_attempts_made,
                self._reconnect_config.max_attempts,
                delay_ms,
            )
            self._reconnect_timer.start(delay_ms)
            return

        if self._state == SessionState.RECONNECTING:
            logger.error(
                "WebSocket reconnection attempts exhausted (%d/%d)",
                self._reconnect_attempts_made,
                self._reconnect_config.max_attempts,
            )
            detail = StateDetail(
                message="Reconnect attempts exhausted",
                error_category="reconnect_exhausted",
            )
            self._transition_to(SessionState.FAILED, detail)
            self.session_failed.emit(
                "reconnect_exhausted",
                "Reconnect attempts exhausted",
            )
            return

        detail = StateDetail(
            message=reason or "Connection closed cleanly",
            close_code=code,
            reason=reason,
        )
        self._transition_to(SessionState.CLOSED, detail)
        self.lifecycle_event.emit("closed", f"{code} {reason}".strip())

    def on_failed(self, category: str, message: str, detail: str) -> None:
        """Transport listener callback on error or handshake rejection."""
        logger.error(
            "websocket_session_failed category=%s message=%s detail=%s",
            category,
            message,
            detail,
        )
        self._stop_all_timers()
        if self._transport is not None:
            self._transport.abort()

        state_detail = StateDetail(
            message=message,
            error_category=category,
            reason=detail,
        )
        self._transition_to(SessionState.FAILED, state_detail)
        self.session_failed.emit(category, message)

    def on_tls_errors(
        self,
        errors: tuple[TlsCertificateError, ...] | tuple[str, ...],
    ) -> bool:
        """Transport listener callback on TLS certificate errors."""
        ignored = bool(self._target and not self._target.verify_tls)
        first_err = errors[0] if errors else None
        if first_err is not None:
            if hasattr(first_err, "message"):
                summary = getattr(first_err, "message")
            else:
                summary = str(first_err)
        else:
            summary = "TLS certificate validation failed"

        logger.warning(
            "websocket_tls_errors_encountered count=%d ignored=%s summary=%s",
            len(errors),
            ignored,
            summary,
        )
        self.tls_errors_raised.emit(errors)
        if ignored:
            return True

        logger.error(
            "websocket_session_tls_validation_failed url=%s error=%s",
            self._target.url if self._target else "unknown",
            summary,
        )

        self._stop_all_timers()
        if self._transport is not None:
            self._transport.abort()

        state_detail = StateDetail(
            message=summary,
            error_category="tls_error",
            reason=str(errors),
        )
        self._transition_to(SessionState.FAILED, state_detail)
        self.session_failed.emit("tls_error", summary)
        return False

    def _transition_to(
        self,
        target: SessionState,
        detail: Optional[StateDetail],
    ) -> None:
        logger.debug(
            "WebSocket session state transition: %s -> %s (detail=%s)",
            self._state.value,
            target.value,
            detail.message if detail else "none",
        )
        self._state = target
        self.state_changed.emit(target.value, detail)

    def _start_heartbeat(self) -> None:
        if self._heartbeat_config.interval_seconds > 0:
            interval_ms = int(self._heartbeat_config.interval_seconds * 1000)
            logger.debug(
                "Starting WebSocket heartbeat timer (interval=%.1fs, timeout=%.1fs)",
                self._heartbeat_config.interval_seconds,
                self._heartbeat_config.timeout_seconds,
            )
            self._heartbeat_interval_timer.start(interval_ms)

    def _stop_heartbeat_timers(self) -> None:
        self._heartbeat_interval_timer.stop()
        self._heartbeat_timeout_timer.stop()

    def _stop_all_timers(self) -> None:
        self._stop_heartbeat_timers()
        self._reconnect_timer.stop()

    def _on_heartbeat_interval(self) -> None:
        if self._state == SessionState.OPEN and self._transport is not None:
            logger.debug(
                "WebSocket heartbeat ping triggered (payload_bytes=%d, timeout=%.1fs)",
                len(self._heartbeat_config.ping_payload),
                self._heartbeat_config.timeout_seconds,
            )
            self._transport.ping(self._heartbeat_config.ping_payload)
            timeout_ms = int(self._heartbeat_config.timeout_seconds * 1000)
            self._heartbeat_timeout_timer.start(timeout_ms)

    def _on_heartbeat_timeout(self) -> None:
        logger.warning(
            "WebSocket heartbeat timeout expired (no pong response within %.1fs)",
            self._heartbeat_config.timeout_seconds,
        )
        self._stop_all_timers()
        if self._transport is not None:
            self._transport.abort()
        detail = StateDetail(
            message="Heartbeat timeout: peer did not respond to ping",
            error_category="heartbeat_timeout",
        )
        self._transition_to(SessionState.FAILED, detail)
        self.session_failed.emit(
            "heartbeat_timeout",
            "Peer did not respond to ping within timeout window",
        )

    def _on_reconnect_timer(self) -> None:
        if self._state != SessionState.RECONNECTING or self._target is None:
            return
        logger.info(
            "Executing scheduled reconnect attempt %d/%d to %s",
            self._reconnect_attempts_made,
            self._reconnect_config.max_attempts,
            self._target.url,
        )
        if self._transport is not None:
            self._transport.abort()
            self._transport = None

        self._transport = self._transport_factory()
        self._transport.set_listener(self)
        self._transport.open(self._target)
