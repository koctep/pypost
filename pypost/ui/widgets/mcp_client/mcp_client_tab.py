"""MCP Client draft workspace page (PYPOST-1166 / MCP-TM-2)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QVBoxLayout, QWidget

from pypost.models.mcp_client import McpClientConnection, McpClientSessionState
from pypost.ui.widget_ids import MCP_CLIENT_TAB_PAGE, set_widget_id
from pypost.ui.widgets.mcp_client.connection_bar import McpClientConnectionBar
from pypost.ui.widgets.mcp_client.tool_browser import McpClientToolBrowser

if TYPE_CHECKING:
    from pypost.ui.presenters.mcp_client_presenter import McpClientPresenter

__all__ = ["McpClientTab"]


class McpClientTab(QWidget):
    """Outbound MCP Client draft editor: URL bar, connect chrome, empty tools."""

    def __init__(
        self,
        connection: McpClientConnection,
        presenter: McpClientPresenter,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        set_widget_id(self, MCP_CLIENT_TAB_PAGE)
        self.connection_data: McpClientConnection = connection
        self.presenter: McpClientPresenter = presenter

        self._init_ui()
        self.url_input.setText(connection.url)
        presenter.set_tab(self)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self._connection_bar = McpClientConnectionBar(self)
        layout.addWidget(self._connection_bar)
        self._tool_browser = McpClientToolBrowser(self)
        layout.addWidget(self._tool_browser, 1)

        self.url_input = self._connection_bar.url_input
        self.connect_btn = self._connection_bar.connect_btn
        self.disconnect_btn = self._connection_bar.disconnect_btn
        self.connect_btn.clicked.connect(self.presenter.connect_requested)
        self.disconnect_btn.clicked.connect(self.presenter.disconnect_requested)
        self.url_input.textChanged.connect(self._on_url_changed)

    def _on_url_changed(self, text: str) -> None:
        self.connection_data.url = text

    def set_session_state(self, state: McpClientSessionState) -> None:
        """Mirror presenter chrome state onto the connection bar badge."""
        self._connection_bar.set_session_state(state)
