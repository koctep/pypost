"""PYPOST-1256 regression tests for the common presenter teardown contract.

The suite exercises public owner APIs and public dependency seams only.  The
controlled gates make asynchronous lifecycle outcomes deterministic.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QObject, QTimer, Qt, Signal
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QListWidget

from pypost.core.history_manager import HistoryManager
from pypost.core.qt.environment_storage_gateway import EnvironmentStorageGateway
from pypost.models.models import Environment, HistoryEntry, RequestData
from pypost.models.response import ResponseData
from pypost.models.settings import AppSettings
from pypost.ui.presenters.env_presenter import EnvPresenter
from pypost.ui.presenters.tabs_presenter import RequestTab, TabsPresenter
from pypost.ui.widgets.history_panel import HistoryPanel
from tests.helpers.process_until import process_until

pytestmark = pytest.mark.timeout(60)


class _ReleaseStopGate(threading.Event):
    """Test-controlled release gate that settles only after stop was requested."""

    def __init__(self, settle: Callable[[], None]) -> None:
        super().__init__()
        self._settle = settle

    def set(self) -> None:
        super().set()
        self._settle()


class _RequestWorkerDouble(QObject):
    """Public worker-shaped fake installed at the request construction seam."""

    request_finished = Signal(object)
    error = Signal(object)
    env_update = Signal(dict)
    script_output = Signal(list, object)
    chunk_received = Signal(str)
    headers_received = Signal(int, dict)
    retry_attempt = Signal(int, int, object)
    finished = Signal()

    def __init__(self, *, gate_wait: bool = False) -> None:
        super().__init__()
        self.started = threading.Event()
        self.stop_entered = threading.Event()
        self.settled = threading.Event()
        self._running = True
        self.release_stop = _ReleaseStopGate(self._settle_if_released)
        if not gate_wait:
            self.release_stop.set()
        self.stop_calls = 0

    def start(self) -> None:
        self.started.set()

    def isRunning(self) -> bool:
        return self._running

    def stop(self) -> None:
        self.stop_calls += 1
        # Cancellation is only a request.  The separate public release gate
        # represents the worker reaching its terminal state after teardown has
        # entered the cancellation/drain path.
        self.stop_entered.set()
        self._settle_if_released()

    def wait(self, timeout_ms: int) -> bool:
        return self.settled.is_set()

    def _settle_if_released(self) -> None:
        if self.stop_entered.is_set() and self.release_stop.is_set():
            self._running = False
            self.settled.set()


class _EventProbe(QObject):
    """One explicit GUI event used to drain queued callbacks deterministically."""

    fired = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.seen = False
        self.fired.connect(self._mark_seen)

    def fire(self) -> None:
        self.fired.emit()

    def _mark_seen(self) -> None:
        self.seen = True


class _EnvironmentStorageDouble:
    """Storage-interface fake with explicit load/save gates and public observations."""

    def __init__(
        self,
        environments: list[Environment],
        *,
        gate_load: bool = False,
        gate_save: bool = False,
        fail_load: bool = False,
        fail_save: bool = False,
    ) -> None:
        self.environments = [env.model_copy(deep=True) for env in environments]
        self.gate_load = gate_load
        self.gate_save = gate_save
        self.fail_load = fail_load
        self.fail_save = fail_save
        self.load_started = threading.Event()
        self.save_started = threading.Event()
        self.release_load = threading.Event()
        self.release_save = threading.Event()
        if not gate_load:
            self.release_load.set()
        if not gate_save:
            self.release_save.set()
        self.operations: list[str] = []
        self.saved: list[list[Environment]] = []

    def load_environments(self) -> list[Environment]:
        self.operations.append("load")
        self.load_started.set()
        self.release_load.wait(timeout=5)
        if self.fail_load:
            raise OSError("controlled load failure")
        return [env.model_copy(deep=True) for env in self.environments]

    def save_environments(self, environments: list[Environment]) -> None:
        self.operations.append("save")
        self.save_started.set()
        self.release_save.wait(timeout=5)
        if self.fail_save:
            raise OSError("controlled save failure")
        self.saved.append([env.model_copy(deep=True) for env in environments])

    def serialize_environment_records(
        self,
        environments: list[Environment],
        *,
        target_envelope_version: int | None = None,
    ) -> list[dict]:
        return [environment.model_dump(mode="json") for environment in environments]


@dataclass(frozen=True)
class _TeardownResultDouble:
    """Small public-result-shaped value used by the composition-root harness."""

    owner: str
    outcome: str
    elapsed_ms: int = 0
    active_count: int = 0
    pending_count: int = 0
    failure_kind: str | None = None
    dispositions: dict[int, str] | None = None


@dataclass
class _SharedDeadlineDouble:
    """Deterministic remaining-budget ledger for composition-root assertions."""

    remaining_ms: int


class _CompositionOwnerDouble:
    """Public owner double recording ordering and propagated teardown budgets."""

    def __init__(
        self,
        name: str,
        calls: list[str],
        result: _TeardownResultDouble,
        *,
        budget: _SharedDeadlineDouble | None = None,
        consume_ms: int = 0,
    ) -> None:
        self.name = name
        self.calls = calls
        self.result = result
        self.budget = budget
        self.consume_ms = consume_ms
        self.timeouts: list[int | None] = []

    def teardown(self, timeout_ms: int | None = None) -> _TeardownResultDouble:
        self.timeouts.append(timeout_ms)
        self.calls.append(self.name)
        if self.budget is not None:
            assert isinstance(timeout_ms, int)
            assert 0 <= timeout_ms <= self.budget.remaining_ms
            self.budget.remaining_ms -= self.consume_ms
        return self.result


class _CompositionRootHarness:
    """Local harness invoking MainWindow's real public composition-root seam."""

    def __init__(
        self,
        tabs: _CompositionOwnerDouble,
        history_panel: _CompositionOwnerDouble,
        history_manager: _CompositionOwnerDouble,
        env: _CompositionOwnerDouble,
    ) -> None:
        from pypost.ui.main_window import MainWindow

        self._main_window_type = MainWindow
        self.tabs = tabs
        self.history_panel = history_panel
        self.history_manager = history_manager
        self.env = env

    def teardown(self, timeout_ms: int) -> _TeardownResultDouble:
        return self._main_window_type.teardown(self, timeout_ms=timeout_ms)


