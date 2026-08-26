"""MCP Client draft headers table (empty-row key/value editor)."""

from __future__ import annotations

from PySide6.QtWidgets import QHeaderView, QTableWidgetItem, QWidget

from pypost.ui.widgets.variable_aware_widgets import VariableAwareTableWidget

__all__ = ["McpClientHeadersTable"]


class McpClientHeadersTable(VariableAwareTableWidget):
    """Editable Key/Value table with a trailing empty row for new headers."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(1, 2, parent)
        self.setHorizontalHeaderLabels(["Key", "Value"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.itemChanged.connect(self._on_item_changed)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if item.row() == self.rowCount() - 1 and item.text():
            self.setRowCount(self.rowCount() + 1)

    def set_data(self, data: dict[str, str]) -> None:
        """Populate table rows from a header dictionary."""
        self.blockSignals(True)
        try:
            self.setRowCount(len(data) + 1)
            for i, (key, value) in enumerate(data.items()):
                self.setItem(i, 0, QTableWidgetItem(key))
                self.setItem(i, 1, QTableWidgetItem(value))
            last = self.rowCount() - 1
            self.setItem(last, 0, QTableWidgetItem(""))
            self.setItem(last, 1, QTableWidgetItem(""))
        finally:
            self.blockSignals(False)

    def get_data(self) -> dict[str, str]:
        """Extract non-empty header names and their values."""
        data: dict[str, str] = {}
        for i in range(self.rowCount()):
            key_item = self.item(i, 0)
            val_item = self.item(i, 1)
            key = key_item.text().strip() if key_item else ""
            if key:
                data[key] = val_item.text() if val_item else ""
        return data
