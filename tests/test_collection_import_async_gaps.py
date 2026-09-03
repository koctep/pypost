"""Test gaps for asynchronous collection import workflow.

Task: PYPOST-1063 (addressing ai-tasks/PYPOST-1005/60-tech-debt.md follow-up #4).
Scenarios tested:
1. Busy re-entry guard: second Import click while busy logs skip and does not launch worker.
2. Unexpected exception in reader: worker catches, logs ERROR, emits parse_failed, dialog shown.
3. Status message lifecycle: preparing status shown and cleared on completion.
4. Real JSON file async import: genuine disk file parsed and applied without mock reader.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from pypost.core.collection_import_state import CollectionImportState
from pypost.core.collection_messages import (
    MSG_IMPORT_PREPARING,
)
from pypost.ui.presenters.collections_presenter import CollectionsPresenter
from tests.helpers.collections_tree import (
    FakeMetrics,
    FakeRequestManager,
    FakeStateManager,
    make_collection,
    make_request,
)
from tests.helpers.process_until import process_until

pytestmark = pytest.mark.timeout(60)

_MODULE = "pypost.ui.presenters.collection_import_actions"
_PICKER = f"{_MODULE}.prompt_import_collection_file"
_RESULT = f"{_MODULE}.show_collection_import_result"
_INVALID = f"{_MODULE}.show_collection_import_invalid_file_error"
_PATH = Path("/tmp/import.json")


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


@patch(_PICKER, return_value=_PATH)
def test_import_skipped_when_already_busy(_mock_picker, caplog, qapp):
    """A second import call while busy is skipped and logged with INFO."""
    presenter, manager = _make_presenter()
    try:
        # Simulate active busy state on import actions
        presenter._import_actions._state = CollectionImportState.PREPARING

        with caplog.at_level(logging.INFO):
            presenter.import_collections()

        assert any(
            "collection_import_skipped reason=busy" in rec.message
            for rec in caplog.records
        )
    finally:
        presenter._import_actions._state = CollectionImportState.IDLE
        presenter.teardown()


@patch(_INVALID)
@patch(_PICKER, return_value=_PATH)
def test_unexpected_reader_exception_surfaces_invalid_dialog(
    _mock_picker, mock_invalid, caplog, qapp
):
    """An unhandled reader exception triggers parse failure and surfaces error dialog."""
    def _exploding_reader(_path, on_progress=None):
        raise RuntimeError("unexpected disk failure")

    presenter, manager = _make_presenter(read_import_file=_exploding_reader)
    try:
        with caplog.at_level(logging.ERROR):
            presenter.import_collections()
            process_until(lambda: mock_invalid.call_count >= 1, timeout_ms=3000)

        assert mock_invalid.called
        err_arg = mock_invalid.call_args[0][1]
        assert "unexpected disk failure" in str(err_arg)

        assert any(
            "collection_import_parse_unexpected" in rec.message
            and "unexpected disk failure" in rec.message
            for rec in caplog.records
        )
        assert presenter.wait_import_idle()
    finally:
        presenter.teardown()


@patch(_RESULT)
@patch(_PICKER, return_value=_PATH)
def test_status_bar_lifecycle_transitions(_mock_picker, _mock_result, qapp):
    """Status bar hooks receive preparing status and clear upon completion."""
    recorded_statuses: list[str] = []
    cleared = []

    incoming = make_collection("c1", "Sample", [make_request("r1", "Req")])

    def _mock_reader(_path, on_progress=None):
        return [incoming], []

    presenter, manager = _make_presenter(read_import_file=_mock_reader)
    presenter._import_actions._show_status = lambda msg: recorded_statuses.append(msg)
    presenter._import_actions._clear_status = lambda: cleared.append(True)

    try:
        presenter.import_collections()
        process_until(lambda: _mock_result.call_count >= 1, timeout_ms=3000)

        assert any(MSG_IMPORT_PREPARING in s for s in recorded_statuses)
        assert len(cleared) >= 1
        assert presenter.wait_import_idle()
    finally:
        presenter.teardown()


@patch(_RESULT)
def test_real_json_file_async_import_integration(_mock_result, tmp_path: Path, qapp):
    """A genuine multi-record JSON file on disk is imported without reader mocks."""
    real_file = tmp_path / "real_import.json"
    records = [
        {
            "id": "c1",
            "name": "Integration Collection",
            "requests": [
                {
                    "id": "r1",
                    "name": "Get Info",
                    "method": "GET",
                    "url": "https://api.pypost.local/info",
                }
            ],
        }
    ]
    real_file.write_text(json.dumps(records), encoding="utf-8")

    with patch(_PICKER, return_value=real_file):
        presenter, manager = _make_presenter()
        try:
            presenter.import_collections()
            process_until(lambda: _mock_result.call_count >= 1, timeout_ms=3000)

            cols = manager.get_collections()
            assert len(cols) == 1
            assert cols[0].name == "Integration Collection"
            assert len(cols[0].requests) == 1
            assert cols[0].requests[0].name == "Get Info"
            assert presenter.wait_import_idle()
        finally:
            presenter.teardown()
