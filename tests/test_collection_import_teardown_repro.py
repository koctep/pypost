"""Reproduction tests for collection import teardown and worker lifecycle gaps.

Task: PYPOST-1148
Addresses:
1. Missing teardown() contract on CollectionsPresenter and CollectionImportActions.
2. Premature is_busy() fall-through while _worker instance is still present.
3. Clean worker thread join and reap guarantees upon reader errors.
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pypost.ui.presenters.collections_presenter import CollectionsPresenter
from tests.helpers.collections_tree import (
    FakeMetrics,
    FakeRequestManager,
    FakeStateManager,
)
from tests.helpers.process_until import process_until

pytestmark = pytest.mark.timeout(30)

_MODULE = "pypost.ui.presenters.collection_import_actions"
_PICKER = f"{_MODULE}.prompt_import_collection_file"
_INVALID = f"{_MODULE}.show_collection_import_invalid_file_error"
_PATH = Path("/tmp/import.json")


def _make_presenter(read_import_file=None):
    manager = FakeRequestManager([])
    presenter = CollectionsPresenter(
        manager,
        FakeStateManager(),
        FakeMetrics(),
        {},
        read_import_file=read_import_file,
    )
    presenter.refresh_tree()
    return presenter, manager


def test_presenter_and_actions_expose_teardown_contract(qapp):
    """CollectionsPresenter and CollectionImportActions must expose callable teardown()."""
    presenter, _ = _make_presenter()
    try:
        assert hasattr(presenter, "teardown") and callable(presenter.teardown), (
            "CollectionsPresenter must expose a callable teardown() method"
        )
        assert hasattr(presenter._import_actions, "teardown") and callable(
            presenter._import_actions.teardown
        ), "CollectionImportActions must expose a callable teardown() method"
    finally:
        presenter.teardown()


def test_is_busy_retains_true_while_worker_instance_exists(qapp):
    """is_busy() must remain True as long as _worker is not None, even if isRunning() is False."""
    presenter, _ = _make_presenter()
    try:
        actions = presenter._import_actions
        mock_worker = MagicMock()
        mock_worker.isRunning.return_value = False
        actions._worker = mock_worker
        actions._preparing = False

        # In unpatched code: is_busy() returns False when isRunning() is False,
        # despite _worker being non-None.
        # The new architecture contract requires is_busy() to be True while _worker is not None.
        assert actions.is_busy() is True, (
            "CollectionImportActions.is_busy() must remain True while _worker is not None"
        )
    finally:
        actions._worker = None
        presenter.teardown()


@patch(_INVALID)
@patch(_PICKER, return_value=_PATH)
def test_unexpected_reader_exception_requires_teardown_and_reaps_worker(
    _mock_picker, mock_invalid, caplog, qapp
):
    """Reader error triggers parse failure; presenter.teardown() joins and reaps worker."""
    def _exploding_reader(_path, on_progress=None):
        raise RuntimeError("unexpected disk failure")

    presenter, manager = _make_presenter(read_import_file=_exploding_reader)
    try:
        with caplog.at_level(logging.ERROR, logger=_MODULE):
            presenter.import_collections()
            process_until(lambda: mock_invalid.call_count >= 1, timeout_ms=3000)

        assert mock_invalid.called

        # On unpatched code, presenter has no teardown() method -> AttributeError.
        # On patched code, presenter.teardown() will join worker thread and set _worker to None.
        presenter.teardown()
        assert presenter._import_actions._worker is None, (
            "presenter.teardown() must clear and reap _worker"
        )
    finally:
        presenter.teardown()


def test_teardown_structured_logging(caplog, qapp):
    """Verify structured logging on teardown start, timeout, worker interrupt/reap, and completion."""
    presenter, _ = _make_presenter()
    actions = presenter._import_actions

    # 1. Clean teardown when idle
    with caplog.at_level(logging.DEBUG):
        clean = presenter.teardown(timeout_ms=100)

    assert clean is True
    messages = [r.message for r in caplog.records]
    assert any("collections_presenter_teardown_started timeout_ms=100" in m for m in messages)
    assert any("collection_import_teardown_started timeout_ms=100" in m for m in messages)
    assert any("collection_import_teardown_completed clean=True" in m for m in messages)
    assert any("collections_presenter_teardown_completed clean=True" in m for m in messages)

    # 2. Worker interruption and reaping when busy
    caplog.clear()
    mock_worker = MagicMock()
    mock_worker.isRunning.return_value = True
    mock_worker.wait.return_value = True
    actions._worker = mock_worker
    actions._preparing = False

    with caplog.at_level(logging.DEBUG):
        clean_interrupted = presenter.teardown(timeout_ms=20)

    assert clean_interrupted is False
    messages = [r.message for r in caplog.records]
    assert any("collection_import_wait_idle_timeout" in m for m in messages)
    assert any("collection_import_worker_interrupting" in m for m in messages)
    assert any("collection_import_worker_interrupted" in m for m in messages)
    assert any("collection_import_worker_reaped" in m for m in messages)
    assert any("collection_import_teardown_completed clean=False" in m for m in messages)
    assert any("collections_presenter_teardown_completed clean=False" in m for m in messages)

    # Ensure no raw collection payloads leak in any log records
    for msg in messages:
        assert "requests" not in msg or "request_count" in msg
        assert "password" not in msg.lower()
        assert "token" not in msg.lower()
