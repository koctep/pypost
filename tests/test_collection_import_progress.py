"""Tests for determinate progress during collection import validation (PYPOST-1061).

Step 3 failing repro verifying:
1. Pure core callback invocation in load_collection_import_candidates(..., on_progress=...).
2. Off-thread parse progress signal emission on CollectionImportParseWorker.
3. Determinate status message updates in CollectionImportActions / presenter.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from pypost.core.collection_import import load_collection_import_candidates
from pypost.core.qt.collection_import_parse_worker import CollectionImportParseWorker
from pypost.models.models import Collection
from pypost.ui.presenters.collections_presenter import CollectionsPresenter
from tests.helpers.collections_tree import (
    FakeMetrics,
    FakeRequestManager,
    FakeStateManager,
)
from tests.helpers.process_until import process_until

pytestmark = pytest.mark.timeout(60)


def test_load_collection_import_candidates_invokes_on_progress_callback(tmp_path):
    """load_collection_import_candidates invokes on_progress(done, total) for each record."""
    path = tmp_path / "collections.json"
    path.write_text(
        json.dumps([
            {"id": "col-1", "name": "API 1", "requests": []},
            {"id": "col-2", "name": "API 2", "requests": []},
            {"id": "col-3", "name": "API 3", "requests": []},
        ]),
        encoding="utf-8",
    )
    progress_calls: list[tuple[int, int]] = []

    collections, parse_errors = load_collection_import_candidates(
        path, on_progress=lambda done, total: progress_calls.append((done, total))
    )

    assert parse_errors == []
    assert len(collections) == 3
    assert progress_calls == [(1, 3), (2, 3), (3, 3)]


def test_collection_import_parse_worker_emits_progress_signal(qapp):
    """CollectionImportParseWorker emits parse_progress(done, total) during off-thread parse."""
    path = Path("/dummy/import.json")

    def dummy_reader(p, on_progress=None):
        if on_progress is not None:
            on_progress(1, 2)
            on_progress(2, 2)
        return [Collection(id="c1", name="C1"), Collection(id="c2", name="C2")], []

    worker = CollectionImportParseWorker(path, dummy_reader)
    emitted_progress: list[tuple[int, int]] = []
    worker.parse_progress.connect(
        lambda done, total: emitted_progress.append((done, total))
    )

    worker.start()
    process_until(lambda: not worker.isRunning(), timeout_ms=5000)

    assert emitted_progress == [(1, 2), (2, 2)]


@patch("pypost.ui.presenters.collection_import_actions.show_collection_import_result")
@patch("pypost.ui.presenters.collection_import_actions.prompt_import_collection_file")
def test_presenter_updates_status_with_determinate_progress(
    mock_picker, mock_result, qapp
):
    """CollectionImportActions updates status with determinate progress string on progress."""
    path = Path("/dummy/import.json")
    mock_picker.return_value = path

    def dummy_reader(p, on_progress=None):
        if on_progress is not None:
            on_progress(1, 2)
            on_progress(2, 2)
        return [Collection(id="c1", name="C1"), Collection(id="c2", name="C2")], []

    status_messages: list[str] = []
    presenter = CollectionsPresenter(
        FakeRequestManager([]),
        FakeStateManager(),
        FakeMetrics(),
        {},
        read_import_file=dummy_reader,
    )
    presenter._show_import_status = lambda msg: status_messages.append(msg)
    presenter._import_actions._show_status = lambda msg: status_messages.append(msg)

    try:
        presenter.import_collections()
        process_until(lambda: mock_result.call_count >= 1, timeout_ms=5000)

        assert "Validating collections (1/2)…" in status_messages
        assert "Validating collections (2/2)…" in status_messages
    finally:
        presenter.panel.close()


def test_load_collection_import_candidates_mixed_valid_invalid(tmp_path):
    """Progress callback is called for every record even when some have errors."""
    path = tmp_path / "mixed.json"
    path.write_text(
        json.dumps([
            {"id": "col-1", "name": "Valid 1", "requests": []},
            {"id": "col-2"},  # Missing name shape error
            {"id": "col-3", "name": "Valid 2", "requests": []},
            {"id": "col-4", "name": "Bad Requests", "requests": "not-a-list"},
        ]),
        encoding="utf-8",
    )
    progress_calls: list[tuple[int, int]] = []
    collections, parse_errors = load_collection_import_candidates(
        path, on_progress=lambda done, total: progress_calls.append((done, total))
    )

    assert len(collections) == 2
    assert len(parse_errors) == 2
    assert progress_calls == [(1, 4), (2, 4), (3, 4), (4, 4)]


def test_collection_import_parse_worker_supports_legacy_single_arg_reader(qapp):
    """CollectionImportParseWorker runs without error when reader does not accept on_progress."""
    path = Path("/dummy/import.json")

    def legacy_reader(p):
        return [Collection(id="c1", name="C1")], []

    worker = CollectionImportParseWorker(path, legacy_reader)
    assert CollectionImportParseWorker.progress is CollectionImportParseWorker.parse_progress

    results = []
    worker.parse_completed.connect(lambda cols, errs: results.append((cols, errs)))
    worker.start()
    process_until(lambda: not worker.isRunning(), timeout_ms=5000)

    assert len(results) == 1
    assert len(results[0][0]) == 1
    assert results[0][0][0].name == "C1"
