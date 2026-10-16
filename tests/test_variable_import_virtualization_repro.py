"""Automated failing repro tests for virtualized table model and background collection fetching.

Verifies the missing functionality specified in PYPOST-1415:
1. Zero-widget virtualized scaling:
   - CollectionVariablesTableModel (subclass of QAbstractTableModel).
   - CollectionVariablesTableView (subclass of QTableView).
   - ConflictStrategyDelegate (subclass of QStyledItemDelegate).
   - Zero persistent QComboBox widgets allocated for off-screen rows.
   - Dual-source secret masking in model.data().
2. Non-blocking remote collection fetching:
   - Background worker (CollectionFetchWorker / QThread).
   - Loading container, spinner/indicator, and cancel button.
   - Main thread UI responsiveness while fetching remote collections.
3. Race condition protection:
   - Monotonic request generation counter (_fetch_generation).
   - Cancellation and selection switches discard stale responses.
4. Non-modal error handling:
   - Inline error banner (error_container, error_label, retry_fetch_btn) on failure.
   - Dialog remains open and interactive without crashing.
   - Retry capability and automatic clearing upon local selection.
5. Backward compatibility:
   - 9-column side-by-side diff inspector and strategy resolution from PYPOST-1414.
"""

from __future__ import annotations

import logging
import time
from typing import Any
from unittest.mock import MagicMock

from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtWidgets import QComboBox, QTableView
import pytest

from pypost.core.collection_variable_import import ConflictStrategy
from pypost.core.constants import HIDDEN_MASK
from pypost.models.collection_variable import CollectionVariable
from pypost.models.models import Collection, Environment
import pypost.ui.dialogs.import_collection_variables_dialog as dialog_module
from pypost.ui.dialogs.import_collection_variables_dialog import (
    COL_CANDIDATE_VALUE,
    COL_CURRENT_VALUE,
    COL_NAME,
    COL_SELECT,
    COL_STATUS,
    COL_STRATEGY,
    ImportCollectionVariablesDialog,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.timeout(30)]


