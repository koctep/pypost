"""Failing repro test suite for PYPOST-1450 / PYPOST-1424.

Validates that catalog manifest discovery has a dedicated status UI container
and error container completely separated from the collection fetch loading chrome.

Requirements:
1. Dialog possesses dedicated discovery UI elements:
   - discovery_container (QWidget)
   - discovery_label (QLabel)
   - cancel_discovery_btn (QPushButton)
   - discovery_error_container (QWidget)
   - discovery_error_label (QLabel)
   - retry_discovery_btn (QPushButton)
   - dedicated slots: _on_cancel_discovery, _on_retry_discovery
2. Active manifest discovery displays discovery_container and sets discovery_label,
   without mutating loading_container (which remains hidden, isVisible() is False).
3. Manifest discovery failure displays discovery_error_container and discovery_error_label,
   without mutating or polluting fetch error_container (which remains hidden, isVisible() is False).
4. Cancelling discovery via cancel_discovery_btn cancels the discovery worker without
   mutating fetch worker state or loading container.
5. Retrying discovery via retry_discovery_btn re-runs discovery without triggering fetch.
6. Concurrent discovery and fetch cancellation operate independently.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any
from unittest.mock import MagicMock

import pytest

from pypost.models.collection_variable import CollectionVariable
from pypost.models.models import Collection, Environment
from pypost.ui.dialogs.import_collection_variables_dialog import (
    ImportCollectionVariablesDialog,
)

pytestmark = [pytest.mark.timeout(30)]


def _wait_until(predicate: Any, qapp: Any, timeout_s: float = 5.0) -> bool:
    """Bounded wait loop processing Qt events."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return True
        qapp.processEvents()
        time.sleep(0.02)
    return bool(predicate())


def _build_test_dialog(
    mock_service: Any = None,
) -> ImportCollectionVariablesDialog:
    """Construct an ImportCollectionVariablesDialog with sample workspace collection."""
    env = Environment(name="Dev", variables={})
    local = Collection(
        name="WorkspaceCol",
        variables=[
            CollectionVariable(name="host", type="string", default="localhost"),
            CollectionVariable(name="port", type="string", default="8080"),
        ],
    )
    return ImportCollectionVariablesDialog(
        target_environment=env,
        workspace_collections=[local],
        library_service=mock_service,
    )


@pytest.mark.timeout(30)
def test_dialog_has_dedicated_discovery_ui_elements(qapp: Any) -> None:
    """ImportCollectionVariablesDialog must provide dedicated discovery UI elements.

    The dialog must have separate discovery_container, discovery_label,
    cancel_discovery_btn, discovery_error_container, discovery_error_label,
    retry_discovery_btn, and matching slots _on_cancel_discovery and _on_retry_discovery.
    All discovery widgets and fetch widgets must have distinct automation IDs.
    """
    mock_service = MagicMock()
    mock_service.list_connections.return_value = []

    dialog = _build_test_dialog(mock_service)
    try:
        # Dedicated discovery container and child controls
        assert hasattr(dialog, "discovery_container"), (
            "Dialog must define self.discovery_container"
        )
        assert hasattr(dialog, "discovery_label"), (
            "Dialog must define self.discovery_label"
        )
        assert hasattr(dialog, "cancel_discovery_btn"), (
            "Dialog must define self.cancel_discovery_btn"
        )
        assert hasattr(dialog, "discovery_error_container"), (
            "Dialog must define self.discovery_error_container"
        )
        assert hasattr(dialog, "discovery_error_label"), (
            "Dialog must define self.discovery_error_label"
        )
        assert hasattr(dialog, "retry_discovery_btn"), (
            "Dialog must define self.retry_discovery_btn"
        )

        # Dedicated slots
        assert hasattr(dialog, "_on_cancel_discovery"), (
            "Dialog must define slot _on_cancel_discovery"
        )
        assert hasattr(dialog, "_on_retry_discovery"), (
            "Dialog must define slot _on_retry_discovery"
        )

        # Check widget automation identities
        assert (
            dialog.discovery_container.objectName()
            == "pypost_import_collection_discovery_container"
        )
        assert (
            dialog.discovery_label.objectName()
            == "pypost_import_collection_discovery_label"
        )
        assert (
            dialog.cancel_discovery_btn.objectName()
            == "pypost_import_collection_cancel_discovery_button"
        )
        assert (
            dialog.discovery_error_container.objectName()
            == "pypost_import_collection_discovery_error_container"
        )
        assert (
            dialog.discovery_error_label.objectName()
            == "pypost_import_collection_discovery_error_label"
        )
        assert (
            dialog.retry_discovery_btn.objectName()
            == "pypost_import_collection_retry_discovery_button"
        )

        # Fetch chrome must also retain distinct automation IDs
        assert (
            dialog.loading_container.objectName()
            == "pypost_import_collection_loading_container"
        )
        assert (
            dialog.error_container.objectName()
            == "pypost_import_collection_error_container"
        )
    finally:
        worker = getattr(dialog, "_active_discovery_worker", None)
        if worker is not None:
            worker.wait(1000)


