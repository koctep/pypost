"""Hidden response fields table widget for RequestEditor."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QContextMenuEvent, QKeyEvent
from PySide6.QtWidgets import (
    QHeaderView,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from pypost.ui.widget_ids import REQUEST_HIDDEN_FIELDS_TABLE, set_widget_id

__all__ = ["HiddenFieldsTable"]


class HiddenFieldsTable(QTableWidget):
    """Single-column table for managing hidden response field selectors.

    Features:
    - Auto-expanding trailing empty row for quick entry.
    - Context menu and keyboard actions for deleting rows.
    - Preserves selector ordering and filters out empty whitespace rows.
    """

    data_changed = Signal()
    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(1, 1, parent)
        set_widget_id(self, REQUEST_HIDDEN_FIELDS_TABLE)
        self.setHorizontalHeaderLabels(["Field Selector"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setItem(0, 0, QTableWidgetItem(""))
        self.itemChanged.connect(self._on_item_changed)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() == 0 and item.row() == self.rowCount() - 1 and item.text().strip():
            self.blockSignals(True)
            new_row = self.rowCount()
            self.setRowCount(new_row + 1)
            self.setItem(new_row, 0, QTableWidgetItem(""))
            self.blockSignals(False)
        self.data_changed.emit()
        self.changed.emit()

    def set_data(self, data: list[str]) -> None:
        """Populate rows from list of selectors; always leave a trailing empty row."""
        self.blockSignals(True)
        try:
            valid_items = [str(x).strip() for x in data if str(x).strip()]
            self.setRowCount(len(valid_items) + 1)
            for i, selector in enumerate(valid_items):
                self.setItem(i, 0, QTableWidgetItem(selector))
            last = self.rowCount() - 1
            self.setItem(last, 0, QTableWidgetItem(""))
        finally:
            self.blockSignals(False)

    def get_data(self) -> list[str]:
        """Collect non-empty selector strings in row order."""
        result: list[str] = []
        for i in range(self.rowCount()):
            item = self.item(i, 0)
            if item is not None:
                text = item.text().strip()
                if text:
                    result.append(text)
        return result

    def add_row(self, selector: str = "") -> None:
        """Add a selector row or focus the empty trailing row."""
        last = self.rowCount() - 1
        if last >= 0:
            last_item = self.item(last, 0)
            if not last_item or not last_item.text().strip():
                if selector:
                    self.setItem(last, 0, QTableWidgetItem(selector))
                    self.blockSignals(True)
                    self.setRowCount(self.rowCount() + 1)
                    self.setItem(self.rowCount() - 1, 0, QTableWidgetItem(""))
                    self.blockSignals(False)
                    self.setCurrentCell(self.rowCount() - 2, 0)
                    self.data_changed.emit()
                    self.changed.emit()
                else:
                    self.setCurrentCell(last, 0)
                    if last_item is not None:
                        self.editItem(last_item)
                return

        row = self.rowCount()
        self.blockSignals(True)
        self.setRowCount(row + 1)
        self.setItem(row, 0, QTableWidgetItem(selector))
        self.setRowCount(row + 2)
        self.setItem(row + 1, 0, QTableWidgetItem(""))
        self.blockSignals(False)
        self.setCurrentCell(row, 0)
        self.data_changed.emit()
        self.changed.emit()

    def remove_selected_rows(self) -> None:
        """Remove currently selected rows except the trailing empty row."""
        selected_indexes = self.selectedIndexes()
        if not selected_indexes:
            return

        selected_rows = sorted({idx.row() for idx in selected_indexes}, reverse=True)
        self.blockSignals(True)
        try:
            for row in selected_rows:
                if row == self.rowCount() - 1:
                    item = self.item(row, 0)
                    if not item or not item.text().strip():
                        continue
                self.removeRow(row)

            if self.rowCount() == 0:
                self.setRowCount(1)
                self.setItem(0, 0, QTableWidgetItem(""))
            else:
                last_row = self.rowCount() - 1
                last_item = self.item(last_row, 0)
                if last_item and last_item.text().strip():
                    self.setRowCount(self.rowCount() + 1)
                    self.setItem(self.rowCount() - 1, 0, QTableWidgetItem(""))
        finally:
            self.blockSignals(False)

        self.data_changed.emit()
        self.changed.emit()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        menu = QMenu(self)
        add_action = menu.addAction("Add Selector")
        remove_action = menu.addAction("Remove Selected")
        selected_rows = [idx.row() for idx in self.selectedIndexes()]
        remove_action.setEnabled(bool(selected_rows))

        action = menu.exec(event.globalPos())
        if action == add_action:
            self.add_row()
        elif action == remove_action:
            self.remove_selected_rows()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            if self.state() != QTableWidget.State.EditingState:
                self.remove_selected_rows()
                return
        super().keyPressEvent(event)