@pytest.mark.timeout(30)
def test_virtualized_model_zero_widget_scaling(qapp: Any) -> None:
    """Verify dialog uses virtualized CollectionVariablesTableModel without persistent widgets."""
    CollectionVariablesTableModel = getattr(
        dialog_module, "CollectionVariablesTableModel", None
    )
    assert CollectionVariablesTableModel is not None, (
        "CollectionVariablesTableModel (QAbstractTableModel) must be implemented "
        "for virtualized table scaling"
    )

    ConflictStrategyDelegate = getattr(dialog_module, "ConflictStrategyDelegate", None)
    assert ConflictStrategyDelegate is not None, (
        "ConflictStrategyDelegate (QStyledItemDelegate) must be implemented "
        "for on-demand conflict editing"
    )

    CollectionVariablesTableView = getattr(
        dialog_module, "CollectionVariablesTableView", None
    )
    assert CollectionVariablesTableView is not None, (
        "CollectionVariablesTableView (QTableView) must be implemented"
    )

    # 1,000 existing variables in environment
    env_vars = {f"var_{i}": f"env_val_{i}" for i in range(1000)}
    env_vars["secret_env_var"] = "super_secret_env_value"
    env = Environment(
        name="ScaleEnv",
        variables=env_vars,
        hidden_keys={"secret_env_var"},
    )

    # 2,000 variables in collection: 1,001 collisions + 999 new
    col_vars: list[CollectionVariable] = []
    # Collisions
    for i in range(1000):
        col_vars.append(
            CollectionVariable(
                name=f"var_{i}",
                type="string",
                default=f"col_val_{i}",
                description=f"Description {i}",
            )
        )
    col_vars.append(
        CollectionVariable(
            name="secret_env_var",
            type="string",
            default="col_candidate_secret_val",
            secret=False,
        )
    )
    # New variables (998 + secret_col_var = 999 new)
    for i in range(1000, 1998):
        col_vars.append(
            CollectionVariable(
                name=f"var_{i}",
                type="string",
                default=f"col_val_{i}",
                description=f"Description {i}",
            )
        )
    col_vars.append(
        CollectionVariable(
            name="secret_col_var",
            type="string",
            default="col_secret_token",
            secret=True,
        )
    )

    col = Collection(name="LargeCollection", variables=col_vars)

    dialog = ImportCollectionVariablesDialog(
        target_environment=env,
        workspace_collections=[col],
    )
    try:
        # Table must use QTableView and CollectionVariablesTableModel
        assert isinstance(dialog.vars_table, QTableView), (
            "vars_table must inherit from QTableView, not QTableWidget"
        )
        assert isinstance(dialog.vars_table, CollectionVariablesTableView), (
            "vars_table must be an instance of CollectionVariablesTableView"
        )
        model = dialog.vars_table.model()
        assert isinstance(model, QAbstractTableModel), (
            "vars_table model must inherit from QAbstractTableModel"
        )
        assert isinstance(model, CollectionVariablesTableModel), (
            "vars_table model must be an instance of CollectionVariablesTableModel"
        )
        assert model.rowCount() == 2000
        assert model.columnCount() == 9

        # Zero persistent QComboBox widgets allocated in table viewport/children
        combos = dialog.vars_table.findChildren(QComboBox)
        assert len(combos) == 0, (
            f"Expected 0 persistent QComboBox cell widgets, found {len(combos)}. "
            "Table must use delegate-based editing instead of allocating permanent cell widgets."
        )

        # Delegate installed on strategy column
        delegate = dialog.vars_table.itemDelegateForColumn(COL_STRATEGY)
        assert isinstance(delegate, ConflictStrategyDelegate), (
            "ConflictStrategyDelegate must be installed on COL_STRATEGY"
        )

        # Dual-source secret masking verification in model
        # 1. secret_env_var: hidden in env -> masked
        # Find row for secret_env_var
        secret_env_row = next(
            r for r in range(2000)
            if model.data(model.index(r, COL_NAME), Qt.ItemDataRole.DisplayRole)
            == "secret_env_var"
        )
        curr_val = model.data(
            model.index(secret_env_row, COL_CURRENT_VALUE), Qt.ItemDataRole.DisplayRole
        )
        cand_val = model.data(
            model.index(secret_env_row, COL_CANDIDATE_VALUE), Qt.ItemDataRole.DisplayRole
        )
        assert curr_val == HIDDEN_MASK
        assert cand_val == HIDDEN_MASK
        assert "super_secret_env_value" not in curr_val
        assert "col_candidate_secret_val" not in cand_val

        # 2. secret_col_var: secret in collection -> masked
        secret_col_row = next(
            r for r in range(2000)
            if model.data(model.index(r, COL_NAME), Qt.ItemDataRole.DisplayRole)
            == "secret_col_var"
        )
        cand_val_col = model.data(
            model.index(secret_col_row, COL_CANDIDATE_VALUE), Qt.ItemDataRole.DisplayRole
        )
        assert cand_val_col == HIDDEN_MASK
        assert "col_secret_token" not in cand_val_col

        # 3. Normal variable: unmasked
        normal_row = next(
            r for r in range(2000)
            if model.data(model.index(r, COL_NAME), Qt.ItemDataRole.DisplayRole) == "var_0"
        )
        assert model.data(
            model.index(normal_row, COL_CURRENT_VALUE), Qt.ItemDataRole.DisplayRole
        ) == "env_val_0"
        assert model.data(
            model.index(normal_row, COL_CANDIDATE_VALUE), Qt.ItemDataRole.DisplayRole
        ) == "col_val_0"
    finally:
        dialog.close()


