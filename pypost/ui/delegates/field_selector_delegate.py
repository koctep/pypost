"""Advisory field-selector editor delegate for Hidden Fields (PYPOST-1387)."""

from __future__ import annotations

from PySide6.QtCore import QAbstractItemModel, QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtWidgets import (
    QLineEdit,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
)

from pypost.core.field_selector_syntax import validate_field_selector
from pypost.ui.styles.ui_tokens import (
    VALIDATION_LABEL_BACKGROUND,
    VALIDATION_LABEL_FOREGROUND,
)

__all__ = ["FieldSelectorDelegate"]


class FieldSelectorDelegate(QStyledItemDelegate):
    """Live editor feedback for field selectors; always commits user text."""

    def createEditor(
        self,
        parent: QWidget | None,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QWidget:
        editor = QLineEdit(parent)
        editor.setClearButtonEnabled(False)
        editor.textChanged.connect(lambda text: self._apply_live_feedback(editor, text))
        return editor

    def setEditorData(
        self,
        editor: QWidget,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        if isinstance(editor, QLineEdit):
            text = index.data(Qt.ItemDataRole.EditRole) or ""
            editor.setText(str(text))
            self._apply_live_feedback(editor, editor.text())
        else:
            super().setEditorData(editor, index)

    def setModelData(
        self,
        editor: QWidget,
        model: QAbstractItemModel,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        if not isinstance(editor, QLineEdit):
            super().setModelData(editor, model, index)
            return
        # Advisory: always commit the typed text (including invalid drafts).
        model.setData(index, editor.text(), Qt.ItemDataRole.EditRole)

    @staticmethod
    def _apply_live_feedback(editor: QLineEdit, text: str) -> None:
        result = validate_field_selector(text)
        if result.ok or result.is_empty:
            editor.setStyleSheet("")
            editor.setToolTip("")
            return
        guidance = f"{result.message} {result.suggestions}".strip()
        editor.setToolTip(guidance)
        editor.setStyleSheet(
            f"QLineEdit {{ background-color: {VALIDATION_LABEL_BACKGROUND}; "
            f"color: {VALIDATION_LABEL_FOREGROUND}; }}"
        )
