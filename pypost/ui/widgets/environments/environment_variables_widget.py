import logging
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pypost.core.constants import HIDDEN_MASK
from pypost.core.environment_messages import (
    ACTION_DELETE,
    ACTION_MOVE_DOWN,
    ACTION_MOVE_UP,
    COLUMN_HIDDEN,
    COLUMN_VALUE,
    COLUMN_VARIABLE,
    MCP_ENABLE_LABEL,
)
from pypost.core.environment_ops import validate_environment_variable_name
from pypost.core.hidden_toggle_log_policy import HiddenToggleLogPolicy
from pypost.models.models import Environment

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
        self.vars_table.itemChanged.connect(self.on_var_changed)
        self.vars_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.vars_table.customContextMenuRequested.connect(self._on_vars_table_context_menu)

        self.mcp_check = QCheckBox(MCP_ENABLE_LABEL)
        self.mcp_check.toggled.connect(self._on_mcp_toggled)
        self.mcp_check.setEnabled(False)

        layout.addWidget(self.vars_table)
        layout.addWidget(self.mcp_check)

    def load_environment(self, env: Environment | None) -> None:
        self._current_env = env
        if env is None:
            self.vars_table.setRowCount(0)
            self.mcp_check.setEnabled(False)
            self.mcp_check.setChecked(False)
            return

        self.mcp_check.setEnabled(True)
        self.mcp_check.blockSignals(True)
        self.mcp_check.setChecked(getattr(env, "enable_mcp", False))
        self.mcp_check.blockSignals(False)

        self.vars_table.blockSignals(True)
        self.vars_table.setRowCount(0)
        self.vars_table.setRowCount(len(env.variables) + 1)

        for i, (k, v) in enumerate(env.variables.items()):
            self.vars_table.setItem(i, COL_VAR, QTableWidgetItem(k))
            is_hidden = k in env.hidden_keys
            value_item = self._make_value_item(v, is_hidden)
            self.vars_table.setItem(i, COL_VAL, value_item)
            self.vars_table.setCellWidget(
                i,
                COL_HIDDEN,
                self._make_hidden_checkbox(is_hidden),
            )

        self.vars_table.setCellWidget(
            len(env.variables),
            COL_HIDDEN,
            self._make_hidden_checkbox(False),
        )

        self.vars_table.blockSignals(False)

    def _on_mcp_toggled(self, checked: bool) -> None:
        env = self._get_selected_env()
        if env is not None:
            env.enable_mcp = checked

    def _make_hidden_checkbox(self, checked: bool = False) -> QWidget:
        widget = QWidget()
        cb = QCheckBox()
        cb.setChecked(checked)
        cb.toggled.connect(self._on_hidden_toggled)
        layout = QHBoxLayout(widget)
        layout.addWidget(cb)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        return widget

    def get_hidden_checkbox(self, row: int) -> QCheckBox | None:
        widget = self.vars_table.cellWidget(row, COL_HIDDEN)
        if widget:
            return widget.findChild(QCheckBox)
        return None

    def _make_value_item(self, value: str, is_hidden: bool) -> QTableWidgetItem:
        if not is_hidden:
            return QTableWidgetItem(value)
        item = QTableWidgetItem(HIDDEN_MASK)
        item.setData(Qt.ItemDataRole.UserRole, value)
        return item

    def _extract_real_value(self, item: QTableWidgetItem | None, fallback: str) -> str:
        if not item:
            return fallback
        if item.text() != HIDDEN_MASK:
            return item.text()
        stored = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(stored, str):
            return stored
        return fallback

    def _on_hidden_toggled(self, checked: bool) -> None:
        env = self._get_selected_env()
        if env is None:
            return

        sender = self.sender()
        for i in range(self.vars_table.rowCount()):
            cb = self.get_hidden_checkbox(i)
            if cb is sender:
                k_item = self.vars_table.item(i, COL_VAR)
                if not k_item or not k_item.text():
                    return
                key = k_item.text()
                self.vars_table.blockSignals(True)
                if checked:
                    env.hidden_keys.add(key)
                    val_item = self.vars_table.item(i, COL_VAL)
                    real_val = self._extract_real_value(
                        val_item,
                        env.variables.get(key, ""),
                    )
                    self.vars_table.setItem(i, COL_VAL, self._make_value_item(real_val, True))
                else:
                    env.hidden_keys.discard(key)
                    val_item = self.vars_table.item(i, COL_VAL)
                    real_val = self._extract_real_value(
                        val_item,
                        env.variables.get(key, ""),
                    )
                    self.vars_table.setItem(
                        i,
                        COL_VAL,
                        self._make_value_item(real_val, False),
                    )
                self.vars_table.blockSignals(False)
                logger.info(
                    "env_hidden_flag_changed env_name=%s key=%s hidden=%s",
                    env.name,
                    HiddenToggleLogPolicy.format_key_name(
                        key,
                        log_hidden_key_names=self._log_hidden_key_names,
                    ),
                    checked,
                )
                return

    def _append_trailing_add_row(self) -> None:
        self.vars_table.setRowCount(self.vars_table.rowCount() + 1)
        self.vars_table.setCellWidget(
            self.vars_table.rowCount() - 1,
            COL_HIDDEN,
            self._make_hidden_checkbox(False),
        )

    def _ensure_trailing_add_row_present(self) -> None:
        row_count = self.vars_table.rowCount()
        if row_count == 0:
            self._append_trailing_add_row()
            return
        last_k = self.vars_table.item(row_count - 1, COL_VAR)
        if last_k and last_k.text():
            self._append_trailing_add_row()

    def _sync_env_variables_from_table(
        self,
        env: Environment,
        edited_item: QTableWidgetItem | None = None,
    ) -> None:
        new_vars: dict[str, str] = {}
        new_hidden: set[str] = set()
        for i in range(self.vars_table.rowCount()):
            k_item = self.vars_table.item(i, COL_VAR)
            v_item = self.vars_table.item(i, COL_VAL)
            cb = self.get_hidden_checkbox(i)

            if k_item and k_item.text():
                key = k_item.text().strip()
                is_valid, _error = validate_environment_variable_name(key)
                if not is_valid:
                    if (
                        edited_item is not None
                        and edited_item.column() == COL_VAR
                        and edited_item.row() == i
                    ):
                        old_keys = list(env.variables.keys())
                        revert = old_keys[i] if i < len(old_keys) else ""
                        k_item.setText(revert)
                    continue
                is_hidden = cb.isChecked() if cb else False
                if is_hidden:
                    new_hidden.add(key)
                    val = self._extract_real_value(v_item, env.variables.get(key, ""))
                    if (
                        edited_item is not None
                        and edited_item.column() == COL_VAL
                        and edited_item.row() == i
                    ):
                        typed = v_item.text() if v_item else ""
                        if typed != HIDDEN_MASK:
                            val = typed
                        self.vars_table.setItem(
                            i,
                            COL_VAL,
                            self._make_value_item(val, True),
                        )
                    new_vars[key] = val
                else:
                    new_vars[key] = self._extract_real_value(v_item, "")

        env.variables = new_vars
        env.hidden_keys = new_hidden

    def on_var_changed(self, item: QTableWidgetItem) -> None:
        env = self._get_selected_env()
        if env is None:
            return

        if item.row() == self.vars_table.rowCount() - 1 and item.text():
            self.vars_table.blockSignals(True)
            self._append_trailing_add_row()
            self.vars_table.blockSignals(False)

        self.vars_table.blockSignals(True)
        self._sync_env_variables_from_table(env, edited_item=item)
        self.vars_table.blockSignals(False)

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

        if row < 0 or row >= len(env.variables):
            return

        items = list(env.variables.items())

        if direction == "up" and row > 0:
            items[row], items[row - 1] = items[row - 1], items[row]
        elif direction == "down" and row < len(items) - 1:
            items[row], items[row + 1] = items[row + 1], items[row]
        else:
            return

        env.variables = dict(items)

        key = items[row - 1][0] if direction == "up" else items[row + 1][0]

        logger.info(
            "env_variable_moved env_name=%s key=%s direction=%s",
            env.name,
            HiddenToggleLogPolicy.format_key_name(
                key,
                log_hidden_key_names=self._log_hidden_key_names,
            ),
            direction,
        )

        self.load_environment(env)

    def delete_variable_at_row(self, row: int) -> None:
        env = self._get_selected_env()
        if env is None:
            return

        k_item = self.vars_table.item(row, COL_VAR)
        if not k_item or not k_item.text():
            return

        key = k_item.text()

        logger.info(
            "env_variable_deleted env_name=%s key=%s",
            env.name,
            HiddenToggleLogPolicy.format_key_name(
                key,
                log_hidden_key_names=self._log_hidden_key_names,
            ),
        )

        self.vars_table.blockSignals(True)
        self.vars_table.removeRow(row)
        self._ensure_trailing_add_row_present()
        self._sync_env_variables_from_table(env)
        self.vars_table.blockSignals(False)
