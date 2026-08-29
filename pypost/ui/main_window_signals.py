"""Presenter and panel signal wiring for MainWindow."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer

if TYPE_CHECKING:
    from pypost.ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def wire_presenter_signals(window: MainWindow) -> None:
    """Connect collections, tabs, env, and history panel cross-presenter signals."""
    logger.debug("wire_presenter_signals_started")
    window.collections.open_request_in_tab.connect(window.tabs.add_new_tab)
    window.collections.open_request_in_isolated_tab.connect(window.tabs.add_new_tab)
    window.collections.open_websocket_in_tab.connect(
        lambda conn: window.tabs.open_websocket_tab(conn)
    )
    window.collections.open_websocket_in_isolated_tab.connect(
        lambda conn: window.tabs.open_websocket_isolated_tab(conn)
    )
    window.collections.open_mcp_client_in_tab.connect(
        lambda conn: window.tabs.open_mcp_client_tab(conn)
    )
    window.collections.open_mcp_client_in_isolated_tab.connect(
        lambda conn: window.tabs.open_mcp_client_isolated_tab(conn)
    )
    window.collections.collections_changed.connect(window.env.load_environments)
    window.collections.collections_changed.connect(window.mcp_controls.refresh_tools)
    window.collections.request_renamed.connect(window.tabs.rename_request_tabs)
    window.collections.websocket_renamed.connect(window.tabs.rename_websocket_tabs)
    window.collections.mcp_client_renamed.connect(window.tabs.rename_mcp_client_tabs)
    window.collections.requests_deleted.connect(window.tabs.close_tabs_for_request_ids)
    window.collections.websockets_deleted.connect(window.tabs.close_tabs_for_websocket_ids)
    window.collections.mcp_clients_deleted.connect(window.tabs.close_tabs_for_mcp_client_ids)
    window.collections.requests_deleted.connect(window.mcp_controls.refresh_tools)
    window.collections.websockets_deleted.connect(window.mcp_controls.refresh_tools)
    window.env.env_variables_changed.connect(window.tabs.on_env_variables_changed)
    window.env.env_keys_changed.connect(window.tabs.on_env_keys_changed)
    window.env.env_hidden_keys_changed.connect(
        window.tabs.on_env_hidden_keys_changed,
    )
    window.env.environment_selected.connect(
        window.mcp_controls.handle_environment_selected
    )
    window.env.environment_updated.connect(window.mcp_controls.refresh_environment)
    window.env.environment_manager_closed.connect(
        window.mcp_controls.on_environment_manager_closed
    )
    window.tabs.variable_set_requested.connect(window.env.handle_variable_set_request)
    window.tabs.env_update_requested.connect(window.env.on_env_update)
    window.tabs.request_saved.connect(window.collections.refresh_tree)
    window.tabs.request_saved.connect(window.collections.restore_tree_state)
    window.tabs.request_saved.connect(window.mcp_controls.refresh_tools)
    window.tabs.request_save_as_completed.connect(
        window.collections.add_saved_request_to_tree,
    )
    window.tabs.websocket_saved.connect(window.collections.refresh_tree)
    window.tabs.websocket_saved.connect(window.collections.restore_tree_state)
    window.tabs.websocket_saved.connect(window.mcp_controls.refresh_tools)
    window.tabs.websocket_save_as_completed.connect(
        window.collections.add_saved_websocket_to_tree,
    )
    window.tabs.mcp_client_saved.connect(window.collections.refresh_tree)
    window.tabs.mcp_client_saved.connect(window.collections.restore_tree_state)
    window.tabs.mcp_client_saved.connect(window.mcp_controls.refresh_tools)
    window.tabs.mcp_client_save_as_completed.connect(
        window.collections.add_saved_mcp_client_to_tree,
    )
    window.tabs.request_executed.connect(window.history_panel.refresh)
    window.history_panel.load_into_editor.connect(window.tabs.load_request_from_history)
    window.history_panel.curl_copied.connect(
        lambda: window.statusBar().showMessage("Copied to clipboard", 3000),
    )
    window.history_manager.load_async(
        on_complete=lambda: QTimer.singleShot(0, window.history_panel.refresh),
    )
    logger.debug("wire_presenter_signals_completed")
