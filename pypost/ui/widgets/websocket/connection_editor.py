"""WebSocket connection editor widget (PYPOST-1132 / WS-4).

Provides editing of WebSocket URL, query parameters, request headers, and subprotocols,
with dynamic read-only parameter locking when a session is active (FR-4 / RFC A-5.3).
"""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pypost.core.websocket_mcp_tools import build_websocket_mcp_preview
from pypost.core.mcp_tool_contract import format_mcp_tool_contract_preview
from pypost.core.websocket_transport_protocol import HandshakeTarget
from pypost.models.websocket import WebSocketConnection
from pypost.ui.widget_ids import (
    WS_DETAIL_TABS,
    WS_HEADERS_TABLE,
    WS_LOCK_NOTICE,
    WS_PARAMS_TABLE,
    WS_SUBPROTOCOLS_INPUT,
    WS_URL_INPUT,
    set_widget_id,
)
from pypost.ui.widgets.variable_aware_widgets import (
    VariableAwareLineEdit,
    VariableAwareTableWidget,
)

logger = logging.getLogger(__name__)

__all__ = ["WebSocketConnectionEditor"]


def _merge_url_and_params(raw_url: str, params: dict[str, str]) -> str:
    """Merge query parameters dictionary into a base URL."""
    if not params:
        return raw_url
    if not raw_url:
        return "?" + urlencode(list(params.items()))
    parsed = urlparse(raw_url)
    existing_query = parse_qsl(parsed.query, keep_blank_values=True)
    new_query = list(existing_query)
    for k, v in params.items():
        new_query.append((k, v))
    encoded_query = urlencode(new_query)
    return urlunparse(parsed._replace(query=encoded_query))


