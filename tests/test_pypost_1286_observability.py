"""PYPOST-1286 observability: structured logs for WebSocketStreamView export lifecycle.

Covers the close-refused WARNING when the export worker outlives the close wait
budget, the one-shot DEBUG for deferred worker finalization, and the DEBUG for
ignored stale worker-finished notifications.
"""

from __future__ import annotations

import logging
from pathlib import Path
from threading import Event

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication

from pypost.core.qt.websocket_stream_export_worker import WebSocketStreamExportWorker
from pypost.ui.widgets.websocket.stream_model import StreamListModel
from pypost.ui.widgets.websocket.stream_view import WebSocketStreamView

pytestmark = pytest.mark.timeout(30)

_LOGGER = "pypost.ui.widgets.websocket.stream_view"
_CLOSE_TIMEOUT_EVENT = "websocket_stream_export_worker_finish_wait_timeout"
_DEFERRED_EVENT = "websocket_stream_export_worker_finalize_deferred"
_FINALIZED_EVENT = "websocket_stream_export_worker_finalized"
_IGNORED_EVENT = "websocket_stream_export_worker_finished_ignored"


def _messages(caplog: pytest.LogCaptureFixture, prefix: str) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.getMessage().startswith(prefix)]


def _spin_events(ms: int) -> None:
    """Run the Qt event loop for a bounded interval."""
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


class _PendingJoinWorker:
    """Worker stub whose nonblocking join fails until released."""

    def __init__(self) -> None:
        self.joined = False
        self.deleted = False

    def wait(self, _timeout_ms: int) -> bool:
        return self.joined

    def deleteLater(self) -> None:  # noqa: N802 - Qt API name
        self.deleted = True


def test_close_refused_logs_finish_wait_timeout_warning(
    tmp_path: Path,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Refused close emits one structured WARNING; a later accepted close emits none."""
    stream_view = WebSocketStreamView(stream_model=StreamListModel())
    entered = Event()
    release = Event()
    original_run = WebSocketStreamExportWorker.run

    def blocked_run(worker_self: WebSocketStreamExportWorker) -> None:
        entered.set()
        if release.wait(timeout=10):
            original_run(worker_self)

    monkeypatch.setattr(WebSocketStreamExportWorker, "run", blocked_run)
    worker = None
    try:
        stream_view.export_json(tmp_path / "closing.json")
        worker = stream_view._export_worker
        assert worker is not None
        assert entered.wait(timeout=5), "Export worker did not start"

        with caplog.at_level(logging.DEBUG, logger=_LOGGER):
            event = QCloseEvent()
            stream_view.closeEvent(event)
            assert not event.isAccepted()
            records = _messages(caplog, _CLOSE_TIMEOUT_EVENT)
            assert len(records) == 1
            assert records[0].levelno == logging.WARNING
            assert records[0].getMessage() == (
                f"{_CLOSE_TIMEOUT_EVENT} wait_ms=100 action=close_refused"
            )

            release.set()
            assert stream_view.wait_for_export(timeout_ms=5000)
            event = QCloseEvent()
            stream_view.closeEvent(event)
            assert event.isAccepted()
            assert len(_messages(caplog, _CLOSE_TIMEOUT_EVENT)) == 1
            assert len(_messages(caplog, _FINALIZED_EVENT)) == 1
    finally:
        release.set()
        if worker is not None and stream_view._export_worker is worker:
            assert worker.wait(5000)
        qapp.processEvents()
        stream_view.deleteLater()


def test_finalize_deferral_logs_once_and_reports_retry_count(
    qapp: QApplication, caplog: pytest.LogCaptureFixture
) -> None:
    """Repeated finalize retries log one DEBUG deferral, then a finalized summary."""
    stream_view = WebSocketStreamView(stream_model=StreamListModel())
    worker = _PendingJoinWorker()
    stream_view._export_worker = worker  # type: ignore[assignment]
    finished: list[bool] = []
    stream_view.export_finished.connect(lambda: finished.append(True))
    try:
        with caplog.at_level(logging.DEBUG, logger=_LOGGER):
            stream_view._finalize_export_worker(worker)  # type: ignore[arg-type]
            # Several 10 ms retry intervals elapse while the join stays pending.
            _spin_events(80)
            deferred = _messages(caplog, _DEFERRED_EVENT)
            assert len(deferred) == 1, "Deferral must be logged once per worker"
            assert deferred[0].levelno == logging.DEBUG
            assert deferred[0].getMessage() == f"{_DEFERRED_EVENT} retry_ms=10"
            assert finished == []

            worker.joined = True
            assert stream_view.wait_for_export(timeout_ms=5000)
            assert finished == [True]
            assert worker.deleted

            finalized = _messages(caplog, _FINALIZED_EVENT)
            assert len(finalized) == 1
            assert finalized[0].levelno == logging.DEBUG
            deferrals = int(finalized[0].getMessage().rsplit("deferrals=", 1)[1])
            assert deferrals >= 1
            assert len(_messages(caplog, _DEFERRED_EVENT)) == 1
    finally:
        worker.joined = True
        qapp.processEvents()
        stream_view.deleteLater()


def test_stale_worker_finished_signal_logs_debug_and_keeps_ownership(
    qapp: QApplication, caplog: pytest.LogCaptureFixture
) -> None:
    """A finished notification not from the owned worker is ignored with a DEBUG log."""
    stream_view = WebSocketStreamView(stream_model=StreamListModel())
    worker = _PendingJoinWorker()
    stream_view._export_worker = worker  # type: ignore[assignment]
    try:
        with caplog.at_level(logging.DEBUG, logger=_LOGGER):
            # Direct call: sender() is None, i.e. not the owned worker.
            stream_view._on_export_worker_finished()
        records = _messages(caplog, _IGNORED_EVENT)
        assert len(records) == 1
        assert records[0].levelno == logging.DEBUG
        assert records[0].getMessage() == f"{_IGNORED_EVENT} reason=stale_worker"
        assert stream_view._export_worker is worker
        assert not worker.deleted
    finally:
        stream_view._export_worker = None
        qapp.processEvents()
        stream_view.deleteLater()
