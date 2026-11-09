"""Hidden response fields table widget for RequestEditor."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QContextMenuEvent, QKeyEvent
from PySide6.QtWidgets import (
    QHeaderView,
    QMenu,
    QTableView,
    QWidget,
)

from pypost.ui.delegates.field_selector_delegate import FieldSelectorDelegate
from pypost.ui.models.hidden_fields_table_model import HiddenFieldsTableModel
from pypost.ui.widget_ids import REQUEST_HIDDEN_FIELDS_TABLE, set_widget_id

__all__ = ["HiddenFieldsTable", "HiddenFieldsTableModel"]


class _TableItemFacade:
    """Lightweight compatibility adapter for ``table.item(row, col).text()``."""

    def __init__(self, text: str) -> None:
        self._text = text

    def text(self) -> str:
        return self._text


class HiddenFieldsTable(QTableView):
    """Virtualized single-column table for hidden response field selectors.

    Features:
    - Auto-expanding trailing empty row for quick entry.
    - Context menu and keyboard actions for deleting rows.
    - Preserves selector ordering and filters out empty whitespace rows.
    """

    data_changed = Signal()
    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        set_widget_id(self, REQUEST_HIDDEN_FIELDS_TABLE)
        self._model = HiddenFieldsTableModel(self)
        self.setModel(self._model)
        self.setItemDelegate(FieldSelectorDelegate(self))
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self.verticalHeader().setDefaultSectionSize(26)
        self._model.data_changed.connect(self.data_changed.emit)
        self._model.changed.connect(self.changed.emit)

    def rowCount(self) -> int:
        """Compatibility facade matching QTableWidget.rowCount()."""
        return self._model.rowCount()

    def columnCount(self) -> int:
        """Compatibility facade matching QTableWidget.columnCount()."""
        return self._model.columnCount()

    def item(self, row: int, column: int) -> _TableItemFacade | None:
        """Return a lightweight item facade for test/API compatibility."""
        if row < 0 or row >= self._model.rowCount() or column != 0:
            return None
        value = self._model.data(
            self._model.index(row, column),
            Qt.ItemDataRole.DisplayRole,
        )
        return _TableItemFacade("" if value is None else str(value))

    def set_data(self, data: list[str]) -> None:
        """Populate rows from list of selectors; always leave a trailing empty row."""
        self._model.set_data(data)

    def get_data(self) -> list[str]:
        """Collect non-empty selector strings in row order."""
        return self._model.get_data()

    def add_row(self, selector: str = "") -> None:
        """Add a selector row or focus the empty trailing row."""
        focus_row = self._model.add_row(selector)
        index = self._model.index(focus_row, 0)
        self.setCurrentIndex(index)
        if not str(selector).strip():
            self.edit(index)

    def remove_selected_rows(self) -> None:
        """Remove currently selected rows except the trailing empty row."""
        selection = self.selectionModel()
        if selection is None:
            return
        rows = sorted({idx.row() for idx in selection.selectedRows()}, reverse=True)
        if not rows:
            return
        self._model.remove_rows(rows)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        menu = QMenu(self)
        add_action = menu.addAction("Add Selector")
        remove_action = menu.addAction("Remove Selected")
        selection = self.selectionModel()
        selected_rows = (
            [idx.row() for idx in selection.selectedRows()] if selection else []
        )
        remove_action.setEnabled(bool(selected_rows))

        action = menu.exec(event.globalPos())
        if action == add_action:
            self.add_row()
        elif action == remove_action:
            self.remove_selected_rows()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            if self.state() != QTableView.State.EditingState:
                self.remove_selected_rows()
                return
        super().keyPressEvent(event)
