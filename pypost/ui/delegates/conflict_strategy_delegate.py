"""Conflict strategy combo delegate for collection variable import table."""
from __future__ import annotations

import logging

from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
)
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QComboBox,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
)

from pypost.core.collection_variable_import import ConflictStrategy
from pypost.ui.models.collection_variables_table_model import (
    COL_STRATEGY,
    CollectionVariablesTableModel,
)
from pypost.ui.widget_ids import (
    IMPORT_COLLECTION_ROW_STRATEGY_COMBO_PREFIX,
    set_widget_id,
)

logger = logging.getLogger(__name__)


class ConflictStrategyDelegate(QStyledItemDelegate):
    """Delegate providing on-demand QComboBox editing for colliding strategy cells."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def createEditor(
        self,
        parent: QWidget | None,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QWidget:
        if index.column() != COL_STRATEGY:
            return super().createEditor(parent, option, index)
        model = index.model()
        if not isinstance(model, CollectionVariablesTableModel):
            return super().createEditor(parent, option, index)
        rec = model.get_record(index.row())
        if rec is None or not rec.is_collision:
            return super().createEditor(parent, option, index)

        combo = QComboBox(parent)
        set_widget_id(combo, f"{IMPORT_COLLECTION_ROW_STRATEGY_COMBO_PREFIX}{rec.name}")
        combo.addItem("Keep Current", userData=ConflictStrategy.SKIP)
        combo.addItem("Overwrite", userData=ConflictStrategy.OVERWRITE)
        combo.currentIndexChanged.connect(lambda: self.commitAndCloseEditor(combo))
        return combo

    def commitAndCloseEditor(self, editor: QWidget) -> None:
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.NoHint)

    def setEditorData(
        self,
        editor: QWidget,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        if isinstance(editor, QComboBox):
            val = index.data(Qt.ItemDataRole.DisplayRole)
            idx = editor.findText(val)
            if idx >= 0:
                editor.setCurrentIndex(idx)

    def setModelData(
        self,
        editor: QWidget,
        model: QAbstractItemModel,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        if isinstance(editor, QComboBox):
            text = editor.currentText()
            strat = ConflictStrategy.OVERWRITE if text == "Overwrite" else ConflictStrategy.SKIP
            logger.debug(
                "conflict_strategy_delegate_committed row=%d strategy=%s",
                index.row(),
                strat.value,
            )
            model.setData(index, strat, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(
        self,
        editor: QWidget,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        editor.setGeometry(option.rect)
