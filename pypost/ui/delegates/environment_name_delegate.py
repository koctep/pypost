"""Item delegates for environment management UI."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QStyledItemDelegate, QStyleOptionViewItem, QWidget

from pypost.core.environment_ops import validate_environment_rename


class EnvironmentNameDelegate(QStyledItemDelegate):
    """Inline editor for environment list names with validation on commit."""

    def __init__(
        self,
        get_existing_names: Callable[[], list[str]],
        on_rename_accepted: Callable[[int, str, str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._get_existing_names = get_existing_names
        self._on_rename_accepted = on_rename_accepted

    def createEditor(
        self,
        parent: QWidget,
        option: QStyleOptionViewItem,
        index,
    ) -> QWidget:
        editor = QLineEdit(parent)
        editor.setClearButtonEnabled(False)
        return editor

    def setEditorData(self, editor: QWidget, index) -> None:
        if isinstance(editor, QLineEdit):
            editor.setText(index.data(Qt.ItemDataRole.DisplayRole) or "")
            editor.setToolTip("")
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor: QWidget, model, index) -> None:
        if not isinstance(editor, QLineEdit):
            super().setModelData(editor, model, index)
            return

        row = index.row()
        old_name = index.data(Qt.ItemDataRole.DisplayRole) or ""
        new_text = editor.text()
        accepted, normalized, error = validate_environment_rename(
            new_text,
            old_name,
            self._get_existing_names(),
            row,
        )

        if not accepted:
            model.setData(index, old_name, Qt.ItemDataRole.EditRole)
            editor.setToolTip(error)
            return

        if normalized == old_name:
            model.setData(index, old_name, Qt.ItemDataRole.EditRole)
            return

        model.setData(index, normalized, Qt.ItemDataRole.EditRole)
        self._on_rename_accepted(row, old_name, normalized)
