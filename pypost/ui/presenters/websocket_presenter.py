"""Headless WebSocket session presenter and coordinator (PYPOST-1132 / WS-4).

Coordinates a single WebSocket tab session, manages frame ingestion with secret masking,
runs the 33ms batch flush timer, enforces parameter locking during active sessions,
and handles Connect/Disconnect/Send user actions.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from PySide6.QtCore import QObject, QTimer, Signal

from pypost.core.qt.websocket_sequence_runner import WebSocketSequenceRunner
from pypost.core.qt.websocket_session import WebSocketSessionController
from pypost.core.sensitive_text_sanitizer import sanitize_text
from pypost.core.template_service import TemplateService
from pypost.core.websocket_sequence import compile_sequence_plan
from pypost.core.websocket_session_policy import (
    HeartbeatConfig,
    ReconnectConfig,
    SessionState,
    StateDetail,
)
from pypost.core.websocket_stream import build_stream_entry
from pypost.core.websocket_transport_protocol import HandshakeTarget
from pypost.models.websocket import WebSocketConnection
from pypost.ui.widgets.websocket.connection_editor import _merge_url_and_params
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
        settings: Optional[Any] = None,
        session_controller: Optional[WebSocketSessionController] = None,
        stream_model: Optional[StreamListModel] = None,
        env_vars: Optional[dict[str, str]] = None,
        hidden_keys: Optional[set[str]] = None,
        template_service: Optional[TemplateService] = None,
        metrics: Optional[Any] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.connection: WebSocketConnection = connection
        self.settings: Optional[Any] = settings
        if isinstance(session_controller, WebSocketSessionController):
            self._session_controller = session_controller
        elif isinstance(settings, WebSocketSessionController):
            self._session_controller = settings
        else:
            self._session_controller = WebSocketSessionController(self)
        self._stream_model: StreamListModel = (
            stream_model if stream_model is not None else StreamListModel(parent=self)
        )
        self._env_vars: dict[str, str] = dict(env_vars) if env_vars is not None else {}
        self._hidden_keys: set[str] = set(hidden_keys) if hidden_keys is not None else set()
        self._metrics: Optional[Any] = metrics
        self._template_service: TemplateService = (
            template_service
            if template_service is not None
            else TemplateService(metrics=metrics)
        )
        self._tab: Optional[WebSocketTab] = None
        self._current_state: SessionState = self._session_controller.state

        self._pending_entries: list = []
        self._next_seq: int = 1
        self._truncate_bytes: int = 262_144

        self._flush_timer = QTimer(self)
        self._flush_timer.setSingleShot(True)
        self._flush_timer.timeout.connect(self._on_flush_timer)

        self._sequence_runner = WebSocketSequenceRunner(self)
        self._wire_controller_signals()

    @property
    def sequence_runner(self) -> WebSocketSequenceRunner:
        """Return the backing WebSocketSequenceRunner."""
        return self._sequence_runner

    @property
    def state(self) -> SessionState:
        """Current session lifecycle state."""
        return self._current_state

    @property
    def _state(self) -> SessionState:
        return self._current_state

    @_state.setter
    def _state(self, val: SessionState) -> None:
        self._current_state = val

    @property
    def stream_model(self) -> StreamListModel:
        """Return the backing StreamListModel."""
        return self._stream_model

    @property
    def session_controller(self) -> WebSocketSessionController:
        """Return the underlying WebSocketSessionController."""
        return self._session_controller

    @property
    def _controller(self) -> WebSocketSessionController:
        return self._session_controller

    @_controller.setter
    def _controller(self, val: WebSocketSessionController) -> None:
        self._session_controller = val

    def set_tab(self, tab: WebSocketTab) -> None:
        """Bind the UI tab widget to this presenter."""
        self._tab = tab
        tab.connect_btn.clicked.connect(self._on_connect_clicked)
        self._propagate_variables_to_tab()
        self._sync_ui_state(self.state, None)

    def _propagate_variables_to_tab(self) -> None:
        if self._tab is None:
            return
        if hasattr(self._tab, "connection_editor") and self._tab.connection_editor:
            if hasattr(self._tab.connection_editor, "set_variables"):
                self._tab.connection_editor.set_variables(self._env_vars)
            if hasattr(self._tab.connection_editor, "set_hidden_keys"):
                self._tab.connection_editor.set_hidden_keys(self._hidden_keys)
        if hasattr(self._tab, "composer") and self._tab.composer:
            if hasattr(self._tab.composer, "set_variables"):
                self._tab.composer.set_variables(self._env_vars)
            if hasattr(self._tab.composer, "set_hidden_keys"):
                self._tab.composer.set_hidden_keys(self._hidden_keys)
        if hasattr(self._tab, "stream_view") and self._tab.stream_view:
            if hasattr(self._tab.stream_view, "set_variables"):
                self._tab.stream_view.set_variables(self._env_vars)
            if hasattr(self._tab.stream_view, "set_hidden_keys"):
                self._tab.stream_view.set_hidden_keys(self._hidden_keys)

    def _wire_controller_signals(self) -> None:
        self._session_controller.state_changed.connect(self._on_state_changed)
        self._session_controller.frame_received.connect(self._on_frame_received)
        self._session_controller.frame_sent.connect(self._on_frame_sent)
        self._session_controller.lifecycle_event.connect(self._on_lifecycle_event)
        self._session_controller.subprotocol_negotiated.connect(self._on_subprotocol_negotiated)
        self._session_controller.session_failed.connect(self._on_session_failed)

    def handle_connect(self) -> None:
        """Initiate connection to target endpoint with connect-time template resolution."""
        if self.state in (SessionState.CONNECTING, SessionState.RECONNECTING, SessionState.OPEN):
            self.handle_disconnect()
            return

        if self._tab is not None:
            raw_url = self._tab.connection_editor.url_input.text().strip()
            raw_params = self._tab.connection_editor.params_table.get_data()
            raw_headers = self._tab.connection_editor.headers_table.get_data()
            subproto_raw = self._tab.connection_editor.subprotocols_input.text()
            raw_subprotocols = [s.strip() for s in subproto_raw.split(",") if s.strip()]
            self._tab.connection_editor.set_read_only(True)
        else:
            raw_url = (self.connection.url or "").strip()
            raw_params = dict(self.connection.params or {})
            raw_headers = dict(self.connection.headers or {})
            raw_subprotocols = list(self.connection.subprotocols or [])

        # Connect-time template resolution (frozen for session duration)
        resolved_url = self._template_service.render_string(raw_url, self._env_vars)
        resolved_params = {
            self._template_service.render_string(k, self._env_vars): (
                self._template_service.render_string(v, self._env_vars)
            )
            for k, v in raw_params.items()
        }
        resolved_headers = {
            self._template_service.render_string(k, self._env_vars): (
                self._template_service.render_string(v, self._env_vars)
            )
            for k, v in raw_headers.items()
        }
        resolved_subprotocols = tuple(
            self._template_service.render_string(s, self._env_vars) for s in raw_subprotocols
        )

        merged_url = _merge_url_and_params(resolved_url, resolved_params)

        target = HandshakeTarget(
            url=merged_url,
            headers=resolved_headers,
            subprotocols=resolved_subprotocols,
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

        # Invariant: sanitize URL before logging to prevent secret token leaks in logs
        masked_log_url = sanitize_text(
            target.url, env_vars=self._env_vars, hidden_keys=self._hidden_keys
        )
        logger.info("websocket_connect_initiated url=%s", masked_log_url)
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
        """Transmit the message in the composer over the active connection."""
        if self.state != SessionState.OPEN:
            logger.warning("websocket_send_blocked_not_open state=%s", self.state.value)
            return

        if self._tab is not None:
            if hasattr(self._tab, "composer") and self._tab.composer:
                success = self._tab.composer.send_current_payload()
                if success:
                    self._tab.composer.set_payload("")
            elif hasattr(self._tab, "composer_edit"):
                text = self._tab.composer_edit.toPlainText()
                if text:
                    logger.debug("websocket_sending_message length=%d", len(text))
                    self._session_controller.send_text(text)
                    self._tab.composer_edit.setPlainText("")

    def run_sequence(self, sequence_id: str) -> bool:
        """Execute a message sequence on the active session."""
        if self.state != SessionState.OPEN:
            logger.warning("run_sequence_blocked_not_open state=%s", self.state.value)
            return False
        if not self.connection or not self.connection.sequences:
            return False
        seq = next((s for s in self.connection.sequences if s.id == sequence_id), None)
        if not seq:
            logger.warning("run_sequence_not_found seq_id=%s", sequence_id)
            return False
        plan = compile_sequence_plan(seq, self.connection.presets)
        return self._sequence_runner.run_sequence(
            plan=plan,
            controller=self._session_controller,
            env_vars=self._env_vars,
        )

    def stop_sequence(self) -> None:
        """Cancel any active sequence run."""
        self._sequence_runner.stop()

    def set_variables(self, variables: dict[str, str]) -> None:
        """Update active environment variables and propagate to tab widgets."""
        self._env_vars = dict(variables)
        self._propagate_variables_to_tab()

    def set_hidden_keys(self, hidden_keys: set[str]) -> None:
        """Update active hidden keys and propagate to tab widgets."""
        self._hidden_keys = set(hidden_keys)
        self._propagate_variables_to_tab()

    def _on_mask_applied(self) -> None:
        """Track metric when secrets are masked on the WebSocket stream."""
        if self._metrics is not None:
            if hasattr(self._metrics, "track_hidden_value_mask_applied"):
                self._metrics.track_hidden_value_mask_applied(surface="websocket")
            elif hasattr(self._metrics, "hidden_value_masks_applied"):
                self._metrics.hidden_value_masks_applied.labels(surface="websocket").inc()

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
            on_mask_applied=self._on_mask_applied,
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
            on_mask_applied=self._on_mask_applied,
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
            on_mask_applied=self._on_mask_applied,
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
            on_mask_applied=self._on_mask_applied,
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
