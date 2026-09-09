from __future__ import annotations

import logging
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHeaderView,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pypost.core.constants import HIDDEN_MASK
from pypost.core.environment_variable_draft import EnvironmentVariableTableDraft
from pypost.core.environment_messages import (
    ACTION_DELETE,
    ACTION_MOVE_DOWN,
    ACTION_MOVE_UP,
    COLUMN_HIDDEN,
    COLUMN_VALUE,
    COLUMN_VARIABLE,
    MCP_ENABLE_LABEL,
    MCP_ENABLE_TOOLTIP,
)
from pypost.core.hidden_toggle_log_policy import HiddenToggleLogPolicy
from pypost.models.models import Environment
from pypost.ui.collection_item_dialogs import show_invalid_variable_name_error

HIDDEN_COLUMN_TOOLTIP = (
    "Hidden variables are masked in the UI and encrypted at rest when encryption is enabled. "
    "Non-hidden variables are stored as plaintext."
)

logger = logging.getLogger(__name__)

COL_VAR = 0
COL_VAL = 1
COL_HIDDEN = 2


class EnvironmentVariablesWidget(QWidget):
    """Right-pane table for editing variables of the selected environment."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        log_hidden_key_names: bool = False,
        get_selected_env: Callable[[], Environment | None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._log_hidden_key_names = log_hidden_key_names
        self._get_selected_env = get_selected_env or (lambda: None)
        self._current_env: Environment | None = None
        self._draft: EnvironmentVariableTableDraft | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.vars_table = QTableWidget(0, 3)
        self.vars_table.setHorizontalHeaderLabels(
            [COLUMN_VARIABLE, COLUMN_VALUE, COLUMN_HIDDEN],
        )
        header = self.vars_table.horizontalHeader()
        header.setSectionResizeMode(COL_VAR, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_VAL, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_HIDDEN, QHeaderView.ResizeToContents)
        hidden_header = self.vars_table.horizontalHeaderItem(COL_HIDDEN)
        if hidden_header is not None:
            hidden_header.setToolTip(HIDDEN_COLUMN_TOOLTIP)
        self.vars_table.itemChanged.connect(self.on_var_changed)
        self.vars_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.vars_table.customContextMenuRequested.connect(self._on_vars_table_context_menu)

        self.mcp_check = QCheckBox(MCP_ENABLE_LABEL)
        self.mcp_check.setToolTip(MCP_ENABLE_TOOLTIP)
        self.mcp_check.toggled.connect(self._on_mcp_toggled)
        self.mcp_check.setEnabled(False)

        layout.addWidget(self.vars_table)
        layout.addWidget(self.mcp_check)

    def load_environment(self, env: Environment | None) -> None:
        self._current_env = env
        self._draft = None if env is None else EnvironmentVariableTableDraft(env)
        if env is None:
            self.vars_table.setRowCount(0)
            self.mcp_check.setEnabled(False)
            self.mcp_check.setChecked(False)
            return

        self.mcp_check.setEnabled(True)
        self.mcp_check.blockSignals(True)
        self.mcp_check.setChecked(getattr(env, "enable_mcp", False))
        self.mcp_check.blockSignals(False)

        self._render_draft()

    def _on_mcp_toggled(self, checked: bool) -> None:
        env = self._get_selected_env()
        if env is not None:
            env.enable_mcp = checked

    def _make_hidden_item(self, checked: bool = False) -> QTableWidgetItem:
        item = QTableWidgetItem()
        flags = item.flags() | Qt.ItemFlag.ItemIsUserCheckable
        item.setFlags(flags & ~Qt.ItemFlag.ItemIsEditable)
        item.setCheckState(
            Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked,
        )
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setToolTip(HIDDEN_COLUMN_TOOLTIP)
        item.setData(Qt.ItemDataRole.AccessibleTextRole, COLUMN_HIDDEN)
        return item

    def get_hidden_item(self, row: int) -> QTableWidgetItem | None:
        return self.vars_table.item(row, COL_HIDDEN)

    def _make_value_item(self, value: str, is_hidden: bool) -> QTableWidgetItem:
        if not is_hidden:
            return QTableWidgetItem(value)
        item = QTableWidgetItem(HIDDEN_MASK)
        item.setData(Qt.ItemDataRole.UserRole, value)
        return item

    def _render_draft(self) -> None:
        if self._draft is None:
            self.vars_table.setRowCount(0)
            return
        self.vars_table.blockSignals(True)
        self.vars_table.setRowCount(len(self._draft.rows))
        for index, row in enumerate(self._draft.rows):
            self.vars_table.setItem(index, COL_VAR, QTableWidgetItem(row.key))
            self.vars_table.setItem(
                index,
                COL_VAL,
                self._make_value_item(row.value, row.hidden),
            )
            self.vars_table.setItem(index, COL_HIDDEN, self._make_hidden_item(row.hidden))
        self.vars_table.blockSignals(False)

    def _apply_draft(self, env: Environment) -> None:
        if self._draft is not None:
            self._draft.apply_to(env)

    def _reject_key_edit(self, item: QTableWidgetItem, message: str) -> None:
        if self._draft is None:
            return
        row = self._draft.row(item.row())
        self.vars_table.blockSignals(True)
        item.setText(row.key if row is not None else "")
        self.vars_table.blockSignals(False)
        show_invalid_variable_name_error(self, message)
        self.vars_table.setCurrentItem(item)
        self.vars_table.editItem(item)

    def _on_hidden_item_changed(self, item: QTableWidgetItem) -> None:
        env = self._get_selected_env()
        if env is None:
            return

        if self._draft is None:
            return
        row_index = item.row()
        row = self._draft.row(row_index)
        if row is None:
            return
        checked = item.checkState() == Qt.CheckState.Checked
        self._draft.edit_hidden(row_index, checked)
        self._apply_draft(env)
        self.vars_table.blockSignals(True)
        self.vars_table.setItem(
            row_index,
            COL_VAL,
            self._make_value_item(row.value, checked),
        )
        self.vars_table.blockSignals(False)
        if not row.key:
            return
        logger.info(
            "env_hidden_flag_changed env_name=%s key=%s hidden=%s",
            env.name,
            HiddenToggleLogPolicy.format_key_name(
                row.key,
                log_hidden_key_names=self._log_hidden_key_names,
            ),
            checked,
        )

    def _append_trailing_add_row(self) -> None:
        self.vars_table.setRowCount(self.vars_table.rowCount() + 1)
        last = self.vars_table.rowCount() - 1
        self.vars_table.setItem(last, COL_VAR, QTableWidgetItem(""))
        self.vars_table.setItem(last, COL_VAL, QTableWidgetItem(""))
        self.vars_table.setItem(last, COL_HIDDEN, self._make_hidden_item(False))

    def on_var_changed(self, item: QTableWidgetItem) -> None:
        env = self._get_selected_env()
        if env is None:
            return

        if item.column() == COL_HIDDEN:
            self._on_hidden_item_changed(item)
            return
        if self._draft is None:
            return

        row = self._draft.row(item.row())
        if row is None:
            return
        if item.column() == COL_VAR:
            if not row.key and not item.text().strip():
                return
            previous_count = len(self._draft.rows)
            validation = self._draft.edit_key(item.row(), item.text())
            if not validation.accepted:
                self._reject_key_edit(item, validation.message)
                return
            self.vars_table.blockSignals(True)
            item.setText(validation.normalized_name)
            if len(self._draft.rows) > previous_count:
                self._append_trailing_add_row()
            self.vars_table.blockSignals(False)
        elif item.column() == COL_VAL:
            value = item.text()
            if row.hidden and value == HIDDEN_MASK:
                value = row.value
            self._draft.edit_value(item.row(), value)
            if row.hidden:
                self.vars_table.blockSignals(True)
                self.vars_table.setItem(
                    item.row(),
                    COL_VAL,
                    self._make_value_item(value, True),
                )
                self.vars_table.blockSignals(False)
        self._apply_draft(env)

    def _on_vars_table_context_menu(self, pos) -> None:
        row = self.vars_table.rowAt(pos.y())
        if row < 0:
            return

        k_item = self.vars_table.item(row, COL_VAR)
        if not k_item or not k_item.text():
            return

        env = self._get_selected_env()
        if env is None:
            return

        var_count = len(env.variables)

        menu = QMenu(self)

        move_up_action = menu.addAction(ACTION_MOVE_UP)
        move_up_action.setEnabled(0 < row < var_count)

        move_down_action = menu.addAction(ACTION_MOVE_DOWN)
        move_down_action.setEnabled(0 <= row < var_count - 1)

        menu.addSeparator()

        delete_action = menu.addAction(ACTION_DELETE)
        chosen = menu.exec(self.vars_table.mapToGlobal(pos))
        if chosen == delete_action:
            self.delete_variable_at_row(row)
        elif chosen == move_up_action:
            self.move_variable_at_row(row, "up")
        elif chosen == move_down_action:
            self.move_variable_at_row(row, "down")

    def move_variable_at_row(self, row: int, direction: str) -> None:
        env = self._get_selected_env()
        if env is None:
            return

        if self._draft is None:
            return
        moved_to = self._draft.move(row, direction)
        if moved_to is None:
            return
        moved = self._draft.row(moved_to)
        if moved is None:
            return
        self._apply_draft(env)

        logger.info(
            "env_variable_moved env_name=%s key=%s direction=%s",
            env.name,
            HiddenToggleLogPolicy.format_key_name(
                moved.key,
                log_hidden_key_names=self._log_hidden_key_names,
            ),
            direction,
        )

        self._render_draft()

    def delete_variable_at_row(self, row: int) -> None:
        env = self._get_selected_env()
        if env is None:
            return

        if self._draft is None:
            return
        deleted = self._draft.delete(row)
        if deleted is None:
            return

        logger.info(
            "env_variable_deleted env_name=%s key=%s",
            env.name,
            HiddenToggleLogPolicy.format_key_name(
                deleted.key,
                log_hidden_key_names=self._log_hidden_key_names,
            ),
        )

        self._apply_draft(env)
        self._render_draft()
