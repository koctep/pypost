"""Shared insert-before-plus tab helper extracted from TabsPresenter (PYPOST-1184)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget

if TYPE_CHECKING:
    from pypost.ui.presenters.tabs_presenter import TabsPresenter


def insert_tab_before_plus(
    presenter: TabsPresenter,
    tab: QWidget,
    name: str,
    *,
    save_state: bool = True,
) -> None:
    """Insert *tab* immediately before the plus tab (or append and re-ensure the
    plus tab), focus it, then optionally persist tab state.

    Mirrors the sequence previously duplicated in ``add_new_tab``,
    ``_insert_mcp_client_tab``, and ``_insert_websocket_tab``: ask the header for
    the index before the plus marker; insert there if found, otherwise append and
    ask the header to (re-)ensure a plus tab exists; focus the new tab; call
    ``save_tabs_state()`` only when the caller asked for it.
    """
    plus_idx = presenter._header.insert_index_before_plus()
    if plus_idx >= 0:
        presenter._tabs.insertTab(plus_idx, tab, name)
    else:
        presenter._tabs.addTab(tab, name)
        presenter._header.ensure_plus_tab()
    presenter._tabs.setCurrentWidget(tab)
    if save_state:
        presenter.save_tabs_state()
