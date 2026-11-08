"""PYPOST-1457: Slow-drip / delayed-success remote read characterization repro suite.

Tests characterize and verify the following contracts for high-latency remote collection reads:
1. Loading chrome remains visible, actions stay disabled, and error banner is suppressed mid-drip.
2. Delayed-success read eventually populates variables table and presets matching schema accurately.
3. Mid-stream user cancellation cooperatively aborts worker promptly (< 0.5s) without false errors.
4. Selection change mid-drip supersedes active worker, discarding stale late completions cleanly.
5. Dialog dismissal or rejection mid-drip cleanly cancels and joins workers without thread leaks.
6. Delayed-success read of zero variables displays clean empty state without errors.
7. Background slicing delay maintains smooth Qt UI thread responsiveness (< 50ms latency).
8. Caplog contracts verify logging for started, completed, cancelled, and stale discarded.
"""
from __future__ import annotations

import logging
import time
from typing import Any
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt

from pypost.models.collection_variable import CollectionVariable
from pypost.models.models import Collection, Environment
from pypost.ui.dialogs.import_collection_variables_dialog import (
    ImportCollectionVariablesDialog,
)
from pypost.ui.models.collection_variables_table_model import (
    COL_CANDIDATE_VALUE,
    COL_NAME,
    COL_SECRET,
    COL_TYPE,
    HIDDEN_MASK,
)
from tests.helpers.remote_collection_faults import (
    SlowDripSimulator,
    build_library_service,
    slow_drip_collection_side_effect,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.timeout(30)]

ABORT_ELAPSED_LIMIT_S = 0.5
MAX_EVENT_LOOP_LATENCY_S = 0.05
DIALOG_LOGGER = "pypost.ui.dialogs.import_collection_variables_dialog"


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


def _open_dialog(
    qapp: Any,
    mock_service: MagicMock,
    workspace_collections: list[Collection] | None = None,
    target_env: Environment | None = None,
) -> ImportCollectionVariablesDialog:
    env = target_env or Environment(name="Dev", variables={})
    local_cols = (
        workspace_collections
        if workspace_collections is not None
        else [
            Collection(
                name="LocalCol",
                variables=[CollectionVariable(name="local_key", default="local_val")],
            )
        ]
    )
    dialog = ImportCollectionVariablesDialog(
        target_environment=env,
        workspace_collections=local_cols,
        library_service=mock_service,
    )
    dialog.show()
    qapp.processEvents()
    return dialog


def test_slow_drip_loading_chrome_and_suppressed_error(qapp: Any) -> None:
    """Loading chrome must stay visible, controls disabled, and errors suppressed mid-drip."""
    sim = slow_drip_collection_side_effect(total_delay_s=0.35, slice_interval_s=0.02)
    service = build_library_service(read_side_effect=sim)
    dialog = _open_dialog(qapp, service)

    try:
        _wait_for_manifest_discovery(dialog, qapp)
        assert not dialog.loading_container.isVisible()
        assert not dialog.error_container.isVisible()

        # Select remote library collection (index 1)
        dialog.collection_combo.setCurrentIndex(1)

        # Wait for worker to enter simulator
        entered = sim.entered.wait(timeout=2.0)
        assert entered, "Slow-drip read worker must enter simulator"
        qapp.processEvents()

        # Assert in-flight invariants while dripping
        if dialog._active_fetch_worker is not None and not sim.completed.is_set():
            assert dialog.loading_container.isVisible(), "Loading chrome must be visible in-flight"
            assert "loading" in dialog.loading_label.text().lower()
            assert dialog.cancel_loading_btn.isEnabled(), "Cancel button must be enabled"
            assert not dialog.error_container.isVisible(), "Error container must remain suppressed"
            assert not dialog.preset_combo.isEnabled(), "Preset combo must be disabled mid-drip"
            assert not dialog.vars_table.isEnabled(), "Vars table must be disabled mid-drip"
            if dialog.import_button is not None:
                assert not dialog.import_button.isEnabled(), "Import button must stay disabled"
            assert dialog.vars_table.model().rowCount() == 0, "No partial rows during slow drip"

        _wait_for_fetch_idle(dialog, qapp)

        # Eventual clean state
        assert not dialog.loading_container.isVisible(), "Loading chrome must hide on completion"
        assert not dialog.error_container.isVisible(), "Error banner must remain hidden on success"
        assert dialog.preset_combo.isEnabled(), "Preset combo must be re-enabled on completion"
        assert dialog.vars_table.isEnabled(), "Vars table must be re-enabled on completion"
        assert dialog.vars_table.model().rowCount() > 0, "Table must populate with variables"
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


