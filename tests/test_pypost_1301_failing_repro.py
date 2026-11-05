"""Failing repro tests for PYPOST-1301.

Asserts desired tab-removal and app-exit export teardown behavior from:
- ai-tasks/PYPOST-1301/10-requirements.md
- ai-tasks/PYPOST-1301/20-architecture.md

RED on current code: close paths only ``removeTab`` (page leaked, cleanup never
reached); ``TabsPresenter.teardown`` ignores WebSocket stream export ownership.
"""

from __future__ import annotations

import logging
from pathlib import Path
from threading import Event
from unittest.mock import MagicMock

import pytest
import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

from pypost.core.qt.websocket_stream_export_worker import WebSocketStreamExportWorker
from pypost.models.settings import AppSettings
from pypost.ui.presenters.tabs_presenter import TabsPresenter, WebSocketTab
from pypost.ui.widgets.new_tab_protocol_picker import TabProtocol
from pypost.ui.widgets.websocket.stream_view import WebSocketStreamView
from tests.test_tabs_presenter import FakeRequestManager, FakeStateManager

pytestmark = pytest.mark.timeout(30)


def _make_tabs_presenter() -> TabsPresenter:
    return TabsPresenter(
        FakeRequestManager(),
        FakeStateManager(),
        AppSettings(),
        metrics=MagicMock(),
        protocol_picker=lambda *_a, **_k: TabProtocol.HTTP,
    )


def _flush_deferred_deletes(qapp: QApplication) -> None:
    """Dispatch queued ``deleteLater`` so ``shiboken6.isValid`` reflects disposal."""
    qapp.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def _install_blocked_export_run(
    monkeypatch: pytest.MonkeyPatch,
    *,
    entered: Event,
    release: Event,
) -> None:
    original_run = WebSocketStreamExportWorker.run

    def blocked_run(worker_self: WebSocketStreamExportWorker) -> None:
        entered.set()
        if release.wait(timeout=10):
            original_run(worker_self)

    monkeypatch.setattr(WebSocketStreamExportWorker, "run", blocked_run)


def _ws_pages_on_strip(presenter: TabsPresenter) -> list[WebSocketTab]:
    pages: list[WebSocketTab] = []
    for index in range(presenter.widget.count()):
        page = presenter.widget.widget(index)
        if isinstance(page, WebSocketTab):
            pages.append(page)
    return pages


def test_busy_websocket_tab_close_defers_page_until_export_ends(
    tmp_path: Path,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production close_tab must attempt cleanup and dispose after ownership ends."""
    presenter = _make_tabs_presenter()
    tab = presenter.add_blank_websocket_tab(save_state=False)
    assert isinstance(tab, WebSocketTab)
    stream_view = tab.stream_view
    tab_index = presenter.widget.indexOf(tab)
    assert tab_index >= 0

    cleanup_calls: list[bool] = []
    original_cleanup = WebSocketStreamView.cleanup

    def tracking_cleanup(self: WebSocketStreamView) -> bool:
        cleanup_calls.append(True)
        return original_cleanup(self)

    monkeypatch.setattr(WebSocketStreamView, "cleanup", tracking_cleanup)

    entered = Event()
    release = Event()
    _install_blocked_export_run(monkeypatch, entered=entered, release=release)
    worker = None
    try:
        stream_view.export_json(tmp_path / "busy-close.json")
        worker = stream_view._export_worker
        assert worker is not None
        assert entered.wait(timeout=5), "Export worker did not start"

        presenter.close_tab(tab_index)

        assert presenter.widget.indexOf(tab) < 0, "Tab must leave the strip promptly"
        assert cleanup_calls, (
            "close_tab must invoke stream_view.cleanup on the production path"
        )
        assert shiboken6.isValid(tab), (
            "Busy page must not be force-destroyed while export ownership remains"
        )
        assert stream_view.is_export_busy(), (
            "Export ownership must remain after the close wait budget"
        )

        release.set()
        assert stream_view.wait_for_export(timeout_ms=5_000)
        _flush_deferred_deletes(qapp)
        assert not shiboken6.isValid(tab), (
            "Deferred page must be deleteLater'd once export ownership ends"
        )
    finally:
        release.set()
        if worker is not None and shiboken6.isValid(stream_view):
            owned = stream_view._export_worker
            if owned is worker:
                assert worker.wait(5_000)
        qapp.processEvents()


def test_idle_websocket_tab_close_disposes_page(
    qapp: QApplication,
) -> None:
    """Idle close must delete the page instead of leaking it until process exit."""
    presenter = _make_tabs_presenter()
    tab = presenter.add_blank_websocket_tab(save_state=False)
    assert isinstance(tab, WebSocketTab)
    stream_view = tab.stream_view
    assert not stream_view.is_export_busy()
    tab_index = presenter.widget.indexOf(tab)
    assert tab_index >= 0

    presenter.close_tab(tab_index)

    assert presenter.widget.indexOf(tab) < 0
    _flush_deferred_deletes(qapp)
    assert not shiboken6.isValid(tab), (
        "Idle WebSocket tab close must dispose the page (deleteLater)"
    )


def test_busy_tabs_teardown_abandons_export_after_budget(
    tmp_path: Path,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """App-exit teardown must release export ownership after the wait budget."""
    presenter = _make_tabs_presenter()
    tab = presenter.add_blank_websocket_tab(save_state=False)
    assert isinstance(tab, WebSocketTab)
    stream_view = tab.stream_view

    entered = Event()
    release = Event()
    _install_blocked_export_run(monkeypatch, entered=entered, release=release)
    worker = None
    try:
        stream_view.export_json(tmp_path / "busy-exit.json")
        worker = stream_view._export_worker
        assert worker is not None
        assert entered.wait(timeout=5), "Export worker did not start"
        assert stream_view.is_export_busy()

        result = presenter.teardown(timeout_ms=50)
        assert result is not None

        assert not stream_view.is_export_busy(), (
            "After the exit budget, teardown must abandon/release export ownership "
            "so the view does not solely own a still-running worker"
        )
        # View may still exist after teardown; ownership must not remain on it.
        if shiboken6.isValid(stream_view):
            assert stream_view._export_worker is None
    finally:
        release.set()
        if worker is not None:
            assert worker.wait(5_000)
        qapp.processEvents()


def test_idle_tabs_teardown_skips_export_abandon(
    qapp: QApplication,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Idle exit must not wait on or abandon stream export ownership."""
    presenter = _make_tabs_presenter()
    tab = presenter.add_blank_websocket_tab(save_state=False)
    assert isinstance(tab, WebSocketTab)
    assert not tab.stream_view.is_export_busy()
    assert _ws_pages_on_strip(presenter)

    with caplog.at_level(logging.WARNING):
        result = presenter.teardown(timeout_ms=200)

    assert result.outcome in {"success", "incomplete"}
    assert not any(
        "action=export_abandoned" in record.getMessage() for record in caplog.records
    ), "Idle exit must not abandon stream export ownership"
    assert tab.stream_view.is_export_busy() is False
