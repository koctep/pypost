"""Unit tests for MainWindow presenter signal wiring."""

import pytest

pytestmark = pytest.mark.timeout(60)

from unittest.mock import MagicMock

from pypost.ui.main_window_signals import wire_presenter_signals


def test_wire_presenter_signals_connects_curl_copied_status_bar():
    window = MagicMock()
    wire_presenter_signals(window)
    window.history_panel.curl_copied.connect.assert_called_once()
    callback = window.history_panel.curl_copied.connect.call_args[0][0]
    callback()
    window.statusBar().showMessage.assert_called_once_with("Copied to clipboard", 3000)


def test_wire_presenter_signals_connects_collection_to_tabs():
    window = MagicMock()
    wire_presenter_signals(window)
    window.collections.open_request_in_tab.connect.assert_called_once_with(
        window.tabs.add_new_tab,
    )
    window.collections.open_request_in_isolated_tab.connect.assert_called_once_with(
        window.tabs.add_new_tab,
    )


def test_wire_presenter_signals_connects_tabs_request_saved_to_collections():
    window = MagicMock()
    wire_presenter_signals(window)
    window.tabs.request_saved.connect.assert_any_call(window.collections.refresh_tree)
    window.tabs.request_saved.connect.assert_any_call(
        window.collections.restore_tree_state,
    )


def test_wire_presenter_signals_connects_mcp_controls_refresh_tools():
    window = MagicMock()
    wire_presenter_signals(window)
    window.collections.collections_changed.connect.assert_any_call(
        window.mcp_controls.refresh_tools
    )
    window.collections.requests_deleted.connect.assert_any_call(
        window.mcp_controls.refresh_tools
    )
    window.tabs.request_saved.connect.assert_any_call(
        window.mcp_controls.refresh_tools
    )