@pytest.mark.timeout(30)
def test_non_blocking_remote_collection_fetch(qapp: Any) -> None:
    """Verify remote fetch uses CollectionFetchWorker on background thread with loading UI."""
    CollectionFetchWorker = getattr(dialog_module, "CollectionFetchWorker", None)
    assert CollectionFetchWorker is not None, (
        "CollectionFetchWorker (QThread) must be implemented for background fetching"
    )

    env = Environment(name="Dev", variables={})
    col_remote = Collection(
        name="RemoteCol",
        variables=[
            CollectionVariable(name="remote_host", type="string", default="api.remote.io")
        ],
    )

    mock_service = MagicMock()
    conn_mock = MagicMock()
    conn_mock.stable_id = "conn_1"
    conn_mock.name = "Remote Conn"
    mock_service.list_connections.return_value = [conn_mock]
    mock_service.list_manifest_collections.return_value = [
        {"name": "RemoteCol", "path": "cols/remote.json"}
    ]

    def slow_read_collection(conn_id: str, path: str) -> Collection:
        time.sleep(0.15)
        return col_remote

    mock_service.read_collection.side_effect = slow_read_collection

    dialog = ImportCollectionVariablesDialog(
        target_environment=env,
        workspace_collections=[],
        library_service=mock_service,
    )
    try:
        # Check loading UI attributes exist
        assert hasattr(dialog, "loading_container"), "Dialog must have loading_container"
        assert hasattr(dialog, "loading_label"), "Dialog must have loading_label"
        assert hasattr(dialog, "cancel_loading_btn"), "Dialog must have cancel_loading_btn"
        assert hasattr(dialog, "_active_fetch_worker"), "Dialog must track _active_fetch_worker"

        assert not dialog.loading_container.isVisible()

        # Select remote collection to trigger background fetch
        # Index 0 is the remote collection (workspace_collections was empty)
        dialog.collection_combo.setCurrentIndex(0)

        # Immediately after trigger: worker should be active, loading UI visible
        assert dialog._active_fetch_worker is not None, "Background worker must be spawned"
        assert isinstance(dialog._active_fetch_worker, CollectionFetchWorker), (
            "Active worker must be an instance of CollectionFetchWorker"
        )
        assert dialog._active_fetch_worker.isRunning(), (
            "Worker must be running on background thread"
        )
        assert dialog.loading_container.isVisible(), (
            "Loading container must be visible while fetching"
        )
        assert dialog.import_button is not None and not dialog.import_button.isEnabled(), (
            "Import button must be disabled while fetching"
        )
        assert dialog.cancel_loading_btn.isEnabled(), "Cancel button must be enabled during fetch"

        # Bounded wait for worker to complete
        deadline = time.monotonic() + 5.0
        while dialog._active_fetch_worker is not None and time.monotonic() < deadline:
            qapp.processEvents()
            time.sleep(0.02)

        assert not dialog.loading_container.isVisible(), (
            "Loading container must hide on completion"
        )
        assert dialog.vars_table.model().rowCount() == 1
        assert dialog.vars_table.model().data(
            dialog.vars_table.model().index(0, COL_NAME), Qt.ItemDataRole.DisplayRole
        ) == "remote_host"
        assert dialog.import_button.isEnabled(), "Import button must become enabled after fetch"
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