def test_slow_drip_eventual_population_matches_schema(qapp: Any) -> None:
    """Delayed-success read must populate variables table and presets matching schema."""
    remote_col = Collection(
        name="SlowRemote",
        variables=[
            CollectionVariable(
                name="api_host",
                type="string",
                default="https://api.example.com",
                description="Endpoint host",
            ),
            CollectionVariable(
                name="api_token",
                type="string",
                default="secret_token",
                secret=True,
                description="Auth token",
            ),
            CollectionVariable(
                name="timeout_sec",
                type="number",
                default=30,
                description="Timeout in seconds",
            ),
        ],
        presets={"Staging": {"api_host": "https://staging.example.com"}},
    )
    sim = slow_drip_collection_side_effect(
        collection=remote_col,
        total_delay_s=0.25,
        slice_interval_s=0.02,
    )
    service = build_library_service(read_side_effect=sim)
    dialog = _open_dialog(qapp, service)

    try:
        _wait_for_manifest_discovery(dialog, qapp)
        dialog.collection_combo.setCurrentIndex(1)
        _wait_for_fetch_idle(dialog, qapp)

        assert not dialog.loading_container.isVisible()
        assert not dialog.error_container.isVisible()

        model = dialog.vars_table.model()
        assert model.rowCount() == 3, "Table must contain all 3 remote variables"

        # Check variable names in table
        names = [
            model.data(model.index(r, COL_NAME), Qt.ItemDataRole.DisplayRole)
            for r in range(3)
        ]
        assert names == ["api_host", "api_token", "timeout_sec"]

        # Check types
        types = [
            model.data(model.index(r, COL_TYPE), Qt.ItemDataRole.DisplayRole)
            for r in range(3)
        ]
        assert types == ["string", "string", "number"]

        # Check candidate values (secret variables are masked with HIDDEN_MASK for display)
        candidates = [
            model.data(model.index(r, COL_CANDIDATE_VALUE), Qt.ItemDataRole.DisplayRole)
            for r in range(3)
        ]
        assert candidates == ["https://api.example.com", HIDDEN_MASK, "30"]

        # Check raw unmasked candidate value in model record
        secret_rec = model._ensure_record(1)
        assert secret_rec is not None
        assert secret_rec.raw_candidate == "secret_token"

        # Check secret flag
        secret_flags = [
            model.data(model.index(r, COL_SECRET), Qt.ItemDataRole.DisplayRole)
            for r in range(3)
        ]
        assert secret_flags == ["No", "Yes", "No"]

        # Check presets populated in preset_combo
        presets = [dialog.preset_combo.itemText(i) for i in range(dialog.preset_combo.count())]
        assert "(Base Defaults)" in presets
        assert "Staging" in presets

        if dialog.import_button is not None:
            assert dialog.import_button.isEnabled(), "Import button must be enabled when vars exist"
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


def test_slow_drip_mid_stream_cancellation_cooperative_abort(qapp: Any) -> None:
    """Mid-stream user cancellation must abort cooperatively and promptly without errors."""
    sim = SlowDripSimulator(total_delay_s=2.0, slice_interval_s=0.02)
    service = build_library_service(read_side_effect=sim)
    dialog = _open_dialog(qapp, service)

    try:
        _wait_for_manifest_discovery(dialog, qapp)
        dialog.collection_combo.setCurrentIndex(1)

        assert sim.entered.wait(timeout=2.0), "Worker must begin slow drip before cancel"
        time.sleep(0.04)
        qapp.processEvents()

        gen_before = dialog._fetch_generation
        t0 = time.monotonic()
        dialog.cancel_loading_btn.click()
        qapp.processEvents()

        # Wait for worker teardown after abort
        _wait_for_fetch_idle(dialog, qapp, timeout_s=1.0)
        elapsed = time.monotonic() - t0

        assert elapsed < ABORT_ELAPSED_LIMIT_S, (
            f"Cancel must abort cooperatively within {ABORT_ELAPSED_LIMIT_S}s, "
            f"elapsed={elapsed:.3f}s"
        )
        assert sim.cancelled.is_set(), "Cancellation token must trigger simulator abort"
        assert dialog._fetch_generation > gen_before, "Fetch generation must increment on cancel"
        assert not dialog.loading_container.isVisible(), "Loading chrome must hide after cancel"
        assert not dialog.error_container.isVisible(), "Cancelled fetch must not show error banner"
        assert dialog.vars_table.model().rowCount() == 0, "Cancelled fetch must leave table empty"
        assert dialog._active_fetch_worker is None, "Active fetch worker must be cleared"
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