class _PublicEnvironmentHandoffProbe(QObject):
    """Passive observer for the public tab-to-environment signal."""

    def __init__(self) -> None:
        super().__init__()
        self.payloads: list[dict] = []

    def observe(self, payload: dict) -> None:
        self.payloads.append(dict(payload))


class _HistoryRefreshBridge(QObject):
    """Controlled signal bridge for the asynchronous history completion callback."""

    refresh_requested = Signal()
    refresh_delivered = Signal()


def _composition_result(
    owner: str,
    outcome: str = "success",
    *,
    failure_kind: str | None = None,
) -> _TeardownResultDouble:
    return _TeardownResultDouble(
        owner=owner,
        outcome=outcome,
        failure_kind=failure_kind,
    )


def _make_composition_root(
    *,
    calls: list[str],
    budget: _SharedDeadlineDouble | None = None,
    env_result: _TeardownResultDouble | None = None,
) -> tuple[_CompositionRootHarness, list[_CompositionOwnerDouble]]:
    owners = [
        _CompositionOwnerDouble(
            "tabs",
            calls,
            _composition_result("tabs"),
            budget=budget,
            consume_ms=10,
        ),
        _CompositionOwnerDouble(
            "history_panel",
            calls,
            _composition_result("history_panel"),
            budget=budget,
            consume_ms=10,
        ),
        _CompositionOwnerDouble(
            "history_manager",
            calls,
            _composition_result("history_manager"),
            budget=budget,
            consume_ms=10,
        ),
        _CompositionOwnerDouble(
            "env",
            calls,
            env_result or _composition_result("env"),
            budget=budget,
            consume_ms=10,
        ),
    ]
    return _CompositionRootHarness(*owners), owners


def _make_request(request_id: str) -> RequestData:
    return RequestData(
        id=request_id,
        name=request_id,
        method="GET",
        url=f"https://{request_id}.example.test",
    )


def _make_history_entry(entry_id: str, *, url: str | None = None) -> HistoryEntry:
    return HistoryEntry(
        id=entry_id,
        timestamp="2026-01-01T00:00:00Z",
        method="POST",
        url=url or f"https://{entry_id}.example.test",
        headers={"Content-Type": "application/json"},
        body=entry_id,
        status_code=201,
        response_time_ms=2,
    )


def _make_tabs_presenter() -> TabsPresenter:
    request_manager = MagicMock()
    request_manager.find_request.return_value = None
    state_manager = MagicMock()
    state_manager.get_open_tabs.return_value = []
    return TabsPresenter(
        request_manager,
        state_manager,
        AppSettings(),
        metrics=MagicMock(),
        protocol_picker=lambda *_args, **_kwargs: None,
    )


def _make_env_presenter(storage: _EnvironmentStorageDouble) -> EnvPresenter:
    return EnvPresenter(
        storage,
        MagicMock(),
        MagicMock(),
        AppSettings(env_encryption_enabled=True),
        lambda: [],
        MagicMock(),
    )


def _assert_result(result: object) -> None:
    assert result.outcome in {"success", "incomplete", "failed"}
    assert result.elapsed_ms >= 0
    assert result.active_count >= 0
    assert result.pending_count >= 0


def _drain_one_gui_turn() -> None:
    probe = _EventProbe()
    QTimer.singleShot(0, probe.fire)
    process_until(lambda: probe.seen, timeout_ms=5_000)


def _teardown_while_releasing_save_gate(
    manager: HistoryManager,
    release_save: threading.Event,
) -> object:
    """Release a save only after teardown enters the public drain primitive."""
    drain_entered = threading.Event()
    results: list[object] = []
    errors: list[BaseException] = []
    original_flush = manager.flush

    def observed_flush(*args, **kwargs):
        drain_entered.set()
        return original_flush(*args, **kwargs)

    def run_teardown() -> None:
        try:
            results.append(manager.teardown(timeout_ms=100))
        except BaseException as exc:  # pragma: no cover - exposes missing contract
            errors.append(exc)

    with patch.object(manager, "flush", side_effect=observed_flush):
        thread = threading.Thread(target=run_teardown)
        thread.start()
        try:
            assert drain_entered.wait(timeout=5) or errors, (
                "teardown must enter the public history drain path before the save gate is released"
            )
            if errors:
                raise errors[0]
        finally:
            release_save.set()
            thread.join(timeout=5)

    assert not thread.is_alive()
    assert errors == []
    assert len(results) == 1
    return results[0]


