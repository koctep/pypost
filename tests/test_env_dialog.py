"""Qt-level tests for EnvironmentDialog (manage environments UI)."""
import logging

import pytest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QTableWidgetItem

from pypost.models.models import Environment
from pypost.ui.dialogs.env_dialog import EnvironmentDialog
from pypost.core.constants import HIDDEN_MASK


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

    def test_hidden_toggle_logs_masked_key_by_default(self, qapp, caplog):
        env = Environment(name="Dev", variables={"API_KEY": "secret"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            hidden_cb = dlg._get_hidden_checkbox(0)
            assert hidden_cb is not None
            with caplog.at_level(logging.INFO):
                hidden_cb.setChecked(True)
            assert any(
                "env_hidden_flag_changed env_name=Dev key=******** hidden=True" in r.message
                for r in caplog.records
            )
            assert not any("API_KEY" in r.message for r in caplog.records)
        finally:
            dlg.close()

    def test_hidden_toggle_logs_readable_key_when_enabled(self, qapp, caplog):
        env = Environment(name="Dev", variables={"API_KEY": "secret"})
        dlg = EnvironmentDialog([env], log_hidden_key_names=True)
        try:
            dlg.on_env_selected(0)
            hidden_cb = dlg._get_hidden_checkbox(0)
            assert hidden_cb is not None
            with caplog.at_level(logging.INFO):
                hidden_cb.setChecked(True)
            assert any(
                "env_hidden_flag_changed env_name=Dev key=API_KEY hidden=True" in r.message
                for r in caplog.records
            )
        finally:
            dlg.close()

    def test_delete_variable_via_handler_removes_from_model(self, qapp):
        env = Environment(name="Dev", variables={"a": "1", "b": "2"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            # Find row for "a"
            row = 0 if dlg.vars_table.item(0, 0).text() == "a" else 1
            dlg._delete_variable_at_row(row)
            assert "a" not in env.variables
            assert "b" in env.variables
            assert dlg.vars_table.rowCount() == 2  # 1 var + 1 empty trailing row
        finally:
            dlg.close()

    def test_delete_hidden_variable_clears_hidden_keys(self, qapp):
        env = Environment(name="Dev", variables={"secret": "val"}, hidden_keys={"secret"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg._delete_variable_at_row(0)
            assert "secret" not in env.variables
            assert "secret" not in env.hidden_keys
        finally:
            dlg.close()

    def test_delete_variable_keeps_trailing_add_row(self, qapp):
        env = Environment(name="Dev", variables={"k": "v"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            assert dlg.vars_table.rowCount() == 2
            dlg._delete_variable_at_row(0)
            assert dlg.vars_table.rowCount() == 1
            assert not dlg.vars_table.item(0, 0) or not dlg.vars_table.item(0, 0).text()
        finally:
            dlg.close()

    @patch("pypost.ui.dialogs.env_dialog.QMenu.exec")
    def test_vars_table_context_menu_ignores_trailing_row(self, mock_exec, qapp):
        env = Environment(name="Dev", variables={})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            # Context menu requested on trailing empty row
            from PySide6.QtCore import QPoint
            # Use rowAt mock or just ensure it returns the valid empty row
            with patch.object(dlg.vars_table, "rowAt", return_value=0):
                dlg._on_vars_table_context_menu(QPoint(0, 0))
            # QMenu should not be executed
            mock_exec.assert_not_called()
        finally:
            dlg.close()

    def test_delete_variable_logs_masked_key_by_default(self, qapp, caplog):
        env = Environment(name="Dev", variables={"API_KEY": "secret"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            with caplog.at_level(logging.INFO):
                dlg._delete_variable_at_row(0)
            assert any(
                "env_variable_deleted env_name=Dev key=********" in r.message
                for r in caplog.records
            )
            assert not any("API_KEY" in r.message for r in caplog.records)
        finally:
            dlg.close()

    def test_delete_variable_logs_readable_key_when_enabled(self, qapp, caplog):
        env = Environment(name="Dev", variables={"API_KEY": "secret"})
        dlg = EnvironmentDialog([env], log_hidden_key_names=True)
        try:
            dlg.on_env_selected(0)
            with caplog.at_level(logging.INFO):
                dlg._delete_variable_at_row(0)
            assert any(
                "env_variable_deleted env_name=Dev key=API_KEY" in r.message
                for r in caplog.records
            )
        finally:
            dlg.close()

    def test_clear_name_still_removes_variable(self, qapp):
        env = Environment(name="Dev", variables={"k": "v"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg.vars_table.item(0, 0).setText("")
            assert "k" not in env.variables
        finally:
            dlg.close()

    def test_move_variable_up_reorders_model(self, qapp):
        env = Environment(name="Dev", variables={"a": "1", "b": "2", "c": "3"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg._move_variable_at_row(1, "up")
            assert list(env.variables.keys()) == ["b", "a", "c"]
        finally:
            dlg.close()

    def test_move_variable_down_reorders_model(self, qapp):
        env = Environment(name="Dev", variables={"a": "1", "b": "2", "c": "3"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg._move_variable_at_row(1, "down")
            assert list(env.variables.keys()) == ["a", "c", "b"]
        finally:
            dlg.close()

    def test_move_up_at_first_row_is_noop(self, qapp):
        env = Environment(name="Dev", variables={"a": "1", "b": "2"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg._move_variable_at_row(0, "up")
            assert list(env.variables.keys()) == ["a", "b"]
        finally:
            dlg.close()

    def test_move_down_at_last_populated_row_is_noop(self, qapp):
        env = Environment(name="Dev", variables={"a": "1", "b": "2"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg._move_variable_at_row(1, "down")
            assert list(env.variables.keys()) == ["a", "b"]
        finally:
            dlg.close()

    def test_move_hidden_variable_preserves_hidden_keys_and_mask(self, qapp):
        env = Environment(name="Dev", variables={"a": "1", "b": "2"}, hidden_keys={"a"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg._move_variable_at_row(0, "down")
            assert list(env.variables.keys()) == ["b", "a"]
            assert env.hidden_keys == {"a"}
            assert dlg.vars_table.item(1, 1).text() == HIDDEN_MASK
        finally:
            dlg.close()

    def test_move_variable_keeps_trailing_add_row(self, qapp):
        env = Environment(name="Dev", variables={"a": "1", "b": "2"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg._move_variable_at_row(0, "down")
            assert dlg.vars_table.rowCount() == 3
        finally:
            dlg.close()

    def test_move_variable_switch_env_and_back(self, qapp):
        envs = [
            Environment(name="Dev", variables={"a": "1", "b": "2"}),
            Environment(name="Prod", variables={"x": "9"}),
        ]
        dlg = EnvironmentDialog(envs)
        try:
            dlg.on_env_selected(0)
            dlg._move_variable_at_row(0, "down")
            dlg.on_env_selected(1)
            dlg.on_env_selected(0)
            assert list(envs[0].variables.keys()) == ["b", "a"]
        finally:
            dlg.close()

    def test_move_variable_logs_masked_key_by_default(self, qapp, caplog):
        env = Environment(name="Dev", variables={"a": "1", "b": "2"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            with caplog.at_level(logging.INFO):
                dlg._move_variable_at_row(0, "down")
            assert any(
                "env_variable_moved env_name=Dev key=******** direction=down" in r.message
                for r in caplog.records
            )
        finally:
            dlg.close()

    def test_rename_environment_updates_model_and_list(self, qapp):
        envs = [Environment(name="Dev", variables={})]
        dlg = EnvironmentDialog(envs)
        try:
            assert dlg._apply_environment_rename(0, "Staging")
            assert envs[0].name == "Staging"
            assert dlg.env_list.item(0).text() == "Staging"
        finally:
            dlg.close()

    def test_rename_environment_empty_name_rejected(self, qapp):
        envs = [Environment(name="Dev", variables={})]
        dlg = EnvironmentDialog(envs)
        try:
            assert not dlg._apply_environment_rename(0, "")
            assert envs[0].name == "Dev"
        finally:
            dlg.close()

    def test_rename_environment_duplicate_name_rejected(self, qapp):
        envs = [Environment(name="Dev", variables={}), Environment(name="Prod", variables={})]
        dlg = EnvironmentDialog(envs)
        try:
            assert not dlg._apply_environment_rename(0, "Prod")
            assert envs[0].name == "Dev"
        finally:
            dlg.close()

    def test_rename_environment_same_name_is_noop(self, qapp):
        envs = [Environment(name="Dev", variables={})]
        dlg = EnvironmentDialog(envs)
        try:
            assert dlg._apply_environment_rename(0, "Dev")
            assert envs[0].name == "Dev"
        finally:
            dlg.close()