@pytest.mark.timeout(30)
def test_generation_race_protection_discards_stale_responses(qapp: Any) -> None:
    """Verify monotonic request generation counter discards late responses from obsolete fetches."""
    assert hasattr(ImportCollectionVariablesDialog, "__init__"), "Dialog class required"

    env = Environment(name="Dev", variables={})
    col_a = Collection(
        name="ColA",
        variables=[CollectionVariable(name="var_from_a", type="string", default="val_a")],
    )
    col_b = Collection(
        name="ColB",
        variables=[CollectionVariable(name="var_from_b", type="string", default="val_b")],
    )

    mock_service = MagicMock()
    conn_mock = MagicMock()
    conn_mock.stable_id = "conn_1"
    conn_mock.name = "Remote Conn"
    mock_service.list_connections.return_value = [conn_mock]
    mock_service.list_manifest_collections.return_value = [
        {"name": "ColA", "path": "cols/a.json"},
        {"name": "ColB", "path": "cols/b.json"},
    ]

    def delayed_read_collection(conn_id: str, path: str) -> Collection:
        if "a.json" in path:
            time.sleep(0.3)
            return col_a
        time.sleep(0.05)
        return col_b

    mock_service.read_collection.side_effect = delayed_read_collection

    dialog = ImportCollectionVariablesDialog(
        target_environment=env,
        workspace_collections=[],
        library_service=mock_service,
    )
    try:
        assert hasattr(dialog, "_fetch_generation"), (
            "Dialog must track _fetch_generation counter to prevent race conditions"
        )
        assert hasattr(dialog, "cancel_loading_btn"), "Dialog must have cancel_loading_btn"

        # 1. Trigger ColA fetch (generation 1)
        dialog.collection_combo.setCurrentIndex(0)
        gen_1 = dialog._fetch_generation
        assert gen_1 > 0, "Fetch generation must increment on remote request"

        # 2. Before ColA finishes, switch to ColB (generation 2)
        dialog.collection_combo.setCurrentIndex(1)
        gen_2 = dialog._fetch_generation
        assert gen_2 > gen_1, "Fetch generation must increment when switching collections"

        # Bounded wait for both background workers to finish
        deadline = time.monotonic() + 5.0
        while (
            dialog._active_fetch_worker is not None
            or mock_service.read_collection.call_count < 2
        ) and time.monotonic() < deadline:
            qapp.processEvents()
            time.sleep(0.02)

        # Allow any pending Qt events/signals to flush
        for _ in range(5):
            qapp.processEvents()
            time.sleep(0.05)

        # The table must contain ColB variables and NOT ColA variables
        assert dialog.vars_table.model().rowCount() == 1
        var_name = dialog.vars_table.model().data(
            dialog.vars_table.model().index(0, COL_NAME), Qt.ItemDataRole.DisplayRole
        )
        assert var_name == "var_from_b", (
            f"Expected 'var_from_b' from ColB, but found '{var_name}'. "
            "Stale response from ColA was not properly discarded!"
        )

        # 3. Test cancel button discards active fetch
        dialog.collection_combo.setCurrentIndex(0)
        gen_3 = dialog._fetch_generation
        assert gen_3 > gen_2
        assert dialog.loading_container.isVisible()

        # Click cancel
        dialog.cancel_loading_btn.click()
        assert not dialog.loading_container.isVisible(), "Loading container must hide on cancel"
        assert dialog._fetch_generation > gen_3, "Cancelling must increment generation token"

        # Wait out ColA delayed worker
        time.sleep(0.4)
        qapp.processEvents()
        # Stale response must be dropped; table should not be populated with ColA
        assert dialog.vars_table.model().rowCount() == 0 or dialog.vars_table.model().data(
            dialog.vars_table.model().index(0, COL_NAME), Qt.ItemDataRole.DisplayRole
        ) != "var_from_a"
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