@pytest.mark.timeout(30)
def test_discovery_does_not_mutate_fetch_loading_container(qapp: Any) -> None:
    """During active manifest discovery, loading_container must remain hidden.

    Active manifest discovery must display discovery_container with
    'Discovering library collections...' while loading_container.isVisible()
    remains False. Workspace collections must remain selected and interactive.
    """
    mock_service = MagicMock()
    unblock_discovery = threading.Event()

    def slow_list_connections() -> list[Any]:
        unblock_discovery.wait(timeout=5.0)
        return []

    mock_service.list_connections.side_effect = slow_list_connections

    dialog = _build_test_dialog(mock_service)
    try:
        # Give worker thread a moment to start
        qapp.processEvents()

        # Discovery container must exist and be visible
        assert hasattr(dialog, "discovery_container"), (
            "Dialog must define self.discovery_container"
        )
        assert dialog.discovery_container.isVisible(), (
            "Dedicated discovery_container must be visible during active discovery"
        )
        assert hasattr(dialog, "discovery_label"), (
            "Dialog must define self.discovery_label"
        )
        assert (
            dialog.discovery_label.text() == "Discovering library collections..."
        ), (
            f"Expected discovery label text 'Discovering library collections...', "
            f"got {dialog.discovery_label.text()!r}"
        )

        # Fetch loading container MUST remain hidden (not hijacked for discovery)
        assert not dialog.loading_container.isVisible(), (
            "loading_container must remain hidden during manifest discovery; "
            "it is reserved exclusively for collection fetching"
        )

        # Workspace collection remains selected and table is populated
        assert dialog.collection_combo.currentIndex() == 0
        assert dialog.vars_table.model() is not None
        assert dialog.vars_table.model().rowCount() == 2
    finally:
        unblock_discovery.set()
        worker = getattr(dialog, "_active_discovery_worker", None)
        if worker is not None:
            worker.wait(1000)


@pytest.mark.timeout(30)
def test_discovery_error_does_not_pollute_fetch_error_container(qapp: Any) -> None:
    """Manifest discovery failure must show discovery_error_container, not error_container.

    When manifest discovery fails, discovery_error_container must be visible
    with error details and retry_discovery_btn enabled. The fetch error_container
    and loading_container must remain hidden.
    """
    mock_service = MagicMock()
    mock_service.list_connections.side_effect = RuntimeError(
        "Remote library discovery failed: Connection refused"
    )

    dialog = _build_test_dialog(mock_service)
    try:
        # Await discovery worker completion
        assert _wait_until(
            lambda: getattr(dialog, "_active_discovery_worker", None) is None,
            qapp,
            timeout_s=5.0,
        ), "Discovery worker should complete with error"

        # Dedicated discovery error container must be visible
        assert hasattr(dialog, "discovery_error_container"), (
            "Dialog must define self.discovery_error_container"
        )
        assert dialog.discovery_error_container.isVisible(), (
            "discovery_error_container must be visible upon discovery failure"
        )
        assert hasattr(dialog, "discovery_error_label"), (
            "Dialog must define self.discovery_error_label"
        )
        assert "Connection refused" in dialog.discovery_error_label.text(), (
            f"discovery_error_label must include failure details, "
            f"got: {dialog.discovery_error_label.text()!r}"
        )
        assert hasattr(dialog, "retry_discovery_btn"), (
            "Dialog must define self.retry_discovery_btn"
        )
        assert dialog.retry_discovery_btn.isEnabled(), (
            "retry_discovery_btn must be enabled on discovery failure"
        )

        # Fetch error container and loading container must NOT be polluted
        assert not dialog.error_container.isVisible(), (
            "Fetch error_container must remain hidden on discovery failure; "
            "discovery errors belong exclusively in discovery_error_container"
        )
        assert not dialog.loading_container.isVisible(), (
            "Fetch loading_container must remain hidden"
        )

        # Discovery container (loading status) must be hidden
        if hasattr(dialog, "discovery_container"):
            assert not dialog.discovery_container.isVisible(), (
                "discovery_container must be hidden when discovery fails"
            )
    finally:
        worker = getattr(dialog, "_active_discovery_worker", None)
        if worker is not None:
            worker.wait(1000)


