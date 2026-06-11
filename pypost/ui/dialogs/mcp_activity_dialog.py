"""Dialog for inspecting recent inbound MCP server activity (PYPOST-141)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from pypost.core.mcp_activity_log import McpActivityEntry


class McpActivityDialog(QDialog):
    """Read-only table of recent list_tools and call_tool operations."""

    _COLUMNS = ("Time", "Operation", "Tool", "Details", "Outcome")

    def __init__(
        self,
        entries: list[McpActivityEntry],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("MCP Activity")
        self.resize(820, 420)
        self._table: QTableWidget | None = None
        self._summary_label: QLabel | None = None
        self._build_ui()
        self.set_entries(entries)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._summary_label = QLabel()
        self._summary_label.setWordWrap(True)
        layout.addWidget(self._summary_label)

        self._table = QTableWidget(0, len(self._COLUMNS))
        self._table.setHorizontalHeaderLabels(list(self._COLUMNS))
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._table)

        buttons = QHBoxLayout()
        buttons.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

    def set_entries(self, entries: list[McpActivityEntry]) -> None:
        if self._summary_label is None or self._table is None:
            return

        if entries:
            summary = f"{len(entries)} recent MCP operation(s)."
        else:
            summary = (
                "No MCP activity recorded yet. Operations appear when an agent "
                "calls list_tools or call_tool while the server is running."
            )
        self._summary_label.setText(summary)

        self._table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            values = (
                _format_timestamp(entry),
                entry.operation,
                _format_tool_column(entry),
                _format_details(entry),
                entry.outcome,
            )
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row, col, item)

        self._table.setVisible(bool(entries))


def _format_timestamp(entry: McpActivityEntry) -> str:
    local = entry.timestamp.astimezone()
    return local.strftime("%H:%M:%S")


def _format_tool_column(entry: McpActivityEntry) -> str:
    if entry.operation == "list_tools":
        count = entry.tool_count if entry.tool_count is not None else 0
        return f"{count} tool(s)"
    return entry.tool_name or ""


def _format_details(entry: McpActivityEntry) -> str:
    parts: list[str] = []
    if entry.mcp_arg_count is not None:
        parts.append(f"args={entry.mcp_arg_count}")
    if entry.http_status is not None:
        parts.append(f"status={entry.http_status}")
    if entry.duration_ms is not None:
        parts.append(f"{entry.duration_ms:.0f}ms")
    if entry.detail:
        parts.append(entry.detail)
    return ", ".join(parts)