def test_slow_drip_supersession_on_collection_change(qapp: Any) -> None:
    """Switching collection mid-drip must supersede worker and discard late completion."""
    col_a = Collection(
        name="RemoteA",
        variables=[CollectionVariable(name="var_from_a", default="val_a")],
    )
    col_b = Collection(
        name="RemoteB",
        variables=[CollectionVariable(name="var_from_b", default="val_b")],
    )

    sim_a = SlowDripSimulator(collection=col_a, total_delay_s=0.4, slice_interval_s=0.02)
    sim_b = SlowDripSimulator(collection=col_b, total_delay_s=0.05, slice_interval_s=0.02)

    def _read_router(connection_id: str, collection_path: str, **kwargs: Any) -> Collection:
        if "a.json" in collection_path:
            return sim_a(connection_id, collection_path, **kwargs)
        if "b.json" in collection_path:
            return sim_b(connection_id, collection_path, **kwargs)
        raise ValueError(f"Unknown path {collection_path}")

    service = build_library_service(
        manifest_collections=[
            {"name": "RemoteA", "path": "cols/a.json"},
            {"name": "RemoteB", "path": "cols/b.json"},
        ],
        read_side_effect=_read_router,
    )
    dialog = _open_dialog(qapp, service)

    try:
        _wait_for_manifest_discovery(dialog, qapp)

        # Select RemoteA (Index 1)
        dialog.collection_combo.setCurrentIndex(1)
        assert sim_a.entered.wait(timeout=2.0), "RemoteA must start dripping"
        time.sleep(0.04)
        qapp.processEvents()

        # Switch to RemoteB (Index 2) while RemoteA is in flight
        dialog.collection_combo.setCurrentIndex(2)
        qapp.processEvents()

        # Wait for all workers to settle
        _wait_for_fetch_idle(dialog, qapp)
        for _ in range(10):
            qapp.processEvents()
            time.sleep(0.01)

        assert not dialog.error_container.isVisible(), "Supersession must not trigger error banner"
        assert not dialog.loading_container.isVisible(), "Loading chrome must hide"

        # Table must display RemoteB variables, RemoteA must be cleanly discarded
        model = dialog.vars_table.model()
        assert model.rowCount() == 1, "Only RemoteB variable must be present"
        var_name = model.data(model.index(0, COL_NAME), Qt.ItemDataRole.DisplayRole)
        assert var_name == "var_from_b", f"Expected 'var_from_b', got '{var_name}'"
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


def test_slow_drip_dialog_close_clean_teardown(qapp: Any) -> None:
    """Closing or rejecting dialog mid-drip must cancel and join worker cleanly."""
    sim = SlowDripSimulator(total_delay_s=2.0, slice_interval_s=0.02)
    service = build_library_service(read_side_effect=sim)
    dialog = _open_dialog(qapp, service)

    try:
        _wait_for_manifest_discovery(dialog, qapp)
        dialog.collection_combo.setCurrentIndex(1)

        assert sim.entered.wait(timeout=2.0), "Worker must begin dripping before close"
        time.sleep(0.04)
        qapp.processEvents()

        worker = dialog._active_fetch_worker
        assert worker is not None, "Worker must be active mid-drip"
        assert worker.isRunning(), "Worker thread must be running"

        t0 = time.monotonic()
        dialog.reject()
        qapp.processEvents()

        assert sim.cancelled.is_set(), "Worker must receive cancellation signal on dialog reject"
        assert dialog._active_fetch_worker is None, "Worker reference must be cleared"
        assert worker.isFinished(), "Worker thread must be finished within teardown"
        elapsed = time.monotonic() - t0
        assert elapsed < 1.0, f"Dialog reject teardown must be fast, elapsed={elapsed:.3f}s"
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


