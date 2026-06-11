"""Item delegate for inline collection tree item rename."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QLineEdit,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
)

from pypost.models.models import RequestData


class CollectionItemRenameDelegate(QStyledItemDelegate):
    """Inline editor for collection tree rename with validation on commit."""

    def __init__(
        self,
        is_rename_index: Callable[[object], bool],
        on_committed: Callable[[str], None],
        on_cancelled: Callable[[], None],
        on_rejected_empty: Callable[[], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._is_rename_index = is_rename_index
        self._on_committed = on_committed
        self._on_cancelled = on_cancelled
        self._on_rejected_empty = on_rejected_empty
        self.closeEditor.connect(self._on_close_editor)

    def createEditor(
        self,
        parent: QWidget,
        option: QStyleOptionViewItem,
        index,
    ) -> QWidget | None:
        if not self._is_rename_index(index):
            return None
        editor = QLineEdit(parent)
        editor.setClearButtonEnabled(False)
        return editor

    def setEditorData(self, editor: QWidget, index) -> None:
        if not isinstance(editor, QLineEdit):
            super().setEditorData(editor, index)
            return

        item = index.model().itemFromIndex(index)
        editor.setText(self._editable_text(item))
        editor.setToolTip("")

    def setModelData(self, editor: QWidget, model, index) -> None:
        if not isinstance(editor, QLineEdit):
            super().setModelData(editor, model, index)
            return

        new_name = editor.text().strip()
        if not new_name:
            self._on_rejected_empty()
            old_text = self._editable_text(index.model().itemFromIndex(index))
            model.setData(index, old_text, Qt.ItemDataRole.EditRole)
            editor.setToolTip("Name cannot be empty.")
            return

        self._on_committed(new_name)

    def _on_close_editor(self, _editor: QWidget, hint) -> None:
        if hint == QAbstractItemDelegate.EndEditHint.RevertModelCache:
            self._on_cancelled()

    @staticmethod
    def _editable_text(item: QStandardItem | None) -> str:
        if item is None:
            return ""
        data = item.data(Qt.UserRole)
        if isinstance(data, RequestData):
            return data.name
        return item.text()
