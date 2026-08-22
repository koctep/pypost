"""Multi-modal WebSocket state badge widget (PYPOST-1132 / WS-4).

Displays accessible session lifecycle state using text labels and symbolic glyphs
(never relying on color alone, satisfying WCAG 2.1 / FR-3).
"""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from pypost.core.websocket_session_policy import SessionState, StateDetail
from pypost.ui.widget_ids import WS_STATE_BADGE, set_widget_id

logger = logging.getLogger(__name__)

__all__ = ["WebSocketStateBadge"]

STATE_GLYPHS = {
    SessionState.IDLE: "○",
    SessionState.CONNECTING: "⏳",
    SessionState.OPEN: "●",
    SessionState.CLOSING: "⏳",
    SessionState.RECONNECTING: "⏳",
    SessionState.FAILED: "✕",
    SessionState.CLOSED: "○",
}

STATE_LABELS = {
    SessionState.IDLE: "Idle",
    SessionState.CONNECTING: "Connecting...",
    SessionState.OPEN: "Open",
    SessionState.CLOSING: "Closing...",
    SessionState.RECONNECTING: "Reconnecting",
    SessionState.FAILED: "Failed",
    SessionState.CLOSED: "Closed",
}


class WebSocketStateBadge(QWidget):
    """Accessible multi-modal badge for WebSocket session state and metrics."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        set_widget_id(self, WS_STATE_BADGE)

        self._state: SessionState = SessionState.IDLE
        self._state_detail: Optional[StateDetail] = None
        self._subprotocol: str = ""
        self._message_count: int = 0
        self._elapsed_seconds: float = 0.0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._label)

        self._update_display()

    @property
    def current_state(self) -> SessionState:
        """Current session lifecycle state."""
        return self._state

    def text(self) -> str:
        """Return the current display text."""
        return self._label.text()

    def set_state(
        self,
        state: SessionState | str,
        detail: Optional[StateDetail] = None,
    ) -> None:
        """Update session state and optional transition detail."""
        if isinstance(state, str):
            try:
                self._state = SessionState(state)
            except ValueError:
                self._state = SessionState.IDLE
        else:
            self._state = state
        self._state_detail = detail
        self._update_display()

    def set_metrics(
        self,
        subprotocol: str = "",
        message_count: int = 0,
        elapsed_seconds: float = 0.0,
    ) -> None:
        """Update secondary metrics summary displayed when connected."""
        self._subprotocol = subprotocol
        self._message_count = message_count
        self._elapsed_seconds = elapsed_seconds
        self._update_display()

    def reset(self) -> None:
        """Reset badge back to default Idle state."""
        self._state = SessionState.IDLE
        self._state_detail = None
        self._subprotocol = ""
        self._message_count = 0
        self._elapsed_seconds = 0.0
        self._update_display()

    def _update_display(self) -> None:
        glyph = STATE_GLYPHS.get(self._state, "○")
        base_label = STATE_LABELS.get(self._state, self._state.value.capitalize())

        parts = [f"{glyph} {base_label}"]

        if self._state == SessionState.OPEN:
            if self._subprotocol:
                parts.append(f"• {self._subprotocol}")
            if self._message_count > 0:
                parts.append(f"• {self._message_count} msgs")
        elif (
            self._state == SessionState.RECONNECTING
            and self._state_detail
            and self._state_detail.message
        ):
            parts = [f"{glyph} {base_label} ({self._state_detail.message})"]
        elif (
            self._state == SessionState.FAILED
            and self._state_detail
            and self._state_detail.message
        ):
            parts = [f"{glyph} {base_label}: {self._state_detail.message}"]

        display_text = " ".join(parts)
        self._label.setText(display_text)

        # Tooltip
        if self._state == SessionState.IDLE:
            self.setToolTip("Session idle. Click Connect to start.")
        elif self._state == SessionState.CONNECTING:
            self.setToolTip("Establishing WebSocket handshake...")
        elif self._state == SessionState.OPEN:
            tooltip = "Connected to endpoint."
            if self._subprotocol:
                tooltip += f" Subprotocol: {self._subprotocol}"
            self.setToolTip(tooltip)
        elif self._state == SessionState.CLOSING:
            self.setToolTip("Closing connection...")
        elif self._state == SessionState.RECONNECTING:
            msg = self._state_detail.message if self._state_detail else "Reconnecting..."
            self.setToolTip(f"Connection lost. {msg}")
        elif self._state == SessionState.FAILED:
            msg = self._state_detail.message if self._state_detail else "Unknown error"
            self.setToolTip(f"Connection failed: {msg}")
        else:
            self.setToolTip("")