def _load_presenter_environment(
    presenter: EnvPresenter,
    storage: _EnvironmentStorageDouble,
) -> None:
    loaded = QSignalSpy(presenter.environments_loaded)
    presenter.load_environments()
    process_until(
        lambda: loaded.count() == 1,
        timeout_ms=5_000,
    )
    assert storage.operations == ["load"]
    presenter.select_environment_index(1)


def test_request_teardown_cancels_all_tabs_and_fences_late_signals(qapp):
    """Every open request tab is cancelled once and ignores all late outcomes."""
    presenter = _make_tabs_presenter()
    presenter.add_new_tab(_make_request("first"), save_state=False)
    presenter.add_new_tab(_make_request("second"), save_state=False)
    first_tab = presenter.widget.widget(0)
    second_tab = presenter.widget.widget(1)
    assert isinstance(first_tab, RequestTab)
    assert isinstance(second_tab, RequestTab)

    workers = [
        _RequestWorkerDouble(gate_wait=True),
        _RequestWorkerDouble(gate_wait=True),
    ]
    with patch(
        "pypost.ui.presenters.tabs_presenter.RequestWorker",
        side_effect=workers,
    ):
        first_tab.request_editor.send_requested.emit(_make_request("first"))
        second_tab.request_editor.send_requested.emit(_make_request("second"))

    assert all(worker.started.is_set() for worker in workers)
    tabs = [first_tab, second_tab]
    original_views = [
        (
            tab.response_view.body_view.toPlainText(),
            tab.response_view.status_label.text(),
            tab.request_editor.send_btn.text(),
            tab.request_editor.send_btn.isEnabled(),
        )
        for tab in tabs
    ]
    terminal_effects = QSignalSpy(presenter.request_executed)

    race_started = threading.Event()

    def emit_during_teardown() -> None:
        if not all(worker.stop_entered.wait(timeout=5) for worker in workers):
            return
        race_started.set()
        for worker in workers:
            worker.chunk_received.emit("late chunk")
            worker.headers_received.emit(599, {"X-Late": "1"})
            worker.retry_attempt.emit(1, 1, None)
            worker.request_finished.emit(
                ResponseData(
                    status_code=200,
                    headers={},
                    body="late body",
                    elapsed_time=0.1,
                    size=9,
                )
            )
            worker.error.emit("late failure")
            worker.error.emit("late cancellation")
        for worker in workers:
            worker.release_stop.set()

    racer = threading.Thread(target=emit_during_teardown)
    racer.start()
    try:
        result = presenter.teardown(timeout_ms=100)
    finally:
        for worker in workers:
            worker.release_stop.set()
        racer.join(timeout=5)

    _assert_result(result)
    assert result.outcome == "success"
    assert race_started.is_set()
    assert [worker.stop_calls for worker in workers] == [1, 1]
    assert all(worker.settled.is_set() for worker in workers)
    _drain_one_gui_turn()

    assert terminal_effects.count() == 0
    assert [
        (
            tab.response_view.body_view.toPlainText(),
            tab.response_view.status_label.text(),
            tab.request_editor.send_btn.text(),
            tab.request_editor.send_btn.isEnabled(),
        )
        for tab in tabs
    ] == original_views


def test_request_teardown_is_idempotent_and_bounds_noncooperative_worker(qapp):
    """Concurrent teardown calls share one bounded result for a gated worker."""
    presenter = _make_tabs_presenter()
    presenter.add_new_tab(_make_request("stuck"), save_state=False)
    tab = presenter.widget.widget(0)
    assert isinstance(tab, RequestTab)
    worker = _RequestWorkerDouble(gate_wait=True)
    with patch(
        "pypost.ui.presenters.tabs_presenter.RequestWorker",
        return_value=worker,
    ):
        tab.request_editor.send_requested.emit(_make_request("stuck"))

    start = threading.Barrier(3)
    results: list[object] = []
    errors: list[BaseException] = []

    def call_teardown() -> None:
        try:
            start.wait(timeout=5)
            results.append(presenter.teardown(timeout_ms=5))
        except BaseException as exc:  # pragma: no cover - exposes broken contract
            errors.append(exc)

    threads = [threading.Thread(target=call_teardown) for _ in range(2)]
    for thread in threads:
        thread.start()
    start.wait(timeout=5)
    # Leave the worker gated while teardown attempts run; release it afterward.
    # On the base revision the missing API lets the callers fail immediately.
    for thread in threads:
        thread.join(timeout=1)
    worker.release_stop.set()
    for thread in threads:
        thread.join(timeout=5)

    assert errors == []
    assert len(results) == 2
    for result in results:
        _assert_result(result)
        assert result.outcome == "incomplete"
        assert result.failure_kind == "timeout"
    assert results[0] is results[1] or results[0] == results[1]
    repeated = presenter.teardown(timeout_ms=5)
    assert repeated is results[0] or repeated == results[0]
    assert worker.stop_calls == 1


