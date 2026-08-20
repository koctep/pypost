"""Qt-level tests for EnvironmentVariablesWidget row-update helpers."""

import pytest

from unittest.mock import patch

from PySide6.QtWidgets import QTableWidgetItem

from pypost.core.constants import HIDDEN_MASK
from pypost.models.models import Environment
from pypost.ui.widgets.environments.environment_variables_widget import (
    EnvironmentVariablesWidget,
)

pytestmark = pytest.mark.timeout(60)


class TestEnvironmentVariablesWidgetRowHelpers:
    def _widget_with_env(self, env: Environment) -> EnvironmentVariablesWidget:
        widget = EnvironmentVariablesWidget(get_selected_env=lambda: env)
        widget.load_environment(env)
        return widget

    def test_hidden_toggle_refreshes_value_cell(self, qapp):
        env = Environment(name="Dev", variables={"API_KEY": "secret"})
        widget = self._widget_with_env(env)
        try:
            hidden_cb = widget.get_hidden_checkbox(0)
            assert hidden_cb is not None
            hidden_cb.setChecked(True)
            assert widget.vars_table.item(0, 1).text() == HIDDEN_MASK
            hidden_cb.setChecked(False)
            assert widget.vars_table.item(0, 1).text() == "secret"
        finally:
            widget.close()

    def test_edit_hidden_value_keeps_mask_and_model(self, qapp):
        env = Environment(
            name="Dev",
            variables={"API_KEY": "old"},
            hidden_keys={"API_KEY"},
        )
        widget = self._widget_with_env(env)
        try:
            widget.vars_table.setItem(0, 1, QTableWidgetItem("new"))
            item = widget.vars_table.item(0, 1)
            widget.on_var_changed(item)
            assert env.variables["API_KEY"] == "new"
            assert widget.vars_table.item(0, 1).text() == HIDDEN_MASK
        finally:
            widget.close()

    @patch(
        "pypost.ui.widgets.environments.environment_variables_widget"
        ".show_invalid_variable_name_error",
    )
    def test_invalid_key_on_trailing_row_reverts(self, mock_invalid_error, qapp):
        env = Environment(name="Dev", variables={"valid_key": "1"})
        widget = self._widget_with_env(env)
        try:
            row = len(env.variables)
            widget.vars_table.setItem(row, 0, QTableWidgetItem("123bad"))
            item = widget.vars_table.item(row, 0)
            widget.on_var_changed(item)
            assert "123bad" not in env.variables
            assert widget.vars_table.item(row, 0).text() == ""
            mock_invalid_error.assert_called_once_with(
                widget,
                "Variable name cannot start with a digit.",
            )
        finally:
            widget.close()

    @patch(
        "pypost.ui.widgets.environments.environment_variables_widget"
        ".show_invalid_variable_name_error",
    )
    def test_invalid_rename_reverts_to_previous_key(self, mock_invalid_error, qapp):
        env = Environment(name="Dev", variables={"valid_key": "1"})
        widget = self._widget_with_env(env)
        try:
            widget.vars_table.item(0, 0).setText("123bad")
            item = widget.vars_table.item(0, 0)
            widget.on_var_changed(item)
            assert list(env.variables.keys()) == ["valid_key"]
            assert widget.vars_table.item(0, 0).text() == "valid_key"
            mock_invalid_error.assert_called_once()
        finally:
            widget.close()

    def test_add_variable_via_trailing_row(self, qapp):
        env = Environment(name="Dev", variables={"existing": "1"})
        widget = self._widget_with_env(env)
        try:
            trailing_row = len(env.variables)
            widget.vars_table.setItem(trailing_row, 0, QTableWidgetItem("new_key"))
            widget.vars_table.setItem(trailing_row, 1, QTableWidgetItem("new_val"))
            item = widget.vars_table.item(trailing_row, 0)
            widget.on_var_changed(item)
            assert env.variables == {"existing": "1", "new_key": "new_val"}
            assert widget.vars_table.rowCount() == 3
        finally:
            widget.close()