@pytest.mark.timeout(30)
def test_cancel_discovery_button_cancels_discovery_without_affecting_fetch(
    qapp: Any,
) -> None:
    """cancel_discovery_btn must abort discovery without mutating fetch state.

    Clicking cancel_discovery_btn should cancel the active discovery worker,
    hide discovery_container, and leave fetch chrome and workspace state intact.
    """
    mock_service = MagicMock()
    unblock_discovery = threading.Event()

    def slow_list_connections() -> list[Any]:
        unblock_discovery.wait(timeout=5.0)
        return []

    mock_service.list_connections.side_effect = slow_list_connections

    dialog = _build_test_dialog(mock_service)
    try:
        qapp.processEvents()

        assert hasattr(dialog, "cancel_discovery_btn"), (
            "Dialog must define self.cancel_discovery_btn"
        )

        # Trigger cancel discovery
        dialog.cancel_discovery_btn.click()
        qapp.processEvents()

        # Discovery worker must be cancelled / reset
        assert getattr(dialog, "_active_discovery_worker", None) is None or getattr(
            dialog._active_discovery_worker, "is_interrupted", False
        ), "Discovery worker should be cancelled after cancel_discovery_btn click"

        # Discovery container should be hidden
        if hasattr(dialog, "discovery_container"):
            assert not dialog.discovery_container.isVisible(), (
                "discovery_container must be hidden after cancel"
            )

        # Fetch chrome must remain unaffected
        assert not dialog.loading_container.isVisible(), (
            "loading_container must not be shown by cancel discovery"
        )
        assert not dialog.error_container.isVisible(), (
            "error_container must not be shown by cancel discovery"
        )
        assert getattr(dialog, "_active_fetch_worker", None) is None, (
            "No fetch worker should be spawned or affected"
        )
    finally:
        unblock_discovery.set()
        worker = getattr(dialog, "_active_discovery_worker", None)
        if worker is not None:
            worker.wait(1000)


@pytest.mark.timeout(30)
def test_discovery_retry_triggers_rediscovery_not_fetch(qapp: Any) -> None:
    """retry_discovery_btn must re-invoke manifest discovery without triggering fetch."""
    mock_service = MagicMock()
    calls = []

    def mock_list_connections() -> list[Any]:
        calls.append("list_connections")
        if len(calls) == 1:
            raise RuntimeError("Transient discovery failure")
        return []

    mock_service.list_connections.side_effect = mock_list_connections

    dialog = _build_test_dialog(mock_service)
    try:
        # Wait for initial failure
        assert _wait_until(
            lambda: getattr(dialog, "_active_discovery_worker", None) is None
            and len(calls) == 1,
            qapp,
            timeout_s=5.0,
        ), "Initial discovery must run and fail"

        assert hasattr(dialog, "retry_discovery_btn"), (
            "Dialog must define self.retry_discovery_btn"
        )
        assert hasattr(dialog, "discovery_error_container"), (
            "Dialog must define self.discovery_error_container"
        )
        assert dialog.discovery_error_container.isVisible()

        # Click retry discovery
        dialog.retry_discovery_btn.click()
        qapp.processEvents()

        # Discovery error container should be hidden during retry
        assert not dialog.discovery_error_container.isVisible(), (
            "discovery_error_container must be hidden when retry is initiated"
        )

        # Wait for second discovery call to succeed
        assert _wait_until(
            lambda: len(calls) == 2,
            qapp,
            timeout_s=5.0,
        ), "Retry must trigger a second list_connections call"

        # Fetch worker must never have been spawned
        assert getattr(dialog, "_active_fetch_worker", None) is None, (
            "Discovery retry must not initiate a collection fetch"
        )
    finally:
        worker = getattr(dialog, "_active_discovery_worker", None)
        if worker is not None:
            worker.wait(1000)