def test_history_panel_teardown_is_local_and_fences_late_refresh(tmp_path, qapp):
    """Panel cleanup fences the real asynchronous completion refresh callback."""
    path = tmp_path / "history.json"
    path.write_text(
        json.dumps([_make_history_entry("late-refresh").model_dump()]),
        encoding="utf-8",
    )
    manager = HistoryManager(history_path=path, defer_initial_load=True)
    panel = HistoryPanel(manager)
    list_widget = panel.findChildren(QListWidget)[0]
    assert list_widget.count() == 0

    load_started = threading.Event()
    release_load = threading.Event()
    callback_requested = threading.Event()
    real_open = open

    def gated_open(file, mode="r", *args, **kwargs):
        if Path(file) == path and "r" in mode:
            load_started.set()
            release_load.wait(timeout=5)
        return real_open(file, mode, *args, **kwargs)

    bridge = _HistoryRefreshBridge()
    bridge.refresh_requested.connect(panel.refresh, Qt.ConnectionType.QueuedConnection)
    bridge.refresh_requested.connect(
        bridge.refresh_delivered,
        Qt.ConnectionType.QueuedConnection,
    )
    refresh_delivered = QSignalSpy(bridge.refresh_delivered)

    def request_refresh() -> None:
        callback_requested.set()
        bridge.refresh_requested.emit()

    with patch("pypost.core.history_manager.open", gated_open):
        assert manager.load_async(on_complete=request_refresh)
        assert load_started.wait(timeout=5)
        try:
            result = panel.teardown(timeout_ms=50)
        finally:
            release_load.set()
            assert callback_requested.wait(timeout=5)
        process_until(lambda: refresh_delivered.count() == 1, timeout_ms=5_000)

    _assert_result(result)
    assert list_widget.count() == 0
    assert [entry.id for entry in manager.get_entries()] == ["late-refresh"]


def test_history_manager_teardown_persists_accepted_append_to_real_file(tmp_path):
    """An accepted append is readable from the real history file after teardown."""
    path = tmp_path / "history.json"
    manager = HistoryManager(history_path=path)
    save_started = threading.Event()
    release_save = threading.Event()
    real_open = open

    def gated_open(file, mode="r", *args, **kwargs):
        if Path(file) == path and "w" in mode:
            save_started.set()
            release_save.wait(timeout=5)
        return real_open(file, mode, *args, **kwargs)

    with patch("pypost.core.history_manager.open", gated_open):
        manager.append(_make_history_entry("accepted"))
        assert save_started.wait(timeout=5)
        result = _teardown_while_releasing_save_gate(manager, release_save)

    _assert_result(result)
    assert result.outcome == "success"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert [item["id"] for item in payload] == ["accepted"]


def test_history_manager_teardown_persists_accepted_delete(tmp_path):
    """Delete state accepted before teardown remains persisted on disk."""
    path = tmp_path / "history.json"
    manager = HistoryManager(history_path=path)
    manager.append(_make_history_entry("kept"))
    manager.append(_make_history_entry("deleted"))
    manager.flush()
    save_started = threading.Event()
    release_save = threading.Event()
    real_open = open

    def gated_open(file, mode="r", *args, **kwargs):
        if Path(file) == path and "w" in mode:
            save_started.set()
            release_save.wait(timeout=5)
        return real_open(file, mode, *args, **kwargs)

    with patch("pypost.core.history_manager.open", gated_open):
        manager.delete_entry("deleted")
        assert save_started.wait(timeout=5)
        result = _teardown_while_releasing_save_gate(manager, release_save)

    _assert_result(result)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert [item["id"] for item in payload] == ["kept"]


def test_history_manager_teardown_persists_accepted_clear(tmp_path):
    """Clear state accepted before teardown remains persisted on disk."""
    path = tmp_path / "history.json"
    manager = HistoryManager(history_path=path)
    manager.append(_make_history_entry("one"))
    manager.append(_make_history_entry("two"))
    manager.flush()
    save_started = threading.Event()
    release_save = threading.Event()
    real_open = open

    def gated_open(file, mode="r", *args, **kwargs):
        if Path(file) == path and "w" in mode:
            save_started.set()
            release_save.wait(timeout=5)
        return real_open(file, mode, *args, **kwargs)

    with patch("pypost.core.history_manager.open", gated_open):
        manager.clear()
        assert save_started.wait(timeout=5)
        result = _teardown_while_releasing_save_gate(manager, release_save)

    _assert_result(result)
    assert json.loads(path.read_text(encoding="utf-8")) == []


def test_history_manager_teardown_bounds_active_save_using_public_api(tmp_path):
    """A gated real save reports incomplete without accessing manager internals."""
    path = tmp_path / "history.json"
    manager = HistoryManager(history_path=path)
    save_started = threading.Event()
    release_save = threading.Event()
    real_open = open

    def gated_open(file, mode="r", *args, **kwargs):
        if Path(file) == path and "w" in mode:
            save_started.set()
            release_save.wait(timeout=5)
        return real_open(file, mode, *args, **kwargs)

    with patch("pypost.core.history_manager.open", gated_open):
        manager.append(_make_history_entry("gated-save"))
        assert save_started.wait(timeout=5)
        try:
            result = manager.teardown(timeout_ms=5)
        finally:
            release_save.set()
            manager.flush()

    _assert_result(result)
    assert result.outcome == "incomplete"
    assert result.failure_kind == "timeout"


