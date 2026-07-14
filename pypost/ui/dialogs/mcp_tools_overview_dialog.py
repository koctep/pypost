from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from pypost.core.mcp_tools_overview import McpToolOverviewEntry


class McpToolsOverviewDialog(QDialog):
    """Read-only overview of requests exposed as MCP tools."""

    _COLUMNS = ("MCP name", "Request", "Collection", "Method", "Description")

    def __init__(
        self,
        entries: list[McpToolOverviewEntry],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("MCP Tools")
        self.resize(760, 420)
        self._build_ui(entries)

    def _build_ui(self, entries: list[McpToolOverviewEntry]) -> None:
        layout = QVBoxLayout(self)

        summary = (
            f"{len(entries)} tool(s) exposed across collections."
            if entries
            else "No requests are marked as MCP tools."
        )
        summary_label = QLabel(summary)
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label)

        table = QTableWidget(len(entries), len(self._COLUMNS))
        table.setHorizontalHeaderLabels(list(self._COLUMNS))
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        for row, entry in enumerate(entries):
            values = (
                entry.mcp_name,
                entry.request_name,
                entry.collection_name,
                entry.method,
                entry.description,
            )
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row, col, item)

        table.setVisible(bool(entries))
        layout.addWidget(table)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
