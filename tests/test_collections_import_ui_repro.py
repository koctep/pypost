"""Automated failing repro tests for collections import UI worker lifecycle and
wait_idle (PYPOST-1182).

Demonstrates:
1. CollectionsPresenter and CollectionImportActions lack wait_import_idle() / wait_idle()
   lifecycle synchronization methods, preventing tests and callers from deterministically
   draining background workers before widget teardown.
2. Background QThread parse worker lifecycle drain is required so that is_busy() cleanly
   returns False and worker threads are joined prior to panel destruction.
"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from pypost.ui.presenters.collections_presenter import CollectionsPresenter
from tests.helpers.collections_tree import (
    FakeMetrics,
    FakeRequestManager,
    FakeStateManager,
    make_collection,
    make_request,
)

pytestmark = pytest.mark.timeout(30)

_MODULE = "pypost.ui.presenters.collection_import_actions"
_PICKER = f"{_MODULE}.prompt_import_collection_file"
_RESULT = f"{_MODULE}.show_collection_import_result"
_PATH = Path("/tmp/repro_import.json")


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


def _delayed_reader(collections, delay_seconds: float = 0.05):
    def read(path):
        time.sleep(delay_seconds)
        return list(collections), []

    return read


def test_collection_import_actions_and_presenter_expose_wait_idle_api(
    qapp: QApplication,
) -> None:
    """CollectionsPresenter and CollectionImportActions must expose wait_idle."""
    presenter, _manager = _make_presenter()
    try:
        assert hasattr(presenter._import_actions, "wait_idle"), (
            "CollectionImportActions missing wait_idle(timeout_ms) method"
        )
        assert callable(getattr(presenter._import_actions, "wait_idle"))

        assert hasattr(presenter, "wait_import_idle"), (
            "CollectionsPresenter is missing wait_import_idle(timeout_ms) delegation method"
        )
        assert callable(getattr(presenter, "wait_import_idle"))
    finally:
        presenter.panel.close()


@patch(_RESULT)
@patch(_PICKER, return_value=_PATH)
def test_wait_import_idle_drains_in_flight_worker_deterministically(
    _mock_picker,
    _mock_result,
    qapp: QApplication,
) -> None:
    """wait_import_idle() must pump event loop and join background worker until idle."""
    incoming = make_collection("repro-col", "Repro Collection", [make_request("r1", "Req1")])
    presenter, manager = _make_presenter([], _delayed_reader([incoming], delay_seconds=0.05))
    try:
        presenter.import_collections()

        # On unpatched code, wait_import_idle does not exist, raising AttributeError.
        # Once implemented in Step 4, it will return True and ensure is_busy() is False.
        idle_result = presenter.wait_import_idle(timeout_ms=5000)
        assert idle_result is True, "wait_import_idle timed out before worker finished"
        assert not presenter._import_actions.is_busy(), (
            "Presenter remained busy after wait_import_idle returned"
        )
        assert len(manager.get_collections()) == 1
    finally:
        presenter.panel.close()


@patch(_RESULT)
@patch(_PICKER, return_value=_PATH)
def test_wait_import_idle_observability_logging(
    _mock_picker,
    _mock_result,
    caplog: pytest.LogCaptureFixture,
    qapp: QApplication,
) -> None:
    """wait_import_idle() emits structured info logs on wait start and completion."""
    incoming = make_collection("repro-col", "Repro Collection", [make_request("r1", "Req1")])
    presenter, _manager = _make_presenter([], _delayed_reader([incoming], delay_seconds=0.05))
    try:
        with caplog.at_level("INFO"):
            presenter.import_collections()
            assert presenter.wait_import_idle(timeout_ms=5000) is True

        assert "collection_import_wait_idle_started" in caplog.text
        assert "collection_import_wait_idle_completed elapsed_ms=" in caplog.text
    finally:
        presenter.panel.close()


@patch(_RESULT)
@patch(_PICKER, return_value=_PATH)
def test_wait_import_idle_timeout_observability_logging(
    _mock_picker,
    _mock_result,
    caplog: pytest.LogCaptureFixture,
    qapp: QApplication,
) -> None:
    """wait_import_idle() emits structured warning log when timeout is reached."""
    incoming = make_collection("repro-col", "Repro Collection", [make_request("r1", "Req1")])
    presenter, _manager = _make_presenter([], _delayed_reader([incoming], delay_seconds=0.1))
    try:
        with caplog.at_level("WARNING"):
            presenter.import_collections()
            # Fast timeout triggers timeout branch
            result = presenter.wait_import_idle(timeout_ms=1)
            assert result is False
            assert "collection_import_wait_idle_timeout elapsed_ms=" in caplog.text

        # Drain worker before teardown
        presenter.wait_import_idle(timeout_ms=5000)
    finally:
        presenter.panel.close()


def test_wait_import_idle_when_not_busy_returns_immediately_without_log(
    caplog: pytest.LogCaptureFixture,
    qapp: QApplication,
) -> None:
    """wait_import_idle() returns True immediately when not busy without wait logs."""
    presenter, _manager = _make_presenter()
    try:
        with caplog.at_level("INFO"):
            assert presenter.wait_import_idle(timeout_ms=5000) is True

        assert "collection_import_wait_idle_started" not in caplog.text
    finally:
        presenter.panel.close()

