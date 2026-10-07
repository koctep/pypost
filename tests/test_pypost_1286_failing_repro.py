"""Failing repro tests for PYPOST-1286.

Asserts the contract and behavior specified in:
- ai-tasks/PYPOST-1286/10-requirements.md
- ai-tasks/PYPOST-1286/20-architecture.md

Covers:
1. Public export completion signals and wait_for_export synchronization on
   WebSocketStreamView.
2. Uncoordinated sequential export actions dropping requests due to unexposed
   busy state, and coordinated exports with wait_for_export completing successfully.
3. Immutability protection for _DEFAULT_CATALOG in function_registry and cache
   management seam clear_cache() on TemplateService.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from threading import Event
from types import MappingProxyType

import pytest
import shiboken6
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication

from pypost.core.function_registry import _DEFAULT_CATALOG
from pypost.core.qt.websocket_stream_export_worker import WebSocketStreamExportWorker
from pypost.core.template_service import TemplateService
from pypost.core.websocket_stream import StreamEntry
from pypost.models.websocket import WebSocketConnection
from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
from pypost.ui.widgets.websocket.stream_model import StreamListModel
from pypost.ui.widgets.websocket.stream_view import WebSocketStreamView

pytestmark = pytest.mark.timeout(30)


@pytest.mark.parametrize("contract", ["busy", "wait"])
def test_export_retains_ownership_until_queued_completion(
    tmp_path: Path, qapp: QApplication, contract: str
) -> None:
    """Native thread exit alone must not expose an idle, unfinalized view."""
    stream_view = WebSocketStreamView(stream_model=StreamListModel())
    finished = []
    stream_view.export_finished.connect(lambda: finished.append(True))
    worker = None
    try:
        stream_view.export_json(tmp_path / "queued.json")
        worker = stream_view._export_worker
        assert worker is not None
        # Blocking QThread.wait does not dispatch queued slots on this GUI thread.
        assert worker.wait(5000), "Export worker did not terminate"
        assert not worker.isRunning()
        assert stream_view._export_worker is worker
        assert finished == []

        if contract == "busy":
            assert stream_view.is_export_busy(), (
                "Queued worker completion must retain busy ownership"
            )
            stream_view.export_text(tmp_path / "rejected.txt")
            assert stream_view._export_worker is worker
        else:
            assert stream_view.wait_for_export(timeout_ms=1000)
            assert finished == [True], "Successful wait must dispatch completion"
            assert stream_view._export_worker is None
            assert stream_view._export_btn.isEnabled()
    finally:
        if worker is not None and stream_view._export_worker is worker:
            assert worker.wait(5000)
        qapp.processEvents()
        stream_view.deleteLater()


def test_close_refuses_disposal_while_export_worker_remains_active(
    tmp_path: Path, qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A bounded join timeout must not permit closing an active export owner."""
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
        event = QCloseEvent()
        stream_view.closeEvent(event)
        assert worker.isRunning(), "Worker must remain held through close attempt"
        assert not event.isAccepted(), "Close must refuse disposal after join timeout"
        assert stream_view._export_worker is worker
        assert stream_view.is_export_busy()
        release.set()
        assert stream_view.wait_for_export(timeout_ms=5000)
        event = QCloseEvent()
        stream_view.closeEvent(event)
        assert event.isAccepted(), "Closing should succeed after export cleanup"
    finally:
        release.set()
        if worker is not None and stream_view._export_worker is worker:
            assert worker.wait(5000)
        qapp.processEvents()
        stream_view.deleteLater()