@pytest.mark.timeout(30)
def test_non_modal_error_handling_and_retry(qapp: Any) -> None:
    """Verify remote fetch network failures display inline error with retry and keep dialog open."""
    env = Environment(name="Dev", variables={})
    local_col = Collection(
        name="LocalCol",
        variables=[CollectionVariable(name="local_key", type="string", default="local_val")],
    )

    mock_service = MagicMock()
    conn_mock = MagicMock()
    conn_mock.stable_id = "conn_1"
    conn_mock.name = "Remote Conn"
    mock_service.list_connections.return_value = [conn_mock]
    mock_service.list_manifest_collections.return_value = [
        {"name": "FailingRemote", "path": "cols/fail.json"}
    ]

    # Fail on first call with TimeoutError, succeed on subsequent call
    attempt = 0

    def failing_read(conn_id: str, path: str) -> Collection:
        nonlocal attempt
        attempt += 1
        if attempt == 1:
            raise TimeoutError("Remote library connection timed out after 30s")
        return Collection(
            name="RecoveredRemote",
            variables=[
                CollectionVariable(name="recovered_key", type="string", default="recovered_val")
            ],
        )

    mock_service.read_collection.side_effect = failing_read

    dialog = ImportCollectionVariablesDialog(
        target_environment=env,
        workspace_collections=[local_col],
        library_service=mock_service,
    )
    try:
        assert hasattr(dialog, "error_container"), "Dialog must have error_container QWidget"
        assert hasattr(dialog, "error_label"), "Dialog must have error_label QLabel"
        assert hasattr(dialog, "retry_fetch_btn"), "Dialog must have retry_fetch_btn QPushButton"

        assert not dialog.error_container.isVisible(), "Error container must initially be hidden"

        # Index 0: LocalCol, Index 1: FailingRemote
        dialog.collection_combo.setCurrentIndex(1)

        # Wait for worker to fail
        deadline = time.monotonic() + 5.0
        while dialog._active_fetch_worker is not None and time.monotonic() < deadline:
            qapp.processEvents()
            time.sleep(0.02)

        # Dialog must remain open and non-modal error displayed
        assert dialog.isVisible(), "Dialog must remain open when network fetch fails"
        assert not dialog.loading_container.isVisible(), "Loading container must be hidden"
        assert dialog.error_container.isVisible(), "Error container must be visible"
        assert "timed out" in dialog.error_label.text().lower(), (
            f"Error label must describe failure, got: '{dialog.error_label.text()}'"
        )
        assert dialog.retry_fetch_btn.isEnabled(), "Retry button must be enabled"

        # Click retry button
        dialog.retry_fetch_btn.click()

        # Wait for retry to finish
        deadline = time.monotonic() + 5.0
        while dialog._active_fetch_worker is not None and time.monotonic() < deadline:
            qapp.processEvents()
            time.sleep(0.02)

        # After successful retry, error banner must hide and variables load
        assert not dialog.error_container.isVisible(), (
            "Error container must hide after successful retry"
        )
        assert dialog.vars_table.model().rowCount() == 1
        assert dialog.vars_table.model().data(
            dialog.vars_table.model().index(0, COL_NAME), Qt.ItemDataRole.DisplayRole
        ) == "recovered_key"

        # Switching back to local collection clears any error and loads local vars
        dialog.collection_combo.setCurrentIndex(0)
        assert not dialog.error_container.isVisible(), (
            "Switching to local collection must clear error"
        )
        assert dialog.vars_table.model().rowCount() == 1
        assert dialog.vars_table.model().data(
            dialog.vars_table.model().index(0, COL_NAME), Qt.ItemDataRole.DisplayRole
        ) == "local_key"
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


@pytest.mark.timeout(30)
def test_bulk_strategy_and_summary_virtualized_performance(qapp: Any) -> None:
    """Verify bulk collision strategy actions and summary updates execute swiftly on model."""
    env_vars = {f"k_{i}": f"v_{i}" for i in range(1000)}
    env = Environment(name="Dev", variables=env_vars)

    col_vars = [
        CollectionVariable(name=f"k_{i}", type="string", default=f"col_v_{i}")
        for i in range(1000)
    ]
    col = Collection(name="Collisions1000", variables=col_vars)

    dialog = ImportCollectionVariablesDialog(
        target_environment=env,
        workspace_collections=[col],
    )
    try:
        # Initial summary: 0 new, 0 overwrite, 1000 keep
        summary_text = dialog.summary_label.text().lower()
        assert "1000 existing to keep" in summary_text
        assert "0 existing to overwrite" in summary_text

        # Bulk overwrite performance: should take < 100ms
        t0 = time.monotonic()
        dialog.bulk_overwrite_btn.click()
        elapsed = time.monotonic() - t0
        assert elapsed < 0.25, f"Bulk overwrite took too long: {elapsed:.3f}s (must be < 250ms)"

        summary_text_over = dialog.summary_label.text().lower()
        assert "1000 existing to overwrite" in summary_text_over
        assert "0 existing to keep" in summary_text_over
        assert dialog.get_row_strategy(0) == ConflictStrategy.OVERWRITE
        assert dialog.get_row_strategy(999) == ConflictStrategy.OVERWRITE

        # Bulk keep current performance: should take < 100ms
        t1 = time.monotonic()
        dialog.bulk_keep_current_btn.click()
        elapsed_keep = time.monotonic() - t1
        assert elapsed_keep < 0.25, f"Bulk keep current took too long: {elapsed_keep:.3f}s"

        summary_text_keep = dialog.summary_label.text().lower()
        assert "1000 existing to keep" in summary_text_keep
        assert "0 existing to overwrite" in summary_text_keep
        assert dialog.get_row_strategy(0) == ConflictStrategy.SKIP
        assert dialog.get_row_strategy(999) == ConflictStrategy.SKIP
    finally:
        dialog.close()


