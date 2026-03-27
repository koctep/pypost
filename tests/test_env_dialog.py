"""Qt-level tests for EnvironmentDialog (manage environments UI)."""
import pytest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QTableWidgetItem

from pypost.models.models import Environment
from pypost.ui.dialogs.env_dialog import EnvironmentDialog
from pypost.ui.widgets.mixins import HIDDEN_MASK


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


class TestEnvironmentDialog:
    def test_load_list_selects_current_env_by_name(self, qapp):
        envs = [
            Environment(name="First", variables={}),
            Environment(name="Second", variables={"a": "b"}, enable_mcp=True),
        ]
        dlg = EnvironmentDialog(envs, current_env_name="Second")
        try:
            assert dlg.env_list.currentRow() == 1
        finally:
            dlg.close()

    def test_empty_environments_shows_no_selection(self, qapp):
        dlg = EnvironmentDialog([])
        try:
            assert dlg.env_list.count() == 0
            assert dlg.env_list.currentRow() < 0
        finally:
            dlg.close()

    def test_on_env_selected_loads_variables_and_mcp_state(self, qapp):
        envs = [
            Environment(
                name="Dev",
                variables={"key": "val"},
                enable_mcp=True,
            )
        ]
        dlg = EnvironmentDialog(envs)
        try:
            dlg.on_env_selected(0)
            assert dlg.mcp_check.isEnabled()
            assert dlg.mcp_check.isChecked()
            assert dlg.vars_table.item(0, 0).text() == "key"
            assert dlg.vars_table.item(0, 1).text() == "val"
        finally:
            dlg.close()

    def test_mcp_checkbox_toggle_updates_environment_model(self, qapp):
        env = Environment(name="E", variables={}, enable_mcp=False)
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg.mcp_check.setChecked(True)
            assert env.enable_mcp is True
            dlg.mcp_check.setChecked(False)
            assert env.enable_mcp is False
        finally:
            dlg.close()

    def test_delete_environment_removes_current_row(self, qapp):
        envs = [
            Environment(name="A", variables={}),
            Environment(name="B", variables={}),
        ]
        dlg = EnvironmentDialog(envs)
        try:
            dlg.env_list.setCurrentRow(0)
            dlg.delete_environment()
            assert len(envs) == 1
            assert envs[0].name == "B"
        finally:
            dlg.close()

    @patch(
        "pypost.ui.dialogs.env_dialog.QInputDialog.getText",
        return_value=("Staging", True),
    )
    def test_add_environment_appends_named_env(self, _mock_input, qapp):
        envs = [Environment(name="Base", variables={})]
        dlg = EnvironmentDialog(envs)
        try:
            dlg.add_environment()
            assert len(envs) == 2
            assert envs[1].name == "Staging"
        finally:
            dlg.close()

    def test_hidden_column_and_mask_loaded_from_environment(self, qapp):
        env = Environment(
            name="Dev",
            variables={"API_KEY": "secret"},
            hidden_keys={"API_KEY"},
        )
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            assert dlg.vars_table.columnCount() == 3
            assert dlg.vars_table.item(0, 1).text() == HIDDEN_MASK
            hidden_cb = dlg._get_hidden_checkbox(0)
            assert hidden_cb is not None
            assert hidden_cb.isChecked()
        finally:
            dlg.close()

    def test_hidden_toggle_updates_model_and_value_cell(self, qapp):
        env = Environment(name="Dev", variables={"API_KEY": "secret"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            hidden_cb = dlg._get_hidden_checkbox(0)
            assert hidden_cb is not None
            hidden_cb.setChecked(True)
            assert "API_KEY" in env.hidden_keys
            assert dlg.vars_table.item(0, 1).text() == HIDDEN_MASK
            hidden_cb.setChecked(False)
            assert "API_KEY" not in env.hidden_keys
            assert dlg.vars_table.item(0, 1).text() == "secret"
        finally:
            dlg.close()

    def test_edit_hidden_value_keeps_real_value_and_masks_display(self, qapp):
        env = Environment(
            name="Dev",
            variables={"API_KEY": "old"},
            hidden_keys={"API_KEY"},
        )
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg.vars_table.setItem(0, 1, QTableWidgetItem("new"))
            assert env.variables["API_KEY"] == "new"
            assert dlg.vars_table.item(0, 1).text() == HIDDEN_MASK
            hidden_cb = dlg._get_hidden_checkbox(0)
            assert hidden_cb is not None
            hidden_cb.setChecked(False)
            assert dlg.vars_table.item(0, 1).text() == "new"
            assert env.hidden_keys == set()
        finally:
            dlg.close()

    def test_rename_hidden_key_keeps_real_value_and_hidden_flag(self, qapp):
        env = Environment(
            name="Dev",
            variables={"API_KEY": "secret"},
            hidden_keys={"API_KEY"},
        )
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg.vars_table.setItem(0, 0, QTableWidgetItem("NEW_KEY"))
            assert env.variables == {"NEW_KEY": "secret"}
            assert env.hidden_keys == {"NEW_KEY"}
            assert dlg.vars_table.item(0, 1).text() == HIDDEN_MASK
        finally:
            dlg.close()
