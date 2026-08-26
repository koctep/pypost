"""MCP Client draft connection bar (URL, Connect, Disconnect, Refresh, state)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from pypost.models.mcp_client import McpClientSessionState
from pypost.ui.widget_ids import (
    MCP_CLIENT_CONNECT_BUTTON,
    MCP_CLIENT_DISCONNECT_BUTTON,
    MCP_CLIENT_REFRESH_BUTTON,
    MCP_CLIENT_STATE_BADGE,
    MCP_CLIENT_URL_INPUT,
    set_widget_id,
)
from pypost.ui.widgets.variable_aware_widgets import VariableAwareLineEdit

__all__ = ["McpClientConnectionBar"]

_STATE_LABELS = {
    McpClientSessionState.DISCONNECTED: "Disconnected",
    McpClientSessionState.CONNECTING: "Connecting",
    McpClientSessionState.CONNECTED: "Connected",
    McpClientSessionState.FAILED: "Failed",
}


class McpClientConnectionBar(QWidget):
    """Header row for an unsaved MCP Client draft."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.url_input = VariableAwareLineEdit(self)
        self.url_input.setPlaceholderText("http://127.0.0.1:1080/mcp")
        set_widget_id(self.url_input, MCP_CLIENT_URL_INPUT)
        layout.addWidget(self.url_input, 1)

        self.connect_btn = QPushButton("Connect", self)
        set_widget_id(self.connect_btn, MCP_CLIENT_CONNECT_BUTTON)
        layout.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("Disconnect", self)
        set_widget_id(self.disconnect_btn, MCP_CLIENT_DISCONNECT_BUTTON)
        layout.addWidget(self.disconnect_btn)

        self.refresh_btn = QPushButton("Refresh", self)
        set_widget_id(self.refresh_btn, MCP_CLIENT_REFRESH_BUTTON)
        layout.addWidget(self.refresh_btn)

        self.state_badge = QLabel("Disconnected", self)
        set_widget_id(self.state_badge, MCP_CLIENT_STATE_BADGE)
        layout.addWidget(self.state_badge)

        self.set_session_state(McpClientSessionState.DISCONNECTED)

    def set_session_state(
        self,
        state: McpClientSessionState,
        *,
        list_in_flight: bool = False,
        invoke_in_flight: bool = False,
    ) -> None:
        """Update badge text and Connect / Disconnect / Refresh gating."""
        self.state_badge.setText(_STATE_LABELS.get(state, "Disconnected"))
        is_connected = state == McpClientSessionState.CONNECTED
        is_connecting = state == McpClientSessionState.CONNECTING
        busy = list_in_flight or invoke_in_flight
        self.connect_btn.setEnabled((not busy) and (not is_connected))
        self.disconnect_btn.setEnabled(is_connected or is_connecting)
        self.refresh_btn.setEnabled(is_connected and not busy)
