"""Collection request tab close helper extracted from TabsPresenter."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pypost.ui.presenters.tabs_presenter import TabsPresenter

logger = logging.getLogger(__name__)


def close_tabs_for_request_ids(
    presenter: TabsPresenter,
    request_ids: list,
) -> None:
    """Closes tabs that reference deleted collection requests."""
    from pypost.ui.presenters.tabs_presenter import RequestTab

    if not request_ids:
        return
    ids_to_close = set(request_ids)
    indices_to_close = []
    for i in range(presenter._tabs.count()):
        tab = presenter._tabs.widget(i)
        if (
            isinstance(tab, RequestTab)
            and tab.request_data
            and tab.request_data.id in ids_to_close
        ):
            indices_to_close.append(i)
    for index in reversed(indices_to_close):
        tab = presenter._tabs.widget(index)
        if isinstance(tab, RequestTab):
            result = presenter.teardown_tab(tab)
            if result.outcome != "success":
                continue
        presenter._tabs.removeTab(index)
    if presenter._request_tab_count() == 0:
        presenter.add_new_tab(save_state=False)
    elif indices_to_close:
        # Qt removeTab can land on trailing +; keep focus on a request tab.
        preferred = max(0, min(indices_to_close) - 1)
        presenter._ensure_current_is_navigable(preferred)
    presenter.save_tabs_state()
    logger.info(
        "close_tabs_for_deleted_requests closed_count=%d request_ids=%s",
        len(indices_to_close),
        sorted(ids_to_close),
    )
