"""Shared empty-row Key/Value table for HTTP, WebSocket, and MCP headers."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidgetItem,
    QWidget,
)

from pypost.ui.widgets.variable_aware_widgets import VariableAwareTableWidget

__all__ = ["EmptyRowKeyValueTable"]


class EmptyRowKeyValueTable(VariableAwareTableWidget):
    """Two-column Key/Value table with a trailing empty row for new pairs.

    ``strip_keys`` selects collect policy: HTTP keeps raw keys (False);
    WebSocket and MCP strip and drop whitespace-only keys (True).
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        strip_keys: bool = True,
    ) -> None:
        super().__init__(1, 2, parent)
        self._strip_keys = strip_keys
        self.setHorizontalHeaderLabels(["Key", "Value"])
        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.itemChanged.connect(self._on_item_changed)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if item.row() == self.rowCount() - 1 and item.text():
            self.setRowCount(self.rowCount() + 1)

    def set_data(self, data: dict[str, str]) -> None:
        """Populate rows from a pair map; always leave a trailing empty row."""
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
        """Collect non-empty key rows; last-wins on duplicate keys."""
        data: dict[str, str] = {}
        for i in range(self.rowCount()):
            key_item = self.item(i, 0)
            val_item = self.item(i, 1)
            if not key_item:
                continue
            raw = key_item.text()
            key = raw.strip() if self._strip_keys else raw
            if key:
                data[key] = val_item.text() if val_item else ""
        return data

    def set_read_only(self, read_only: bool) -> None:
        """Toggle edit triggers (used by WebSocket while connected)."""
        if read_only:
            self.setEditTriggers(
                QAbstractItemView.EditTrigger.NoEditTriggers
            )
        else:
            self.setEditTriggers(
                QAbstractItemView.EditTrigger.DoubleClicked
                | QAbstractItemView.EditTrigger.SelectedClicked
                | QAbstractItemView.EditTrigger.EditKeyPressed
                | QAbstractItemView.EditTrigger.AnyKeyPressed
            )