def test_history_manager_teardown_bounds_active_load_using_public_api(tmp_path):
    """A gated real load reports incomplete without accessing manager internals."""
    path = tmp_path / "history.json"
    path.write_text(
        json.dumps([_make_history_entry("loaded").model_dump()]),
        encoding="utf-8",
    )
    manager = HistoryManager(history_path=path, defer_initial_load=True)
    load_started = threading.Event()
    load_complete = threading.Event()
    release_load = threading.Event()
    real_open = open

    def gated_open(file, mode="r", *args, **kwargs):
        if Path(file) == path and "r" in mode:
            load_started.set()
            release_load.wait(timeout=5)
        return real_open(file, mode, *args, **kwargs)

    with patch("pypost.core.history_manager.open", gated_open):
        assert manager.load_async(on_complete=load_complete.set)
        assert load_started.wait(timeout=5)
        try:
            result = manager.teardown(timeout_ms=5)
        finally:
            release_load.set()
            assert load_complete.wait(timeout=5)

    _assert_result(result)
    assert result.outcome == "incomplete"
    assert result.failure_kind == "timeout"


def test_history_manager_retains_accepted_write_when_load_wait_times_out(tmp_path):
    """A bounded load wait defers, rather than drops, an accepted append."""
    path = tmp_path / "history.json"
    path.write_text(
        json.dumps([_make_history_entry("loaded").model_dump()]),
        encoding="utf-8",
    )
    manager = HistoryManager(history_path=path, defer_initial_load=True)
    load_started = threading.Event()
    load_complete = threading.Event()
    release_load = threading.Event()
    real_open = open

    def gated_open(file, mode="r", *args, **kwargs):
        if Path(file) == path and "r" in mode:
            load_started.set()
            release_load.wait(timeout=5)
        return real_open(file, mode, *args, **kwargs)

    with patch("pypost.core.history_manager.open", gated_open):
        assert manager.load_async(on_complete=load_complete.set)
        assert load_started.wait(timeout=5)
        with patch.object(HistoryManager, "DEFAULT_LIFECYCLE_TIMEOUT_MS", 5):
            manager.append(_make_history_entry("accepted"))
        result = manager.teardown(timeout_ms=5)
        assert result.outcome == "incomplete"
        release_load.set()
        assert load_complete.wait(timeout=5)
        assert manager.flush(timeout_ms=5_000)

    assert [entry.id for entry in manager.get_entries()] == ["accepted", "loaded"]
    assert [item["id"] for item in json.loads(path.read_text(encoding="utf-8"))] == [
        "accepted",
        "loaded",
    ]


def test_history_manager_teardown_reports_accepted_save_failure(tmp_path, caplog):
    """An accepted save error is a failed teardown, not a clean shutdown."""
    path = tmp_path / "history.json"
    manager = HistoryManager(history_path=path)
    real_open = open

    def failing_open(file, mode="r", *args, **kwargs):
        if Path(file) == path and "w" in mode:
            raise OSError("controlled history save failure")
        return real_open(file, mode, *args, **kwargs)

    with (
        patch("pypost.core.history_manager.open", failing_open),
        caplog.at_level("ERROR", logger="pypost.core.history_manager"),
    ):
        manager.append(_make_history_entry("failed-save"))
        result = manager.teardown(timeout_ms=5_000)

    _assert_result(result)
    assert result.outcome == "failed"
    assert result.failure_kind == "worker_error"
    assert any("history_manager_save_failed" in record.message for record in caplog.records)


def test_history_manager_repeated_and_concurrent_teardown_share_result(tmp_path):
    """Concurrent teardown calls share one result while a save is active."""
    path = tmp_path / "history.json"
    manager = HistoryManager(history_path=path)
    save_started = threading.Event()
    release_save = threading.Event()
    real_open = open

    def gated_open(file, mode="r", *args, **kwargs):
        if Path(file) == path and "w" in mode:
            save_started.set()
            release_save.wait(timeout=5)
        return real_open(file, mode, *args, **kwargs)

    start = threading.Barrier(3)
    results: list[object] = []
    errors: list[BaseException] = []

    def call_teardown() -> None:
        try:
            start.wait(timeout=5)
            results.append(manager.teardown(timeout_ms=5))
        except BaseException as exc:  # pragma: no cover - exposes broken contract
            errors.append(exc)

    with patch("pypost.core.history_manager.open", gated_open):
        manager.append(_make_history_entry("active-save"))
        assert save_started.wait(timeout=5)
        threads = [threading.Thread(target=call_teardown) for _ in range(2)]
        for thread in threads:
            thread.start()
        start.wait(timeout=5)
        for thread in threads:
            thread.join(timeout=5)
        release_save.set()
        manager.flush()

    assert errors == []
    assert len(results) == 2
    assert all(result.outcome == "incomplete" for result in results)
    assert results[0] is results[1] or results[0] == results[1]
    repeated = manager.teardown(timeout_ms=5)
    assert repeated is results[0] or repeated == results[0]


