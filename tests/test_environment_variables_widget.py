"""Qt-level tests for EnvironmentVariablesWidget row-update helpers."""

import pytest

from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QStyle, QStyleOptionViewItem, QTableWidgetItem

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
            hidden_item = widget.get_hidden_item(0)
            assert hidden_item is not None
            hidden_item.setCheckState(Qt.CheckState.Checked)
            assert widget.vars_table.item(0, 1).text() == HIDDEN_MASK
            hidden_item.setCheckState(Qt.CheckState.Unchecked)
            assert widget.vars_table.item(0, 1).text() == "secret"
        finally:
            widget.close()

    def test_hidden_column_uses_checkable_items_without_cell_widgets(self, qapp):
        env = Environment(
            name="Dev",
            variables={"API_KEY": "secret"},
            hidden_keys={"API_KEY"},
        )
        widget = self._widget_with_env(env)
        try:
            for row in range(widget.vars_table.rowCount()):
                assert widget.vars_table.cellWidget(row, 2) is None
                hidden_item = widget.get_hidden_item(row)
                assert hidden_item is not None
                assert hidden_item.flags() & Qt.ItemFlag.ItemIsUserCheckable
                assert not hidden_item.flags() & Qt.ItemFlag.ItemIsEditable
        finally:
            widget.close()

    def test_hidden_item_can_be_toggled_with_keyboard(self, qapp):
        env = Environment(name="Dev", variables={"API_KEY": "secret"})
        widget = self._widget_with_env(env)
        try:
            widget.show()
            widget.vars_table.setCurrentCell(0, 2)
            widget.vars_table.setFocus()
            QTest.keyClick(widget.vars_table, Qt.Key.Key_Space)
            assert widget.get_hidden_item(0).checkState() == Qt.CheckState.Checked
            assert env.hidden_keys == {"API_KEY"}
            assert widget.vars_table.item(0, 1).text() == HIDDEN_MASK
        finally:
            widget.close()

    def test_hidden_item_can_be_toggled_with_mouse(self, qapp):
        env = Environment(name="Dev", variables={"API_KEY": "secret"})
        widget = self._widget_with_env(env)
        try:
            widget.show()
            qapp.processEvents()
            hidden_item = widget.get_hidden_item(0)
            index = widget.vars_table.model().index(0, 2)
            option = QStyleOptionViewItem()
            widget.vars_table.itemDelegate().initStyleOption(option, index)
            option.rect = widget.vars_table.visualItemRect(hidden_item)
            indicator_rect = widget.vars_table.style().subElementRect(
                QStyle.SubElement.SE_ItemViewItemCheckIndicator,
                option,
                widget.vars_table,
            )
            QTest.mouseClick(
                widget.vars_table.viewport(),
                Qt.MouseButton.LeftButton,
                pos=indicator_rect.center(),
            )
            assert hidden_item.checkState() == Qt.CheckState.Checked
            assert env.hidden_keys == {"API_KEY"}
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

    @patch(
        "pypost.ui.widgets.environments.environment_variables_widget"
        ".show_invalid_variable_name_error",
    )
    def test_duplicate_rename_is_atomic(self, mock_invalid_error, qapp):
        env = Environment(
            name="Dev",
            variables={"A": "1", "B": "2"},
            hidden_keys={"B"},
        )
        widget = self._widget_with_env(env)
        try:
            original_row_id = widget._draft.row(1).row_id
            widget.vars_table.item(1, 0).setText("A")

            assert env.variables == {"A": "1", "B": "2"}
            assert env.hidden_keys == {"B"}
            assert widget.vars_table.item(1, 0).text() == "B"
            assert widget.vars_table.currentRow() == 1
            assert widget._draft.row(1).row_id == original_row_id
            mock_invalid_error.assert_called_once_with(
                widget,
                'Variable "A" already exists.',
            )
        finally:
            widget.close()

    @patch(
        "pypost.ui.widgets.environments.environment_variables_widget"
        ".show_invalid_variable_name_error",
    )
    def test_duplicate_in_trailing_row_does_not_change_model(
        self, mock_invalid_error, qapp
    ):
        env = Environment(
            name="Dev",
            variables={"SECRET": "original-secret"},
            hidden_keys={"SECRET"},
        )
        widget = self._widget_with_env(env)
        try:
            trailing = len(env.variables)
            widget.vars_table.item(trailing, 1).setText("new")
            widget.get_hidden_item(trailing).setCheckState(Qt.CheckState.Checked)
            widget.vars_table.item(trailing, 0).setText(" SECRET ")

            assert env.variables == {"SECRET": "original-secret"}
            assert env.hidden_keys == {"SECRET"}
            assert widget.vars_table.item(0, 1).text() == HIDDEN_MASK
            assert widget._draft.row(trailing).value == "new"
            assert widget._draft.row(trailing).hidden is True
            assert widget.vars_table.item(trailing, 0).text() == ""
            mock_invalid_error.assert_called_once()
            assert "original-secret" not in str(mock_invalid_error.call_args)
        finally:
            widget.close()

    @patch(
        "pypost.ui.widgets.environments.environment_variables_widget"
        ".show_invalid_variable_name_error",
    )
    def test_invalid_hidden_rename_preserves_value_order_and_flag(
        self, mock_invalid_error, qapp
    ):
        env = Environment(
            name="Dev",
            variables={"VISIBLE": "one", "SECRET": "s3cr3t"},
            hidden_keys={"SECRET"},
        )
        widget = self._widget_with_env(env)
        try:
            widget.vars_table.item(1, 0).setText("bad-key")

            assert list(env.variables.items()) == [
                ("VISIBLE", "one"),
                ("SECRET", "s3cr3t"),
            ]
            assert env.hidden_keys == {"SECRET"}
            assert widget.vars_table.item(1, 1).text() == HIDDEN_MASK
            mock_invalid_error.assert_called_once()
        finally:
            widget.close()
