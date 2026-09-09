from __future__ import annotations

from pathlib import Path
from typing import Callable, List

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QVBoxLayout

from pypost.core.environment_ops import clone_environments
from pypost.models.models import Environment
from pypost.core.environment_messages import DIALOG_TITLE_MANAGE_ENVIRONMENTS
from pypost.ui.widgets.environments import (
    EnvironmentListWidget,
    EnvironmentVariablesWidget,
)


class EnvironmentDialog(QDialog):
    def __init__(
        self,
        environments: List[Environment],
        parent=None,
        current_env_name: str = None,
        log_hidden_key_names: bool = False,
        read_import_file: Callable[[Path], tuple[list[Environment], list[str]]] | None = None,
        serialize_export_records: Callable[[list[Environment]], list[dict]] | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(DIALOG_TITLE_MANAGE_ENVIRONMENTS)
        self.resize(800, 600)
        self._environments = clone_environments(environments)
        self.current_env_name = current_env_name

        self._env_list_widget = EnvironmentListWidget(
            self._environments,
            current_env_name=current_env_name,
            get_current_env_name=lambda: self.current_env_name,
            set_current_env_name=lambda name: setattr(self, "current_env_name", name),
            read_import_file=read_import_file,
            serialize_export_records=serialize_export_records,
        )
        self._vars_widget = EnvironmentVariablesWidget(
            log_hidden_key_names=log_hidden_key_names,
            get_selected_env=self._selected_environment,
        )

        content_layout = QHBoxLayout()
        content_layout.addWidget(self._env_list_widget, 1)
        content_layout.addWidget(self._vars_widget, 3)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel,
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(content_layout)
        layout.addWidget(self.button_box)

        self._env_list_widget.environment_selected.connect(self.on_env_selected)

        # Initial synchronization: load the initially selected environment into the variables table
        self.on_env_selected(self.env_list.currentRow())

    @property
    def environments(self) -> List[Environment]:
        """Working copy edited in the dialog; presenter applies on close."""
        return self._environments

    @property
    def env_list(self):
        return self._env_list_widget.env_list

    @property
    def vars_table(self):
        return self._vars_widget.vars_table

    @property
    def mcp_check(self):
        return self._vars_widget.mcp_check

    def _selected_environment(self) -> Environment | None:
        row = self.env_list.currentRow()
        if row < 0 or row >= len(self._environments):
            return None
        return self._environments[row]

    def on_env_selected(self, row: int) -> None:
        if row < 0 or row >= len(self._environments):
            self._vars_widget.load_environment(None)
            return
        self._vars_widget.load_environment(self._environments[row])

    def add_environment(self) -> None:
        self._env_list_widget.add_environment()

    def import_environments(self) -> None:
        self._env_list_widget.import_environments()

    def export_environments(self) -> None:
        self._env_list_widget.export_environments()

    def delete_environment(self, row: int | None = None) -> None:
        self._env_list_widget.delete_environment(row)

    def _apply_environment_rename(self, row: int, new_name: str) -> bool:
        return self._env_list_widget.apply_environment_rename(row, new_name)

    def _get_hidden_item(self, row: int):
        return self._vars_widget.get_hidden_item(row)

    def _delete_variable_at_row(self, row: int) -> None:
        self._vars_widget.delete_variable_at_row(row)

    def _move_variable_at_row(self, row: int, direction: str) -> None:
        self._vars_widget.move_variable_at_row(row, direction)

    def _on_vars_table_context_menu(self, pos) -> None:
        self._vars_widget._on_vars_table_context_menu(pos)

    def on_var_changed(self, item) -> None:
        self._vars_widget.on_var_changed(item)