def test_environment_gateway_teardown_drains_ordered_queued_work(qapp):
    """Public gateway calls preserve active load, queued load, and newest save order."""
    storage = _EnvironmentStorageDouble(
        [Environment(id="loaded", name="Loaded")],
        gate_load=True,
    )
    gateway = EnvironmentStorageGateway(storage)
    gateway.load_async()
    assert storage.load_started.wait(timeout=5)
    gateway.load_async()
    gateway.save_async([Environment(id="old", name="Old")])
    newest = [Environment(id="newest", name="Newest")]
    gateway.save_async(newest)
    assert gateway.has_pending_work()

    try:
        result = gateway.teardown(timeout_ms=5)
    finally:
        storage.release_load.set()
        assert gateway.wait_idle(timeout_ms=5_000)

    _assert_result(result)
    assert result.outcome == "incomplete"
    assert result.failure_kind == "timeout"
    assert storage.operations == ["load", "save", "load"]
    assert [env.id for env in storage.saved[-1]] == ["newest"]


@pytest.mark.parametrize(
    ("fail_load", "signal_name"),
    [
        (False, "load_completed"),
        (True, "load_failed"),
    ],
    ids=["late-load-success", "late-load-failure"],
)
def test_environment_gateway_late_load_signal_does_not_retroactively_settle(
    fail_load: bool,
    signal_name: str,
):
    """Both explicit late load signals leave the prior incomplete result terminal."""
    storage = _EnvironmentStorageDouble(
        [Environment(id="late", name="Late")],
        gate_load=True,
        fail_load=fail_load,
    )
    gateway = EnvironmentStorageGateway(storage)
    signal = getattr(gateway, signal_name)
    late_signal = QSignalSpy(signal)
    gateway.load_async()
    assert storage.load_started.wait(timeout=5)

    try:
        result = gateway.teardown(timeout_ms=5)
        outcome_at_cutoff = result.outcome
        failure_at_cutoff = result.failure_kind
    finally:
        storage.release_load.set()
        assert gateway.wait_idle(timeout_ms=5_000)

    _assert_result(result)
    assert outcome_at_cutoff == "incomplete"
    assert failure_at_cutoff == "timeout"
    assert late_signal.count() == 1
    assert result.outcome == outcome_at_cutoff
    assert result.failure_kind == failure_at_cutoff


@pytest.mark.parametrize(
    ("fail_save", "signal_name"),
    [
        (False, "save_completed"),
        (True, "save_failed"),
    ],
    ids=["late-save-success", "late-save-failure"],
)
def test_environment_gateway_late_save_signal_does_not_retroactively_settle(
    fail_save: bool,
    signal_name: str,
):
    """Both explicit late save signals leave the prior incomplete result terminal."""
    storage = _EnvironmentStorageDouble(
        [Environment(id="selected", name="Selected")],
        gate_save=True,
        fail_save=fail_save,
    )
    gateway = EnvironmentStorageGateway(storage)
    signal = getattr(gateway, signal_name)
    late_signal = QSignalSpy(signal)
    gateway.save_async([Environment(id="accepted", name="Accepted")])
    assert storage.save_started.wait(timeout=5)

    try:
        result = gateway.teardown(timeout_ms=5)
        outcome_at_cutoff = result.outcome
        failure_at_cutoff = result.failure_kind
    finally:
        storage.release_save.set()
        assert gateway.wait_idle(timeout_ms=5_000)

    _assert_result(result)
    assert outcome_at_cutoff == "incomplete"
    assert failure_at_cutoff == "timeout"
    assert late_signal.count() == 1
    assert result.outcome == outcome_at_cutoff
    assert result.failure_kind == failure_at_cutoff


def test_environment_presenter_teardown_fences_late_load_success(qapp):
    """A late public load completion cannot repopulate a fenced presenter."""
    storage = _EnvironmentStorageDouble(
        [Environment(id="late", name="Late")],
        gate_load=True,
    )
    presenter = _make_env_presenter(storage)
    loaded = QSignalSpy(presenter.environments_loaded)
    presenter.load_environments()
    assert storage.load_started.wait(timeout=5)
    before_count = presenter.environment_count()

    try:
        result = presenter.teardown(timeout_ms=5)
        outcome_at_cutoff = result.outcome
        failure_at_cutoff = result.failure_kind
    finally:
        storage.release_load.set()
        assert presenter.wait_storage_idle(timeout_ms=5_000)

    _assert_result(result)
    assert outcome_at_cutoff == "incomplete"
    assert failure_at_cutoff == "timeout"
    assert result.outcome == outcome_at_cutoff
    assert result.failure_kind == failure_at_cutoff
    assert loaded.count() == 0
    assert presenter.environment_count() == before_count


def test_environment_presenter_teardown_fences_late_load_failure(qapp):
    """A late public load failure cannot replace the fenced UI state."""
    storage = _EnvironmentStorageDouble(
        [Environment(id="unused", name="Unused")],
        gate_load=True,
        fail_load=True,
    )
    presenter = _make_env_presenter(storage)
    presenter.load_environments()
    assert storage.load_started.wait(timeout=5)
    before_count = presenter.environment_count()
    loaded = QSignalSpy(presenter.environments_loaded)

    try:
        result = presenter.teardown(timeout_ms=5)
        outcome_at_cutoff = result.outcome
        failure_at_cutoff = result.failure_kind
    finally:
        storage.release_load.set()
        assert presenter.wait_storage_idle(timeout_ms=5_000)

    _assert_result(result)
    assert outcome_at_cutoff == "incomplete"
    assert failure_at_cutoff == "timeout"
    assert result.outcome == outcome_at_cutoff
    assert result.failure_kind == failure_at_cutoff
    assert presenter.environment_count() == before_count
    assert loaded.count() == 0


