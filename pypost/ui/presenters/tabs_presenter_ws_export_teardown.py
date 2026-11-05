"""WebSocket stream export disposal helper for tab close and app exit (PYPOST-1301).

Owns bounded export wait, strip removal via indexOf, immediate vs deferred
deleteLater, and exit abandon orchestration. Does not call session teardown.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

from pypost.ui.widgets.websocket.websocket_tab import WebSocketTab

if TYPE_CHECKING:
    from pypost.ui.presenters.tabs_presenter import TabsPresenter

logger = logging.getLogger(__name__)

DisposeMode = Literal["tab_close", "app_exit"]
DisposeOutcome = Literal["disposed", "deferred", "abandoned"]


def ensure_deferred_set(presenter: TabsPresenter) -> set[WebSocketTab]:
    """Return the presenter-private deferred page set, creating it if needed."""
    deferred = getattr(presenter, "_ws_export_deferred_pages", None)
    if deferred is None:
        deferred = set()
        presenter._ws_export_deferred_pages = deferred
    return deferred


def snapshot_websocket_pages_for_exit(
    presenter: TabsPresenter,
) -> list[WebSocketTab]:
    """Snapshot strip WebSocketTab pages union deferred set (no strip mutation)."""
    pages: list[WebSocketTab] = []
    seen: set[int] = set()
    for index in range(presenter._tabs.count()):
        page = presenter._tabs.widget(index)
        if isinstance(page, WebSocketTab) and id(page) not in seen:
            pages.append(page)
            seen.add(id(page))
    for page in list(ensure_deferred_set(presenter)):
        if id(page) not in seen:
            pages.append(page)
            seen.add(id(page))
    return pages


def dispose_websocket_tab_page(
    presenter: TabsPresenter,
    tab: WebSocketTab,
    *,
    mode: DisposeMode,
    timeout_ms: int | None = None,
) -> DisposeOutcome:
    """Attempt export-safe disposal of a WebSocket tab page.

    Args:
        presenter: TabsPresenter owning the tab strip and deferred set.
        tab: WebSocketTab page to remove/dispose.
        mode: ``tab_close`` defers after budget; ``app_exit`` abandons.
        timeout_ms: Export wait budget. ``None`` uses stream_view.cleanup()
            (100 ms). Non-None uses wait_for_export(timeout_ms).

    Returns:
        ``disposed`` when the page is deleteLater'd after ownership ends,
        ``deferred`` when tab_close keeps the page alive until export ends,
        ``abandoned`` when app_exit releases ownership after the budget.
    """
    stream_view = tab.stream_view
    if timeout_ms is None:
        ownership_ended = stream_view.cleanup()
        wait_ms = 100
    else:
        ownership_ended = stream_view.wait_for_export(timeout_ms)
        wait_ms = max(0, timeout_ms)

    index = presenter._tabs.indexOf(tab)
    if index >= 0:
        presenter._tabs.removeTab(index)

    deferred = ensure_deferred_set(presenter)
    if ownership_ended:
        deferred.discard(tab)
        tab.deleteLater()
        return "disposed"

    if mode == "tab_close":
        if _schedule_deferred_dispose(presenter, tab):
            logger.warning(
                "websocket_stream_export_worker_finish_wait_timeout "
                "wait_ms=%d action=dispose_deferred",
                wait_ms,
            )
            return "deferred"
        return "disposed"

    stream_view.abandon_export_for_shutdown(wait_ms=wait_ms)
    deferred.discard(tab)
    tab.deleteLater()
    return "abandoned"


def _schedule_deferred_dispose(
    presenter: TabsPresenter,
    tab: WebSocketTab,
) -> bool:
    """Keep page alive until export_finished, then deleteLater.

    Returns:
        True when the page remains deferred; False when it was disposed
        immediately because export was already idle after connect.
    """
    deferred = ensure_deferred_set(presenter)
    if tab in deferred:
        return True
    deferred.add(tab)
    stream_view = tab.stream_view

    def _on_export_finished() -> None:
        if tab not in deferred:
            return
        deferred.discard(tab)
        try:
            stream_view.export_finished.disconnect(_on_export_finished)
        except (RuntimeError, TypeError):
            pass
        tab.deleteLater()
        logger.info(
            "websocket_stream_export_deferred_dispose_completed "
            "action=dispose_deferred",
        )

    stream_view.export_finished.connect(_on_export_finished)
    # Re-check after connect: a nested event-loop finish during removeTab /
    # wait_for_export can emit export_finished before the slot was attached.
    if not stream_view.is_export_busy():
        _on_export_finished()
        return False
    return True
