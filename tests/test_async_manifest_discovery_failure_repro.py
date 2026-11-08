"""Automated test suite for PYPOST-1451 / PYPOST-1424.

Exhaustive verification of async library manifest discovery failure handling,
retry lifecycle recovery, stale generation discard, cooperative cancellation,
workspace collection isolation, and clean worker thread teardown.
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
from pypost.ui.workers.manifest_discovery_worker import ManifestDiscoveryWorker

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
    target_env: Environment | None = None,
    workspace_collections: list[Collection] | None = None,
) -> ImportCollectionVariablesDialog:
    """Construct an ImportCollectionVariablesDialog with sample workspace data."""
    if target_env is None:
        target_env = Environment(name="Dev", variables={})
    if workspace_collections is None:
        workspace_collections = [
            Collection(
                name="WorkspaceCol",
                variables=[
                    CollectionVariable(name="host", type="string", default="localhost"),
                    CollectionVariable(name="port", type="string", default="8080"),
                ],
            )
        ]
    return ImportCollectionVariablesDialog(
        target_environment=target_env,
        workspace_collections=workspace_collections,
        library_service=mock_service,
    )


@pytest.mark.timeout(30)
def test_list_connections_network_and_os_faults(
    qapp: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify that network and OS faults during list_connections are safely handled.

    Tested exceptions include ConnectionResetError, TimeoutError, BrokenPipeError,
    and OSError. For each fault:
    - ManifestDiscoveryWorker catches exception without crashing the UI thread.
    - Worker logs collection_variable_manifest_discovery_worker_failed.
    - Dialog logs collection_variable_manifest_discovery_failed with context.
    - Dialog displays discovery_error_container with error message and enabled retry button.
    - discovery_container, loading_container, and error_container remain hidden.
    """
    fault_types = [
        ConnectionResetError("Connection reset by peer"),
        TimeoutError("Connection timed out"),
        BrokenPipeError("Broken pipe"),
        OSError("Network is unreachable"),
    ]

    for fault in fault_types:
        caplog.clear()
        mock_service = MagicMock()
        mock_service.list_connections.side_effect = fault

        dialog = _build_test_dialog(mock_service)
        try:
            with caplog.at_level(logging.WARNING):
                # Wait for discovery failure to be received and processed
                assert _wait_until(
                    lambda: dialog.discovery_error_container.isVisible(),
                    qapp,
                    timeout_s=5.0,
                ), f"discovery_error_container must be shown for {type(fault).__name__}"

                # Discovery error banner assertions
                assert dialog.discovery_error_container.isVisible()
                assert str(fault) in dialog.discovery_error_label.text()
                assert dialog.retry_discovery_btn.isEnabled()

                # Other containers must be hidden
                assert not dialog.discovery_container.isVisible()
                assert not dialog.loading_container.isVisible()
                assert not dialog.error_container.isVisible()

                # Active discovery worker should be cleared
                assert getattr(dialog, "_active_discovery_worker", None) is None

                # Observability verification: check dialog and worker failure logs
                assert any(
                    "collection_variable_manifest_discovery_failed" in r.message
                    for r in caplog.records
                ), f"Expected dialog discovery_failed log for {type(fault).__name__}"
                assert any(
                    "collection_variable_manifest_discovery_worker_failed" in r.message
                    for r in caplog.records
                ), f"Expected worker discovery_worker_failed log for {type(fault).__name__}"
        finally:
            worker = getattr(dialog, "_active_discovery_worker", None)
            if worker is not None and hasattr(worker, "cancel"):
                worker.cancel()
                worker.wait(1000)
            dialog.close()