def test_slow_drip_zero_variables_clean_empty_state(qapp: Any) -> None:
    """Delayed-success read with 0 variables must display clean empty state."""
    empty_col = Collection(name="EmptyRemote", variables=[])
    sim = slow_drip_collection_side_effect(collection=empty_col, total_delay_s=0.2)
    service = build_library_service(read_side_effect=sim)
    dialog = _open_dialog(qapp, service)

    try:
        _wait_for_manifest_discovery(dialog, qapp)
        dialog.collection_combo.setCurrentIndex(1)
        _wait_for_fetch_idle(dialog, qapp)

        assert not dialog.loading_container.isVisible(), "Loading chrome must hide"
        assert not dialog.error_container.isVisible(), "Error banner must not show for empty vars"
        assert dialog.vars_table.model().rowCount() == 0, "Table must have 0 rows"
        if dialog.import_button is not None:
            assert not dialog.import_button.isEnabled(), "Import button must be disabled for 0 vars"
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


def test_slow_drip_ui_event_loop_responsiveness(qapp: Any) -> None:
    """Qt event loop must remain responsive (< 50ms latency) during background slow-drip."""
    sim = SlowDripSimulator(total_delay_s=0.35, slice_interval_s=0.02)
    service = build_library_service(read_side_effect=sim)
    dialog = _open_dialog(qapp, service)

    try:
        _wait_for_manifest_discovery(dialog, qapp)
        dialog.collection_combo.setCurrentIndex(1)

        assert sim.entered.wait(timeout=2.0), "Worker must begin slow drip"

        max_latency = 0.0
        iterations = 0
        while dialog._active_fetch_worker is not None and not sim.completed.is_set():
            t0 = time.monotonic()
            qapp.processEvents()
            latency = time.monotonic() - t0
            if latency > max_latency:
                max_latency = latency
            iterations += 1
            time.sleep(0.01)

        _wait_for_fetch_idle(dialog, qapp)
        assert iterations >= 5, f"Must have exercised multiple loop iterations, got {iterations}"
        assert max_latency < MAX_EVENT_LOOP_LATENCY_S, (
            f"Event loop latency exceeded 50ms threshold: max_latency={max_latency * 1000:.2f}ms"
        )
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


