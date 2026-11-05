"""PYPOST-1321: collections join main-window shutdown under a shared budget.

Contract covered by these tests:

* ``main_window_lifecycle.teardown`` includes ``window.collections`` in the owner
  list immediately before ``env``.
* Collections receives a fair share of the shared shutdown budget.
* App close during an active file-parse or library import worker runs collections
  teardown under that share and reports a ``TeardownResult``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtWidgets import QWidget

from pypost.core.collection_import_state import CollectionImportState
from pypost.core.lifecycle import TeardownResult
from pypost.models.models import Collection
from pypost.ui.presenters.collection_import_actions import CollectionImportActions
from tests.helpers.collections_tree import FakeRequestManager

pytestmark = pytest.mark.timeout(30)

_PATH = Path("/tmp/pypost-1321-import.json")
_OWNER_ORDER = (
    "tabs",
    "history_panel",
    "history_manager",
    "collections",
    "env",
)
_COLLECTIONS_INDEX = _OWNER_ORDER.index("collections")


@dataclass(frozen=True)
class _TeardownResultDouble:
    """Public-result-shaped value used by composition-root owner doubles."""

    owner: str
    outcome: str
    elapsed_ms: int = 0
    active_count: int = 0
    pending_count: int = 0
    failure_kind: str | None = None
    dispositions: dict[int, str] | None = None


class _CompositionOwnerDouble:
    """Owner double recording call order, begin-teardown fencing, and budgets."""

    def __init__(
        self,
        name: str,
        calls: list[str],
        result: _TeardownResultDouble,
    ) -> None:
        self.name = name
        self.calls = calls
        self.result = result
        self.timeouts: list[int | None] = []
        self.begin_calls = 0

    def begin_teardown(self) -> None:
        self.begin_calls += 1

    def teardown(self, timeout_ms: int | None = None) -> _TeardownResultDouble:
        self.timeouts.append(timeout_ms)
        self.calls.append(self.name)
        return self.result


class _SpySignal:
    """Signal stand-in whose ``disconnect`` is a no-op."""

    def disconnect(self, *_args: Any) -> None:
        return None


class _SpyWorker:
    """Worker stand-in that stays running and records interruption / waits."""

    def __init__(self) -> None:
        self.waits: list[int] = []
        self.interruptions = 0
        self.deleted = 0
        self.parse_progress = _SpySignal()
        self.parse_completed = _SpySignal()
        self.parse_failed = _SpySignal()
        self.parse_cancelled = _SpySignal()
        self.operation_completed = _SpySignal()
        self.operation_failed = _SpySignal()
        self.finished = _SpySignal()

    def isRunning(self) -> bool:  # noqa: N802 - mirrors QThread API
        return True

    def requestInterruption(self) -> None:  # noqa: N802 - mirrors QThread API
        self.interruptions += 1

    def deleteLater(self) -> None:  # noqa: N802 - mirrors QThread API
        self.deleted += 1

    def wait(self, ms: int) -> bool:
        self.waits.append(ms)
        return False


class _CollectionsImportOwner:
    """Collections shutdown participant backed by real import-actions teardown.

    After the production fix this owner is invoked by
    ``main_window_lifecycle.teardown`` with a fair-share budget and must return a
    ``TeardownResult``. Today the composition root never calls it.
    """

    def __init__(self, actions: CollectionImportActions) -> None:
        self._actions = actions
        self.calls: list[str] = []
        self.timeouts: list[int | None] = []
        self.begin_calls = 0
        self.last_result: TeardownResult | None = None

    def begin_teardown(self) -> None:
        self.begin_calls += 1

    def teardown(self, timeout_ms: int | None = None) -> TeardownResult:
        self.timeouts.append(timeout_ms)
        self.calls.append("collections")
        active_count = 0
        worker = self._actions._worker
        if worker is not None and worker.isRunning():
            active_count += 1
        library_worker = self._actions._library_worker
        if library_worker is not None and library_worker.isRunning():
            active_count += 1
        pending_count = 0 if self._actions._state is CollectionImportState.IDLE else 1
        clean = self._actions.teardown(timeout_ms=timeout_ms)
        outcome = "success" if clean else "incomplete"
        self.last_result = TeardownResult(
            owner="collections_presenter",
            outcome=outcome,
            elapsed_ms=0,
            active_count=active_count,
            pending_count=pending_count,
            failure_kind=None if clean else "timeout",
        )
        return self.last_result


class _CompositionRootHarness:
    """Harness binding real ``MainWindow.teardown`` to a five-owner root."""

    def __init__(
        self,
        tabs: object,
        history_panel: object,
        history_manager: object,
        collections: object,
        env: object,
    ) -> None:
        from pypost.ui.main_window import MainWindow

        self._main_window_type = MainWindow
        self.tabs = tabs
        self.history_panel = history_panel
        self.history_manager = history_manager
        self.collections = collections
        self.env = env

    def teardown(self, timeout_ms: int) -> TeardownResult:
        return self._main_window_type.teardown(self, timeout_ms=timeout_ms)


def _peer_result(owner: str) -> _TeardownResultDouble:
    return _TeardownResultDouble(owner=owner, outcome="success")


def _make_peer_owners(calls: list[str]) -> dict[str, _CompositionOwnerDouble]:
    return {
        name: _CompositionOwnerDouble(name, calls, _peer_result(name))
        for name in ("tabs", "history_panel", "history_manager", "env")
    }


def _make_actions(parent: QWidget) -> CollectionImportActions:
    def _unused_reader(
        _path: Path, /, *, on_progress: Callable[[int, int], None]
    ) -> tuple[list[Collection], list[str]]:
        return [], []

    return CollectionImportActions(
        parent,
        FakeRequestManager([]),
        read_import_file=_unused_reader,
        refresh_tree=lambda: None,
        restore_tree_state=lambda: None,
        emit_collections_changed=lambda: None,
    )


def _fair_share_ms(budget_ms: int, index: int, owner_count: int) -> int:
    """Mirror ``main_window_lifecycle`` allocated share before remaining clamp."""
    slots_left = owner_count - index
    return int(budget_ms * slots_left / owner_count)


def test_main_window_teardown_includes_collections_before_env_with_fair_share(
    qapp,
) -> None:
    """Composition root must call collections before env with a fair budget share."""
    calls: list[str] = []
    peers = _make_peer_owners(calls)
    collections = _CompositionOwnerDouble(
        "collections",
        calls,
        _peer_result("collections"),
    )
    root = _CompositionRootHarness(
        peers["tabs"],
        peers["history_panel"],
        peers["history_manager"],
        collections,
        peers["env"],
    )
    budget_ms = 100

    result = root.teardown(timeout_ms=budget_ms)

    assert result.outcome == "success"
    assert calls == list(_OWNER_ORDER), (
        f"owner order {calls!r} must include collections immediately before env"
    )
    assert collections.begin_calls == 1, (
        "collections must receive early begin_teardown with other non-last owners"
    )
    assert peers["env"].begin_calls == 1
    assert len(collections.timeouts) == 1
    timeout_ms = collections.timeouts[0]
    allocated = _fair_share_ms(budget_ms, _COLLECTIONS_INDEX, len(_OWNER_ORDER))
    assert isinstance(timeout_ms, int)
    assert 0 <= timeout_ms <= budget_ms
    assert timeout_ms <= allocated, (
        f"collections timeout_ms={timeout_ms} exceeds fair share allocated={allocated}"
    )


def test_main_window_teardown_runs_collections_during_file_import(qapp) -> None:
    """Close during an active file-parse worker must tear down collections under budget."""
    calls: list[str] = []
    peers = _make_peer_owners(calls)
    parent = QWidget()
    actions = _make_actions(parent)
    file_spy = _SpyWorker()
    # IDLE skips wait-idle; teardown still joins/interrupts the live file worker.
    actions._state = CollectionImportState.IDLE
    actions._worker = file_spy  # type: ignore[assignment]
    actions._library_worker = None
    collections = _CollectionsImportOwner(actions)
    root = _CompositionRootHarness(
        peers["tabs"],
        peers["history_panel"],
        peers["history_manager"],
        collections,
        peers["env"],
    )
    budget_ms = 100
    allocated = _fair_share_ms(budget_ms, _COLLECTIONS_INDEX, len(_OWNER_ORDER))

    root.teardown(timeout_ms=budget_ms)

    assert collections.calls == ["collections"], (
        "main-window teardown must invoke collections.teardown while a file import "
        "worker is in flight (collections omitted from owner list today)"
    )
    assert collections.begin_calls == 1
    assert len(collections.timeouts) == 1
    timeout_ms = collections.timeouts[0]
    assert isinstance(timeout_ms, int)
    assert 0 <= timeout_ms <= budget_ms
    assert timeout_ms <= allocated
    assert collections.last_result is not None
    assert collections.last_result.outcome in {"success", "incomplete"}
    assert collections.last_result.active_count >= 1
    assert file_spy.interruptions >= 1, (
        "file-parse worker must be cooperatively interrupted during shutdown"
    )
    assert actions._worker is None, "file-parse worker field must be cleared after teardown"


def test_main_window_teardown_runs_collections_during_library_import(qapp) -> None:
    """Close during an active library worker must tear down collections under budget."""
    calls: list[str] = []
    peers = _make_peer_owners(calls)
    parent = QWidget()
    actions = _make_actions(parent)
    library_spy = _SpyWorker()
    actions._state = CollectionImportState.IDLE
    actions._worker = None
    actions._library_worker = library_spy  # type: ignore[assignment]
    collections = _CollectionsImportOwner(actions)
    root = _CompositionRootHarness(
        peers["tabs"],
        peers["history_panel"],
        peers["history_manager"],
        collections,
        peers["env"],
    )
    budget_ms = 100
    allocated = _fair_share_ms(budget_ms, _COLLECTIONS_INDEX, len(_OWNER_ORDER))

    root.teardown(timeout_ms=budget_ms)

    assert collections.calls == ["collections"], (
        "main-window teardown must invoke collections.teardown while a library import "
        "worker is in flight (collections omitted from owner list today)"
    )
    assert collections.begin_calls == 1
    assert len(collections.timeouts) == 1
    timeout_ms = collections.timeouts[0]
    assert isinstance(timeout_ms, int)
    assert 0 <= timeout_ms <= budget_ms
    assert timeout_ms <= allocated
    assert collections.last_result is not None
    assert collections.last_result.outcome in {"success", "incomplete"}
    assert collections.last_result.active_count >= 1
    # Library worker is join-only (PYPOST-1324); unclean/incomplete is allowed.
    assert library_spy.waits, "library worker must be waited under the collections share"
    assert actions._library_worker is None, (
        "library worker field must be cleared after collections teardown"
    )
