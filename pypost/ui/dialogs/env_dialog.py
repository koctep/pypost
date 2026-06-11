import logging
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pypost.core.environment_ops import (
    clone_environment,
    validate_environment_rename,
    validate_environment_variable_name,
)
from pypost.ui.delegates import EnvironmentNameDelegate
from pypost.core.hidden_toggle_log_policy import HiddenToggleLogPolicy
from pypost.models.models import Environment
from pypost.core.constants import HIDDEN_MASK

logger = logging.getLogger(__name__)

COL_VAR = 0
COL_VAL = 1
COL_HIDDEN = 2


class EnvironmentDialog(QDialog):
    def __init__(
        self,
        environments: List[Environment],
        parent=None,
        current_env_name: str = None,
        log_hidden_key_names: bool = False,
    ):
        super().__init__(parent)
        self.setWindowTitle("Manage Environments")
        self.resize(800, 600)
        self.environments = environments
        self.current_env_name = current_env_name
        self._log_hidden_key_names = log_hidden_key_names

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Left: Environment List
        left_layout = QVBoxLayout()
        self.env_list = QListWidget()
        self.env_list.currentRowChanged.connect(self.on_env_selected)
        self.env_list.setItemDelegate(
            EnvironmentNameDelegate(
                get_existing_names=lambda: [e.name for e in self.environments],
                on_rename_accepted=self._on_environment_renamed,
                parent=self.env_list,
            )
        )
        self.env_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu,
        )
        self.env_list.customContextMenuRequested.connect(
            self._on_env_list_context_menu,
        )

        rename_shortcut = QShortcut(QKeySequence("F2"), self.env_list)
        rename_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        rename_shortcut.activated.connect(self._rename_current_environment)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_environment)

        left_layout.addWidget(self.env_list)
        left_layout.addWidget(add_btn)

        layout.addLayout(left_layout, 1)

        # Right: Variables Table
        right_layout = QVBoxLayout()
        self.vars_table = QTableWidget(0, 3)
        self.vars_table.setHorizontalHeaderLabels(
            ["Variable", "Value", "Hidden"],
        )
        header = self.vars_table.horizontalHeader()
        header.setSectionResizeMode(COL_VAR, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_VAL, QHeaderView.Stretch)
        header.setSectionResizeMode(
            COL_HIDDEN,
            QHeaderView.ResizeToContents,
        )
        self.vars_table.itemChanged.connect(self.on_var_changed)
        self.vars_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.vars_table.customContextMenuRequested.connect(self._on_vars_table_context_menu)

        self.mcp_check = QCheckBox(
            "Enable MCP (Model Context Protocol)",
        )
        self.mcp_check.toggled.connect(self.on_mcp_toggled)
        self.mcp_check.setEnabled(False)

        right_layout.addWidget(self.vars_table)
        right_layout.addWidget(self.mcp_check)
        layout.addLayout(right_layout, 3)

        self.load_list()

    def load_list(self):
        self.env_list.blockSignals(True)
        self.env_list.clear()
        target_row = 0
        for i, env in enumerate(self.environments):
            item = QListWidgetItem(env.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.env_list.addItem(item)
            if self.current_env_name and env.name == self.current_env_name:
                target_row = i

        if self.environments:
            self.env_list.setCurrentRow(target_row)
        self.env_list.blockSignals(False)

    def add_environment(self):
        name, ok = QInputDialog.getText(self, "New Environment", "Name:")
        if ok and name:
            env = Environment(name=name)
            self.environments.append(env)
            self.env_list.blockSignals(True)
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.env_list.addItem(item)
            self.env_list.setCurrentRow(len(self.environments) - 1)
            self.env_list.blockSignals(False)

    def delete_environment(self, row: int | None = None) -> None:
        if row is None:
            row = self.env_list.currentRow()
        if row < 0:
            return

        deleted_env = self.environments[row]
        confirm = QMessageBox.question(
            self,
            "Delete Environment",
            f'Are you sure you want to delete "{deleted_env.name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        logger.info("environment_deleted env_name=%s", deleted_env.name)
        del self.environments[row]
        self.env_list.takeItem(row)

    def _on_vars_table_context_menu(self, pos) -> None:
        row = self.vars_table.rowAt(pos.y())
        if row < 0:
            return

        k_item = self.vars_table.item(row, COL_VAR)
        if not k_item or not k_item.text():
            return

        env_row = self.env_list.currentRow()
        if env_row < 0:
            return

        env = self.environments[env_row]
        var_count = len(env.variables)

        menu = QMenu(self)

        move_up_action = menu.addAction("Move Up")
        move_up_action.setEnabled(0 < row < var_count)

        move_down_action = menu.addAction("Move Down")
        move_down_action.setEnabled(0 <= row < var_count - 1)

        menu.addSeparator()

        delete_action = menu.addAction("Delete")
        chosen = menu.exec(self.vars_table.mapToGlobal(pos))
        if chosen == delete_action:
            self._delete_variable_at_row(row)
        elif chosen == move_up_action:
            self._move_variable_at_row(row, "up")
        elif chosen == move_down_action:
            self._move_variable_at_row(row, "down")

    def _move_variable_at_row(self, row: int, direction: str) -> None:
        env_row = self.env_list.currentRow()
        if env_row < 0:
            return

        env = self.environments[env_row]

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

        # The key we moved is now at row - 1 or row + 1
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

        self.on_env_selected(env_row)

    def _delete_variable_at_row(self, row: int) -> None:
        env_row = self.env_list.currentRow()
        if env_row < 0:
            return

        env = self.environments[env_row]
        k_item = self.vars_table.item(row, COL_VAR)
        if not k_item or not k_item.text():
            return

        key = k_item.text()

        env.variables.pop(key, None)
        env.hidden_keys.discard(key)

        logger.info(
            "env_variable_deleted env_name=%s key=%s",
            env.name,
            HiddenToggleLogPolicy.format_key_name(
                key,
                log_hidden_key_names=self._log_hidden_key_names,
            ),
        )

        self.on_env_selected(env_row)

    def _on_env_list_context_menu(self, pos) -> None:
        item = self.env_list.itemAt(pos)
        if item is None:
            return
        row = self.env_list.row(item)
        menu = QMenu(self)
        rename_action = menu.addAction("Rename")
        copy_action = menu.addAction("Copy")
        delete_action = menu.addAction("Delete")
        chosen = menu.exec(self.env_list.mapToGlobal(pos))
        if chosen == rename_action:
            self._rename_environment_at_row(row)
        elif chosen == copy_action:
            self._duplicate_environment_at_row(row)
        elif chosen == delete_action:
            self.delete_environment(row)

    def _rename_current_environment(self) -> None:
        row = self.env_list.currentRow()
        if row >= 0:
            self._rename_environment_at_row(row)

    def _rename_environment_at_row(self, row: int) -> None:
        item = self.env_list.item(row)
        if item:
            self.env_list.editItem(item)

    def _apply_environment_rename(self, row: int, new_name: str) -> bool:
        """Commit an environment rename programmatically (used by tests and delegate)."""
        if row < 0 or row >= len(self.environments):
            return False

        env = self.environments[row]
        old_name = env.name
        accepted, normalized, _error = validate_environment_rename(
            new_name,
            old_name,
            [e.name for e in self.environments],
            row,
        )
        if not accepted:
            return False
        if normalized == old_name:
            return True

        env.name = normalized
        if self.current_env_name == old_name:
            self.current_env_name = normalized

        item = self.env_list.item(row)
        if item:
            self.env_list.blockSignals(True)
            item.setText(normalized)
            self.env_list.blockSignals(False)

        logger.info(
            "environment_renamed old_name=%s new_name=%s",
            old_name,
            normalized,
        )
        return True

    def _on_environment_renamed(self, row: int, old_name: str, new_name: str) -> None:
        if row < 0 or row >= len(self.environments):
            return

        env = self.environments[row]
        env.name = new_name
        if self.current_env_name == old_name:
            self.current_env_name = new_name

        logger.info(
            "environment_renamed old_name=%s new_name=%s",
            old_name,
            new_name,
        )

    def _duplicate_environment_at_row(self, row: int) -> None:
        if row < 0 or row >= len(self.environments):
            return
        source = self.environments[row]
        default_name = f"Copy of {source.name}"
        while True:
            name, ok = QInputDialog.getText(self, "Copy Environment", "Name:", text=default_name)
            if not ok:
                return
            stripped = name.strip()
            if not stripped:
                QMessageBox.warning(self, "Copy Environment", "Name cannot be empty.")
                default_name = name
                continue
            if any(e.name == stripped for e in self.environments):
                QMessageBox.warning(
                    self,
                    "Copy Environment",
                    f'An environment named "{stripped}" already exists.',
                )
                default_name = stripped
                continue
            break
        new_env = clone_environment(source, stripped)
        logger.info(
            "environment_copied source_name=%s new_name=%s",
            source.name,
            stripped,
        )
        insert_at = row + 1
        self.environments.insert(insert_at, new_env)
        self.load_list()
        self.env_list.setCurrentRow(insert_at)

    def _make_hidden_checkbox(self, checked: bool = False) -> QWidget:
        """Create a centered checkbox widget for the Hidden column."""
        widget = QWidget()
        cb = QCheckBox()
        cb.setChecked(checked)
        cb.toggled.connect(self._on_hidden_toggled)
        layout = QHBoxLayout(widget)
        layout.addWidget(cb)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        return widget

    def _get_hidden_checkbox(self, row: int) -> QCheckBox | None:
        """Return the QCheckBox for the given table row."""
        widget = self.vars_table.cellWidget(row, COL_HIDDEN)
        if widget:
            cb = widget.findChild(QCheckBox)
            return cb
        return None

    def _make_value_item(self, value: str, is_hidden: bool) -> QTableWidgetItem:
        """Build a table item for value column preserving hidden real value in UserRole."""
        if not is_hidden:
            return QTableWidgetItem(value)
        item = QTableWidgetItem(HIDDEN_MASK)
        item.setData(Qt.ItemDataRole.UserRole, value)
        return item

    def _extract_real_value(self, item: QTableWidgetItem | None, fallback: str) -> str:
        """Extract real value from a value-cell item when it may be masked."""
        if not item:
            return fallback
        if item.text() != HIDDEN_MASK:
            return item.text()
        stored = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(stored, str):
            return stored
        return fallback

    def on_env_selected(self, row):
        if row < 0 or row >= len(self.environments):
            self.vars_table.setRowCount(0)
            self.mcp_check.setEnabled(False)
            self.mcp_check.setChecked(False)
            return

        env = self.environments[row]
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

        # Empty last row for adding new variables
        self.vars_table.setCellWidget(
            len(env.variables),
            COL_HIDDEN,
            self._make_hidden_checkbox(False),
        )

        self.vars_table.blockSignals(False)

    def _on_hidden_toggled(self, checked: bool) -> None:
        """Handle hidden checkbox toggle for a variable row."""
        env_row = self.env_list.currentRow()
        if env_row < 0:
            return
        env = self.environments[env_row]

        # Find which table row this checkbox belongs to
        sender = self.sender()
        for i in range(self.vars_table.rowCount()):
            cb = self._get_hidden_checkbox(i)
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
                    masked_item = self._make_value_item(real_val, True)
                    self.vars_table.setItem(
                        i,
                        COL_VAL,
                        masked_item,
                    )
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

    def on_var_changed(self, item):
        env_row = self.env_list.currentRow()
        if env_row < 0:
            return

        env = self.environments[env_row]

        # Add new row if editing last
        if item.row() == self.vars_table.rowCount() - 1:
            if item.text():
                self.vars_table.blockSignals(True)
                self.vars_table.setRowCount(
                    self.vars_table.rowCount() + 1,
                )
                self.vars_table.setCellWidget(
                    self.vars_table.rowCount() - 1,
                    COL_HIDDEN,
                    self._make_hidden_checkbox(False),
                )
                self.vars_table.blockSignals(False)

        # Rebuild env variables and hidden_keys
        new_vars = {}
        new_hidden = set()
        for i in range(self.vars_table.rowCount()):
            k_item = self.vars_table.item(i, COL_VAR)
            v_item = self.vars_table.item(i, COL_VAL)
            cb = self._get_hidden_checkbox(i)

            if k_item and k_item.text():
                key = k_item.text().strip()
                is_valid, _error = validate_environment_variable_name(key)
                if not is_valid:
                    if item.column() == COL_VAR and item.row() == i:
                        old_keys = list(env.variables.keys())
                        revert = old_keys[i] if i < len(old_keys) else ""
                        self.vars_table.blockSignals(True)
                        k_item.setText(revert)
                        self.vars_table.blockSignals(False)
                    continue
                is_hidden = cb.isChecked() if cb else False
                if is_hidden:
                    new_hidden.add(key)
                    val = self._extract_real_value(
                        v_item,
                        env.variables.get(key, ""),
                    )
                    if item.column() == COL_VAL and item.row() == i:
                        # User just edited the value cell
                        typed = v_item.text() if v_item else ""
                        if typed != HIDDEN_MASK:
                            val = typed
                        # Re-mask the display
                        self.vars_table.blockSignals(True)
                        self.vars_table.setItem(
                            i,
                            COL_VAL,
                            self._make_value_item(val, True),
                        )
                        self.vars_table.blockSignals(False)
                    new_vars[key] = val
                else:
                    new_vars[key] = self._extract_real_value(v_item, "")

        env.variables = new_vars
        env.hidden_keys = new_hidden

    def on_mcp_toggled(self, checked):
        row = self.env_list.currentRow()
        if row >= 0:
            env = self.environments[row]
            env.enable_mcp = checked
