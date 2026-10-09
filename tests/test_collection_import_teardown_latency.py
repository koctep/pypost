"""Collection import teardown latency measurement (PYPOST-1264, DoD 5).

Slow, measurement-only module: excluded from ``make test`` and run on one worker with
``make test-slow PYTEST_ARGS="tests/test_collection_import_teardown_latency.py -m slow -s"``.
It prints environment, load average, and per-scenario n/min/p50/p95/max. Percentiles are
recorded decision inputs, never asserted; only structural outcomes (``n`` and ``clean``)
are checked.
"""

from __future__ import annotations

import logging
import os
import platform
import statistics
import sys
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
import PySide6
from PySide6.QtCore import qVersion
from PySide6.QtWidgets import QWidget

from pypost.core.collection_import_lifecycle_policy import (
    DEFAULT_COLLECTION_IMPORT_LIFECYCLE_POLICY,
)
from pypost.models.models import Collection
from pypost.ui.presenters.collection_import_actions import CollectionImportActions
from tests.helpers.collections_tree import FakeRequestManager

pytestmark = [pytest.mark.slow, pytest.mark.timeout(120)]

logger = logging.getLogger(__name__)

_N = 20
_PATH = Path("/tmp/import-latency.json")
_ENTER_TIMEOUT_S = 5.0
_CLEANUP_JOIN_MS = 2000
_CHECKPOINT_SLEEP_S = 0.002
_MAX_CHECKPOINTS = 5000  # bounded: about 10 s if never interrupted
_LIBRARY_OP_S = 0.2
_REFERENCE_BUDGET_MS = 100

_SUMMARIES: list[str] = []


def _emit(line: str) -> None:
    # Measurement output for ``-s`` runs (the recorded evidence), not a debug print.
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def _loadavg() -> str:
    try:
        return "%.2f %.2f %.2f" % os.getloadavg()
    except OSError:
        return "unavailable"


@pytest.fixture(scope="module", autouse=True)
def _environment_report() -> Iterator[None]:
    policy = DEFAULT_COLLECTION_IMPORT_LIFECYCLE_POLICY
    _emit(
        f"\ncollection_import_teardown_latency_env os={platform.platform()} "
        f"arch={platform.machine()} python={sys.version.split()[0]} "
        f"pyside6={PySide6.__version__} qt={qVersion()} "
        f"qpa={os.environ.get('QT_QPA_PLATFORM', '')} workers=1 cpus={os.cpu_count()} "
        f"budget_ms={policy.teardown_budget_ms} "
        f"tolerance_ms={policy.budget_tolerance_ms} loadavg_before={_loadavg()}"
    )
    yield
    for line in _SUMMARIES:
        _emit(line)
    _emit(f"collection_import_teardown_latency_env loadavg_after={_loadavg()}")


def _record(scenario: str, samples_ms: list[float], clean: list[bool]) -> None:
    ordered = sorted(samples_ms)
    p95 = ordered[max(0, int(round(0.95 * len(ordered))) - 1)]
    line = (
        f"collection_import_teardown_latency scenario={scenario} n={len(ordered)} "
        f"min_ms={ordered[0]:.2f} p50_ms={statistics.median(ordered):.2f} "
        f"p95_ms={p95:.2f} max_ms={ordered[-1]:.2f} "
        f"clean={sum(clean)}/{len(clean)}"
    )
    logger.info(line)
    _SUMMARIES.append(line)


def _make_actions(read_import_file: Callable[..., Any] | None = None) -> Any:
    def _unused_reader(
        _path: Path, /, *, on_progress: Callable[[int, int], None]
    ) -> tuple[list[Collection], list[str]]:
        return [], []

    return CollectionImportActions(
        QWidget(),
        FakeRequestManager([]),
        read_import_file=read_import_file or _unused_reader,
        refresh_tree=lambda: None,
        restore_tree_state=lambda: None,
        emit_collections_changed=lambda: None,
    )


def _defer_delete(worker: Any, deferred: list[Callable[[], None]]) -> None:
    # Keep a possibly still-running QThread alive until it is joined in cleanup.
    deferred.append(worker.deleteLater)
    worker.deleteLater = lambda: None


