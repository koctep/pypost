"""Virtualized collection variables table view with legacy item facade."""
from __future__ import annotations

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, Signal
from PySide6.QtWidgets import QComboBox, QTableView, QWidget

from pypost.core.collection_variable_import import ConflictStrategy
from pypost.ui.models.collection_variables_table_model import (
    COL_STRATEGY,
    CollectionVariablesTableModel,
)
from pypost.ui.widget_ids import (
    IMPORT_COLLECTION_ROW_STRATEGY_COMBO_PREFIX,
    set_widget_id,
)


class HeaderItemProxy:
    """Backward-compatibility proxy for horizontalHeaderItem(col)."""

    def __init__(self, text: str) -> None:
        self._text = text

    def text(self) -> str:
        return self._text


class TableItemProxy:
    """Backward-compatibility proxy mimicking QTableWidgetItem."""

    def __init__(
        self,
        model: CollectionVariablesTableModel,
        row: int,
        col: int,
    ) -> None:
        self._model = model
        self._row = row
        self._col = col

    def text(self) -> str:
        idx = self._model.index(self._row, self._col)
        val = self._model.data(idx, Qt.ItemDataRole.DisplayRole)
        return str(val) if val is not None else ""

    def setText(self, text: str) -> None:
        idx = self._model.index(self._row, self._col)
        self._model.setData(idx, text, Qt.ItemDataRole.DisplayRole)

    def checkState(self) -> Qt.CheckState:
        idx = self._model.index(self._row, self._col)
        val = self._model.data(idx, Qt.ItemDataRole.CheckStateRole)
        if isinstance(val, Qt.CheckState):
            return val
        return Qt.CheckState.Checked if val else Qt.CheckState.Unchecked

    def setCheckState(self, state: Qt.CheckState) -> None:
        idx = self._model.index(self._row, self._col)
        self._model.setData(idx, state, Qt.ItemDataRole.CheckStateRole)

    def flags(self) -> Qt.ItemFlag:
        idx = self._model.index(self._row, self._col)
        return self._model.flags(idx)


class CollectionVariablesTableView(QTableView):
    """Virtualized table view with backward-compatibility proxies for legacy tests."""

    itemChanged = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._proxies: dict[tuple[int, int], TableItemProxy] = {}
        self._strategy_combos: dict[int, QComboBox] = {}

    def setModel(self, model: QAbstractItemModel | None) -> None:
        old_model = self.model()
        if old_model is not None:
            try:
                old_model.dataChanged.disconnect(self._on_model_data_changed)
            except Exception:
                pass
        super().setModel(model)
        self._proxies.clear()
        self._strategy_combos.clear()
        if model is not None:
            model.dataChanged.connect(self._on_model_data_changed)

    def _on_model_data_changed(
        self,
        top_left: QModelIndex,
        bottom_right: QModelIndex,
        roles: list[int] | None = None,
    ) -> None:
        for r in range(top_left.row(), bottom_right.row() + 1):
            if r in self._strategy_combos:
                combo = self._strategy_combos[r]
                m = self.model()
                if isinstance(m, CollectionVariablesTableModel):
                    strat = m.get_strategy(r)
                    target_text = (
                        "Overwrite" if strat == ConflictStrategy.OVERWRITE else "Keep Current"
                    )
                    idx = combo.findText(target_text)
                    if idx >= 0 and combo.currentIndex() != idx:
                        combo.blockSignals(True)
                        combo.setCurrentIndex(idx)
                        combo.blockSignals(False)
            if top_left.row() == bottom_right.row():
                for c in range(top_left.column(), bottom_right.column() + 1):
                    proxy = self.item(r, c)
                    if proxy is not None:
                        self.itemChanged.emit(proxy)

    def columnCount(self) -> int:
        m = self.model()
        return m.columnCount() if m is not None else 0

    def rowCount(self) -> int:
        m = self.model()
        return m.rowCount() if m is not None else 0

    def horizontalHeaderItem(self, col: int) -> HeaderItemProxy | None:
        m = self.model()
        if m is None or col < 0 or col >= m.columnCount():
            return None
        text = str(
            m.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) or ""
        )
        return HeaderItemProxy(text)

    def item(self, row: int, col: int) -> TableItemProxy | None:
        m = self.model()
        if not isinstance(m, CollectionVariablesTableModel):
            return None
        if row < 0 or row >= m.rowCount() or col < 0 or col >= m.columnCount():
            return None
        key = (row, col)
        if key not in self._proxies:
            self._proxies[key] = TableItemProxy(m, row, col)
        return self._proxies[key]

    def cellWidget(self, row: int, col: int) -> QWidget | None:
        m = self.model()
        if not isinstance(m, CollectionVariablesTableModel):
            return None
        if col != COL_STRATEGY:
            return None
        rec = m.get_record(row)
        if rec is None or not rec.is_collision:
            return None
        if row not in self._strategy_combos:
            combo = QComboBox(parent=None)
            set_widget_id(combo, f"{IMPORT_COLLECTION_ROW_STRATEGY_COMBO_PREFIX}{rec.name}")
            combo.addItem("Keep Current", userData=ConflictStrategy.SKIP)
            combo.addItem("Overwrite", userData=ConflictStrategy.OVERWRITE)
            if rec.strategy == ConflictStrategy.OVERWRITE:
                combo.setCurrentIndex(1)
            else:
                combo.setCurrentIndex(0)

            def _on_combo_index_changed(idx: int, target_row: int = row) -> None:
                strat = ConflictStrategy.OVERWRITE if idx == 1 else ConflictStrategy.SKIP
                m.setData(
                    m.index(target_row, COL_STRATEGY),
                    strat,
                    Qt.ItemDataRole.EditRole,
                )

            combo.currentIndexChanged.connect(_on_combo_index_changed)
            self._strategy_combos[row] = combo
        return self._strategy_combos[row]