def test_environment_update_handoff_records_cutoff_and_dispositions(qapp):
    """The public queued handoff records pre-cutoff work and rejects late work."""
    environment = Environment(id="selected", name="Selected", variables={"A": "1"})
    storage = _EnvironmentStorageDouble([environment], gate_save=True)
    presenter = _make_env_presenter(storage)
    _load_presenter_environment(presenter, storage)
    tabs = _make_tabs_presenter()
    tabs.add_new_tab(_make_request("env-update"), save_state=False)
    tab = tabs.widget.widget(0)
    assert isinstance(tab, RequestTab)
    worker = _RequestWorkerDouble(gate_wait=True)
    with patch(
        "pypost.ui.presenters.tabs_presenter.RequestWorker",
        return_value=worker,
    ):
        tab.request_editor.send_requested.emit(_make_request("env-update"))

    probe = _PublicEnvironmentHandoffProbe()
    tabs.env_update_requested.connect(
        probe.observe,
        Qt.ConnectionType.DirectConnection,
    )
    tabs.env_update_requested.connect(
        presenter.on_env_update,
        Qt.ConnectionType.QueuedConnection,
    )
    worker.env_update.emit({"B": "2"})
    assert probe.payloads == [{"B": "2"}]

    race_started = threading.Event()

    def emit_after_cutoff() -> None:
        if not worker.stop_entered.wait(timeout=5):
            return
        race_started.set()
        worker.env_update.emit({"C": "3"})
        worker.release_stop.set()

    racer = threading.Thread(target=emit_after_cutoff)
    racer.start()

    try:
        tabs_result = tabs.teardown(timeout_ms=100)
        racer.join(timeout=5)
        assert race_started.is_set()
        process_until(lambda: storage.save_started.is_set(), timeout_ms=5_000)
        assert storage.save_started.wait(timeout=5)
        before_teardown = dict(presenter.current_variables)
        env_result = presenter.teardown(timeout_ms=5)
    finally:
        worker.release_stop.set()
        racer.join(timeout=5)
        storage.release_save.set()
        assert presenter.wait_storage_idle(timeout_ms=5_000)

    _assert_result(tabs_result)
    _assert_result(env_result)
    assert env_result.outcome == "incomplete"
    dispositions = getattr(tabs_result, "dispositions", {}) or {}
    accepted_disposition = dispositions.get(1, dispositions.get("1"))
    assert accepted_disposition in {
        "persisted",
        "coalesced_into_newer_save",
        "failed",
        "incomplete",
    }
    assert dispositions.get(2, dispositions.get("2")) == "rejected_after_cutoff"
    assert storage.saved[-1][0].variables == {"A": "1", "B": "2"}
    _drain_one_gui_turn()
    assert presenter.current_variables == before_teardown
    assert presenter.current_variables == {"A": "1", "B": "2"}


def test_environment_presenter_teardown_handles_late_save_success(qapp):
    """A late save success cannot retroactively mutate an incomplete result."""
    environment = Environment(id="selected", name="Selected", variables={"A": "1"})
    storage = _EnvironmentStorageDouble([environment], gate_save=True)
    presenter = _make_env_presenter(storage)
    _load_presenter_environment(presenter, storage)
    updates = QSignalSpy(presenter.environment_updated)
    presenter.on_env_update({"B": "2"})
    assert storage.save_started.wait(timeout=5)

    try:
        result = presenter.teardown(timeout_ms=100)
        outcome_at_cutoff = result.outcome
        failure_at_cutoff = result.failure_kind
    finally:
        storage.release_save.set()
        assert presenter.wait_storage_idle(timeout_ms=5_000)

    _assert_result(result)
    assert outcome_at_cutoff == "incomplete"
    assert failure_at_cutoff == "timeout"
    assert result.outcome == outcome_at_cutoff
    assert result.failure_kind == failure_at_cutoff
    assert storage.saved[-1][0].variables == {"A": "1", "B": "2"}
    assert presenter.current_variables == {"A": "1", "B": "2"}
    assert updates.count() == 1


def test_environment_update_ledger_reports_gateway_persistence(qapp):
    """The sequence ledger follows the gateway's real successful save outcome."""
    storage = _EnvironmentStorageDouble(
        [Environment(id="selected", name="Selected", variables={"A": "1"})]
    )
    presenter = _make_env_presenter(storage)
    _load_presenter_environment(presenter, storage)
    dispositions = QSignalSpy(presenter.environment_update_disposition)

    presenter.on_env_update({"B": "2"}, sequence=7)
    process_until(lambda: dispositions.count() == 1, timeout_ms=5_000)
    assert presenter.wait_storage_idle(timeout_ms=5_000)
    assert dispositions.at(0) == [7, "persisted"]
    assert storage.saved[-1][0].variables == {"A": "1", "B": "2"}