def test_slow_drip_observability_completion_contract(
    qapp: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """Delayed-success read logs structured started and completed events at INFO level."""
    remote_col = Collection(
        name="ObsCol",
        variables=[CollectionVariable(name="k1", default="v1")],
    )
    sim = slow_drip_collection_side_effect(
        collection=remote_col,
        total_delay_s=0.2,
        slice_interval_s=0.02,
    )
    service = build_library_service(read_side_effect=sim)
    dialog = _open_dialog(qapp, service)

    try:
        _wait_for_manifest_discovery(dialog, qapp)
        caplog.clear()

        with caplog.at_level(logging.INFO, logger=DIALOG_LOGGER):
            dialog.collection_combo.setCurrentIndex(1)
            _wait_for_fetch_idle(dialog, qapp)

        started_records = [
            r for r in caplog.records
            if "collection_variable_remote_fetch_started" in r.message
        ]
        assert len(started_records) == 1, "Must log exactly one fetch started event"
        start_rec = started_records[0]
        assert start_rec.levelno == logging.INFO
        assert "gen=1" in start_rec.message
        assert "connection_id=conn_1" in start_rec.message
        assert "path=cols/faulty.json" in start_rec.message

        completed_records = [
            r for r in caplog.records
            if "collection_variable_remote_fetch_completed" in r.message
        ]
        assert len(completed_records) == 1, "Must log exactly one fetch completed event"
        comp_rec = completed_records[0]
        assert comp_rec.levelno == logging.INFO
        assert "gen=1" in comp_rec.message
        assert "collection_name=ObsCol" in comp_rec.message
        assert "vars_count=1" in comp_rec.message

        # Verify no failure or cancel logs occurred
        err_records = [
            r for r in caplog.records
            if "collection_variable_remote_fetch_failed" in r.message
        ]
        assert len(err_records) == 0, "No fetch failed events on successful slow drip"
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


def test_slow_drip_observability_cancellation_contract(
    qapp: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """Mid-drip cancellation logs cancelled event at INFO level without failure errors."""
    sim = SlowDripSimulator(total_delay_s=2.0, slice_interval_s=0.02)
    service = build_library_service(read_side_effect=sim)
    dialog = _open_dialog(qapp, service)

    try:
        _wait_for_manifest_discovery(dialog, qapp)
        caplog.clear()

        with caplog.at_level(logging.INFO, logger=DIALOG_LOGGER):
            dialog.collection_combo.setCurrentIndex(1)
            assert sim.entered.wait(timeout=2.0), "Worker must begin dripping before cancel"
            time.sleep(0.04)
            qapp.processEvents()

            dialog.cancel_loading_btn.click()
            _wait_for_fetch_idle(dialog, qapp, timeout_s=1.0)

        started_records = [
            r for r in caplog.records
            if "collection_variable_remote_fetch_started" in r.message
        ]
        assert len(started_records) == 1, "Must log fetch started event"
        assert started_records[0].levelno == logging.INFO
        assert "gen=1" in started_records[0].message

        cancelled_records = [
            r for r in caplog.records
            if "collection_variable_remote_fetch_cancelled" in r.message
        ]
        assert len(cancelled_records) == 1, "Must log fetch cancelled event"
        cancel_rec = cancelled_records[0]
        assert cancel_rec.levelno == logging.INFO
        assert "gen=1" in cancel_rec.message

        # Contract: No fetch completed or fetch failed events on cancellation
        comp_records = [
            r for r in caplog.records
            if "collection_variable_remote_fetch_completed" in r.message
        ]
        assert len(comp_records) == 0, "Cancelled drip must not emit fetch completed log"

        err_records = [
            r for r in caplog.records
            if "collection_variable_remote_fetch_failed" in r.message
        ]
        assert len(err_records) == 0, "Cancelled drip must not emit fetch failed log"
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()


def test_slow_drip_observability_supersession_discard_contract(
    qapp: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """Superseded slow-drip completion emits stale discarded warning log."""
    col_a = Collection(
        name="StaleA",
        variables=[CollectionVariable(name="k_a", default="val_a")],
    )
    col_b = Collection(
        name="FreshB",
        variables=[CollectionVariable(name="k_b", default="val_b")],
    )

    sim_b = slow_drip_collection_side_effect(
        collection=col_b,
        total_delay_s=0.05,
        slice_interval_s=0.01,
    )
    service = build_library_service(
        manifest_collections=[
            {"name": "ColA", "path": "cols/a.json"},
            {"name": "ColB", "path": "cols/b.json"},
        ],
        read_side_effect=sim_b,
    )
    dialog = _open_dialog(qapp, service)

    try:
        _wait_for_manifest_discovery(dialog, qapp)
        caplog.clear()

        with caplog.at_level(logging.DEBUG, logger=DIALOG_LOGGER):
            # Select ColB (Index 2) -> generation 1
            dialog.collection_combo.setCurrentIndex(2)
            _wait_for_fetch_idle(dialog, qapp)
            assert dialog._fetch_generation == 1

            # Bump generation (simulate user action or supersession)
            dialog._fetch_generation = 2

            # Deliver stale completion for generation 1
            dialog._on_fetch_completed(col_a, gen=1)
            qapp.processEvents()

        # Contract: Verify warning log for stale discard
        stale_records = [
            r for r in caplog.records
            if "collection_variable_remote_fetch_stale_discarded" in r.message
        ]
        assert len(stale_records) == 1, "Must log stale discarded event"
        stale_rec = stale_records[0]
        assert stale_rec.levelno == logging.WARNING
        assert "gen=1" in stale_rec.message
        assert "current_gen=2" in stale_rec.message

        # Verify dialog view was NOT overwritten by stale collection
        assert dialog._model._collection == col_b
        model = dialog.vars_table.model()
        assert model.rowCount() == 1
        var_name = model.data(model.index(0, COL_NAME), Qt.ItemDataRole.DisplayRole)
        assert var_name == "k_b"
    finally:
        if getattr(dialog, "_active_fetch_worker", None) is not None:
            dialog._active_fetch_worker.cancel()
            dialog._active_fetch_worker.wait(1000)
        dialog.close()
