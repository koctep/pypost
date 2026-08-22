"""Headless WebSocket session presenter and coordinator (PYPOST-1132 / WS-4).

Coordinates a single WebSocket tab session, manages frame ingestion with secret masking,
runs the 33ms batch flush timer, enforces parameter locking during active sessions,
and handles Connect/Disconnect/Send user actions.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from PySide6.QtCore import QObject, QTimer, Signal

from pypost.core.qt.websocket_session import WebSocketSessionController
from pypost.core.websocket_session_policy import (
    HeartbeatConfig,
    ReconnectConfig,
    SessionState,
    StateDetail,
)
from pypost.core.websocket_stream import build_stream_entry
from pypost.core.websocket_transport_protocol import HandshakeTarget
from pypost.models.websocket import WebSocketConnection
from pypost.ui.widgets.websocket.state_badge import STATE_GLYPHS
from pypost.ui.widgets.websocket.stream_model import StreamListModel

if TYPE_CHECKING:
    from pypost.ui.widgets.websocket.websocket_tab import WebSocketTab

logger = logging.getLogger(__name__)

__all__ = ["WebSocketPresenter"]


class WebSocketPresenter(QObject):
    """Coordinates lifecycle, state sync, secret masking, and ingestion for a WebSocket tab."""

    tab_title_changed = Signal(str, str)  # (glyph, title)
    connection_saved = Signal(object)     # WebSocketConnection

    def __init__(
        self,
        connection: WebSocketConnection,
        session_controller: Optional[WebSocketSessionController] = None,
        stream_model: Optional[StreamListModel] = None,
        env_vars: Optional[dict[str, str]] = None,
        hidden_keys: Optional[set[str]] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.connection: WebSocketConnection = connection
        self._session_controller: WebSocketSessionController = (
            session_controller
            if session_controller is not None
            else WebSocketSessionController(self)
        )
        self._stream_model: StreamListModel = (
            stream_model if stream_model is not None else StreamListModel(parent=self)
        )
        self._env_vars: dict[str, str] = dict(env_vars) if env_vars is not None else {}
        self._hidden_keys: set[str] = set(hidden_keys) if hidden_keys is not None else set()
        self._tab: Optional[WebSocketTab] = None
        self._current_state: SessionState = self._session_controller.state

        self._pending_entries: list = []
        self._next_seq: int = 1
        self._truncate_bytes: int = 262_144

        self._flush_timer = QTimer(self)
        self._flush_timer.setSingleShot(True)
        self._flush_timer.timeout.connect(self._on_flush_timer)

        self._wire_controller_signals()

    @property
    def state(self) -> SessionState:
        """Current session lifecycle state."""
        return self._current_state

    @property
    def stream_model(self) -> StreamListModel:
        """Return the backing StreamListModel."""
        return self._stream_model

    @property
    def session_controller(self) -> WebSocketSessionController:
        """Return the underlying WebSocketSessionController."""
        return self._session_controller

    def set_tab(self, tab: WebSocketTab) -> None:
        """Bind the UI tab widget to this presenter."""
        self._tab = tab
        tab.connect_btn.clicked.connect(self._on_connect_clicked)
        tab.send_btn.clicked.connect(self.handle_send_message)
        self._sync_ui_state(self.state, None)

    def _wire_controller_signals(self) -> None:
        self._session_controller.state_changed.connect(self._on_state_changed)
        self._session_controller.frame_received.connect(self._on_frame_received)
        self._session_controller.frame_sent.connect(self._on_frame_sent)
        self._session_controller.lifecycle_event.connect(self._on_lifecycle_event)
        self._session_controller.subprotocol_negotiated.connect(self._on_subprotocol_negotiated)
        self._session_controller.session_failed.connect(self._on_session_failed)

    def handle_connect(self) -> None:
        """Initiate connection to target endpoint."""
        if self.state in (SessionState.CONNECTING, SessionState.RECONNECTING, SessionState.OPEN):
            self.handle_disconnect()
            return

        if self._tab is not None:
            target = self._tab.connection_editor.get_target()
            self._tab.connection_editor.set_read_only(True)
        else:
            target = HandshakeTarget(
                url=self.connection.url or "",
                headers=self.connection.headers or {},
                subprotocols=tuple(self.connection.subprotocols or []),
            )

        heartbeat = (
            HeartbeatConfig(
                interval_seconds=float(self.connection.heartbeat.interval_seconds)
                if self.connection.heartbeat.enabled
                else 0.0,
                timeout_seconds=float(self.connection.heartbeat.timeout_seconds),
            )
            if hasattr(self.connection, "heartbeat") and self.connection.heartbeat is not None
            else None
        )
        reconnect = (
            ReconnectConfig(
                enabled=self.connection.reconnect.enabled,
                max_attempts=self.connection.reconnect.max_attempts,
                initial_delay_seconds=float(self.connection.reconnect.initial_delay_seconds),
                multiplier=float(self.connection.reconnect.backoff_multiplier),
                max_delay_seconds=float(self.connection.reconnect.max_delay_seconds),
            )
            if hasattr(self.connection, "reconnect") and self.connection.reconnect is not None
            else None
        )

        logger.info("websocket_connect_initiated url=%s", target.url)
        self._session_controller.open(target, heartbeat=heartbeat, reconnect=reconnect)

    def handle_disconnect(self) -> None:
        """Disconnect or cancel the active session."""
        logger.info("websocket_disconnect_initiated")
        self._session_controller.close(1000, "user requested disconnect")

    def _on_connect_clicked(self) -> None:
        if self.state in (SessionState.CONNECTING, SessionState.RECONNECTING, SessionState.OPEN):
            self.handle_disconnect()
        else:
            self.handle_connect()

    def handle_send_message(self) -> None:
        """Transmit the text in the message composer over the active connection."""
        if self.state != SessionState.OPEN:
            logger.warning("websocket_send_blocked_not_open state=%s", self.state.value)
            return

        if self._tab is not None:
            text = self._tab.composer_edit.toPlainText()
            if text:
                logger.debug("websocket_sending_message length=%d", len(text))
                self._session_controller.send_text(text)
                self._tab.composer_edit.setPlainText("")

    def set_variables(self, variables: dict[str, str]) -> None:
        """Update active environment variables for secret masking."""
        self._env_vars = dict(variables)

    def set_hidden_keys(self, hidden_keys: set[str]) -> None:
        """Update active hidden keys for secret masking."""
        self._hidden_keys = set(hidden_keys)

    def _on_state_changed(self, state_val: str, detail: Any = None) -> None:
        try:
            state = SessionState(state_val)
        except ValueError:
            state = SessionState.IDLE
        self._current_state = state
        self._sync_ui_state(state, detail)

    def _sync_ui_state(self, state: SessionState, detail: Optional[StateDetail]) -> None:
        glyph = STATE_GLYPHS.get(state, "○")
        tab_name = self.connection.name if self.connection and self.connection.name else "WebSocket"
        self.tab_title_changed.emit(glyph, tab_name)

        if self._tab is None:
            return

        self._tab.state_badge.set_state(state, detail)

        is_active = state not in (SessionState.IDLE, SessionState.FAILED, SessionState.CLOSED)
        self._tab.connection_editor.set_read_only(is_active)

        if state in (SessionState.IDLE, SessionState.FAILED, SessionState.CLOSED):
            self._tab.connect_btn.setText("Connect")
            self._tab.connect_btn.setEnabled(True)
            self._tab.send_btn.setEnabled(False)
        elif state in (SessionState.CONNECTING, SessionState.RECONNECTING):
            self._tab.connect_btn.setText("Cancel")
            self._tab.connect_btn.setEnabled(True)
            self._tab.send_btn.setEnabled(False)
        elif state == SessionState.OPEN:
            self._tab.connect_btn.setText("Disconnect")
            self._tab.connect_btn.setEnabled(True)
            self._tab.send_btn.setEnabled(True)
        elif state == SessionState.CLOSING:
            self._tab.connect_btn.setText("Closing...")
            self._tab.connect_btn.setEnabled(False)
            self._tab.send_btn.setEnabled(False)

    def _on_subprotocol_negotiated(self, subprotocol: str) -> None:
        if self._tab is not None:
            self._tab.state_badge.set_metrics(subprotocol=subprotocol)

    def _on_frame_sent(self, frame: Any) -> None:
        entry = build_stream_entry(
            frame,
            env_vars=self._env_vars,
            hidden_keys=self._hidden_keys,
            truncate_bytes=self._truncate_bytes,
            seq=self._next_seq,
            kind="message",
            direction="out",
        )
        self._next_seq += 1
        self._pending_entries.append(entry)
        if not self._flush_timer.isActive():
            self._flush_timer.start(33)

    def _on_frame_received(self, frame: Any) -> None:
        entry = build_stream_entry(
            frame,
            env_vars=self._env_vars,
            hidden_keys=self._hidden_keys,
            truncate_bytes=self._truncate_bytes,
            seq=self._next_seq,
            kind="message",
            direction="in",
        )
        self._next_seq += 1
        self._pending_entries.append(entry)
        if not self._flush_timer.isActive():
            self._flush_timer.start(33)

    def _on_lifecycle_event(self, event_type: str, detail: str) -> None:
        entry = build_stream_entry(
            None,
            env_vars=self._env_vars,
            hidden_keys=self._hidden_keys,
            truncate_bytes=self._truncate_bytes,
            seq=self._next_seq,
            kind="lifecycle",
            direction="none",
            payload=f"[{event_type.upper()}] {detail}".strip(),
            detail=detail,
        )
        self._next_seq += 1
        self._pending_entries.append(entry)
        if not self._flush_timer.isActive():
            self._flush_timer.start(33)

    def _on_session_failed(self, category: str, message: str) -> None:
        entry = build_stream_entry(
            None,
            env_vars=self._env_vars,
            hidden_keys=self._hidden_keys,
            truncate_bytes=self._truncate_bytes,
            seq=self._next_seq,
            kind="lifecycle",
            direction="none",
            payload=f"[FAILED] ({category}) {message}".strip(),
            detail=message,
        )
        self._next_seq += 1
        self._pending_entries.append(entry)
        if not self._flush_timer.isActive():
            self._flush_timer.start(33)

    def _on_flush_timer(self) -> None:
        if not self._pending_entries:
            return
        batch = list(self._pending_entries)
        self._pending_entries.clear()
        self._stream_model.append_batch(batch)

    def teardown(self) -> None:
        """Teardown session controller and timer resources."""
        logger.info("websocket_presenter_teardown")
        self._flush_timer.stop()
        self._on_flush_timer()
        self._session_controller.close(1000, "tab closed")
        self._session_controller.abort()
