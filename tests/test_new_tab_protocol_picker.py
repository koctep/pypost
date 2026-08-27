"""Hermetic tests for the blank-tab protocol picker (PYPOST-1157 / PYPOST-1180).

Do not call QMenu.exec() here — it blocks the Qt event loop. Mock instance
menu.exec after build_menu instead (same pattern as MCP Client mapping).
"""

from __future__ import annotations

import unittest
from collections.abc import Callable

import pytest
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

from pypost.ui.widgets.new_tab_protocol_picker import (
    NewTabProtocolPicker,
    TabProtocol,
)

pytestmark = pytest.mark.timeout(60)


def _install_fake_exec(
    picker: NewTabProtocolPicker,
    chosen: Callable[[QMenu], QAction | None],
) -> None:
    """Override build_menu so the returned menu has a non-blocking exec."""
    original_build = picker.build_menu

    def build_menu_with_mocked_exec(parent=None):
        menu = original_build(parent)

        def fake_exec(*_args, **_kwargs):
            return chosen(menu)

        menu.exec = fake_exec
        return menu

    picker.build_menu = build_menu_with_mocked_exec


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

    def test_prompt_maps_http_request_action(self):
        picker = NewTabProtocolPicker()
        _install_fake_exec(picker, lambda menu: menu.actions()[0])
        result = picker.prompt()
        self.assertEqual(result, TabProtocol.HTTP)

    def test_prompt_maps_websocket_action(self):
        picker = NewTabProtocolPicker()
        _install_fake_exec(picker, lambda menu: menu.actions()[1])
        result = picker.prompt()
        self.assertEqual(result, TabProtocol.WEBSOCKET)

    def test_prompt_dismiss_returns_none(self):
        picker = NewTabProtocolPicker()
        _install_fake_exec(picker, lambda _menu: None)
        result = picker.prompt()
        self.assertIsNone(result)

    def test_prompt_maps_mcp_client_action(self):
        picker = NewTabProtocolPicker()
        _install_fake_exec(picker, lambda menu: menu.actions()[2])
        result = picker.prompt()
        self.assertEqual(result, TabProtocol.MCP_CLIENT)