def _cleanup(threads: list[Any], deferred: list[Callable[[], None]]) -> None:
    for thread in threads:
        thread.wait(_CLEANUP_JOIN_MS)
    for real_delete in deferred:
        real_delete()


def _timed_teardown(actions: Any, timeout_ms: int | None = None) -> tuple[float, bool]:
    started = time.perf_counter()
    clean = actions.teardown() if timeout_ms is None else actions.teardown(timeout_ms)
    return (time.perf_counter() - started) * 1000.0, clean


def test_idle_teardown_latency(qapp) -> None:
    samples: list[float] = []
    clean: list[bool] = []
    for _ in range(_N):
        elapsed_ms, ok = _timed_teardown(_make_actions())
        samples.append(elapsed_ms)
        clean.append(ok)
    _record("idle", samples, clean)
    assert len(samples) == _N
    assert all(clean)


def test_active_file_import_cancel_latency(qapp) -> None:
    samples: list[float] = []
    clean: list[bool] = []
    for _ in range(_N):
        entered = threading.Event()

        def _checkpoint_reader(
            _path: Path, /, *, on_progress: Callable[[int, int], None]
        ) -> tuple[list[Collection], list[str]]:
            # Cancellation-aware: checkpoints raise once interruption is requested.
            entered.set()
            for _i in range(_MAX_CHECKPOINTS):
                time.sleep(_CHECKPOINT_SLEEP_S)
                on_progress(0, 0)
            return [], []

        actions = _make_actions(_checkpoint_reader)
        threads: list[Any] = []
        deferred: list[Callable[[], None]] = []
        try:
            actions._start_parse(_PATH)
            threads.append(actions._worker)
            _defer_delete(actions._worker, deferred)
            assert entered.wait(timeout=_ENTER_TIMEOUT_S), "reader never started"
            elapsed_ms, ok = _timed_teardown(actions)
        finally:
            _cleanup(threads, deferred)
        samples.append(elapsed_ms)
        clean.append(ok)
    _record("file_cancel", samples, clean)
    assert len(samples) == _N
    assert all(clean)


def _run_library_scenario(
    op: Callable[[], bool], entered: threading.Event, timeout_ms: int | None
) -> tuple[float, bool, Any]:
    actions = _make_actions()
    threads: list[Any] = []
    deferred: list[Callable[[], None]] = []
    try:
        actions._start_library_operation(op, lambda _result: None)
        worker = actions._library_worker
        threads.append(worker)
        _defer_delete(worker, deferred)
        assert entered.wait(timeout=_ENTER_TIMEOUT_S), "library op never started"
        elapsed_ms, ok = _timed_teardown(actions, timeout_ms)
        return elapsed_ms, ok, worker
    finally:
        _cleanup(threads, deferred)


def test_active_library_operation_latency(qapp) -> None:
    samples: list[float] = []
    clean: list[bool] = []
    for _ in range(_N):
        entered = threading.Event()

        def _short_op() -> bool:
            entered.set()
            time.sleep(_LIBRARY_OP_S)
            return True

        elapsed_ms, ok, _worker = _run_library_scenario(_short_op, entered, None)
        samples.append(elapsed_ms)
        clean.append(ok)
    _record("library_200ms", samples, clean)
    assert len(samples) == _N
    assert all(clean)


def test_blocked_library_operation_reference_latency(qapp) -> None:
    """Reference: a library op outliving a reduced budget gives a bounded unclean result."""
    samples: list[float] = []
    clean: list[bool] = []
    for _ in range(_N):
        entered = threading.Event()
        release = threading.Event()

        def _blocked_op() -> bool:
            entered.set()
            return release.wait(timeout=_ENTER_TIMEOUT_S)

        # Release from a timer so the cleanup join cannot wait on a stuck op.
        timer = threading.Timer(_REFERENCE_BUDGET_MS * 3 / 1000.0, release.set)
        timer.start()
        try:
            elapsed_ms, ok, _worker = _run_library_scenario(
                _blocked_op, entered, _REFERENCE_BUDGET_MS
            )
        finally:
            release.set()
            timer.cancel()
        samples.append(elapsed_ms)
        clean.append(ok)
    _record(f"library_blocked_budget{_REFERENCE_BUDGET_MS}", samples, clean)
    assert len(samples) == _N
    assert not any(clean)
