"""Construction-only tests for the blank-tab protocol picker (PYPOST-1157).

Do not call QMenu.exec() here — it blocks the Qt event loop.
"""

import unittest

import pytest
from PySide6.QtWidgets import QMenu

pytestmark = pytest.mark.timeout(60)


@pytest.mark.usefixtures("qapp")
class TestNewTabProtocolPicker(unittest.TestCase):
    def test_build_menu_http_request_is_first_default(self):
        from pypost.ui.widgets.new_tab_protocol_picker import (
            NewTabProtocolPicker,
        )

        menu = NewTabProtocolPicker().build_menu()
        self.assertIsInstance(menu, QMenu)
        labels = [
            action.text().replace("&", "") for action in menu.actions()
        ]
        self.assertEqual(labels, ["HTTP Request", "WebSocket"])
        self.assertIs(menu.activeAction(), menu.actions()[0])
        lowered = [label.lower() for label in labels]
        self.assertTrue(all("mcp" not in label for label in lowered))
        self.assertFalse(
            any("mcp client" in label for label in lowered),
        )
