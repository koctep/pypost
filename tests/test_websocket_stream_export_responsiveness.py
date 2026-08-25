"""Responsiveness tests for WebSocket stream transcript export (PYPOST-1144).

Export formatting and disk writes must run off the GUI thread so the Qt
event loop stays responsive during large transcript exports.
"""

from __future__ import annotations

import inspect
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QPushButton

from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
from pypost.ui.widget_ids import WS_STREAM_EXPORT_BUTTON
from pypost.ui.widgets.websocket import stream_view as stream_view_module
from pypost.ui.widgets.websocket.stream_view import WebSocketStreamView
from tests.helpers.process_until import process_until
from tests.test_websocket_stream_view_repro import (
    _create_stream_entry,
    _make_sample_connection,
)
from pypost.ui.widgets.websocket.stream_model import StreamListModel

pytestmark = pytest.mark.timeout(120)

_EXPORT_HOLD_S = 0.4
_JSON_EXPORT = "pypost.core.qt.websocket_stream_export_worker.export_stream_to_json_file"


def _make_stream_view() -> tuple[WebSocketStreamView, WebSocketPresenter]:
    conn = _make_sample_connection()
    stream_model = StreamListModel()
    presenter = WebSocketPresenter(connection=conn, stream_model=stream_model)
    stream_view = WebSocketStreamView(stream_model=stream_model, presenter=presenter)
    entry = _create_stream_entry(seq=1, payload="export responsiveness test")
    stream_model.append_batch([entry])
    return stream_view, presenter


def test_stream_view_export_uses_background_worker() -> None:
    """WebSocketStreamView export path must delegate to WebSocketStreamExportWorker."""
    source = inspect.getsource(stream_view_module.WebSocketStreamView._start_export)
    assert "WebSocketStreamExportWorker" in source
    assert ".start()" in source


@patch(_JSON_EXPORT)
def test_event_loop_stays_responsive_during_stream_json_export(
    mock_export_json,
    qapp,
    tmp_path: Path,
) -> None:
    """JSON export must not monopolize the GUI thread during slow disk writes."""
    export_started = threading.Event()
    export_finished = threading.Event()
    export_threads: list[int] = []
    main_thread_id = threading.get_ident()
    timer_during_export: list[bool] = []

    def slow_export_json(path: Path, stream, **kwargs) -> None:
        export_threads.append(threading.get_ident())
        export_started.set()
        try:
            time.sleep(_EXPORT_HOLD_S)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{"entries":[]}', encoding="utf-8")
        finally:
            export_finished.set()

    mock_export_json.side_effect = slow_export_json

    stream_view, presenter = _make_stream_view()
    out_file = tmp_path / "slow_export.json"
    try:

        def on_responsiveness_timeout() -> None:
            if export_started.is_set() and not export_finished.is_set():
                timer_during_export.append(True)

        responsiveness_timer = QTimer()
        responsiveness_timer.setInterval(20)
        responsiveness_timer.timeout.connect(on_responsiveness_timeout)
        responsiveness_timer.start()

        stream_view.export_json(out_file)
        process_until(lambda: out_file.exists(), timeout_ms=10_000)
        responsiveness_timer.stop()

        assert export_threads, "export helper should have been invoked"
        assert export_threads[0] != main_thread_id, (
            "export serialization must run off the GUI thread"
        )
        assert timer_during_export, (
            "event loop should process a QTimer during export; "
            "synchronous export on the GUI thread blocks the timer until after "
            "export finishes"
        )
    finally:
        stream_view.deleteLater()
        presenter.deleteLater()


@patch(_JSON_EXPORT)
def test_export_button_disabled_while_export_busy(
    mock_export_json,
    qapp,
    tmp_path: Path,
) -> None:
    """Export control should reflect busy state while worker is in flight."""
    export_started = threading.Event()
    export_finished = threading.Event()
    disabled_during_export: list[bool] = []

    def slow_export_json(path: Path, stream, **kwargs) -> None:
        export_started.set()
        try:
            time.sleep(_EXPORT_HOLD_S)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{"entries":[]}', encoding="utf-8")
        finally:
            export_finished.set()

    mock_export_json.side_effect = slow_export_json

    stream_view, presenter = _make_stream_view()
    export_btn = stream_view.findChild(QPushButton, WS_STREAM_EXPORT_BUTTON)
    assert export_btn is not None
    out_file = tmp_path / "busy_export.json"
    try:

        def sample_busy_state() -> None:
            if export_started.is_set() and not export_finished.is_set():
                if not export_btn.isEnabled() or stream_view.is_export_busy():
                    disabled_during_export.append(True)

        busy_timer = QTimer()
        busy_timer.setInterval(20)
        busy_timer.timeout.connect(sample_busy_state)
        busy_timer.start()

        stream_view.export_json(out_file)
        process_until(lambda: out_file.exists(), timeout_ms=10_000)
        busy_timer.stop()

        assert disabled_during_export, (
            "export button should be disabled or is_export_busy() true during export"
        )
    finally:
        stream_view.deleteLater()
        presenter.deleteLater()
