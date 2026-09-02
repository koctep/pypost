"""Key-value table for custom MCP server headers with variable autocompletion."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import re
from typing import TYPE_CHECKING

from PySide6.QtCore import QAbstractItemModel, QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtGui import (
    QColor,
    QContextMenuEvent,
    QFocusEvent,
    QHideEvent,
    QKeyEvent,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidgetItem,
    QWidget,
)

from pypost.ui.widgets.empty_row_key_value_table import EmptyRowKeyValueTable
from pypost.ui.widgets.variable_autocomplete_line_edit import (
    VariableAutocompleteDelegate as SharedVariableAutocompleteDelegate,
    VariableAutocompleteLineEdit as SharedVariableAutocompleteLineEdit,
)
from pypost.ui.styles.ui_tokens import (
    AUTOCOMPLETE_POPUP_MAX_HEIGHT,
    AUTOCOMPLETE_POPUP_MIN_WIDTH,
    AUTOCOMPLETE_POPUP_ROW_HEIGHT,
    AUTOCOMPLETE_POPUP_VERTICAL_PADDING,
)

if TYPE_CHECKING:
    from pypost.models.models import Environment

__all__ = [
    "HeaderValidationEngine",
    "HeaderValidationResult",
    "McpServerHeadersTable",
    "VariableAutocompleteDelegate",
    "VariableAutocompleteLineEdit",
    "validate_header_key",
    "validate_header_value",
]

logger = logging.getLogger(__name__)

RFC_7230_TOKEN_RE = re.compile(r"^[a-zA-Z0-9!#$%&'*+\-.^_`|~]+$")


@dataclass(frozen=True)
class HeaderValidationResult:
    """Outcome of validating a single header field (key or value)."""

    is_valid: bool
    is_structural_error: bool
    message: str


def validate_header_key(key: str, has_value: bool) -> HeaderValidationResult | None:
    """Validate RFC 7230 header field name requirements.

    Returns None for blank rows without values.
    """
    stripped_key = key.strip()
    if not stripped_key:
        if has_value:
            return HeaderValidationResult(
                is_valid=False,
                is_structural_error=True,
                message="Header key cannot be empty when a value is specified.",
            )
        return None

    if " " in key or "\t" in key:
        return HeaderValidationResult(
            is_valid=False,
            is_structural_error=True,
            message=f"Header key '{key}' cannot contain spaces.",
        )
    if ":" in key:
        return HeaderValidationResult(
            is_valid=False,
            is_structural_error=True,
            message=f"Header key '{key}' cannot contain colons.",
        )
    if not RFC_7230_TOKEN_RE.match(stripped_key):
        return HeaderValidationResult(
            is_valid=False,
            is_structural_error=True,
            message=f"Header key '{key}' contains invalid characters per RFC 7230.",
        )
    return HeaderValidationResult(
        is_valid=True,
        is_structural_error=False,
        message="",
    )


def validate_header_value(
    value: str, env_vars: set[str] | None
) -> list[HeaderValidationResult]:
    """Validate template syntax and check variable references against the environment."""
    results: list[HeaderValidationResult] = []
    if not value:
        return results

    # 1. Unclosed template expression
    cleaned = re.sub(r"\{\{[^{}]*\}\}", "", value)
    if "{{" in cleaned:
        results.append(
            HeaderValidationResult(
                is_valid=False,
                is_structural_error=False,
                message="Unclosed template placeholder '{{'. Missing closing '}}'.",
            )
        )

    # 2. Empty placeholder
    if re.search(r"\{\{\s*\}\}", value):
        results.append(
            HeaderValidationResult(
                is_valid=False,
                is_structural_error=False,
                message="Template placeholder '{{ }}' cannot be empty.",
            )
        )

    # 3. Undefined variables
    for m in re.finditer(r"\{\{\s*([^{}\s]+)\s*\}\}", value):
        var_name = m.group(1)
        if env_vars is not None and var_name not in env_vars:
            results.append(
                HeaderValidationResult(
                    is_valid=False,
                    is_structural_error=False,
                    message=f"Variable '{var_name}' is not defined in the active environment.",
                )
            )

    return results


class HeaderValidationEngine:
    """Namespace providing header validation utilities."""

    @staticmethod
    def validate_key(key: str, has_value: bool) -> HeaderValidationResult | None:
        return validate_header_key(key, has_value)

    @staticmethod
    def validate_value(
        value: str, env_vars: set[str] | None
    ) -> list[HeaderValidationResult]:
        return validate_header_value(value, env_vars)


class _LegacyVariableAutocompleteLineEdit(QLineEdit):
    """QLineEdit editor with inline {{ autocompletion popup for environment variables."""

    def __init__(
        self,
        variables: list[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._variables: list[str] = list(variables or [])
        self._popup = QListWidget(self)
        self._popup.setObjectName("autocompletePopup")
        self._popup.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self._popup.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._popup.itemClicked.connect(self._on_item_clicked)
        self.textEdited.connect(self._on_text_edited)

    def set_variables(self, variables: list[str]) -> None:
        self._variables = list(variables)

    def is_popup_visible(self) -> bool:
        return self._popup.isVisible()

    def current_candidates(self) -> list[str]:
        return [self._popup.item(i).text() for i in range(self._popup.count())]

    def dismiss_popup(self) -> None:
        self._popup.hide()

    def _update_popup(self, candidates: list[str]) -> None:
        self._popup.clear()
        if not candidates:
            self.dismiss_popup()
            return
        for item in candidates:
            self._popup.addItem(item)
        self._popup.setCurrentRow(0)

        if self.isVisible():
            global_pos = self.mapToGlobal(self.rect().bottomLeft())
            self._popup.move(global_pos)
            self._popup.resize(
                max(self.width(), AUTOCOMPLETE_POPUP_MIN_WIDTH),
                min(
                    AUTOCOMPLETE_POPUP_MAX_HEIGHT,
                    AUTOCOMPLETE_POPUP_ROW_HEIGHT * len(candidates)
                    + AUTOCOMPLETE_POPUP_VERTICAL_PADDING,
                ),
            )
        self._popup.show()

    def trigger_autocomplete(self) -> None:
        text = self.text()
        cursor_pos = self.cursorPosition()
        if cursor_pos == 0 and len(text) > 0:
            cursor_pos = len(text)
            self.setCursorPosition(cursor_pos)
        prefix_text = text[:cursor_pos]
        m = re.search(r"\{\{\s*([a-zA-Z0-9_]*)$", prefix_text)
        if not m:
            m = re.search(r"\{\{\s*([a-zA-Z0-9_]*)(?:\s*\}\})?", text)
        if m:
            token = m.group(1)
            matches = [v for v in self._variables if v.upper().startswith(token.upper())]
            logger.debug(
                "Autocomplete triggered: prefix=%r, matched %d candidate(s)",
                token,
                len(matches),
            )
            self._update_popup(matches)
        else:
            self.dismiss_popup()

    def _on_text_edited(self, _text: str) -> None:
        self.trigger_autocomplete()

    def apply_completion(self, candidate: str) -> None:
        logger.info("Autocomplete selected variable: %s", candidate)
        text = self.text()
        cursor_pos = self.cursorPosition()
        if cursor_pos == 0 and len(text) > 0:
            cursor_pos = len(text)
        prefix_text = text[:cursor_pos]
        suffix_text = text[cursor_pos:]

        m = re.search(r"\{\{\s*([a-zA-Z0-9_]*)$", prefix_text)
        if m:
            start_idx = m.start()
            suffix_match = re.match(r"^\s*\}\}", suffix_text)
            if suffix_match:
                suffix_text = suffix_text[suffix_match.end():]
            inserted = f"{{{{ {candidate} }}}}"
            new_text = text[:start_idx] + inserted + suffix_text
            self.setText(new_text)
            self.setCursorPosition(start_idx + len(inserted))
        else:
            m_full = re.search(r"\{\{\s*([a-zA-Z0-9_]*)(?:\s*\}\})?$", text)
            if m_full:
                start_idx = m_full.start()
                inserted = f"{{{{ {candidate} }}}}"
                new_text = text[:start_idx] + inserted
                self.setText(new_text)
                self.setCursorPosition(len(new_text))
            else:
                self.insert(f"{{{{ {candidate} }}}}")
        self.dismiss_popup()

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        self.apply_completion(item.text())

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self.is_popup_visible():
            key = event.key()
            if key == Qt.Key.Key_Down:
                cur = self._popup.currentRow()
                cnt = self._popup.count()
                if cnt > 0:
                    self._popup.setCurrentRow((cur + 1) % cnt)
                event.accept()
                return
            if key == Qt.Key.Key_Up:
                cur = self._popup.currentRow()
                cnt = self._popup.count()
                if cnt > 0:
                    self._popup.setCurrentRow((cur - 1 + cnt) % cnt)
                event.accept()
                return
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
                item = self._popup.currentItem() or (
                    self._popup.item(0) if self._popup.count() > 0 else None
                )
                if item:
                    self.apply_completion(item.text())
                    event.accept()
                    return
            if key == Qt.Key.Key_Escape:
                self.dismiss_popup()
                event.accept()
                return
        super().keyPressEvent(event)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        self.dismiss_popup()
        super().focusOutEvent(event)

    def hideEvent(self, event: QHideEvent) -> None:
        self.dismiss_popup()
        super().hideEvent(event)


class _LegacyVariableAutocompleteDelegate(QStyledItemDelegate):
    """Delegate providing VariableAutocompleteLineEdit for the Value column."""

    def __init__(self, parent: McpServerHeadersTable) -> None:
        super().__init__(parent)

    def createEditor(
        self,
        parent: QWidget | None,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QWidget:
        if index.column() == 1:
            table = self.parent()
            var_names = (
                table.environment_variable_names
                if isinstance(table, McpServerHeadersTable)
                else []
            )
            return VariableAutocompleteLineEdit(variables=var_names, parent=parent)
        return super().createEditor(parent, option, index)

    def setEditorData(
        self, editor: QWidget, index: QModelIndex | QPersistentModelIndex
    ) -> None:
        if isinstance(editor, VariableAutocompleteLineEdit):
            val = index.data(Qt.ItemDataRole.EditRole) or ""
            editor.setText(str(val))
        else:
            super().setEditorData(editor, index)

    def setModelData(
        self,
        editor: QWidget,
        model: QAbstractItemModel,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        if isinstance(editor, VariableAutocompleteLineEdit):
            model.setData(index, editor.text(), Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(
        self,
        editor: QWidget,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        editor.setGeometry(option.rect)


# Keep the historical import surface while sharing the implementation.
VariableAutocompleteDelegate = SharedVariableAutocompleteDelegate
VariableAutocompleteLineEdit = SharedVariableAutocompleteLineEdit


class McpServerHeadersTable(EmptyRowKeyValueTable):
    """Two-column Key-Value table for custom headers with autocomplete and syntax validation."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, strip_keys=True)
        self._environment: Environment | None = None
        self._environment_variable_names: list[str] = []
        self._structural_errors: list[str] = []
        self._validation_warnings: list[str] = []
        self._validating: bool = False

        self.setItem(0, 0, QTableWidgetItem(""))
        self.setItem(0, 1, QTableWidgetItem(""))

        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self._delegate = VariableAutocompleteDelegate(self)
        self.setItemDelegateForColumn(1, self._delegate)

    @property
    def environment_variable_names(self) -> list[str]:
        return list(self._environment_variable_names)

    def set_environment(self, environment: Environment | None) -> None:
        """Bind active environment context, updating autocomplete and validation."""
        self._environment = environment
        if environment:
            vars_dict = environment.variables or {}
            hidden_keys: set[str] = getattr(environment, "hidden_keys", set()) or set()
            self.set_environment_variables(vars_dict, hidden_keys)
            logger.debug(
                "Bound environment '%s' (%s) with %d variables to headers table",
                environment.name,
                environment.id,
                len(self._environment_variable_names),
            )
        else:
            self.set_environment_variables({}, set())
            logger.debug("Cleared environment binding from headers table")

    def set_environment_variables(
        self,
        variables: dict[str, str],
        hidden_keys: set[str] | None = None,
    ) -> None:
        """Set available environment variables and mask sensitive keys."""
        self._environment_variable_names = sorted(variables.keys())
        self.set_variables(variables)
        self.set_hidden_keys(hidden_keys or set())
        self.validate_rows()

    def set_data(self, data: dict[str, str]) -> None:
        """Populate table with header pairs and validate rows."""
        super().set_data(data)
        for r in range(self.rowCount()):
            for c in range(2):
                if not self.item(r, c):
                    self.setItem(r, c, QTableWidgetItem(""))
        self.validate_rows()

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        super()._on_item_changed(item)
        for r in range(self.rowCount()):
            for c in range(2):
                if not self.item(r, c):
                    self.setItem(r, c, QTableWidgetItem(""))
        self.validate_rows()

    def validate_rows(self) -> None:
        """Inspect all rows for RFC 7230 key errors and template syntax/variable warnings."""
        if self._validating:
            return
        self._validating = True
        try:
            self._structural_errors.clear()
            self._validation_warnings.clear()

            known_vars = set(self._environment_variable_names)
            total_rows = self.rowCount()

            for r in range(total_rows):
                key_item = self.item(r, 0)
                val_item = self.item(r, 1)

                key_str = key_item.text() if key_item else ""
                val_str = val_item.text() if val_item else ""

                if r == total_rows - 1 and not key_str and not val_str:
                    if key_item:
                        key_item.setToolTip("")
                        key_item.setData(Qt.ItemDataRole.ForegroundRole, None)
                    if val_item:
                        val_item.setToolTip("")
                        val_item.setData(Qt.ItemDataRole.ForegroundRole, None)
                    continue

                has_value = bool(val_str.strip())
                key_res = validate_header_key(key_str, has_value=has_value)
                if key_res and not key_res.is_valid:
                    if key_res.is_structural_error:
                        self._structural_errors.append(f"Row {r + 1}: {key_res.message}")
                    if key_item:
                        key_item.setToolTip(key_res.message)
                        key_item.setForeground(QColor("#b00020"))
                else:
                    if key_item:
                        key_item.setToolTip("")
                        key_item.setData(Qt.ItemDataRole.ForegroundRole, None)

                val_res_list = validate_header_value(val_str, known_vars)
                if val_res_list:
                    messages = [res.message for res in val_res_list]
                    self._validation_warnings.extend([f"Row {r + 1}: {m}" for m in messages])
                    if val_item:
                        val_item.setToolTip("\n".join(messages))
                        val_item.setForeground(QColor("#e65100"))
                else:
                    if val_item:
                        val_item.setToolTip("")
                        val_item.setData(Qt.ItemDataRole.ForegroundRole, None)

            # Note: Validation messages only contain header keys and variable names,
            # never raw secret values.
            if self._structural_errors:
                logger.debug(
                    "MCP server headers table structural errors (%d): %s",
                    len(self._structural_errors),
                    self._structural_errors,
                )
            if self._validation_warnings:
                logger.debug(
                    "MCP server headers table validation warnings (%d): %s",
                    len(self._validation_warnings),
                    self._validation_warnings,
                )
        finally:
            self._validating = False

    def has_structural_errors(self) -> bool:
        self.validate_rows()
        return len(self._structural_errors) > 0

    def get_validation_errors(self) -> list[str]:
        self.validate_rows()
        return list(self._structural_errors)

    def get_validation_warnings(self) -> list[str]:
        self.validate_rows()
        return list(self._validation_warnings)

    def remove_selected_rows(self) -> None:
        """Remove selected data rows while preserving the trailing empty row."""
        selected_indexes = self.selectedIndexes()
        if not selected_indexes:
            return
        rows_to_delete = sorted(set(idx.row() for idx in selected_indexes), reverse=True)
        last_row = self.rowCount() - 1
        self.blockSignals(True)
        try:
            for r in rows_to_delete:
                if r == last_row:
                    continue
                self.removeRow(r)
                last_row = self.rowCount() - 1
        finally:
            self.blockSignals(False)

        if self.rowCount() == 0:
            self.setRowCount(1)
            self.setItem(0, 0, QTableWidgetItem(""))
            self.setItem(0, 1, QTableWidgetItem(""))
        else:
            last_r = self.rowCount() - 1
            item_0 = self.item(last_r, 0)
            item_1 = self.item(last_r, 1)
            key_text = item_0.text().strip() if item_0 is not None else ""
            val_text = item_1.text().strip() if item_1 is not None else ""
            if key_text or val_text:
                self.setRowCount(self.rowCount() + 1)
                self.setItem(self.rowCount() - 1, 0, QTableWidgetItem(""))
                self.setItem(self.rowCount() - 1, 1, QTableWidgetItem(""))

        self.validate_rows()

    def clear_all_rows(self) -> None:
        """Clear all header rows and reset to a single trailing empty row."""
        self.set_data({})

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            if self.state() != QAbstractItemView.State.EditingState:
                self.remove_selected_rows()
                event.accept()
                return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        menu = QMenu(self)
        delete_action = menu.addAction("Delete Row")
        clear_action = menu.addAction("Clear All")
        action = menu.exec(event.globalPos())
        if action == delete_action:
            self.remove_selected_rows()
        elif action == clear_action:
            self.clear_all_rows()