@pytest.mark.parametrize("timeout_ms", [-1, 0, 10])
def test_export_wait_timeout_preserves_active_worker(
    tmp_path: Path,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    timeout_ms: int,
) -> None:
    """Expired and nonpositive wait budgets retain ownership for a later successful wait."""
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
        assert stream_view.wait_for_export(timeout_ms=timeout_ms)
        stream_view.export_json(tmp_path / "timeout.json")
        worker = stream_view._export_worker
        assert worker is not None
        assert entered.wait(timeout=5)
        assert not stream_view.wait_for_export(timeout_ms=timeout_ms)
        assert stream_view._export_worker is worker
        assert stream_view.is_export_busy()
        assert not stream_view._export_btn.isEnabled()
        release.set()
        assert stream_view.wait_for_export(timeout_ms=5000)
        assert stream_view._export_worker is None
        assert stream_view._export_btn.isEnabled()
    finally:
        release.set()
        if worker is not None and stream_view._export_worker is worker:
            assert worker.wait(5000)
        qapp.processEvents()
        stream_view.deleteLater()


class _PendingJoinWorker:
    """Worker stub whose nonblocking join fails until released."""

    def __init__(self) -> None:
        self.joined = False
        self.wait_calls = 0

    def wait(self, _timeout_ms: int) -> bool:
        self.wait_calls += 1
        return self.joined