@pytest.mark.timeout(30)
def test_concurrent_discovery_and_fetch_cancellation_independence(
    qapp: Any,
) -> None:
    """Cancelling discovery must not affect active fetch, and vice versa.

    When both a discovery worker and a fetch worker are in flight, clicking
    cancel_discovery_btn cancels only discovery, while clicking cancel_loading_btn
    cancels only fetch.
    """
    mock_service = MagicMock()
    unblock_discovery = threading.Event()
    unblock_fetch = threading.Event()

    def slow_discovery() -> list[Any]:
        unblock_discovery.wait(timeout=5.0)
        return []

    def slow_fetch(conn_id: str, path: str) -> Collection:
        unblock_fetch.wait(timeout=5.0)
        return Collection(name="FetchedCol", variables=[])

    mock_service.list_connections.side_effect = slow_discovery
    mock_service.read_collection.side_effect = slow_fetch

    dialog = _build_test_dialog(mock_service)
    try:
        qapp.processEvents()
        assert getattr(dialog, "_active_discovery_worker", None) is not None, (
            "Discovery worker should be running"
        )

        # Manually trigger a remote fetch worker concurrently
        dialog._start_fetch_remote_collection("conn_1", "path/to/col.json")
        qapp.processEvents()
        assert getattr(dialog, "_active_fetch_worker", None) is not None, (
            "Fetch worker should be running"
        )

        # Required UI elements must exist
        assert hasattr(dialog, "cancel_discovery_btn"), (
            "Dialog must define self.cancel_discovery_btn"
        )
        assert hasattr(dialog, "discovery_container"), (
            "Dialog must define self.discovery_container"
        )

        # Cancel discovery
        dialog.cancel_discovery_btn.click()
        qapp.processEvents()

        # Fetch worker must STILL be active
        assert dialog._active_fetch_worker is not None, (
            "Cancelling discovery must not abort the active fetch worker"
        )
        assert dialog.loading_container.isVisible(), (
            "loading_container must remain visible while fetch worker is active"
        )
        assert not dialog.discovery_container.isVisible(), (
            "discovery_container must be hidden after discovery cancellation"
        )

        # Now cancel fetch
        dialog.cancel_loading_btn.click()
        qapp.processEvents()

        # Fetch worker must now be cancelled
        assert (
            dialog._active_fetch_worker is None
            or dialog._active_fetch_worker.is_interrupted
        ), "Fetch worker must be cancelled after cancel_loading_btn click"
        assert not dialog.loading_container.isVisible(), (
            "loading_container must be hidden after fetch cancellation"
        )
    finally:
        unblock_discovery.set()
        unblock_fetch.set()
        disc_worker = getattr(dialog, "_active_discovery_worker", None)
        if disc_worker is not None:
            disc_worker.wait(1000)
        fetch_worker = getattr(dialog, "_active_fetch_worker", None)
        if fetch_worker is not None:
            fetch_worker.wait(1000)


