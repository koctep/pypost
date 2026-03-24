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

logger = logging.getLogger(__name__)


class EnvironmentDialog(QDialog):
    def __init__(self, environments: List[Environment], parent=None, current_env_name: str = None):
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
        self.env_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.env_list.customContextMenuRequested.connect(
            self._on_env_list_context_menu
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
        self.vars_table = QTableWidget(0, 2)
        self.vars_table.setHorizontalHeaderLabels(["Variable", "Value"])
        self.vars_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.vars_table.itemChanged.connect(self.on_var_changed)

        self.mcp_check = QCheckBox("Enable MCP (Model Context Protocol)")
        self.mcp_check.toggled.connect(self.on_mcp_toggled)
        # Initially disabled until env is selected
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

    def on_env_selected(self, row):
        if row < 0 or row >= len(self.environments):
            self.vars_table.setRowCount(0)
            self.mcp_check.setEnabled(False)
            self.mcp_check.setChecked(False)
            return

        env = self.environments[row]
        self.mcp_check.setEnabled(True)
        # Block signals to prevent triggering on_mcp_toggled during load
        self.mcp_check.blockSignals(True)
        self.mcp_check.setChecked(getattr(env, 'enable_mcp', False))
        self.mcp_check.blockSignals(False)

        self.vars_table.blockSignals(True)
        self.vars_table.setRowCount(len(env.variables) + 1)

        for i, (k, v) in enumerate(env.variables.items()):
            self.vars_table.setItem(i, 0, QTableWidgetItem(k))
            self.vars_table.setItem(i, 1, QTableWidgetItem(v))

        self.vars_table.blockSignals(False)

    def on_var_changed(self, item):
        row = self.env_list.currentRow()
        if row < 0:
            return

        env = self.environments[row]

        # Add new row if editing last
        if item.row() == self.vars_table.rowCount() - 1:
            if item.text():
                self.vars_table.blockSignals(True)
                self.vars_table.setRowCount(self.vars_table.rowCount() + 1)
                self.vars_table.blockSignals(False)

        # Update env variables
        new_vars = {}
        for i in range(self.vars_table.rowCount()):
            k_item = self.vars_table.item(i, 0)
            v_item = self.vars_table.item(i, 1)

            if k_item and k_item.text():
                new_vars[k_item.text()] = v_item.text() if v_item else ""

        env.variables = new_vars

    def on_mcp_toggled(self, checked):
        row = self.env_list.currentRow()
        if row >= 0:
            env = self.environments[row]
            env.enable_mcp = checked
