import unittest

import pytest
from PySide6.QtWidgets import QComboBox

from pypost.models.models import McpToolParam
from pypost.ui.widgets.request_editor import McpParamsTable, RequestWidget

pytestmark = pytest.mark.timeout(60)


@pytest.mark.usefixtures("qapp")
class TestMcpParamsTable(unittest.TestCase):
    def setUp(self):
        self.table = McpParamsTable()

    def tearDown(self):
        self.table.close()
        self.table.deleteLater()

    def test_type_combo_includes_array_and_object(self):
        self.table.set_data({})
        combo = self.table.cellWidget(0, 1)
        self.assertIsInstance(combo, QComboBox)
        options = [combo.itemText(i) for i in range(combo.count())]
        self.assertIn("array", options)
        self.assertIn("object", options)

    def test_type_combo_change_emits_item_changed(self):
        self.table.set_data(
            {
                "id": McpToolParam(type="string", description="Identifier"),
            }
        )
        received: list = []
        self.table.itemChanged.connect(received.append)
        combo = self.table.cellWidget(0, 1)
        self.assertIsInstance(combo, QComboBox)
        combo.setCurrentText("integer")
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].row(), 0)
        self.assertEqual(received[0].column(), 2)

    def test_round_trip_array_object_types(self):
        params = {
            "items": McpToolParam(type="array", description="List"),
            "meta": McpToolParam(type="object", required=False),
        }
        self.table.set_data(params)
        self.assertEqual(self.table.get_data(), params)

    def test_round_trip_preserves_default(self):
        params = {
            "maxResults": McpToolParam(
                type="integer_or_string",
                description="Max results",
                required=False,
                default=50,
            ),
            "startAt": McpToolParam(
                type="integer_or_string",
                description="Start at",
                required=False,
                default=0,
            ),
        }
        self.table.set_data(params)
        self.assertEqual(self.table.get_data(), params)


@pytest.mark.usefixtures("qapp")
class TestRequestWidgetMcpParamSync(unittest.TestCase):
    def setUp(self):
        self.widget = RequestWidget()

    def tearDown(self):
        self.widget.close()
        self.widget.deleteLater()

    def test_url_placeholder_populates_mcp_params_table(self):
        self.widget.url_input.setText(
            "http://api.example/{{ mcp.request.user_id }}"
        )
        self.widget._sync_mcp_params_from_template()
        params = self.widget.mcp_params_table.get_data()
        self.assertIn("user_id", params)
        self.assertEqual(params["user_id"].type, "string")
        self.assertTrue(params["user_id"].required)

    def test_sync_preserves_existing_param_metadata(self):
        self.widget.mcp_params_table.set_data(
            {
                "token": McpToolParam(
                    type="integer",
                    description="Auth token",
                    required=False,
                ),
            }
        )
        self.widget.url_input.setText(
            "http://api.example/{{ mcp.request.token }}"
        )
        self.widget._sync_mcp_params_from_template()
        params = self.widget.mcp_params_table.get_data()
        self.assertEqual(
            params["token"],
            McpToolParam(
                type="integer",
                description="Auth token",
                required=False,
            ),
        )

    def test_sync_keeps_explicit_params_not_in_templates(self):
        self.widget.mcp_params_table.set_data(
            {
                "extra": McpToolParam(
                    type="object",
                    description="Manual entry",
                ),
            }
        )
        self.widget.url_input.setText("http://api.example/")
        self.widget._sync_mcp_params_from_template()
        params = self.widget.mcp_params_table.get_data()
        self.assertIn("extra", params)
        self.assertEqual(params["extra"].type, "object")

    def test_body_change_triggers_sync_via_preview_handler(self):
        self.widget.body_edit.setPlainText(
            '{"id": "{{ mcp.request.item_id }}"}'
        )
        self.widget._on_mcp_preview_source_changed()
        params = self.widget.mcp_params_table.get_data()
        self.assertIn("item_id", params)

    def test_wrapped_placeholder_populates_mcp_params_table(self):
        self.widget.url_input.setText(
            "http://api.example/boards/{{ to_int(mcp.request.board_id) }}"
        )
        self.widget.body_edit.setPlainText(
            '{"data": "{{ base64(mcp.request.raw_data) }}"}'
        )
        self.widget._sync_mcp_params_from_template()
        params = self.widget.mcp_params_table.get_data()
        self.assertIn("board_id", params)
        self.assertIn("raw_data", params)
        self.assertEqual(params["board_id"].type, "string")
        self.assertTrue(params["board_id"].required)
        self.assertEqual(params["raw_data"].type, "string")
        self.assertTrue(params["raw_data"].required)


# ---------------------------------------------------------------------------
# PYPOST-1089 — Step 3: Failing repro tests for McpParamsTable 5-column UI
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("qapp")
class TestMcpParamsTableFiveColumns(unittest.TestCase):
    """Failing repro for PYPOST-1089: Default column must exist at index 4."""

    def setUp(self):
        self.table = McpParamsTable()

    def tearDown(self):
        self.table.close()
        self.table.deleteLater()

    def test_mcp_params_table_has_five_columns(self):
        """McpParamsTable must have 5 columns with 'Default' as the 5th header.

        Currently fails because __init__ creates 4 columns only.
        """
        self.assertEqual(self.table.columnCount(), 5)
        header_item = self.table.horizontalHeaderItem(4)
        self.assertIsNotNone(header_item, "Column 4 header item must exist")
        self.assertEqual(header_item.text(), "Default")

    def test_default_column_survives_rename(self):
        """Default value must survive a param rename (Name cell text change).

        Currently fails because get_data() reads self._defaults keyed by the
        *original* name; after renaming the cell text the key no longer matches.
        """
        params = {
            "maxResults": McpToolParam(
                type="integer",
                description="Max results",
                required=False,
                default=50,
            ),
        }
        self.table.set_data(params)

        # Simulate user renaming the param by editing the Name cell directly
        name_item = self.table.item(0, 0)
        self.assertIsNotNone(name_item)
        name_item.setText("limit")

        result = self.table.get_data()
        self.assertIn("limit", result)
        self.assertEqual(
            result["limit"].default,
            50,
            "Default must be preserved after renaming the param",
        )