def test_environment_update_ledger_reports_pending_save_coalescing(qapp):
    """A replaced queued save is explicitly attributed to the newer save."""
    storage = _EnvironmentStorageDouble(
        [Environment(id="selected", name="Selected", variables={"A": "1"})],
        gate_save=True,
    )
    presenter = _make_env_presenter(storage)
    _load_presenter_environment(presenter, storage)
    dispositions = QSignalSpy(presenter.environment_update_disposition)

    presenter.on_env_update({"B": "2"}, sequence=7)
    assert storage.save_started.wait(timeout=5)
    presenter.on_env_update({"C": "3"}, sequence=8)
    presenter.on_env_update({"D": "4"}, sequence=9)
    assert dispositions.count() == 1
    assert dispositions.at(0) == [8, "coalesced_into_newer_save"]
    storage.release_save.set()
    assert presenter.wait_storage_idle(timeout_ms=5_000)
    assert any(
        dispositions.at(index)[1] == "persisted"
        for index in range(dispositions.count())
    )
    assert storage.saved[-1][0].variables == {
        "A": "1",
        "B": "2",
        "C": "3",
        "D": "4",
    }


def test_environment_presenter_teardown_fences_late_save_failure(qapp):
    """A late save failure cannot retroactively mutate an incomplete result."""
    environment = Environment(id="selected", name="Selected", variables={"A": "1"})
    storage = _EnvironmentStorageDouble(
        [environment],
        gate_save=True,
        fail_save=True,
    )
    presenter = _make_env_presenter(storage)
    _load_presenter_environment(presenter, storage)
    updates = QSignalSpy(presenter.environment_updated)
    presenter.on_env_update({"B": "2"})
    assert storage.save_started.wait(timeout=5)

    with patch("pypost.ui.presenters.env_presenter.show_env_save_failed") as show_save_failed:
        try:
            result = presenter.teardown(timeout_ms=100)
            outcome_at_cutoff = result.outcome
            failure_at_cutoff = result.failure_kind
        finally:
            storage.release_save.set()
            assert presenter.wait_storage_idle(timeout_ms=5_000)
        assert show_save_failed.call_count == 0

    _assert_result(result)
    assert outcome_at_cutoff == "incomplete"
    assert failure_at_cutoff == "timeout"
    assert result.outcome == outcome_at_cutoff
    assert result.failure_kind == failure_at_cutoff
    assert presenter.current_variables == {"A": "1", "B": "2"}
    assert updates.count() == 1
    assert storage.saved == []


def test_each_owner_has_bounded_idle_idempotent_teardown(qapp, tmp_path):
    """Every public owner scope has one stable result for idle repeated teardown."""
    owners = [
        _make_tabs_presenter(),
        HistoryPanel(HistoryManager(history_path=tmp_path / "idle-history.json")),
        HistoryManager(history_path=tmp_path / "idle-manager.json"),
        _make_env_presenter(_EnvironmentStorageDouble([])),
        EnvironmentStorageGateway(_EnvironmentStorageDouble([])),
    ]

    for owner in owners:
        first = owner.teardown(timeout_ms=50)
        second = owner.teardown(timeout_ms=50)
        _assert_result(first)
        assert first.outcome == "success"
        assert second is first or second == first


def test_main_window_teardown_orders_public_owners_and_aggregates(qapp):
    """The public composition seam drains request, history, then environment owners."""
    calls: list[str] = []
    root, owners = _make_composition_root(calls=calls)

    result = root.teardown(timeout_ms=100)

    _assert_result(result)
    assert result.outcome == "success"
    assert calls == ["tabs", "history_panel", "history_manager", "env"]
    assert all(
        isinstance(owner.timeouts[0], int) and 0 <= owner.timeouts[0] <= 100
        for owner in owners
    )


def test_main_window_teardown_passes_one_shared_remaining_deadline(qapp):
    """Each public owner receives the remaining part of one deterministic budget."""
    calls: list[str] = []
    budget = _SharedDeadlineDouble(remaining_ms=100)
    root, owners = _make_composition_root(calls=calls, budget=budget)

    result = root.teardown(timeout_ms=100)

    _assert_result(result)
    assert result.outcome == "success"
    timeouts = [owner.timeouts[0] for owner in owners]
    assert all(isinstance(timeout_ms, int) for timeout_ms in timeouts)
    assert timeouts == sorted(timeouts, reverse=True)
    assert timeouts[0] <= 100
    assert budget.remaining_ms == 60


def test_main_window_teardown_aggregates_owner_failure_after_draining_all(qapp):
    """One failed owner makes the public aggregate failed without skipping later owners."""
    calls: list[str] = []
    root, owners = _make_composition_root(
        calls=calls,
        env_result=_composition_result(
            "env",
            "failed",
            failure_kind="worker_error",
        ),
    )

    result = root.teardown(timeout_ms=100)

    _assert_result(result)
    assert result.outcome == "failed"
    assert calls == ["tabs", "history_panel", "history_manager", "env"]


def test_main_window_close_event_rejects_incomplete_cleanup(qapp):
    """Window-manager close cannot accept an aggregate incomplete result."""
    calls: list[str] = []
    root, _ = _make_composition_root(
        calls=calls,
        env_result=_composition_result("env", "incomplete", failure_kind="timeout"),
    )
    from pypost.ui.main_window import MainWindow

    root._shutdown_for_exit = lambda: root.teardown(timeout_ms=100)
    event = MagicMock()
    MainWindow.closeEvent(root, event)

    event.accept.assert_not_called()
    event.ignore.assert_called_once()
