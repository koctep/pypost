"""MCP Client draft workspace page (PYPOST-1166 / PYPOST-1167 / PYPOST-1169)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from pypost.core.metrics_protocol import resolve_metrics
from pypost.models.mcp_client import (
    McpClientConnection,
    McpClientSessionState,
    McpRemoteTool,
)
from pypost.ui.hotkeys import tag_action
from pypost.ui.presenters.tab_dirty import mcp_client_snapshot_from_tab
from pypost.ui.widget_ids import (
    MCP_CLIENT_ERROR_LABEL,
    MCP_CLIENT_HEADERS_TABLE,
    MCP_CLIENT_TAB_PAGE,
    set_widget_id,
)
from pypost.ui.widgets.mcp_client.connection_bar import McpClientConnectionBar
from pypost.ui.widgets.mcp_client.headers_table import McpClientHeadersTable
from pypost.ui.widgets.mcp_client.mcp_result_view import McpResultView
from pypost.ui.widgets.mcp_client.tool_browser import McpClientToolBrowser
from pypost.ui.widgets.mcp_client.tool_invoke_form import McpClientToolInvokeForm
from pypost.ui.widgets.mixins import push_snapshot_to_widgets

if TYPE_CHECKING:
    from pypost.ui.presenters.mcp_client_presenter import McpClientPresenter

__all__ = ["McpClientTab"]


class McpClientTab(QWidget):
    """Outbound MCP Client draft: URL bar, headers table, connect chrome, tools."""

    save_requested = Signal(McpClientConnection)
    save_as_requested = Signal(McpClientConnection)

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
        self.persisted_baseline: McpClientConnection | None = None
        self.stale_persisted = False

        self._init_ui()
        self._setup_save_shortcuts()
        self.url_input.setText(connection.url)
        self._headers_table.set_data(connection.headers)
        presenter.set_tab(self)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self._connection_bar = McpClientConnectionBar(self)
        layout.addWidget(self._connection_bar)

        header_row = QHBoxLayout()
        header_row.addStretch()
        self.actions_btn = QToolButton(self)
        self.actions_btn.setText("Actions")
        self.actions_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.actions_menu = QMenu(self.actions_btn)
        self.save_as_action = QAction("Save As...", self)
        self.save_as_action.triggered.connect(self.handle_save_as_menu_action)
        self.actions_menu.addAction(self.save_as_action)
        self.save_action = QAction("Save", self)
        self.save_action.triggered.connect(self.handle_save_menu_action)
        self.actions_menu.addAction(self.save_action)
        self.actions_btn.setMenu(self.actions_menu)
        header_row.addWidget(self.actions_btn)
        layout.addLayout(header_row)

        self._error_label = QLabel("", self)
        self._error_label.setWordWrap(True)
        set_widget_id(self._error_label, MCP_CLIENT_ERROR_LABEL)
        layout.addWidget(self._error_label)
        layout.addWidget(QLabel("Headers", self))
        self._headers_table = McpClientHeadersTable(self)
        set_widget_id(self._headers_table, MCP_CLIENT_HEADERS_TABLE)
        layout.addWidget(self._headers_table)

        splitter = QSplitter(self)
        self._tool_browser = McpClientToolBrowser(self)
        splitter.addWidget(self._tool_browser)
        invoke_column = QWidget(self)
        invoke_layout = QVBoxLayout(invoke_column)
        invoke_layout.setContentsMargins(0, 0, 0, 0)
        self._invoke_form = McpClientToolInvokeForm(invoke_column)
        self._result_view = McpResultView(invoke_column)
        invoke_layout.addWidget(self._invoke_form)
        invoke_layout.addWidget(self._result_view, 1)
        splitter.addWidget(invoke_column)
        layout.addWidget(splitter, 1)

        self.url_input = self._connection_bar.url_input
        self.connect_btn = self._connection_bar.connect_btn
        self.disconnect_btn = self._connection_bar.disconnect_btn
        self.refresh_btn = self._connection_bar.refresh_btn
        self.connect_btn.clicked.connect(self.presenter.connect_requested)
        self.disconnect_btn.clicked.connect(
            self.presenter.disconnect_requested,
        )
        self.refresh_btn.clicked.connect(self.presenter.refresh_requested)
        self.url_input.textChanged.connect(self._on_url_changed)
        self._headers_table.itemChanged.connect(self._on_headers_changed)
        self._tool_browser.tool_selected.connect(self._on_tool_selected)
        self._invoke_form.invoke_clicked.connect(
            self.presenter.invoke_requested,
        )

    @property
    def invoke_form(self) -> McpClientToolInvokeForm:
        """Return the embedded tool invoke form widget."""
        return self._invoke_form

    def _setup_save_shortcuts(self) -> None:
        self.save_action.setShortcut(QKeySequence("Ctrl+S"))
        self.save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.addAction(self.save_action)
        self.addAction(self.save_as_action)
        tag_action(
            self.save_action,
            section="MCP Client",
            order=2,
            keys=("Ctrl+S",),
            label="Save MCP Client Profile",
        )
        tag_action(
            self.save_as_action,
            section="MCP Client",
            order=3,
            keys=("Ctrl+Shift+S",),
            label="Save As MCP Client Profile",
        )

    def _emit_save(self, source: str) -> None:
        resolve_metrics(getattr(self.presenter, "_metrics", None)).track_gui_save_action(
            source
        )
        snapshot = mcp_client_snapshot_from_tab(self)
        self.connection_data = snapshot
        self.save_requested.emit(snapshot)

    def _emit_save_as(self, source: str) -> None:
        resolve_metrics(getattr(self.presenter, "_metrics", None)).track_gui_save_as_action(
            source
        )
        snapshot = mcp_client_snapshot_from_tab(self)
        self.connection_data = snapshot
        self.save_as_requested.emit(snapshot)

    def handle_save_request_shortcut(self) -> None:
        self._emit_save("shortcut")

    def handle_save_menu_action(self) -> None:
        self._emit_save("menu")

    def handle_save_as_shortcut(self) -> None:
        self._emit_save_as("shortcut")

    def handle_save_as_menu_action(self) -> None:
        self._emit_save_as("menu")

    def _on_tool_selected(self, name: object) -> None:
        if name is None or isinstance(name, str):
            self.presenter.select_tool(name)
            return
        self.presenter.select_tool(None)

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

    def set_session_state(
        self,
        state: McpClientSessionState,
        *,
        list_in_flight: bool = False,
        invoke_in_flight: bool = False,
    ) -> None:
        """Mirror presenter chrome state onto the connection bar badge."""
        self._connection_bar.set_session_state(
            state,
            list_in_flight=list_in_flight,
            invoke_in_flight=invoke_in_flight,
        )

    def set_invoke_enabled(self, enabled: bool) -> None:
        """Gate the Invoke control from presenter chrome state."""
        self._invoke_form.set_invoke_enabled(enabled)

    def set_status_text(self, text: str) -> None:
        """Show Connect/Refresh error or in-flight progress on the tab."""
        self._error_label.setText(text)

    def set_tools(self, tools: list[tuple[str, str]]) -> None:
        """Replace the tool browser rows with name/description pairs."""
        self._tool_browser.set_tools(tools)

    def select_tool_by_name(self, name: str) -> None:
        """Restore a catalog selection after Refresh without rebinding args."""
        self._tool_browser.select_tool_by_name(name)

    def clear_tools(self) -> None:
        """Empty the tool browser (disconnect / failed Connect)."""
        self._tool_browser.clear_tools()

    def bind_invoke_tool(self, tool: McpRemoteTool | None) -> None:
        """Rebuild the argument form for the selected tool."""
        self._invoke_form.bind_tool(tool)

    def collect_invoke_arguments(self) -> dict[str, Any]:
        """Return the current argument object or raise ArgValidationError."""
        return self._invoke_form.collect_arguments()

    def apply_invoke_arguments(self, arguments: dict[str, Any]) -> None:
        """Pre-fill invoke argument editors from migration mapping."""
        self._invoke_form.apply_arguments(arguments)

    def set_invoke_in_progress(self) -> None:
        """Show in-flight chrome in the result pane."""
        self._result_view.set_in_progress()

    def set_invoke_result(
        self,
        payload: dict[str, Any],
        elapsed_s: float,
        *,
        is_error: bool,
    ) -> None:
        """Render a CallToolResult body in the result pane."""
        self._result_view.set_result(payload, elapsed_s, is_error=is_error)

    def set_invoke_error(
        self,
        message: str,
        elapsed_s: float | None = None,
    ) -> None:
        """Show a validation or transport error in the result pane."""
        self._result_view.set_error(message, elapsed_s)

    def clear_result(self) -> None:
        """Clear only the result pane (tool switch / lost selection)."""
        self._result_view.clear()

    def clear_invoke(self) -> None:
        """Clear selection-bound args and the last result."""
        self._invoke_form.bind_tool(None)
        self._result_view.clear()