class WebSocketKeyValueTable(VariableAwareTableWidget):
    """Editable key-value table for WebSocket query parameters and handshake headers."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(1, 2, parent)
        self.setHorizontalHeaderLabels(["Key", "Value"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.itemChanged.connect(self._on_item_changed)

    def _on_item_changed(self, item) -> None:
        if item.row() == self.rowCount() - 1 and item.text():
            self.setRowCount(self.rowCount() + 1)

    def set_data(self, data: dict[str, str]) -> None:
        """Populate table rows from dictionary."""
        self.blockSignals(True)
        try:
            self.setRowCount(len(data) + 1)
            for i, (k, v) in enumerate(data.items()):
                from PySide6.QtWidgets import QTableWidgetItem
                self.setItem(i, 0, QTableWidgetItem(k))
                self.setItem(i, 1, QTableWidgetItem(v))
            from PySide6.QtWidgets import QTableWidgetItem
            self.setItem(self.rowCount() - 1, 0, QTableWidgetItem(""))
            self.setItem(self.rowCount() - 1, 1, QTableWidgetItem(""))
        finally:
            self.blockSignals(False)

    def get_data(self) -> dict[str, str]:
        """Extract key-value dictionary from non-empty rows."""
        data: dict[str, str] = {}
        for i in range(self.rowCount()):
            key_item = self.item(i, 0)
            val_item = self.item(i, 1)
            if key_item and key_item.text().strip():
                data[key_item.text().strip()] = val_item.text() if val_item else ""
        return data

    def set_read_only(self, read_only: bool) -> None:
        """Toggle edit triggers on the table."""
        if read_only:
            self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        else:
            self.setEditTriggers(
                QAbstractItemView.EditTrigger.DoubleClicked
                | QAbstractItemView.EditTrigger.SelectedClicked
                | QAbstractItemView.EditTrigger.EditKeyPressed
                | QAbstractItemView.EditTrigger.AnyKeyPressed
            )


class WebSocketConnectionEditor(QWidget):
    """Editor hosting endpoint URL, query params, headers, subprotocols, and lock banner."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._read_only: bool = False
        self._init_ui()
        self.setVisible(True)

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # Lock notice banner (revealed when connected)
        self.lock_notice = QFrame(self)
        set_widget_id(self.lock_notice, WS_LOCK_NOTICE)
        self.lock_notice.setFrameShape(QFrame.Shape.StyledPanel)
        self.lock_notice.setStyleSheet(
            "QFrame#pypost_ws_lock_notice { background-color: #332b00; "
            "border: 1px solid #886e00; border-radius: 4px; padding: 4px; }"
        )
        lock_layout = QHBoxLayout(self.lock_notice)
        lock_layout.setContentsMargins(8, 4, 8, 4)
        self._lock_label = QLabel(
            "🔒 Connection parameters are read-only while connected. Disconnect to edit.",
            self.lock_notice,
        )
        lock_layout.addWidget(self._lock_label)
        self.lock_notice.setVisible(False)
        main_layout.addWidget(self.lock_notice)

        # URL Input row
        url_row = QHBoxLayout()
        url_label = QLabel("URL:", self)
        self.url_input = VariableAwareLineEdit(self)
        set_widget_id(self.url_input, WS_URL_INPUT)
        self.url_input.setPlaceholderText("wss://example.com/stream or ws://localhost:8080/feed")
        url_row.addWidget(url_label)
        url_row.addWidget(self.url_input)
        main_layout.addLayout(url_row)

        # Detail tabs for Params, Headers, Subprotocols
        self.detail_tabs = QTabWidget(self)
        set_widget_id(self.detail_tabs, WS_DETAIL_TABS)

        # 1. Query Params
        self.params_table = WebSocketKeyValueTable(self)
        set_widget_id(self.params_table, WS_PARAMS_TABLE)
        self.detail_tabs.addTab(self.params_table, "Params")

        # 2. Handshake Headers
        self.headers_table = WebSocketKeyValueTable(self)
        set_widget_id(self.headers_table, WS_HEADERS_TABLE)
        self.detail_tabs.addTab(self.headers_table, "Headers")

        # 3. Subprotocols
        subproto_tab = QWidget(self)
        subproto_layout = QVBoxLayout(subproto_tab)
        subproto_row = QHBoxLayout()
        subproto_label = QLabel("Subprotocols (comma-separated):", subproto_tab)
        self.subprotocols_input = VariableAwareLineEdit(subproto_tab)
        set_widget_id(self.subprotocols_input, WS_SUBPROTOCOLS_INPUT)
        self.subprotocols_input.setPlaceholderText("json.v2, chat.v1")
        subproto_row.addWidget(subproto_label)
        subproto_row.addWidget(self.subprotocols_input)
        subproto_layout.addLayout(subproto_row)
        subproto_layout.addStretch()
        self.detail_tabs.addTab(subproto_tab, "Subprotocols")

        # 4. MCP Preview sub-tab
        mcp_tab = QWidget(self)
        mcp_layout = QVBoxLayout(mcp_tab)
        mcp_layout.setContentsMargins(8, 8, 8, 8)
        mcp_layout.setSpacing(6)

        # Expose as MCP checkbox
        self.mcp_expose_check = QCheckBox("Expose as MCP Tool", mcp_tab)
        mcp_layout.addWidget(self.mcp_expose_check)

        # Tool description field
        desc_row = QHBoxLayout()
        desc_row.addWidget(QLabel("Tool Description:", mcp_tab))
        self.mcp_description_edit = QLineEdit(mcp_tab)
        self.mcp_description_edit.setPlaceholderText("Agent-visible tool description")
        desc_row.addWidget(self.mcp_description_edit)
        mcp_layout.addLayout(desc_row)

        # Read-only contract preview
        mcp_layout.addWidget(QLabel("Agent Contract Preview:", mcp_tab))
        self.mcp_preview_text = QPlainTextEdit(mcp_tab)
        self.mcp_preview_text.setReadOnly(True)
        self.mcp_preview_text.setPlaceholderText(
            "Enable 'Expose as MCP Tool' to see the generated tool contract."
        )
        mcp_layout.addWidget(self.mcp_preview_text)

        self.detail_tabs.addTab(mcp_tab, "MCP")

        # Wire live refresh
        self.mcp_expose_check.toggled.connect(self._refresh_mcp_preview)
        self.mcp_description_edit.textChanged.connect(self._refresh_mcp_preview)

        main_layout.addWidget(self.detail_tabs)

    def _refresh_mcp_preview(self) -> None:
        """Regenerate and display the agent contract preview for the current MCP config."""
        conn = WebSocketConnection(
            name="preview",
            expose_as_mcp=self.mcp_expose_check.isChecked(),
            mcp_description=self.mcp_description_edit.text(),
            url=self.url_input.text(),
        )
        preview = build_websocket_mcp_preview(conn)
        if preview is None:
            self.mcp_preview_text.setPlainText(
                "Enable 'Expose as MCP Tool' to see the generated tool contract."
            )
        else:
            self.mcp_preview_text.setPlainText(format_mcp_tool_contract_preview(preview))

    @property
    def is_read_only(self) -> bool:
        """Return True if connection fields are locked."""
        return self._read_only

    def set_variables(self, variables: dict[str, str]) -> None:
        """Propagate environment variables to inputs and tables."""
        self.url_input.set_variables(variables)
        self.subprotocols_input.set_variables(variables)
        self.params_table.set_variables(variables)
        self.headers_table.set_variables(variables)

    def set_hidden_keys(self, hidden_keys: set[str]) -> None:
        """Propagate hidden keys to inputs and tables."""
        self.url_input.set_hidden_keys(hidden_keys)
        self.subprotocols_input.set_hidden_keys(hidden_keys)
        self.params_table.set_hidden_keys(hidden_keys)
        self.headers_table.set_hidden_keys(hidden_keys)

    def set_data(
        self,
        url: str = "",
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, str]] = None,
        subprotocols: Optional[list[str]] = None,
    ) -> None:
        """Set editor input values from raw parameters."""
        self.url_input.setText(url)
        if headers is not None:
            self.headers_table.set_data(headers)
        if params is not None:
            self.params_table.set_data(params)
        if subprotocols is not None:
            self.subprotocols_input.setText(", ".join(subprotocols))

    def load_connection(self, conn: WebSocketConnection) -> None:
        """Populate editor fields from a WebSocketConnection profile."""
        self.url_input.setText(conn.url or "")
        self.params_table.set_data(conn.params or {})
        self.headers_table.set_data(conn.headers or {})
        self.subprotocols_input.setText(", ".join(conn.subprotocols or []))
        # MCP tab
        self.mcp_expose_check.setChecked(conn.expose_as_mcp)
        self.mcp_description_edit.setText(conn.mcp_description or "")
        self._refresh_mcp_preview()

    def get_target(self) -> HandshakeTarget:
        """Construct and return resolved HandshakeTarget from editor inputs."""
        raw_url = self.url_input.text().strip()
        params = self.params_table.get_data()
        headers = self.headers_table.get_data()
        subproto_raw = self.subprotocols_input.text()
        subprotocols = tuple(
            s.strip() for s in subproto_raw.split(",") if s.strip()
        )
        merged_url = _merge_url_and_params(raw_url, params)
        return HandshakeTarget(
            url=merged_url,
            headers=headers,
            subprotocols=subprotocols,
        )

    def set_read_only(self, read_only: bool) -> None:
        """Toggle read-only locking on all connection parameter inputs."""
        self._read_only = read_only
        self.url_input.setReadOnly(read_only)
        self.subprotocols_input.setReadOnly(read_only)
        self.params_table.set_read_only(read_only)
        self.headers_table.set_read_only(read_only)
        self.lock_notice.setVisible(read_only)
        if read_only:
            self.url_input.setToolTip(
                "Connection parameters are read-only while connected. Disconnect to edit."
            )
        else:
            self.url_input.setToolTip("")
