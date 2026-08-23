"""Dedicated short-lived QThread runner for bounded MCP WebSocket probes.

PYPOST-1137 / WS-9 — Executes a single bounded probe on a Qt event loop, with
hard-deadline timer, SessionSlots concurrency control, and guaranteed termination.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
import time
from typing import Optional
import uuid

from PySide6.QtCore import QEventLoop, QObject, QThread, QTimer

from pypost.core.qt.websocket_transport import QtWebSocketTransport
from pypost.core.websocket_probe import (
    ProbeEvent,
    ProbeOutcome,
    WebSocketProbeConfig,
    WebSocketProbeResult,
    WebSocketProbeStopCondition,
)
from pypost.core.websocket_session_policy import get_session_slots
from pypost.core.websocket_transport_protocol import (
    TlsCertificateError,
    WebSocketTransportListener,
)

logger = logging.getLogger(__name__)

_DEADLINE_GRACE_MS = 1000  # extra ms beyond max_duration_ms before hard abort


class _ProbeTransportListener(WebSocketTransportListener):
    """Internal listener bridging QtWebSocketTransport events to the probe runner."""

    def __init__(
        self,
        config: WebSocketProbeConfig,
        transport: QtWebSocketTransport,
        loop: QEventLoop,
        events: list[ProbeEvent],
    ) -> None:
        self.config = config
        self.transport = transport
        self.loop = loop
        self.events = events
        self.stop_evaluator = WebSocketProbeStopCondition(
            max_messages=config.max_messages,
            stop_when=config.stop_when,
        )
        self.received_count = 0
        self.outcome = ProbeOutcome.SUCCESS
        self.close_code: Optional[int] = None
        self.close_reason: Optional[str] = None
        self.error_msg: Optional[str] = None
        self._intake_stopped = False

    def _log_event(
        self,
        direction: str,
        payload: str,
        is_binary: bool = False,
        size: int = 0,
    ) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        self.events.append(ProbeEvent(ts, direction, payload, is_binary, size))

    def on_opened(self, subprotocol: str) -> None:
        logger.debug(
            "websocket_probe_opened probe_id=%s subprotocol=%s",
            self.config.probe_id,
            subprotocol or "none",
        )
        self._log_event("connect", f"Connected to {self.config.target.url}")
        if self.config.initial_payload:
            payload_bytes = len(self.config.initial_payload.encode("utf-8"))
            logger.debug(
                "websocket_probe_initial_payload_sent probe_id=%s bytes=%d",
                self.config.probe_id,
                payload_bytes,
            )
            self.transport.send_text(self.config.initial_payload)
            self._log_event("sent", self.config.initial_payload)

    def on_text(self, message: str) -> None:
        if self._intake_stopped:
            return
        self.received_count += 1
        msg_bytes = len(message.encode("utf-8"))
        logger.debug(
            "websocket_probe_frame_received probe_id=%s kind=text bytes=%d count=%d",
            self.config.probe_id,
            msg_bytes,
            self.received_count,
        )
        self._log_event("received", message, size=msg_bytes)
        should_stop, stop_outcome = self.stop_evaluator.should_stop(message)
        if should_stop:
            self._intake_stopped = True
            self.outcome = stop_outcome or ProbeOutcome.LIMIT_REACHED
            logger.info(
                "websocket_probe_stop_condition_triggered probe_id=%s outcome=%s messages_count=%d",
                self.config.probe_id,
                self.outcome.value,
                self.received_count,
            )
            self.transport.close(1000, "probe complete")

    def on_binary(self, payload: bytes) -> None:
        if self._intake_stopped:
            return
        self.received_count += 1
        msg_bytes = len(payload)
        logger.debug(
            "websocket_probe_frame_received probe_id=%s kind=binary bytes=%d count=%d",
            self.config.probe_id,
            msg_bytes,
            self.received_count,
        )
        self._log_event(
            "received",
            f"<binary frame {msg_bytes} bytes>",
            is_binary=True,
            size=msg_bytes,
        )
        should_stop, stop_outcome = self.stop_evaluator.should_stop("")
        if should_stop:
            self._intake_stopped = True
            self.outcome = stop_outcome or ProbeOutcome.LIMIT_REACHED
            logger.info(
                "websocket_probe_stop_condition_triggered probe_id=%s outcome=%s messages_count=%d",
                self.config.probe_id,
                self.outcome.value,
                self.received_count,
            )
            self.transport.close(1000, "probe complete")

    def on_pong(self, elapsed_ms: int, payload: bytes) -> None:
        pass

    def on_closed(self, code: int, reason: str, peer_initiated: bool) -> None:
        self.close_code = code
        self.close_reason = reason
        logger.debug(
            "websocket_probe_closed probe_id=%s code=%d reason=%s peer_initiated=%s",
            self.config.probe_id,
            code,
            reason,
            peer_initiated,
        )
        self._log_event("closed", f"Code: {code}, Reason: {reason}")
        if self.loop.isRunning():
            self.loop.quit()

    def on_failed(self, category: str, message: str, detail: str) -> None:
        self.outcome = ProbeOutcome.ERROR
        self.error_msg = message
        logger.warning(
            "websocket_probe_failed probe_id=%s category=%s message=%s",
            self.config.probe_id,
            category,
            message,
        )
        self._log_event("error", f"Socket error: {message}")
        if self.loop.isRunning():
            self.loop.quit()

    def on_tls_errors(self, errors: tuple[TlsCertificateError, ...]) -> bool:
        self.outcome = ProbeOutcome.ERROR
        self.error_msg = "; ".join(e.message for e in errors) or "TLS error"
        logger.warning(
            "websocket_probe_tls_errors probe_id=%s error=%s",
            self.config.probe_id,
            self.error_msg,
        )
        self._log_event("error", f"TLS error: {self.error_msg}")
        if self.loop.isRunning():
            self.loop.quit()
        return False


class WebSocketProbeRunner(QThread):
    """Executes a bounded WebSocket probe on a short-lived thread with a dedicated Qt event loop.

    The runner acquires a ``SessionSlots`` concurrency token before attempting any
    network activity, and always releases it — even on error or hard-deadline abort.
    A hard-deadline ``QTimer`` fires ``_DEADLINE_GRACE_MS`` after ``max_duration_ms``
    to abort the socket and exit the loop unconditionally.
    """

    def __init__(
        self,
        config: WebSocketProbeConfig,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.result: WebSocketProbeResult | None = None
        self._session_id = config.probe_id or str(uuid.uuid4())

    def run(self) -> None:
        """Entry point executed on the QThread.

        Acquires a session slot, opens the WebSocket, runs the event loop to
        completion (or hard deadline), and stores the result in ``self.result``.
        """
        logger.info(
            "websocket_probe_started probe_id=%s max_messages=%d max_duration_ms=%d "
            "has_stop_when=%s has_initial_payload=%s",
            self._session_id,
            self.config.max_messages,
            self.config.max_duration_ms,
            bool(self.config.stop_when),
            bool(self.config.initial_payload),
        )
        slots = get_session_slots()
        slot_res = slots.acquire(self._session_id)
        if not slot_res.allowed:
            logger.warning(
                "websocket_probe_refused probe_id=%s active_count=%d limit=%d reason=%s",
                self._session_id,
                slot_res.active_count,
                slot_res.limit,
                slot_res.reason,
            )
            self.result = WebSocketProbeResult(
                outcome=ProbeOutcome.REFUSED,
                messages_received=0,
                duration_ms=0.0,
                error_message=(
                    f"WebSocket probe refused: session limit reached "
                    f"({slot_res.active_count}/{slot_res.limit})."
                ),
            )
            return

        events: list[ProbeEvent] = []
        started_perf = time.perf_counter()

        loop = QEventLoop()
        transport = QtWebSocketTransport()
        listener = _ProbeTransportListener(
            config=self.config,
            transport=transport,
            loop=loop,
            events=events,
        )
        transport.set_listener(listener)

        deadline_timer = QTimer()
        deadline_timer.setSingleShot(True)

        def _on_deadline() -> None:
            listener.outcome = ProbeOutcome.TIMEOUT
            logger.warning(
                "websocket_probe_timeout probe_id=%s max_duration_ms=%d",
                self._session_id,
                self.config.max_duration_ms,
            )
            listener._log_event(
                "timeout",
                f"Probe reached hard deadline of {self.config.max_duration_ms}ms",
            )
            transport.abort()
            if loop.isRunning():
                loop.quit()

        deadline_timer.timeout.connect(_on_deadline)

        try:
            deadline_timer.start(self.config.max_duration_ms + _DEADLINE_GRACE_MS)
            transport.open(self.config.target)
            loop.exec()
        finally:
            deadline_timer.stop()
            transport.abort()
            slots.release(self._session_id)
            duration_ms = (time.perf_counter() - started_perf) * 1000.0
            self.result = WebSocketProbeResult(
                outcome=listener.outcome,
                messages_received=listener.received_count,
                duration_ms=duration_ms,
                events=events,
                close_code=listener.close_code,
                close_reason=listener.close_reason,
                error_message=listener.error_msg,
            )
            logger.info(
                "websocket_probe_finished probe_id=%s outcome=%s duration_ms=%.1f "
                "messages_received=%d slot_released=true",
                self._session_id,
                self.result.outcome.value,
                self.result.duration_ms,
                self.result.messages_received,
            )
