from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                               QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox, QInputDialog)
from typing import List
from pypost.models.models import Environment

class EnvironmentDialog(QDialog):
    def __init__(self, environments: List[Environment], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Environments")
        self.resize(800, 600)
        self.environments = environments
        # Deep copy or direct modification? Direct for simplicity now, but be careful with cancel
        # For a "Manage" dialog, changes usually apply immediately or on "Save"

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Left: Environment List
        left_layout = QVBoxLayout()
        self.env_list = QListWidget()
        self.env_list.currentRowChanged.connect(self.on_env_selected)

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

        right_layout.addWidget(self.vars_table)
        layout.addLayout(right_layout, 3)

        self.load_list()

    def load_list(self):
        self.env_list.clear()
        for env in self.environments:
            self.env_list.addItem(env.name)

        if self.environments:
            self.env_list.setCurrentRow(0)

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

    def on_env_selected(self, row):
        if row < 0 or row >= len(self.environments):
            self.vars_table.setRowCount(0)
            return

        env = self.environments[row]
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