@pytest.mark.timeout(30)
def test_list_manifest_collections_partial_failure(qapp: Any) -> None:
    """Verify mid-stream catalog traversal failure discards partial results.

    When list_connections returns multiple connections, and an exception occurs
    on a subsequent connection's list_manifest_collections call:
    - Traversal aborts without emitting discovery_completed.
    - discovery_failed is emitted and discovery_error_container is displayed.
    - Partial collections from preceding connections are NOT inserted into collection_combo.
    """
    mock_service = MagicMock()
    conn1 = MagicMock()
    conn1.stable_id = "conn_1"
    conn1.name = "Conn 1"
    conn2 = MagicMock()
    conn2.stable_id = "conn_2"
    conn2.name = "Conn 2"

    mock_service.list_connections.return_value = [conn1, conn2]

    def mock_list_manifest_cols(conn_id: str, **kwargs: Any) -> list[dict[str, str]]:
        if conn_id == "conn_1":
            return [{"name": "ColFromConn1", "path": "cols/c1.json"}]
        raise ConnectionResetError("Mid-stream catalog drop on conn_2")

    mock_service.list_manifest_collections.side_effect = mock_list_manifest_cols

    dialog = _build_test_dialog(mock_service)
    try:
        assert _wait_until(
            lambda: dialog.discovery_error_container.isVisible(),
            qapp,
            timeout_s=5.0,
        ), "discovery_error_container must be displayed on mid-stream fault"

        # Verify error feedback
        assert "Mid-stream catalog drop on conn_2" in dialog.discovery_error_label.text()
        assert dialog.retry_discovery_btn.isEnabled()
        assert not dialog.discovery_container.isVisible()

        # Partial collection ColFromConn1 must NOT be in collection_combo
        combo_items = [
            dialog.collection_combo.itemText(i)
            for i in range(dialog.collection_combo.count())
        ]
        assert not any("ColFromConn1" in item for item in combo_items), (
            f"Partial collection results must not appear in combo: {combo_items}"
        )

        # Only initial workspace collection should be present
        assert dialog.collection_combo.count() == 1
        assert dialog.collection_combo.itemText(0).startswith("WorkspaceCol")
    finally:
        worker = getattr(dialog, "_active_discovery_worker", None)
        if worker is not None and hasattr(worker, "cancel"):
            worker.cancel()
            worker.wait(1000)
        dialog.close()


