"""Construction-only tests for the blank-tab protocol picker (PYPOST-1157).

Do not call QMenu.exec() here — it blocks the Qt event loop.
"""

import unittest

import pytest
from PySide6.QtWidgets import QMenu

from pypost.ui.widgets.new_tab_protocol_picker import (
    NewTabProtocolPicker,
    TabProtocol,
)

pytestmark = pytest.mark.timeout(60)


@pytest.mark.usefixtures("qapp")
class TestNewTabProtocolPicker(unittest.TestCase):
    def test_build_menu_http_request_is_first_default(self):
        menu = NewTabProtocolPicker().build_menu()
        self.assertIsInstance(menu, QMenu)
        labels = [
            action.text().replace("&", "") for action in menu.actions()
        ]
        self.assertEqual(
            labels,
            ["HTTP Request", "WebSocket", "MCP Client"],
        )
        self.assertIs(menu.activeAction(), menu.actions()[0])

    def test_build_menu_includes_mcp_client_as_third_item(self):
        menu = NewTabProtocolPicker().build_menu()
        self.assertIsInstance(menu, QMenu)
        labels = [
            action.text().replace("&", "") for action in menu.actions()
        ]
        self.assertEqual(
            labels,
            ["HTTP Request", "WebSocket", "MCP Client"],
        )
        self.assertIs(menu.activeAction(), menu.actions()[0])
        self.assertEqual(
            menu.actions()[2].data(),
            TabProtocol.MCP_CLIENT,
        )

    def test_prompt_maps_mcp_client_action(self):
        picker = NewTabProtocolPicker()
        original_build = picker.build_menu

        def build_menu_with_mocked_exec(parent=None):
            menu = original_build(parent)

            def fake_exec(*_args, **_kwargs):
                return menu.actions()[2]

            menu.exec = fake_exec
            return menu

        picker.build_menu = build_menu_with_mocked_exec
        result = picker.prompt()
        self.assertEqual(result, TabProtocol.MCP_CLIENT)