@pytest.mark.timeout(30)
def test_backward_compatibility_table_facade(qapp: Any) -> None:
    """Verify CollectionVariablesTableView backward-compatible API preserves existing callers."""
    env = Environment(
        name="Dev",
        variables={"host": "localhost:8000"},
        hidden_keys=set(),
    )
    col = Collection(
        name="API",
        variables=[
            CollectionVariable(name="host", type="string", default="api.example.com"),
            CollectionVariable(name="timeout", type="integer", default=30),
        ],
    )

    dialog = ImportCollectionVariablesDialog(
        target_environment=env,
        workspace_collections=[col],
    )
    try:
        CollectionVariablesTableView = getattr(
            dialog_module, "CollectionVariablesTableView", None
        )
        assert CollectionVariablesTableView is not None, (
            "CollectionVariablesTableView (QTableView) must be implemented"
        )
        assert isinstance(dialog.vars_table, CollectionVariablesTableView), (
            "vars_table must be an instance of CollectionVariablesTableView"
        )

        # Table geometry & headers
        assert dialog.vars_table.columnCount() == 9
        assert dialog.vars_table.rowCount() == 2
        headers = [
            dialog.vars_table.horizontalHeaderItem(c).text()
            for c in range(dialog.vars_table.columnCount())
        ]
        assert headers == [
            "",
            "Name",
            "Current Value",
            "Candidate Value",
            "Conflict Strategy",
            "Type",
            "Secret",
            "Status",
            "Description",
        ]

        # Table item proxy API (.item(row, col).text())
        assert dialog.vars_table.item(0, COL_NAME).text() == "host"
        assert dialog.vars_table.item(0, COL_CURRENT_VALUE).text() == "localhost:8000"
        assert dialog.vars_table.item(0, COL_CANDIDATE_VALUE).text() == "api.example.com"
        assert dialog.vars_table.item(0, COL_STATUS).text() == "Exists (Collision)"

        assert dialog.vars_table.item(1, COL_NAME).text() == "timeout"
        assert dialog.vars_table.item(1, COL_CURRENT_VALUE).text() == "—"
        assert dialog.vars_table.item(1, COL_CANDIDATE_VALUE).text() == "30"
        assert dialog.vars_table.item(1, COL_STATUS).text() == "New"

        # Checkbox checkState proxy API
        assert dialog.vars_table.item(0, COL_SELECT).checkState() == Qt.CheckState.Checked

        # cellWidget proxy for strategy column
        combo_keep = dialog.vars_table.cellWidget(0, COL_STRATEGY)
        assert combo_keep is not None, "Colliding row must return strategy widget proxy"
        assert getattr(combo_keep, "currentText", lambda: "")() == "Keep Current"

        # Non-colliding row has no strategy widget
        assert dialog.vars_table.cellWidget(1, COL_STRATEGY) is None
        assert dialog.vars_table.item(1, COL_STRATEGY).text() == "—"

        # Dialog helper methods
        dialog.set_row_strategy(0, ConflictStrategy.OVERWRITE)
        assert dialog.get_row_strategy(0) == ConflictStrategy.OVERWRITE
        strategies = dialog.get_variable_conflict_strategies()
        assert strategies == {"host": ConflictStrategy.OVERWRITE}

        # Deselect and select all
        dialog.deselect_all()
        assert not dialog.is_row_selected(0)
        assert not dialog.is_row_selected(1)
        dialog.select_all()
        assert dialog.is_row_selected(0)
        assert dialog.is_row_selected(1)

        # Import execution
        dialog.accept()
        assert env.variables["host"] == "api.example.com"
        assert env.variables["timeout"] == "30"
    finally:
        dialog.close()
