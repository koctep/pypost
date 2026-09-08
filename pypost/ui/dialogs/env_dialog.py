import logging
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QListWidget,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from pypost.core.environment_ops import clone_environment
from pypost.models.models import Environment
from pypost.ui.widgets.mixins import HIDDEN_MASK

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
    ):
        super().__init__(parent)
        self.setWindowTitle("Manage Environments")
        self.resize(800, 600)
        self.environments = environments
        self.current_env_name = current_env_name

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Left: Environment List
        left_layout = QVBoxLayout()
        self.env_list = QListWidget()
        self.env_list.currentRowChanged.connect(self.on_env_selected)
        self.env_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu,
        )
        self.env_list.customContextMenuRequested.connect(
            self._on_env_list_context_menu,
        )

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_environment)

        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_environment)

        left_layout.addWidget(self.env_list)
        left_layout.addWidget(add_btn)
        left_layout.addWidget(del_btn)

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
            COL_HIDDEN, QHeaderView.ResizeToContents,
        )
        self.vars_table.itemChanged.connect(self.on_var_changed)

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
        self.env_list.clear()
        target_row = 0
        for i, env in enumerate(self.environments):
            self.env_list.addItem(env.name)
            if self.current_env_name and env.name == self.current_env_name:
                target_row = i

        if self.environments:
            self.env_list.setCurrentRow(target_row)

    def add_environment(self):
        name, ok = QInputDialog.getText(self, "New Environment", "Name:")
        if ok and name:
            env = Environment(name=name)
            self.environments.append(env)
            self.env_list.addItem(name)
            self.env_list.setCurrentRow(len(self.environments) - 1)

    def delete_environment(self):
        row = self.env_list.currentRow()
        if row >= 0:
            del self.environments[row]
            self.env_list.takeItem(row)

    def _on_env_list_context_menu(self, pos) -> None:
        item = self.env_list.itemAt(pos)
        if item is None:
            return
        row = self.env_list.row(item)
        menu = QMenu(self)
        copy_action = menu.addAction("Copy")
        chosen = menu.exec(self.env_list.mapToGlobal(pos))
        if chosen == copy_action:
            self._duplicate_environment_at_row(row)

    def _duplicate_environment_at_row(self, row: int) -> None:
        if row < 0 or row >= len(self.environments):
            return
        source = self.environments[row]
        default_name = f"Copy of {source.name}"
        while True:
            name, ok = QInputDialog.getText(
                self, "Copy Environment", "Name:", text=default_name
            )
            if not ok:
                return
            stripped = name.strip()
            if not stripped:
                QMessageBox.warning(
                    self, "Copy Environment", "Name cannot be empty."
                )
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

    def _make_hidden_item(self, checked: bool = False) -> QTableWidgetItem:
        """Create a checkable item for the Hidden column.

        A checkable item is used rather than a cell widget: Qt 6.11 crashes when a
        QTableWidget cell widget is clicked repeatedly, and the item carries the same
        state without an extra child widget to keep alive.
        """
        item = QTableWidgetItem()
        item.setFlags(
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsUserCheckable
        )
        item.setCheckState(
            Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked,
        )
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item

    def _is_hidden(self, row: int) -> bool:
        """Return the Hidden check state for the given table row."""
        item = self.vars_table.item(row, COL_HIDDEN)
        if item is None:
            return False
        return item.checkState() == Qt.CheckState.Checked

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
        self.mcp_check.setChecked(getattr(env, 'enable_mcp', False))
        self.mcp_check.blockSignals(False)

        self.vars_table.blockSignals(True)
        self.vars_table.setRowCount(len(env.variables) + 1)

        for i, (k, v) in enumerate(env.variables.items()):
            self.vars_table.setItem(i, COL_VAR, QTableWidgetItem(k))
            is_hidden = k in env.hidden_keys
            value_item = self._make_value_item(v, is_hidden)
            self.vars_table.setItem(i, COL_VAL, value_item)
            self.vars_table.setItem(
                i, COL_HIDDEN, self._make_hidden_item(is_hidden),
            )

        # Empty last row for adding new variables
        self.vars_table.setItem(
            len(env.variables), COL_HIDDEN,
            self._make_hidden_item(False),
        )

        self.vars_table.blockSignals(False)

    def _on_hidden_changed(self, item: QTableWidgetItem) -> None:
        """Handle the Hidden check state changing for a variable row."""
        env_row = self.env_list.currentRow()
        if env_row < 0:
            return
        env = self.environments[env_row]

        row = item.row()
        k_item = self.vars_table.item(row, COL_VAR)
        if not k_item or not k_item.text():
            return

        key = k_item.text()
        checked = item.checkState() == Qt.CheckState.Checked
        val_item = self.vars_table.item(row, COL_VAL)
        real_val = self._extract_real_value(
            val_item,
            env.variables.get(key, ""),
        )

        self.vars_table.blockSignals(True)
        if checked:
            env.hidden_keys.add(key)
        else:
            env.hidden_keys.discard(key)
        if val_item is None:
            self.vars_table.setItem(
                row, COL_VAL, self._make_value_item(real_val, checked),
            )
        elif checked:
            # Mutate in place rather than replacing the item: replacing it while Qt
            # dispatches itemChanged can free the native item still in use.
            val_item.setData(Qt.ItemDataRole.UserRole, real_val)
            val_item.setText(HIDDEN_MASK)
        else:
            val_item.setData(Qt.ItemDataRole.UserRole, None)
            val_item.setText(real_val)
        self.vars_table.blockSignals(False)

        logger.info(
            "env_hidden_flag_changed env_name=%s key=%s hidden=%s",
            env.name,
            key,
            checked,
        )

    def on_var_changed(self, item):
        env_row = self.env_list.currentRow()
        if env_row < 0:
            return

        env = self.environments[env_row]

        if item.column() == COL_HIDDEN:
            self._on_hidden_changed(item)
            return

        # Add new row if editing last
        if item.row() == self.vars_table.rowCount() - 1:
            if item.text():
                self.vars_table.blockSignals(True)
                self.vars_table.setRowCount(
                    self.vars_table.rowCount() + 1,
                )
                self.vars_table.setItem(
                    self.vars_table.rowCount() - 1,
                    COL_HIDDEN,
                    self._make_hidden_item(False),
                )
                self.vars_table.blockSignals(False)

        # Rebuild env variables and hidden_keys
        new_vars = {}
        new_hidden = set()
        for i in range(self.vars_table.rowCount()):
            k_item = self.vars_table.item(i, COL_VAR)
            v_item = self.vars_table.item(i, COL_VAL)

            if k_item and k_item.text():
                key = k_item.text()
                is_hidden = self._is_hidden(i)
                if is_hidden:
                    new_hidden.add(key)
                    val = self._extract_real_value(
                        v_item,
                        env.variables.get(key, ""),
                    )
                    if (
                        item.column() == COL_VAL
                        and item.row() == i
                    ):
                        # User just edited the value cell
                        typed = v_item.text() if v_item else ""
                        if typed != HIDDEN_MASK:
                            val = typed
                        # Re-mask the existing item in place. Replacing the
                        # item here deletes the native QTableWidgetItem while
                        # Qt is still dispatching itemChanged for it, which
                        # can cause a use-after-free and a segmentation fault.
                        self.vars_table.blockSignals(True)
                        v_item.setData(Qt.ItemDataRole.UserRole, val)
                        v_item.setText(HIDDEN_MASK)
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
