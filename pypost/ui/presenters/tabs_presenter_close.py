"""Workspace tab close helper extracted from TabsPresenter (PYPOST-1159)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pypost.ui.collection_item_dialogs import prompt_unsaved_draft_tab_close
from pypost.ui.presenters.tabs_presenter_draft import (
    PromptClose,
    confirm_close_request_draft,
    confirm_close_websocket_draft,
    make_websocket_saved_predicate,
)

if TYPE_CHECKING:
    from pypost.ui.presenters.tabs_presenter import TabsPresenter


def close_workspace_tab(
    presenter: TabsPresenter,
    index: int,
    *,
    prompt_close: PromptClose | None = None,
) -> None:
    """Close one workspace tab; last-tab empty strip uses handle_new_tab('last_tab')."""
    if presenter._header.is_plus_tab_index(index):
        return
    tab = presenter._tabs.widget(index)
    closer = (
        prompt_close if prompt_close is not None else prompt_unsaved_draft_tab_close
    )
    if not confirm_close_websocket_draft(
        presenter._tabs,
        tab,
        prompt_close=closer,
        websocket_id_is_saved=make_websocket_saved_predicate(
            presenter._request_manager
        ),
    ):
        return
    if not confirm_close_request_draft(
        presenter._tabs,
        tab,
        prompt_close=closer,
        request_id_is_saved=lambda item_id: (
            presenter._request_manager.find_request(item_id) is not None
        ),
    ):
        return
    from pypost.ui.presenters.tabs_presenter import RequestTab

    if isinstance(tab, RequestTab):
        result = presenter.teardown_tab(tab)
        if result.outcome != "success":
            return
    tab_presenter = getattr(tab, "presenter", None)
    teardown = getattr(tab_presenter, "teardown", None)
    if callable(teardown):
        teardown()
    presenter._tabs.removeTab(index)
    if presenter._request_tab_count() == 0:
        presenter.handle_new_tab("last_tab")
    else:
        presenter._ensure_current_is_navigable(max(0, index - 1))
    presenter.save_tabs_state()
