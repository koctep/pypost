"""MCP Client draft workspace page (PYPOST-1166 / PYPOST-1167)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from pypost.models.mcp_client import McpClientConnection, McpClientSessionState
from pypost.ui.widget_ids import (
    MCP_CLIENT_HEADERS_TABLE,
    MCP_CLIENT_TAB_PAGE,
    set_widget_id,
)
from pypost.ui.widgets.mcp_client.connection_bar import McpClientConnectionBar
from pypost.ui.widgets.mcp_client.headers_table import McpClientHeadersTable
from pypost.ui.widgets.mcp_client.tool_browser import McpClientToolBrowser
from pypost.ui.widgets.mixins import push_snapshot_to_widgets

if TYPE_CHECKING:
    from pypost.ui.presenters.mcp_client_presenter import McpClientPresenter

__all__ = ["McpClientTab"]


class McpClientTab(QWidget):
    """Outbound MCP Client draft: URL bar, headers table, connect chrome, tools."""

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
        self._headers_table.set_data(connection.headers)
        presenter.set_tab(self)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self._connection_bar = McpClientConnectionBar(self)
        layout.addWidget(self._connection_bar)
        layout.addWidget(QLabel("Headers", self))
        self._headers_table = McpClientHeadersTable(self)
        set_widget_id(self._headers_table, MCP_CLIENT_HEADERS_TABLE)
        layout.addWidget(self._headers_table)
        self._tool_browser = McpClientToolBrowser(self)
        layout.addWidget(self._tool_browser, 1)

        self.url_input = self._connection_bar.url_input
        self.connect_btn = self._connection_bar.connect_btn
        self.disconnect_btn = self._connection_bar.disconnect_btn
        self.connect_btn.clicked.connect(self.presenter.connect_requested)
        self.disconnect_btn.clicked.connect(
            self.presenter.disconnect_requested,
        )
        self.url_input.textChanged.connect(self._on_url_changed)
        self._headers_table.itemChanged.connect(self._on_headers_changed)

    def _env_widgets(self) -> tuple[QWidget, QWidget]:
        return (self.url_input, self._headers_table)

    def set_variables(self, variables: dict[str, str]) -> None:
        """Push the active environment snapshot onto URL and headers widgets."""
        push_snapshot_to_widgets(
            self._env_widgets(),
            "set_variables",
            variables,
        )

    def set_hidden_keys(self, hidden_keys: set[str]) -> None:
        """Push hidden environment keys onto URL and headers widgets."""
        push_snapshot_to_widgets(
            self._env_widgets(),
            "set_hidden_keys",
            hidden_keys,
        )

    def headers_data(self) -> dict[str, str]:
        """Return the current headers table contents."""
        return self._headers_table.get_data()

    def _on_url_changed(self, text: str) -> None:
        self.connection_data.url = text

    def _on_headers_changed(self, _item: object = None) -> None:
        self.connection_data.headers = self._headers_table.get_data()

    def set_session_state(self, state: McpClientSessionState) -> None:
        """Mirror presenter chrome state onto the connection bar badge."""
        self._connection_bar.set_session_state(state)
