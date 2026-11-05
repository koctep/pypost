"""PYPOST-1301 observability: defer/abandon export dispose structured logs."""

from __future__ import annotations

import logging
from pathlib import Path
from threading import Event
from unittest.mock import MagicMock

import pytest
import shiboken6
from PySide6.QtWidgets import QApplication

from pypost.models.settings import AppSettings
from pypost.ui.presenters.tabs_presenter import TabsPresenter, WebSocketTab
from pypost.ui.widgets.new_tab_protocol_picker import TabProtocol
from tests.test_pypost_1301_failing_repro import (
    _flush_deferred_deletes,
    _install_blocked_export_run,
)
from tests.test_tabs_presenter import FakeRequestManager, FakeStateManager

pytestmark = pytest.mark.timeout(30)

_HELPER_LOGGER = "pypost.ui.presenters.tabs_presenter_ws_export_teardown"
_VIEW_LOGGER = "pypost.ui.widgets.websocket.stream_view"
_TIMEOUT_EVENT = "websocket_stream_export_worker_finish_wait_timeout"
_DEFERRED_DONE = "websocket_stream_export_deferred_dispose_completed"


def _make_tabs_presenter() -> TabsPresenter:
    return TabsPresenter(
        FakeRequestManager(),
        FakeStateManager(),
        AppSettings(),
        metrics=MagicMock(),
        protocol_picker=lambda *_a, **_k: TabProtocol.HTTP,
    )


def _messages(
    caplog: pytest.LogCaptureFixture,
    prefix: str,
) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.getMessage().startswith(prefix)]


def test_busy_tab_close_logs_dispose_deferred_then_completed(
    tmp_path: Path,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Tab-close defer path emits WARNING then INFO with action=dispose_deferred."""
    presenter = _make_tabs_presenter()
    tab = presenter.add_blank_websocket_tab(save_state=False)
    assert isinstance(tab, WebSocketTab)
    stream_view = tab.stream_view
    tab_index = presenter.widget.indexOf(tab)

    entered = Event()
    release = Event()
    _install_blocked_export_run(monkeypatch, entered=entered, release=release)
    worker = None
    try:
        stream_view.export_json(tmp_path / "obs-defer.json")
        worker = stream_view._export_worker
        assert worker is not None
        assert entered.wait(timeout=5)

        with caplog.at_level(logging.INFO, logger=_HELPER_LOGGER):
            presenter.close_tab(tab_index)
            deferred = _messages(caplog, _TIMEOUT_EVENT)
            assert len(deferred) == 1
            assert deferred[0].levelno == logging.WARNING
            msg = deferred[0].getMessage()
            assert "action=dispose_deferred" in msg
            assert "wait_ms=" in msg

            release.set()
            assert stream_view.wait_for_export(timeout_ms=5_000)
            _flush_deferred_deletes(qapp)

            completed = _messages(caplog, _DEFERRED_DONE)
            assert len(completed) == 1
            assert completed[0].levelno == logging.INFO
            assert "action=dispose_deferred" in completed[0].getMessage()
    finally:
        release.set()
        if (
            worker is not None
            and shiboken6.isValid(stream_view)
            and stream_view._export_worker is worker
        ):
            assert worker.wait(5_000)
        qapp.processEvents()


def test_busy_teardown_logs_export_abandoned_with_wait_ms(
    tmp_path: Path,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """App-exit abandon path emits WARNING with wait_ms and action=export_abandoned."""
    presenter = _make_tabs_presenter()
    tab = presenter.add_blank_websocket_tab(save_state=False)
    assert isinstance(tab, WebSocketTab)
    stream_view = tab.stream_view

    entered = Event()
    release = Event()
    _install_blocked_export_run(monkeypatch, entered=entered, release=release)
    worker = None
    try:
        stream_view.export_json(tmp_path / "obs-abandon.json")
        worker = stream_view._export_worker
        assert worker is not None
        assert entered.wait(timeout=5)

        with caplog.at_level(logging.WARNING, logger=_VIEW_LOGGER):
            presenter.teardown(timeout_ms=50)
            abandoned = [
                r
                for r in _messages(caplog, _TIMEOUT_EVENT)
                if "action=export_abandoned" in r.getMessage()
            ]
            assert len(abandoned) == 1
            msg = abandoned[0].getMessage()
            assert "wait_ms=" in msg
            assert abandoned[0].levelno == logging.WARNING
    finally:
        release.set()
        if worker is not None:
            assert worker.wait(5_000)
        qapp.processEvents()


def test_idle_tab_close_skips_defer_and_abandon_logs(
    qapp: QApplication,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Idle close must not emit dispose_deferred or export_abandoned WARNINGs."""
    presenter = _make_tabs_presenter()
    tab = presenter.add_blank_websocket_tab(save_state=False)
    assert isinstance(tab, WebSocketTab)
    tab_index = presenter.widget.indexOf(tab)

    with caplog.at_level(logging.INFO, logger=_HELPER_LOGGER):
        with caplog.at_level(logging.WARNING, logger=_VIEW_LOGGER):
            presenter.close_tab(tab_index)

    assert not any(
        "action=dispose_deferred" in r.getMessage() for r in caplog.records
    )
    assert not any(
        "action=export_abandoned" in r.getMessage() for r in caplog.records
    )
