"""PYPOST-1426: fault-injection suite for flaky networks and corrupted manifests.

Desired behavior for remote collection variable import:
1. Network drop / TCP reset mid-stream → inline error + Retry; dialog stays open;
   table has no partial rows.
2. Truncated JSON / malformed variable schema → same recoverable UX (no crash,
   no silent success with invalid data).
3. Retry after reset recovers when the subsequent read succeeds.
4. Cancel during a mid-stream blocked transfer aborts via CancellationToken
   (PYPOST-1425) without presenting a fetch failure for that generation.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Any
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication

from pypost.core.collection_serializer import CollectionSerializationError
from pypost.models.collection_variable import CollectionVariable
from pypost.models.models import Collection, Environment
from pypost.ui.dialogs.import_collection_variables_dialog import (
    COL_NAME,
    ImportCollectionVariablesDialog,
)
from pypost.ui.workers.collection_fetch_worker import CollectionFetchWorker
from tests.helpers.remote_collection_faults import (
    BLOCK_BUDGET_S,
    assert_raises_collection_serialization,
    broken_pipe_side_effect,
    build_library_service,
    connection_reset_side_effect,
    fail_then_recover_side_effect,
    malformed_variable_name_side_effect,
    malformed_variable_type_side_effect,
    mid_stream_reset_or_abort_side_effect,
    raise_from_malformed_variable_name,
    raise_from_malformed_variable_type,
    raise_from_truncated_json,
    truncated_json_side_effect,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.timeout(30)]

ABORT_ELAPSED_LIMIT_S = 0.5


def _ensure_qapp() -> QCoreApplication:
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


def _wait_for_manifest_discovery(dialog: Any, qapp: Any, timeout_s: float = 5.0) -> None:
    deadline = time.monotonic() + timeout_s
    while getattr(dialog, "_active_discovery_worker", None) is not None:
        if time.monotonic() >= deadline:
            break
        qapp.processEvents()
        time.sleep(0.02)
    for _ in range(5):
        qapp.processEvents()
        time.sleep(0.01)


def _wait_for_fetch_idle(dialog: Any, qapp: Any, timeout_s: float = 5.0) -> None:
    deadline = time.monotonic() + timeout_s
    while dialog._active_fetch_worker is not None and time.monotonic() < deadline:
        qapp.processEvents()
        time.sleep(0.02)
    for _ in range(5):
        qapp.processEvents()
        time.sleep(0.01)


def _select_remote_and_await_error(
    dialog: Any,
    qapp: Any,
    *,
    error_substr: str,
) -> None:
    _wait_for_manifest_discovery(dialog, qapp)
    assert not dialog.error_container.isVisible()
    # Index 0: local workspace collection; Index 1: remote library entry.
    dialog.collection_combo.setCurrentIndex(1)
    _wait_for_fetch_idle(dialog, qapp)

    assert dialog.isVisible(), "Dialog must remain open after remote fault"
    assert not dialog.loading_container.isVisible(), "Loading chrome must hide on fault"
    assert dialog.error_container.isVisible(), "Inline error banner must be visible"
    assert error_substr.lower() in dialog.error_label.text().lower(), (
        f"Error label must mention {error_substr!r}, got: {dialog.error_label.text()!r}"
    )
    assert dialog.retry_fetch_btn.isEnabled(), "Retry must be enabled after fault"
    assert dialog.vars_table.model().rowCount() == 0, (
        "Fault must not leave partial variable rows in the table"
    )


def _open_fault_dialog(qapp: Any, mock_service: MagicMock) -> ImportCollectionVariablesDialog:
    env = Environment(name="Dev", variables={})
    local_col = Collection(
        name="LocalCol",
        variables=[CollectionVariable(name="local_key", type="string", default="local_val")],
    )
    dialog = ImportCollectionVariablesDialog(
        target_environment=env,
        workspace_collections=[local_col],
        library_service=mock_service,
    )
    dialog.show()
    qapp.processEvents()
    return dialog


@pytest.mark.timeout(30)
def test_helper_serialization_faults_raise_collection_serialization_error() -> None:
    """Sanity: truncated JSON and malformed schemas raise CollectionSerializationError."""
    assert_raises_collection_serialization(raise_from_truncated_json)
    assert_raises_collection_serialization(raise_from_malformed_variable_name)
    assert_raises_collection_serialization(raise_from_malformed_variable_type)


@pytest.mark.timeout(30)
def test_connection_reset_mid_stream_shows_inline_error(qapp: Any) -> None:
    """TCP reset / connection drop must surface inline error without partial rows."""
    mock_service = build_library_service(
        read_side_effect=connection_reset_side_effect(),
    )
    dialog = _open_fault_dialog(qapp, mock_service)
    try:
        _select_remote_and_await_error(dialog, qapp, error_substr="reset")
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


@pytest.mark.timeout(30)
def test_broken_pipe_shows_inline_error(qapp: Any) -> None:
    """Broken pipe during transfer must use the same recoverable error UX."""
    mock_service = build_library_service(
        read_side_effect=broken_pipe_side_effect(),
    )
    dialog = _open_fault_dialog(qapp, mock_service)
    try:
        _select_remote_and_await_error(dialog, qapp, error_substr="broken pipe")
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


@pytest.mark.timeout(30)
def test_truncated_json_manifest_shows_inline_error(qapp: Any) -> None:
    """Partial / truncated JSON manifest must not crash or partially populate."""
    mock_service = build_library_service(
        read_side_effect=truncated_json_side_effect(),
    )
    dialog = _open_fault_dialog(qapp, mock_service)
    try:
        _select_remote_and_await_error(dialog, qapp, error_substr="json")
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


@pytest.mark.timeout(30)
def test_malformed_variable_name_schema_shows_inline_error(qapp: Any) -> None:
    """Non-string variable names in remote payload must fail recoverably."""
    mock_service = build_library_service(
        read_side_effect=malformed_variable_name_side_effect(),
    )
    dialog = _open_fault_dialog(qapp, mock_service)
    try:
        _select_remote_and_await_error(dialog, qapp, error_substr="schema")
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


@pytest.mark.timeout(30)
def test_malformed_variable_type_schema_shows_inline_error(qapp: Any) -> None:
    """Unsupported variable types in remote payload must fail recoverably."""
    mock_service = build_library_service(
        read_side_effect=malformed_variable_type_side_effect(),
    )
    dialog = _open_fault_dialog(qapp, mock_service)
    try:
        _select_remote_and_await_error(dialog, qapp, error_substr="schema")
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


@pytest.mark.timeout(30)
def test_connection_reset_retry_recovers(qapp: Any) -> None:
    """Retry after ConnectionResetError must load variables when the next read works."""
    mock_service = build_library_service(
        read_side_effect=fail_then_recover_side_effect(
            ConnectionResetError("Connection reset by peer mid-stream"),
        ),
    )
    dialog = _open_fault_dialog(qapp, mock_service)
    try:
        _select_remote_and_await_error(dialog, qapp, error_substr="reset")
        dialog.retry_fetch_btn.click()
        _wait_for_fetch_idle(dialog, qapp)
        assert not dialog.error_container.isVisible(), (
            "Error banner must hide after successful retry"
        )
        assert dialog.vars_table.model().rowCount() == 1
        from PySide6.QtCore import Qt

        name = dialog.vars_table.model().data(
            dialog.vars_table.model().index(0, COL_NAME),
            Qt.ItemDataRole.DisplayRole,
        )
        assert name == "recovered_key"
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


@pytest.mark.timeout(30)
def test_cancel_during_mid_stream_aborts_without_fetch_failure(qapp: Any) -> None:
    """Cancel mid-stream must abort transport quietly (no fetch_failed banner)."""
    entered = threading.Event()
    aborted = threading.Event()
    mock_service = build_library_service(
        read_side_effect=mid_stream_reset_or_abort_side_effect(
            entered=entered,
            aborted=aborted,
        ),
    )
    dialog = _open_fault_dialog(qapp, mock_service)
    try:
        _wait_for_manifest_discovery(dialog, qapp)
        dialog.collection_combo.setCurrentIndex(1)

        deadline = time.monotonic() + 2.0
        while not entered.is_set() and time.monotonic() < deadline:
            qapp.processEvents()
            time.sleep(0.02)
        assert entered.is_set(), "mid-stream read must start before cancel"

        gen_before = dialog._fetch_generation
        t0 = time.monotonic()
        dialog.cancel_loading_btn.click()
        qapp.processEvents()

        # Wait for worker teardown after abort.
        deadline = time.monotonic() + ABORT_ELAPSED_LIMIT_S + 1.0
        while dialog._active_fetch_worker is not None and time.monotonic() < deadline:
            qapp.processEvents()
            time.sleep(0.02)
        elapsed = time.monotonic() - t0

        assert elapsed < ABORT_ELAPSED_LIMIT_S + 0.5, (
            f"cancel must abort promptly; elapsed={elapsed:.3f}s "
            f"(full block would be {BLOCK_BUDGET_S}s)"
        )
        assert aborted.is_set(), "cancel must fire transport abort callbacks"
        assert dialog._fetch_generation > gen_before
        assert not dialog.error_container.isVisible(), (
            "Cancelled mid-stream must not show a fetch failure banner"
        )
        assert dialog.vars_table.model().rowCount() == 0
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


def _drain_queued_signals(app: QCoreApplication, rounds: int = 20) -> None:
    """Deliver cross-thread QueuedConnection signals after a QThread finishes."""
    for _ in range(rounds):
        app.processEvents()
        time.sleep(0.01)


@pytest.mark.timeout(30)
def test_fetch_worker_emits_failed_for_truncated_json() -> None:
    """CollectionFetchWorker must emit fetch_failed for CollectionSerializationError."""
    app = _ensure_qapp()
    service = MagicMock()
    service.read_collection.side_effect = truncated_json_side_effect()

    failures: list[Exception] = []
    worker = CollectionFetchWorker(
        library_service=service,
        connection_id="conn_1",
        collection_path="cols/partial.json",
        generation_id=7,
    )
    worker.fetch_failed.connect(lambda exc, _gen: failures.append(exc))
    worker.start()
    assert worker.wait(5000), "worker must finish after serialization fault"
    _drain_queued_signals(app)
    assert len(failures) == 1
    assert isinstance(failures[0], CollectionSerializationError)


@pytest.mark.timeout(30)
def test_fetch_worker_emits_failed_for_connection_reset() -> None:
    """CollectionFetchWorker must emit fetch_failed for ConnectionResetError."""
    app = _ensure_qapp()
    service = MagicMock()
    service.read_collection.side_effect = connection_reset_side_effect()

    failures: list[Exception] = []
    worker = CollectionFetchWorker(
        library_service=service,
        connection_id="conn_1",
        collection_path="cols/reset.json",
        generation_id=8,
    )
    worker.fetch_failed.connect(lambda exc, _gen: failures.append(exc))
    worker.start()
    assert worker.wait(5000), "worker must finish after connection reset"
    _drain_queued_signals(app)
    assert len(failures) == 1
    assert isinstance(failures[0], ConnectionResetError)