@pytest.mark.timeout(30)
def test_discovery_fail_then_recover_end_to_end_retry(
    qapp: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify complete fail-then-recover lifecycle upon clicking retry_discovery_btn.

    1. Initial discovery fails with ConnectionRefusedError.
    2. discovery_error_container appears with retry button.
    3. Mock service is restored.
    4. User triggers retry via retry_discovery_btn.click().
    5. Second worker executes successfully, discovery_error_container is hidden,
       and remote collections populate into collection_combo.
    6. Workspace collection selection at index 0 is preserved.
    7. Red repro contract: discovery_error_label text is reset on recovery.
    8. Observability logs verified: discovery_failed, retry_requested, completed.
    """
    mock_service = MagicMock()
    mock_service.list_connections.side_effect = ConnectionRefusedError("Server offline")

    with caplog.at_level(logging.INFO):
        dialog = _build_test_dialog(mock_service)
        try:
            # 1. Wait for initial failure
            assert _wait_until(
                lambda: dialog.discovery_error_container.isVisible(),
                qapp,
                timeout_s=5.0,
            ), "discovery_error_container must be displayed on initial failure"
            assert "Server offline" in dialog.discovery_error_label.text()

            # Observability check: initial failure log
            assert any(
                "collection_variable_manifest_discovery_failed" in r.message
                for r in caplog.records
            ), "Initial failure must emit collection_variable_manifest_discovery_failed log"

            # 2. Heal the service
            conn = MagicMock()
            conn.stable_id = "conn_remote"
            conn.name = "Remote Conn"
            mock_service.list_connections.side_effect = None
            mock_service.list_connections.return_value = [conn]
            mock_service.list_manifest_collections.side_effect = None
            mock_service.list_manifest_collections.return_value = [
                {"name": "RemoteCol", "path": "cols/remote.json"}
            ]

            # 3. User clicks Retry
            dialog.retry_discovery_btn.click()
            qapp.processEvents()

            # Observability check: retry requested log
            assert any(
                "collection_variable_manifest_discovery_retry_requested" in r.message
                for r in caplog.records
            ), (
                "Clicking retry must emit "
                "collection_variable_manifest_discovery_retry_requested log"
            )

            # 4. Wait for retry discovery to finish and populate combo
            assert _wait_until(
                lambda: any(
                    "RemoteCol" in dialog.collection_combo.itemText(i)
                    for i in range(dialog.collection_combo.count())
                ),
                qapp,
                timeout_s=5.0,
            ), "Remote collection must appear in combo after retry recovery"

            # Observability check: recovery completed log
            assert any(
                "collection_variable_manifest_discovery_completed" in r.message
                for r in caplog.records
            ), (
                "Successful retry recovery must emit "
                "collection_variable_manifest_discovery_completed log"
            )

            # 5. UI state assertions
            assert not dialog.discovery_container.isVisible()
            assert not dialog.discovery_error_container.isVisible()

            # Workspace collection index 0 must be preserved
            assert dialog.collection_combo.currentIndex() == 0
            assert dialog.collection_combo.itemText(0).startswith("WorkspaceCol")

            # 6. Red repro contract probe:
            # Upon successful retry recovery, stale error label text must be cleared.
            assert dialog.discovery_error_label.text() == "", (
                f"Expected discovery_error_label text to be reset on successful recovery, "
                f"got '{dialog.discovery_error_label.text()}'"
            )
        finally:
            worker = getattr(dialog, "_active_discovery_worker", None)
            if worker is not None and hasattr(worker, "cancel"):
                worker.cancel()
                worker.wait(1000)
            dialog.close()


@pytest.mark.timeout(30)
def test_rapid_retries_stale_generation_discard(
    qapp: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify stale failure and completion signals from superseded generations are discarded.

    If a background worker from generation N finishes after a retry has advanced
    the dialog to generation N+1:
    - _on_discovery_failed with stale generation is discarded and logged.
    - Stale error banner is NOT shown.
    - _on_discovery_completed with stale generation is discarded and does NOT populate combo.
    """
    mock_service = MagicMock()
    unblock_worker = threading.Event()

    def slow_list_connections(**kwargs: Any) -> list[Any]:
        unblock_worker.wait(timeout=5.0)
        return []

    mock_service.list_connections.side_effect = slow_list_connections

    dialog = _build_test_dialog(mock_service)
    try:
        qapp.processEvents()
        gen_1 = dialog._discovery_generation
        assert gen_1 >= 1

        # Advance dialog generation to simulate a retry having been triggered
        dialog._discovery_generation += 1
        current_gen = dialog._discovery_generation
        assert current_gen > gen_1

        with caplog.at_level(logging.WARNING):
            # Simulate stale failure signal arrival from gen_1
            dialog._on_discovery_failed(
                RuntimeError("Late error from obsolete generation"),
                gen_1,
            )
            qapp.processEvents()

            # Must log stale discard warning
            assert any(
                "collection_variable_manifest_discovery_error_stale_discarded" in r.message
                for r in caplog.records
            ), (
                "Stale discovery error must log "
                "collection_variable_manifest_discovery_error_stale_discarded"
            )

            # Error container must NOT be displayed for stale generation
            assert not dialog.discovery_error_container.isVisible(), (
                "discovery_error_container must not be shown for stale generation error"
            )

        with caplog.at_level(logging.WARNING):
            # Simulate stale completion signal arrival from gen_1
            stale_entries = [("StaleCollection (Conn)", ("library", "c1", "p1"))]
            dialog._on_discovery_completed(stale_entries, gen_1)
            qapp.processEvents()

            # Must log stale discard warning
            assert any(
                "collection_variable_manifest_discovery_stale_discarded" in r.message
                for r in caplog.records
            ), (
                "Stale discovery completion must log "
                "collection_variable_manifest_discovery_stale_discarded"
            )

            # Stale collection must NOT be added to combo
            combo_items = [
                dialog.collection_combo.itemText(i)
                for i in range(dialog.collection_combo.count())
            ]
            assert not any("StaleCollection" in item for item in combo_items), (
                "Stale collection from obsolete generation must not be inserted"
            )
    finally:
        unblock_worker.set()
        worker = getattr(dialog, "_active_discovery_worker", None)
        if worker is not None and hasattr(worker, "cancel"):
            worker.cancel()
            worker.wait(1000)
        dialog.close()


@pytest.mark.timeout(30)
def test_discovery_cancellation_during_fault_state(
    qapp: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify cooperative cancellation while worker is running in a faulting network state.

    Clicking cancel_discovery_btn while discovery is in-flight:
    - Logs collection_variable_manifest_discovery_cancelled.
    - Sets worker interruption and cancels CancellationToken.
    - Immediately hides discovery_container and discovery_error_container.
    - Worker exits cleanly on error without emitting discovery_failed.
    - Discovery error container is NOT displayed after worker aborts.
    """
    mock_service = MagicMock()
    entered_call = threading.Event()
    unblock_call = threading.Event()

    def blocked_failing_connections(**kwargs: Any) -> list[Any]:
        entered_call.set()
        unblock_call.wait(timeout=5.0)
        raise ConnectionResetError("Connection died during read")

    mock_service.list_connections.side_effect = blocked_failing_connections

    dialog = _build_test_dialog(mock_service)
    try:
        # Wait until worker enters the network call
        assert entered_call.wait(timeout=5.0), "Worker must enter list_connections"
        qapp.processEvents()

        worker = getattr(dialog, "_active_discovery_worker", None)
        assert worker is not None
        assert isinstance(worker, ManifestDiscoveryWorker)

        # Trigger cancellation via UI button
        assert dialog.discovery_container.isVisible()
        with caplog.at_level(logging.INFO):
            dialog.cancel_discovery_btn.click()
            qapp.processEvents()

            # Observability check: cancellation log
            assert any(
                "collection_variable_manifest_discovery_cancelled" in r.message
                for r in caplog.records
            ), (
                "Clicking cancel must emit "
                "collection_variable_manifest_discovery_cancelled log"
            )

        # Both containers must be hidden immediately
        assert not dialog.discovery_container.isVisible()
        assert not dialog.discovery_error_container.isVisible()

        # Worker must have cancellation and interruption flagged
        assert worker.isInterruptionRequested()
        assert worker._cancelled

        # Now unblock the worker and let it catch the exception while cancelled
        unblock_call.set()
        assert worker.wait(1000), "Worker must terminate within 1000ms"

        qapp.processEvents()

        # Because worker was cancelled, discovery_failed must not show error container
        assert not dialog.discovery_error_container.isVisible(), (
            "Cancelled worker must not cause discovery_error_container to be displayed"
        )
    finally:
        unblock_call.set()
        worker = getattr(dialog, "_active_discovery_worker", None)
        if worker is not None and hasattr(worker, "cancel"):
            worker.cancel()
            worker.wait(1000)
        dialog.close()


@pytest.mark.timeout(30)
def test_workspace_collections_fully_functional_during_discovery_failure(
    qapp: Any,
) -> None:
    """Verify local workspace collections remain fully functional when discovery fails.

    When remote discovery fails completely:
    - Workspace collection remains selected in collection_combo.
    - Variables table displays workspace variables accurately.
    - User can modify conflict strategies, preview imports, and click Import.
    - Import executes successfully and updates target_environment.
    """
    env = Environment(
        name="Production",
        variables={"host": "prod.internal", "db_pass": "secret123"},
    )
    workspace_col = Collection(
        name="LocalOpsCol",
        variables=[
            CollectionVariable(
                name="host",
                type="string",
                default="dev.internal",
                description="Target host",
            ),
            CollectionVariable(
                name="new_var",
                type="string",
                default="fresh_value",
                description="New variable",
            ),
        ],
    )

    mock_service = MagicMock()
    mock_service.list_connections.side_effect = ConnectionResetError("Connection refused")

    dialog = _build_test_dialog(
        mock_service=mock_service,
        target_env=env,
        workspace_collections=[workspace_col],
    )
    try:
        # Wait for discovery failure to complete
        assert _wait_until(
            lambda: dialog.discovery_error_container.isVisible(),
            qapp,
            timeout_s=5.0,
        ), "discovery_error_container must be shown"

        # Workspace collection must remain selected
        assert dialog.collection_combo.currentIndex() == 0
        assert dialog.collection_combo.itemText(0).startswith("LocalOpsCol")

        # Variables table must contain exactly the 2 workspace collection variables
        assert dialog.vars_table.rowCount() == 2
        var_names = [
            dialog.vars_table.item(row, 1).text()
            for row in range(dialog.vars_table.rowCount())
            if dialog.vars_table.item(row, 1) is not None
        ]
        assert "host" in var_names
        assert "new_var" in var_names

        # Import button must be enabled
        assert dialog.import_button.isEnabled()

        # Execute import
        dialog.accept()
        qapp.processEvents()

        # Import summary must be present and reflect variables
        assert dialog.summary is not None
        assert "new_var" in dialog.summary.added_keys
        assert "host" in dialog.summary.skipped_keys
        assert dialog.summary.total_imported == 1
        # new_var was added to target environment
        assert env.variables.get("new_var") == "fresh_value"
    finally:
        worker = getattr(dialog, "_active_discovery_worker", None)
        if worker is not None and hasattr(worker, "cancel"):
            worker.cancel()
            worker.wait(1000)
        dialog.close()


@pytest.mark.timeout(30)
def test_dialog_close_during_discovery_failure_clean_teardown(qapp: Any) -> None:
    """Verify dialog close or reject cleanly aborts worker thread without leaks.

    Ensures that when dialog is closed/rejected while discovery is running
    or in a failure state:
    - Worker thread cancel() is called.
    - Worker thread terminates cleanly (wait returns True).
    - No dangling active worker references remain.
    """
    # 1. Close while discovery is in-flight
    mock_service = MagicMock()
    unblock_worker = threading.Event()
    worker_started = threading.Event()

    def slow_call(**kwargs: Any) -> list[Any]:
        worker_started.set()
        unblock_worker.wait(timeout=5.0)
        return []

    mock_service.list_connections.side_effect = slow_call

    dialog = _build_test_dialog(mock_service)
    try:
        assert worker_started.wait(timeout=5.0), "Worker must begin execution"
        qapp.processEvents()

        worker = getattr(dialog, "_active_discovery_worker", None)
        assert worker is not None
        assert worker.isRunning()

        # Reject dialog while worker is running
        dialog.reject()
        qapp.processEvents()

        # Worker must have been cancelled
        assert worker.isInterruptionRequested()
        assert worker._cancelled
        assert getattr(dialog, "_active_discovery_worker", None) is None

        # Unblock thread and confirm clean termination
        unblock_worker.set()
        assert worker.wait(1000), "Worker thread must terminate within 1000ms"
        assert not worker.isRunning()
    finally:
        unblock_worker.set()
        worker = getattr(dialog, "_active_discovery_worker", None)
        if worker is not None and hasattr(worker, "cancel"):
            worker.cancel()
            worker.wait(1000)
        dialog.close()

    # 2. Close while discovery is in failure state
    mock_service_fail = MagicMock()
    mock_service_fail.list_connections.side_effect = ConnectionResetError("Fatal I/O")

    dialog2 = _build_test_dialog(mock_service_fail)
    try:
        assert _wait_until(
            lambda: dialog2.discovery_error_container.isVisible(),
            qapp,
            timeout_s=5.0,
        ), "discovery_error_container must be shown"

        # Close dialog
        dialog2.close()
        qapp.processEvents()

        assert getattr(dialog2, "_active_discovery_worker", None) is None
    finally:
        dialog2.close()