def test_pending_finalize_retry_is_dropped_with_destroyed_view(
    qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A pending finalize retry must not touch a view whose C++ object was destroyed."""
    hook_errors: list[BaseException] = []
    monkeypatch.setattr(
        sys, "excepthook", lambda _type, value, _tb: hook_errors.append(value)
    )
    stream_view = WebSocketStreamView(stream_model=StreamListModel())
    worker = _PendingJoinWorker()
    stream_view._export_worker = worker  # type: ignore[assignment]

    stream_view._finalize_export_worker(worker)  # type: ignore[arg-type]
    assert worker.wait_calls == 1, "Unjoined worker must schedule a retry"
    worker.joined = True
    shiboken6.delete(stream_view)

    # Bounded window well beyond the 10 ms retry interval; no sleeps.
    loop = QEventLoop()
    QTimer.singleShot(200, loop.quit)
    loop.exec()
    qapp.processEvents()

    assert worker.wait_calls == 1, "Retry must be dropped with its context widget"
    assert hook_errors == []


def test_websocket_stream_view_public_signals_and_wait_helper(qapp: QApplication) -> None:
    """Verify WebSocketStreamView exposes public completion signals and wait_for_export."""
    assert hasattr(WebSocketStreamView, "export_completed"), (
        "WebSocketStreamView must expose public 'export_completed' signal"
    )
    assert hasattr(WebSocketStreamView, "export_failed"), (
        "WebSocketStreamView must expose public 'export_failed' signal"
    )
    assert hasattr(WebSocketStreamView, "export_finished"), (
        "WebSocketStreamView must expose public 'export_finished' signal"
    )
    assert hasattr(WebSocketStreamView, "wait_for_export"), (
        "WebSocketStreamView must expose public 'wait_for_export' helper method"
    )
    assert callable(getattr(WebSocketStreamView, "wait_for_export", None)), (
        "WebSocketStreamView.wait_for_export must be callable"
    )


def test_uncoordinated_export_drops_request_and_coordinated_export_succeeds(
    tmp_path: Path, qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Demonstrate uncoordinated export drop and assert wait_for_export coordination."""
    conn = WebSocketConnection(
        id="ws_repro_conn",
        name="Repro Feed",
        url="wss://stream.example.com/v1/repro",
    )
    stream_model = StreamListModel()
    presenter = WebSocketPresenter(connection=conn, stream_model=stream_model)
    stream_view = WebSocketStreamView(stream_model=stream_model, presenter=presenter)
    written = Event()
    release = Event()

    try:
        e1 = StreamEntry(
            seq=1,
            ts_utc="2026-10-06T10:00:00.000Z",
            kind="message",
            direction="in",
            payload_format="json",
            payload='{"seq": 1, "test": "export_race"}',
            byte_size=32,
            truncated=False,
            detail="",
        )
        stream_model.append_batch([e1])
        qapp.processEvents()

        # Hold native thread exit until the assertions explicitly release it.
        orig_worker_run = WebSocketStreamExportWorker.run

        def delayed_worker_run(worker_self: WebSocketStreamExportWorker) -> None:
            orig_worker_run(worker_self)
            written.set()
            assert release.wait(timeout=10), "Test did not release export worker"

        monkeypatch.setattr(WebSocketStreamExportWorker, "run", delayed_worker_run)

        json_file_uncoord = tmp_path / "export_uncoord.json"
        text_file_uncoord = tmp_path / "export_uncoord.txt"

        # 1. Uncoordinated export: poll file existence only without thread synchronization
        stream_view.export_json(json_file_uncoord)
        assert written.wait(timeout=5), "Export did not finish writing"
        assert json_file_uncoord.exists()

        # File is written, but worker thread exit is still in flight -> view is busy
        assert stream_view.is_export_busy(), (
            "Export view must be busy while background worker thread terminates"
        )

        # Second export requested while busy is silently dropped without queueing/sync
        stream_view.export_text(text_file_uncoord)
        qapp.processEvents()
        assert not text_file_uncoord.exists(), (
            "Uncoordinated sequential export must drop request when view is busy"
        )

        # 2. Coordinated export: wait_for_export waits for worker and resets busy state
        assert hasattr(stream_view, "wait_for_export"), (
            "WebSocketStreamView missing wait_for_export helper method"
        )
        release.set()
        assert stream_view.wait_for_export(timeout_ms=5_000) is True, (
            "wait_for_export must return True when worker completes and cleans up"
        )
        assert not stream_view.is_export_busy(), (
            "is_export_busy must be False after wait_for_export completes"
        )

        # Subsequent exports coordinated via wait_for_export succeed for both formats
        json_file_coord = tmp_path / "export_coord.json"
        text_file_coord = tmp_path / "export_coord.txt"

        stream_view.export_json(json_file_coord)
        assert stream_view.wait_for_export(timeout_ms=5_000) is True
        assert json_file_coord.exists()

        stream_view.export_text(text_file_coord)
        assert stream_view.wait_for_export(timeout_ms=5_000) is True
        assert text_file_coord.exists()

        parsed_json = json.loads(json_file_coord.read_text(encoding="utf-8"))
        assert len(parsed_json["entries"]) == 1
        assert "export_race" in text_file_coord.read_text(encoding="utf-8")
    finally:
        release.set()
        worker = getattr(stream_view, "_export_worker", None)
        if worker is not None:
            assert worker.wait(5000)
        qapp.processEvents()
        stream_view.deleteLater()
        presenter.deleteLater()


def test_function_registry_default_catalog_immutability() -> None:
    """Verify _DEFAULT_CATALOG is protected against in-process mutations."""
    assert isinstance(_DEFAULT_CATALOG, MappingProxyType), (
        f"_DEFAULT_CATALOG must be MappingProxyType, got {type(_DEFAULT_CATALOG).__name__}"
    )
    with pytest.raises(TypeError):
        _DEFAULT_CATALOG["mutation_probe"] = lambda: None  # type: ignore[index]


def test_template_service_clear_cache_and_strict_conversion_isolation() -> None:
    """Verify TemplateService provides clear_cache() and isolates strict fallbacks."""
    assert hasattr(TemplateService, "clear_cache"), (
        "TemplateService must provide public 'clear_cache' method"
    )
    svc = TemplateService()
    assert callable(getattr(svc, "clear_cache", None)), (
        "TemplateService.clear_cache must be callable"
    )
    svc.clear_cache()

    content = "{{to_int(issue_id)}}/{{not_allowed(value)}}"
    result = svc.render_string_strict_conversion(
        content, {"issue_id": "42", "value": "ignored"}
    )
    assert result == content, (
        f"Strict conversion with valid to_int must preserve literal fallback, got {result!r}"
    )
