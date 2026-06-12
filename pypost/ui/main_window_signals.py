"""Presenter and panel signal wiring for MainWindow."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pypost.ui.main_window import MainWindow


def wire_presenter_signals(window: MainWindow) -> None:
    """Connect collections, tabs, env, and history panel cross-presenter signals."""
    window.collections.open_request_in_tab.connect(window.tabs.add_new_tab)
    window.collections.open_request_in_isolated_tab.connect(window.tabs.add_new_tab)
    window.collections.collections_changed.connect(window.env.load_environments)
    window.collections.collections_changed.connect(window.env.refresh_mcp_tools)
    window.collections.request_renamed.connect(window.tabs.rename_request_tabs)
    window.collections.requests_deleted.connect(window.tabs.close_tabs_for_request_ids)
    window.collections.requests_deleted.connect(window.env.refresh_mcp_tools)
    window.env.env_variables_changed.connect(window.tabs.on_env_variables_changed)
    window.env.env_keys_changed.connect(window.tabs.on_env_keys_changed)
    window.env.env_hidden_keys_changed.connect(
        window.tabs.on_env_hidden_keys_changed,
    )
    window.tabs.variable_set_requested.connect(window.env.handle_variable_set_request)
    window.tabs.env_update_requested.connect(window.env.on_env_update)
    window.tabs.request_saved.connect(window.collections.refresh_tree)
    window.tabs.request_saved.connect(window.collections.restore_tree_state)
    window.tabs.request_saved.connect(window.env.refresh_mcp_tools)
    window.tabs.request_save_as_completed.connect(
        window.collections.add_saved_request_to_tree,
    )
    window.tabs.request_executed.connect(window.history_panel.refresh)
    window.history_panel.load_into_editor.connect(window.tabs.load_request_from_history)
    window.history_panel.curl_copied.connect(
        lambda: window.statusBar().showMessage("Copied to clipboard", 3000),
    )
