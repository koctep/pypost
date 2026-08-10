"""Responsiveness tests for collection import parse (PYPOST-1005).

While import preparation (parse) runs after the user picks a file, the Qt
event loop must still process events and a busy/progress cue must be visible.
Parse runs on ``CollectionImportParseWorker`` (``QThread``); these asserts
guard against regressing to a GUI-thread-blocking parse.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QPushButton

from pypost.ui.presenters.collections_presenter import CollectionsPresenter
from pypost.ui.widget_ids import COLLECTION_IMPORT_BUTTON
from tests.helpers.collections_tree import (
    FakeMetrics,
    FakeRequestManager,
    FakeStateManager,
    make_collection,
    make_request,
)
from tests.helpers.process_until import process_until

pytestmark = pytest.mark.timeout(120)

_MODULE = "pypost.ui.presenters.collection_import_actions"
_PICKER = f"{_MODULE}.prompt_import_collection_file"
_RESULT = f"{_MODULE}.show_collection_import_result"
_PATH = Path("/tmp/pypost-import-responsiveness.json")
_PARSE_HOLD_S = 0.4


def _make_presenter(collections=None, read_import_file=None):
    manager = FakeRequestManager(list(collections or []))
    presenter = CollectionsPresenter(
        manager,
        FakeStateManager(),
        FakeMetrics(),
        {},
        read_import_file=read_import_file,
    )
    presenter.refresh_tree()
    return presenter, manager


def _busy_cue_active(presenter: CollectionsPresenter) -> bool:
    """True when import shows a preparing/busy cue (button and/or is_busy)."""
    if presenter._import_actions.is_busy():
        return True
    button = presenter.panel.findChild(QPushButton, COLLECTION_IMPORT_BUTTON)
    return button is not None and not button.isEnabled()


@patch(_RESULT)
@patch(_PICKER, return_value=_PATH)
def test_event_loop_stays_responsive_during_collection_import_parse(
    _mock_picker, mock_result, qapp
):
    """Parse must not monopolize the GUI thread; busy cue must appear."""
    incoming = make_collection("new-id", "Imported", [make_request("r1", "Ping")])
    parse_started = threading.Event()
    parse_finished = threading.Event()
    timer_during_parse: list[bool] = []
    busy_during_parse: list[bool] = []

    def slow_read_import_file(path: Path):
        assert path == _PATH
        parse_started.set()
        try:
            time.sleep(_PARSE_HOLD_S)
            return [incoming], []
        finally:
            parse_finished.set()

    def on_responsiveness_timeout() -> None:
        if parse_started.is_set() and not parse_finished.is_set():
            timer_during_parse.append(True)

    def on_busy_sample() -> None:
        if parse_started.is_set() and not parse_finished.is_set():
            if _busy_cue_active(presenter):
                busy_during_parse.append(True)

    presenter, manager = _make_presenter([], slow_read_import_file)
    try:
        responsiveness_timer = QTimer()
        responsiveness_timer.setInterval(0)
        responsiveness_timer.setSingleShot(True)
        responsiveness_timer.timeout.connect(on_responsiveness_timeout)

        busy_sample_timer = QTimer()
        busy_sample_timer.setInterval(20)
        busy_sample_timer.timeout.connect(on_busy_sample)

        responsiveness_timer.start()
        busy_sample_timer.start()
        presenter.import_collections()

        process_until(
            lambda: mock_result.call_count >= 1,
            timeout_ms=10_000,
        )
        busy_sample_timer.stop()

        assert timer_during_parse, (
            "event loop should process a QTimer during import parse; "
            "synchronous parse on the GUI thread blocks the timer until after "
            "parse finishes"
        )
        assert busy_during_parse, (
            "busy/progress cue should be visible during import parse "
            "(Import control disabled and/or is_busy)"
        )
        assert [col.name for col in manager.get_collections()] == ["Imported"]
        _args, kwargs = mock_result.call_args
        assert kwargs["success"] is True
    finally:
        presenter.panel.close()
