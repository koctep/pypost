"""Qt-level tests for EnvironmentDialog (manage environments UI)."""

import pytest

import logging

from unittest.mock import patch

from PySide6.QtWidgets import QMessageBox, QTableWidgetItem

from pypost.models.models import Environment
from pypost.ui.dialogs.env_dialog import EnvironmentDialog
from pypost.core.constants import HIDDEN_MASK

pytestmark = pytest.mark.timeout(60)


class TestEnvironmentDialog:
    def test_dialog_does_not_mutate_input_environments(self, qapp):
        env = Environment(name="Dev", variables={"k": "v"}, enable_mcp=False)
        input_envs = [env]
        dlg = EnvironmentDialog(input_envs)
        try:
            dlg.on_env_selected(0)
            dlg.mcp_check.setChecked(True)
            dlg.vars_table.setItem(0, 1, QTableWidgetItem("changed"))
            assert env.enable_mcp is False
            assert env.variables == {"k": "v"}
            assert dlg.environments[0].enable_mcp is True
            assert dlg.environments[0].variables["k"] == "changed"
        finally:
            dlg.close()

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
            assert dlg.environments[0].enable_mcp is True
            dlg.mcp_check.setChecked(False)
            assert dlg.environments[0].enable_mcp is False
        finally:
            dlg.close()

    @patch(
        "pypost.ui.widgets.environments.environment_list_widget.confirm_delete_environment",
        return_value=True,
    )
    def test_delete_environment_removes_current_row(self, mock_question, qapp):
        envs = [
            Environment(name="A", variables={}),
            Environment(name="B", variables={}),
        ]
        dlg = EnvironmentDialog(envs)
        try:
            dlg.env_list.setCurrentRow(0)
            dlg.delete_environment()
            assert len(dlg.environments) == 1
            assert dlg.environments[0].name == "B"
            mock_question.assert_called_once()
        finally:
            dlg.close()

    @patch(
        "pypost.ui.widgets.environments.environment_list_widget.confirm_delete_environment",
    )
    def test_delete_environment_cancelled_leaves_env(self, mock_confirm, qapp):
        mock_confirm.return_value = False
        envs = [Environment(name="A", variables={})]
        dlg = EnvironmentDialog(envs)
        try:
            dlg.env_list.setCurrentRow(0)
            dlg.delete_environment()
            assert len(envs) == 1
            assert envs[0].name == "A"
        finally:
            dlg.close()

    @patch(
        "pypost.ui.widgets.environments.environment_list_widget.QInputDialog.getText",
        return_value=("Staging", True),
    )
    def test_add_environment_appends_named_env(self, _mock_input, qapp):
        envs = [Environment(name="Base", variables={})]
        dlg = EnvironmentDialog(envs)
        try:
            dlg.add_environment()
            assert len(dlg.environments) == 2
            assert dlg.environments[1].name == "Staging"
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
            assert "API_KEY" in dlg.environments[0].hidden_keys
            assert dlg.vars_table.item(0, 1).text() == HIDDEN_MASK
            hidden_cb.setChecked(False)
            assert "API_KEY" not in dlg.environments[0].hidden_keys
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
            assert dlg.environments[0].variables["API_KEY"] == "new"
            assert dlg.vars_table.item(0, 1).text() == HIDDEN_MASK
            hidden_cb = dlg._get_hidden_checkbox(0)
            assert hidden_cb is not None
            hidden_cb.setChecked(False)
            assert dlg.vars_table.item(0, 1).text() == "new"
            assert dlg.environments[0].hidden_keys == set()
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
            assert dlg.environments[0].variables == {"NEW_KEY": "secret"}
            assert dlg.environments[0].hidden_keys == {"NEW_KEY"}
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
            assert "a" not in dlg.environments[0].variables
            assert "b" in dlg.environments[0].variables
            assert dlg.vars_table.rowCount() == 2  # 1 var + 1 empty trailing row
        finally:
            dlg.close()

    def test_delete_hidden_variable_clears_hidden_keys(self, qapp):
        env = Environment(name="Dev", variables={"secret": "val"}, hidden_keys={"secret"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg._delete_variable_at_row(0)
            assert "secret" not in dlg.environments[0].variables
            assert "secret" not in dlg.environments[0].hidden_keys
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

    @patch("pypost.ui.widgets.environments.environment_variables_widget.QMenu.exec")
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
            assert "k" not in dlg.environments[0].variables
        finally:
            dlg.close()

    def test_move_variable_up_reorders_model(self, qapp):
        env = Environment(name="Dev", variables={"a": "1", "b": "2", "c": "3"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg._move_variable_at_row(1, "up")
            assert list(dlg.environments[0].variables.keys()) == ["b", "a", "c"]
        finally:
            dlg.close()

    def test_move_variable_down_reorders_model(self, qapp):
        env = Environment(name="Dev", variables={"a": "1", "b": "2", "c": "3"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg._move_variable_at_row(1, "down")
            assert list(dlg.environments[0].variables.keys()) == ["a", "c", "b"]
        finally:
            dlg.close()

    def test_move_up_at_first_row_is_noop(self, qapp):
        env = Environment(name="Dev", variables={"a": "1", "b": "2"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg._move_variable_at_row(0, "up")
            assert list(dlg.environments[0].variables.keys()) == ["a", "b"]
        finally:
            dlg.close()

    def test_move_down_at_last_populated_row_is_noop(self, qapp):
        env = Environment(name="Dev", variables={"a": "1", "b": "2"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg._move_variable_at_row(1, "down")
            assert list(dlg.environments[0].variables.keys()) == ["a", "b"]
        finally:
            dlg.close()

    def test_move_hidden_variable_preserves_hidden_keys_and_mask(self, qapp):
        env = Environment(name="Dev", variables={"a": "1", "b": "2"}, hidden_keys={"a"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg._move_variable_at_row(0, "down")
            assert list(dlg.environments[0].variables.keys()) == ["b", "a"]
            assert dlg.environments[0].hidden_keys == {"a"}
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
            assert list(dlg.environments[0].variables.keys()) == ["b", "a"]
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
            assert dlg.environments[0].name == "Staging"
            assert dlg.env_list.item(0).text() == "Staging"
        finally:
            dlg.close()

    def test_rename_environment_empty_name_rejected(self, qapp):
        envs = [Environment(name="Dev", variables={})]
        dlg = EnvironmentDialog(envs)
        try:
            assert not dlg._apply_environment_rename(0, "")
            assert dlg.environments[0].name == "Dev"
        finally:
            dlg.close()

    def test_rename_environment_duplicate_name_rejected(self, qapp):
        envs = [Environment(name="Dev", variables={}), Environment(name="Prod", variables={})]
        dlg = EnvironmentDialog(envs)
        try:
            assert not dlg._apply_environment_rename(0, "Prod")
            assert dlg.environments[0].name == "Dev"
        finally:
            dlg.close()

    def test_rename_environment_same_name_is_noop(self, qapp):
        envs = [Environment(name="Dev", variables={})]
        dlg = EnvironmentDialog(envs)
        try:
            assert dlg._apply_environment_rename(0, "Dev")
            assert dlg.environments[0].name == "Dev"
        finally:
            dlg.close()

    @patch(
        "pypost.ui.widgets.environments.environment_variables_widget"
        ".show_invalid_variable_name_error",
    )
    def test_invalid_variable_name_rejected_in_table(self, mock_invalid_error, qapp):
        env = Environment(name="Dev", variables={"valid_key": "1"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            row = len(dlg.environments[0].variables)
            dlg.vars_table.setItem(row, 0, QTableWidgetItem("123bad"))
            item = dlg.vars_table.item(row, 0)
            dlg.on_var_changed(item)
            assert "123bad" not in dlg.environments[0].variables
            assert dlg.vars_table.item(row, 0).text() == ""
            mock_invalid_error.assert_called_once_with(
                dlg._vars_widget,
                "Variable name cannot start with a digit.",
            )
        finally:
            dlg.close()

    @patch(
        "pypost.ui.widgets.environments.environment_list_widget.QInputDialog.getText",
        return_value=("Staging Copy", True),
    )
    def test_duplicate_environment_clones_model_and_selects_new_row(
        self, _mock_input, qapp
    ):
        source = Environment(
            name="Staging",
            variables={"API_KEY": "secret", "HOST": "localhost"},
            hidden_keys={"API_KEY"},
            enable_mcp=True,
        )
        envs = [Environment(name="Dev", variables={}), source]
        dlg = EnvironmentDialog(envs)
        try:
            dlg._env_list_widget._duplicate_environment_at_row(1)
            assert len(dlg.environments) == 3
            assert dlg.environments[1].name == "Staging"
            copy_env = dlg.environments[2]
            assert copy_env.name == "Staging Copy"
            assert copy_env.variables == source.variables
            assert copy_env.hidden_keys == source.hidden_keys
            assert copy_env.enable_mcp is True
            assert copy_env.id != source.id
            assert dlg.env_list.currentRow() == 2
            assert dlg.env_list.item(2).text() == "Staging Copy"
        finally:
            dlg.close()

    @patch(
        "pypost.ui.widgets.environments.environment_list_widget.QInputDialog.getText",
        return_value=("", False),
    )
    def test_duplicate_environment_cancelled_leaves_list_unchanged(
        self, _mock_input, qapp
    ):
        envs = [Environment(name="Dev", variables={"a": "1"})]
        dlg = EnvironmentDialog(envs)
        try:
            dlg._env_list_widget._duplicate_environment_at_row(0)
            assert len(envs) == 1
            assert envs[0].name == "Dev"
        finally:
            dlg.close()

    @patch(
        "pypost.ui.widgets.environments.environment_list_widget.show_copy_environment_empty_name_error"
    )
    @patch(
        "pypost.ui.widgets.environments.environment_list_widget.QInputDialog.getText"
    )
    def test_duplicate_environment_empty_name_reprompts(
        self, mock_get_text, mock_empty_error, qapp
    ):
        mock_get_text.side_effect = [("   ", True), ("Valid Copy", True)]
        envs = [Environment(name="Dev", variables={})]
        dlg = EnvironmentDialog(envs)
        try:
            dlg._env_list_widget._duplicate_environment_at_row(0)
            assert mock_empty_error.call_count == 1
            assert len(dlg.environments) == 2
            assert dlg.environments[1].name == "Valid Copy"
            assert mock_get_text.call_count == 2
        finally:
            dlg.close()

    @patch(
        "pypost.ui.widgets.environments.environment_list_widget.show_copy_environment_duplicate_name_error"
    )
    @patch(
        "pypost.ui.widgets.environments.environment_list_widget.QInputDialog.getText"
    )
    def test_duplicate_environment_duplicate_name_reprompts(
        self, mock_get_text, mock_dup_error, qapp
    ):
        mock_get_text.side_effect = [("Dev", True), ("Dev Copy", True)]
        envs = [Environment(name="Dev", variables={})]
        dlg = EnvironmentDialog(envs)
        try:
            dlg._env_list_widget._duplicate_environment_at_row(0)
            assert mock_dup_error.call_count == 1
            mock_dup_error.assert_called_with(dlg._env_list_widget, "Dev")
            assert len(dlg.environments) == 2
            assert dlg.environments[1].name == "Dev Copy"
            assert mock_get_text.call_count == 2
        finally:
            dlg.close()

    @patch(
        "pypost.ui.widgets.environments.environment_list_widget.QInputDialog.getText",
        return_value=("Copy of Dev", True),
    )
    def test_duplicate_environment_logs_copied_event(self, _mock_input, qapp, caplog):
        envs = [Environment(name="Dev", variables={})]
        dlg = EnvironmentDialog(envs)
        try:
            with caplog.at_level(logging.INFO):
                dlg._env_list_widget._duplicate_environment_at_row(0)
            assert any(
                "environment_copied source_name=Dev new_name=Copy of Dev" in r.message
                for r in caplog.records
            )
        finally:
            dlg.close()

    @patch(
        "pypost.ui.widgets.environments.environment_list_widget.QInputDialog.getText",
        return_value=("", False),
    )
    def test_add_environment_cancelled_leaves_list_unchanged(self, _mock_input, qapp):
        envs = [Environment(name="Base", variables={})]
        dlg = EnvironmentDialog(envs)
        try:
            dlg.add_environment()
            assert len(envs) == 1
            assert envs[0].name == "Base"
        finally:
            dlg.close()

    @patch(
        "pypost.ui.widgets.environments.environment_list_widget.QInputDialog.getText",
        return_value=("", True),
    )
    def test_add_environment_empty_name_not_appended(self, _mock_input, qapp):
        envs = [Environment(name="Base", variables={})]
        dlg = EnvironmentDialog(envs)
        try:
            dlg.add_environment()
            assert len(envs) == 1
        finally:
            dlg.close()

    def test_add_variable_via_trailing_row_appends_to_model(self, qapp):
        env = Environment(name="Dev", variables={"existing": "1"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            trailing_row = len(dlg.environments[0].variables)
            dlg.vars_table.setItem(trailing_row, 0, QTableWidgetItem("new_key"))
            dlg.vars_table.setItem(trailing_row, 1, QTableWidgetItem("new_val"))
            item = dlg.vars_table.item(trailing_row, 0)
            dlg.on_var_changed(item)
            assert dlg.environments[0].variables == {"existing": "1", "new_key": "new_val"}
            assert dlg.vars_table.rowCount() == 3
        finally:
            dlg.close()

    @patch(
        "pypost.ui.widgets.environments.environment_variables_widget"
        ".show_invalid_variable_name_error",
    )
    def test_edit_existing_key_to_invalid_name_reverts(self, mock_invalid_error, qapp):
        env = Environment(name="Dev", variables={"valid_key": "1"})
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            dlg.vars_table.item(0, 0).setText("123bad")
            item = dlg.vars_table.item(0, 0)
            dlg.on_var_changed(item)
            assert list(dlg.environments[0].variables.keys()) == ["valid_key"]
            assert dlg.vars_table.item(0, 0).text() == "valid_key"
            mock_invalid_error.assert_called_once_with(
                dlg._vars_widget,
                "Variable name cannot start with a digit.",
            )
        finally:
            dlg.close()

    def test_on_env_selected_invalid_row_clears_table_and_disables_mcp(self, qapp):
        env = Environment(name="Dev", variables={"k": "v"}, enable_mcp=True)
        dlg = EnvironmentDialog([env])
        try:
            dlg.on_env_selected(0)
            assert dlg.mcp_check.isEnabled()
            dlg.on_env_selected(-1)
            assert dlg.vars_table.rowCount() == 0
            assert not dlg.mcp_check.isEnabled()
            assert not dlg.mcp_check.isChecked()
        finally:
            dlg.close()

    @patch(
        "pypost.ui.widgets.environments.environment_list_widget.QInputDialog.getText",
        return_value=("Dev Copy", True),
    )
    def test_env_list_context_menu_copy_duplicates_environment(
        self, _mock_input, qapp
    ):
        envs = [Environment(name="Dev", variables={"x": "1"})]
        dlg = EnvironmentDialog(envs)
        try:
            list_widget = dlg._env_list_widget
            item = dlg.env_list.item(0)
            rename_action = object()
            copy_action = object()
            delete_action = object()

            with patch.object(list_widget.env_list, "itemAt", return_value=item):
                with patch(
                    "pypost.ui.widgets.environments.environment_list_widget.QMenu"
                ) as mock_menu_cls:
                    mock_menu = mock_menu_cls.return_value
                    mock_menu.addAction.side_effect = [
                        rename_action,
                        copy_action,
                        delete_action,
                    ]
                    mock_menu.exec.return_value = copy_action
                    from PySide6.QtCore import QPoint

                    list_widget._on_env_list_context_menu(QPoint(0, 0))

            assert len(dlg.environments) == 2
            assert dlg.environments[1].name == "Dev Copy"
            assert dlg.environments[1].variables == {"x": "1"}
        finally:
            dlg.close()