@pytest.mark.timeout(30)
def test_discovery_observability_lifecycle_events(
    qapp: Any,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Audit structured logging lifecycle events for manifest discovery (Step 6).

    Verifies:
    - collection_variable_manifest_discovery_started (INFO)
    - collection_variable_manifest_discovery_completed (INFO)
    - collection_variable_manifest_discovery_retry_requested (INFO)
    - collection_variable_manifest_discovery_cancelled (INFO)
    - collection_variable_manifest_discovery_failed (WARNING with exc context)
    """
    mock_service = MagicMock()
    mock_service.list_connections.return_value = []

    dialog_logger = "pypost.ui.dialogs.import_collection_variables_dialog"

    with caplog.at_level(logging.INFO, logger=dialog_logger):
        dialog = _build_test_dialog(mock_service)
        try:
            assert _wait_until(
                lambda: getattr(dialog, "_active_discovery_worker", None) is None,
                qapp,
                timeout_s=5.0,
            ), "Discovery worker should complete"

            # Check started and completed logs
            assert "collection_variable_manifest_discovery_started gen=1" in caplog.text
            assert (
                "collection_variable_manifest_discovery_completed gen=1 entry_count=0"
                in caplog.text
            )

            # Trigger retry
            dialog.retry_discovery_btn.click()
            qapp.processEvents()
            assert (
                "collection_variable_manifest_discovery_retry_requested env_name=Dev"
                in caplog.text
            )

            assert _wait_until(
                lambda: getattr(dialog, "_active_discovery_worker", None) is None,
                qapp,
                timeout_s=5.0,
            )

            # Trigger cancel on subsequent round
            dialog._start_manifest_discovery()
            qapp.processEvents()
            dialog.cancel_discovery_btn.click()
            qapp.processEvents()
            assert "collection_variable_manifest_discovery_cancelled" in caplog.text
        finally:
            worker = getattr(dialog, "_active_discovery_worker", None)
            if worker is not None:
                worker.wait(1000)

    # Now verify failure logging (WARNING level with exception context)
    fail_service = MagicMock()
    fail_service.list_connections.side_effect = RuntimeError("Manifest discovery unreachable")

    with caplog.at_level(logging.WARNING, logger=dialog_logger):
        fail_dialog = _build_test_dialog(fail_service)
        try:
            assert _wait_until(
                lambda: getattr(fail_dialog, "_active_discovery_worker", None) is None,
                qapp,
                timeout_s=5.0,
            ), "Discovery worker should complete with error"

            assert "collection_variable_manifest_discovery_failed" in caplog.text
            assert "Manifest discovery unreachable" in caplog.text

            # Ensure discovery failure did not emit remote fetch failure log
            assert "collection_variable_remote_fetch_failed" not in caplog.text
        finally:
            worker = getattr(fail_dialog, "_active_discovery_worker", None)
            if worker is not None:
                worker.wait(1000)


@pytest.mark.timeout(30)
def test_remote_fetch_observability_lifecycle_events(
    qapp: Any,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Audit structured logging lifecycle events for remote collection fetch (Step 6).

    Verifies:
    - collection_variable_remote_fetch_started (INFO)
    - collection_variable_remote_fetch_completed (INFO)
    - collection_variable_remote_fetch_cancelled (INFO)
    - collection_variable_remote_fetch_retry_requested (INFO)
    - collection_variable_remote_fetch_failed (ERROR with exc context)
    """
    mock_service = MagicMock()
    sample_col = Collection(
        name="RemoteCol",
        variables=[
            CollectionVariable(name="api_key", type="string", default="test-key", secret=True)
        ],
    )
    mock_service.read_collection.return_value = sample_col

    dialog_logger = "pypost.ui.dialogs.import_collection_variables_dialog"

    with caplog.at_level(logging.INFO, logger=dialog_logger):
        dialog = _build_test_dialog(mock_service)
        try:
            dialog._start_fetch_remote_collection("conn_1", "path/to/col.json")
            qapp.processEvents()

            assert (
                "collection_variable_remote_fetch_started "
                "connection_id=conn_1 path=path/to/col.json"
                in caplog.text
            )

            assert _wait_until(
                lambda: getattr(dialog, "_active_fetch_worker", None) is None,
                qapp,
                timeout_s=5.0,
            ), "Fetch worker should complete"

            assert "collection_variable_remote_fetch_completed" in caplog.text
            assert "collection_name=RemoteCol vars_count=1" in caplog.text

            # Retry fetch
            dialog.collection_combo.addItem(
                "Remote Item", userData=("library", "conn_1", "path/to/col.json")
            )
            dialog.collection_combo.setCurrentIndex(dialog.collection_combo.count() - 1)
            dialog._on_retry_fetch()
            qapp.processEvents()
            assert (
                "collection_variable_remote_fetch_retry_requested env_name=Dev"
                in caplog.text
            )

            assert _wait_until(
                lambda: getattr(dialog, "_active_fetch_worker", None) is None,
                qapp,
                timeout_s=5.0,
            )

            # Cancel fetch
            unblock_fetch = threading.Event()
            mock_service.read_collection.side_effect = lambda cid, p: (
                unblock_fetch.wait(timeout=5.0),
                sample_col,
            )[1]
            dialog._start_fetch_remote_collection("conn_1", "path/to/col.json")
            qapp.processEvents()
            dialog.cancel_loading_btn.click()
            qapp.processEvents()
            assert "collection_variable_remote_fetch_cancelled" in caplog.text
            unblock_fetch.set()
        finally:
            worker = getattr(dialog, "_active_fetch_worker", None)
            if worker is not None:
                worker.wait(1000)

    # Now verify failure logging (ERROR level with exception context)
    fail_service = MagicMock()
    fail_service.read_collection.side_effect = RuntimeError("Remote collection corrupted")

    with caplog.at_level(logging.ERROR, logger=dialog_logger):
        fail_dialog = _build_test_dialog(fail_service)
        try:
            fail_dialog._start_fetch_remote_collection("conn_1", "corrupted.json")
            assert _wait_until(
                lambda: getattr(fail_dialog, "_active_fetch_worker", None) is None,
                qapp,
                timeout_s=5.0,
            ), "Fetch worker should complete with error"

            assert "collection_variable_remote_fetch_failed" in caplog.text
            assert "Remote collection corrupted" in caplog.text

            # Ensure fetch failure did not emit discovery failure log
            assert "collection_variable_manifest_discovery_failed" not in caplog.text
        finally:
            worker = getattr(fail_dialog, "_active_fetch_worker", None)
            if worker is not None:
                worker.wait(1000)
