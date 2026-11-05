"""Collections export UI dispose contract + red→green drivers (PYPOST-1357).

Assertion polarities (ai-tasks/PYPOST-1357/20-architecture.md):

- **A-complete**: full ``dispose_collections_export_fixture`` → desired end-state
  (panel invalid, no leftover collections export roots). Permanent positive guard;
  may already be green after PYPOST-1315 wiring.
- **A-incomplete**: close-only / production ``teardown`` without DeferredDelete drain
  → residual liveness. Permanent **green** negative control (opposite polarity).
- **R-autouse**: omit ``dispose_collections_export_fixture`` (missed-``finally`` /
  PYPOST-1315 TD-5) → assert desired end-state after registry autouse dispose.
- **B**: bounded subprocess of the nineteen-node collection export UI file; fails
  only on live native-crash class; zero-crash matrix + dependency versions is an
  accepted diagnostic artifact when SIGSEGV is unavailable on the restored host.
"""

from __future__ import annotations

import importlib.metadata
import os
import signal
import subprocess
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
import shiboken6
from PySide6.QtWidgets import QApplication, QTreeView, QWidget

from pypost.ui.presenters.collections_presenter import CollectionsPresenter
from tests.helpers.collections_tree import (
    FakeMetrics,
    FakeRequestManager,
    FakeStateManager,
    make_collection,
)
from tests.helpers.qt_widget_dispose import dispose_collections_export_fixture

pytestmark = pytest.mark.timeout(60)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_COLLECTION_EXPORT_UI = "tests/test_collection_export_ui.py"
_NATIVE_CRASH_CODES = frozenset({-11, -7, 139, 135})
_SUBPROCESS_ATTEMPT_BUDGET = 3
_SUBPROCESS_TIMEOUT_S = 120.0

# Registry + autouse dispose (env-export pattern / PYPOST-1315 TD-5) so omitted
# ``finally`` still reaches ``dispose_collections_export_fixture`` (R-autouse).
_created_presenters: list[CollectionsPresenter] = []


def _make_presenter(
    collections=None,
) -> tuple[CollectionsPresenter, FakeRequestManager]:
    """Mirror ``tests/test_collection_export_ui.py`` fixture construction."""
    manager = FakeRequestManager(list(collections or [make_collection("c1", "Billing")]))
    presenter = CollectionsPresenter(
        manager,
        FakeStateManager(),
        FakeMetrics(),
        {},
        serialize_collection=None,
    )
    presenter.refresh_tree()
    _created_presenters.append(presenter)
    return presenter, manager


@pytest.fixture
def _collections_export_end_state_checks() -> Iterator[list[Callable[[], None]]]:
    """Post-dispose checks; teardown runs after autouse dispose (LIFO)."""
    checks: list[Callable[[], None]] = []
    yield checks
    for check in checks:
        check()


@pytest.fixture(autouse=True)
def _cleanup_collections_export_presenters(
    qapp: QApplication,
    _collections_export_end_state_checks: list[Callable[[], None]],
) -> Iterator[None]:
    # Depends on end-state checks so dispose runs before those assertions.
    yield
    while _created_presenters:
        dispose_collections_export_fixture(_created_presenters.pop(), qapp)


def _leftover_collections_export_roots(
    qapp: QApplication,
    *,
    panel: QWidget | None = None,
) -> list[QWidget]:
    """Collect still-valid collections export panel / top-level tree leftovers."""
    leftovers: list[QWidget] = []
    for top in qapp.topLevelWidgets():
        if not shiboken6.isValid(top):
            continue
        if panel is not None and top is panel:
            leftovers.append(top)
            continue
        if isinstance(top, QTreeView):
            leftovers.append(top)
    return leftovers


def _assert_desired_collections_dispose_end_state(
    qapp: QApplication,
    panel: QWidget,
) -> None:
    """Desired dispose contract: panel destroyed; no collections export leftovers."""
    assert not shiboken6.isValid(panel), (
        "collections export panel must be destroyed after dispose "
        "(omit dispose / close-only still leaves a live C++ object)"
    )
    leftovers = _leftover_collections_export_roots(qapp, panel=panel)
    assert leftovers == [], (
        "No collections export panel / QTreeView roots may remain in "
        f"QApplication.topLevelWidgets() after dispose; still live: {leftovers!r}"
    )


def _describe_returncode(returncode: int) -> str:
    if returncode >= 0:
        return f"exit code {returncode}"
    raw_signum = -returncode
    try:
        name = signal.Signals(raw_signum).name
    except ValueError:
        name = "unknown signal"
    return f"killed by signal {raw_signum} ({name})"


def _dependency_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for dist in ("PySide6", "shiboken6", "pydantic"):
        try:
            versions[dist] = importlib.metadata.version(dist)
        except importlib.metadata.PackageNotFoundError:
            versions[dist] = "not-installed"
    return versions


def _run_collection_export_ui_child(
    *, timeout_s: float = _SUBPROCESS_TIMEOUT_S
) -> subprocess.CompletedProcess[str]:
    """Run the collection export UI suite in an isolated offscreen subprocess."""
    env = {
        **os.environ,
        "QT_QPA_PLATFORM": "offscreen",
        "PYTHONPATH": str(_REPO_ROOT),
        "PYTHONFAULTHANDLER": "1",
    }
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            _COLLECTION_EXPORT_UI,
            "-m",
            "not slow",
            "-q",
            "--tb=line",
        ],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )


def test_a_complete_collections_dispose_reaches_desired_end_state(
    qapp: QApplication,
) -> None:
    """A-complete: full dispose helper reaches the desired end-state (positive guard)."""
    presenter, _manager = _make_presenter()
    panel = presenter.panel
    assert shiboken6.isValid(panel)

    dispose_collections_export_fixture(presenter, qapp)

    _assert_desired_collections_dispose_end_state(qapp, panel)


def test_a_incomplete_collections_dispose_leaves_residual_liveness(
    qapp: QApplication,
) -> None:
    """A-incomplete: close-only cleanup leaves residual liveness (green negative control).

    Production ``teardown`` closes the panel but does not ``deleteLater`` /
    ``sendPostedEvents(DeferredDelete)``. This asserts the opposite polarity of
    A-complete / R-autouse so the member stays green after Step 4.
    """
    presenter, _manager = _make_presenter()
    panel = presenter.panel
    assert shiboken6.isValid(panel)

    try:
        presenter.teardown(timeout_ms=50)
        # Close-only path: no dispose_qt_root / DeferredDelete drain.
        assert shiboken6.isValid(panel), (
            "incomplete cleanup must leave the collections panel C++ object live "
            "(negative control for why full dispose is required)"
        )
        leftovers = _leftover_collections_export_roots(qapp, panel=panel)
        assert leftovers, (
            "incomplete cleanup must leave collections export panel / tree roots "
            "among topLevelWidgets (residual-liveness negative control)"
        )
    finally:
        # Opt out of polluting later tests; Step 4 autouse must not swallow this
        # control — we assert liveness *before* any full dispose.
        dispose_collections_export_fixture(presenter, qapp)


def test_missed_collections_dispose_reaches_desired_end_state(
    qapp: QApplication,
    _collections_export_end_state_checks: list[Callable[[], None]],
) -> None:
    """R-autouse: omitted dispose must still reach desired end-state via autouse.

    Missed-``finally`` / PYPOST-1315 TD-5 guard: do not call
    ``dispose_collections_export_fixture`` in the test body; registry autouse must
    dispose after the test. Desired end-state is asserted after that autouse
    teardown (fixture LIFO), not before it.
    """
    presenter, _manager = _make_presenter()
    panel = presenter.panel
    assert shiboken6.isValid(panel)

    # Deliberately omit dispose_collections_export_fixture (missed-finally / TD-5).
    _collections_export_end_state_checks.append(
        lambda: _assert_desired_collections_dispose_end_state(qapp, panel)
    )


@pytest.mark.timeout(360)
def test_b_bounded_collection_export_ui_subprocess_evidence_matrix() -> None:
    """B: bounded subprocess evidence / diagnostic matrix for the collections worker.

    Parent must survive any child native death. Fails only on historically matching
    native-crash codes. Zero-crash matrix plus dependency versions is the accepted
    diagnostic artifact when the restored host cannot reproduce SIGSEGV.
    """
    versions = _dependency_versions()
    results: list[tuple[int, str]] = []

    for attempt in range(1, _SUBPROCESS_ATTEMPT_BUDGET + 1):
        try:
            proc = _run_collection_export_ui_child()
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or "")[-2000:]
            stderr = (exc.stderr or "")[-2000:]
            pytest.fail(
                f"Attempt {attempt}/{_SUBPROCESS_ATTEMPT_BUDGET}: child timed out "
                f"after {_SUBPROCESS_TIMEOUT_S}s; versions={versions!r}\n"
                f"STDOUT tail:\n{stdout}\nSTDERR tail:\n{stderr}"
            )

        desc = _describe_returncode(proc.returncode)
        results.append((proc.returncode, desc))
        if proc.returncode in _NATIVE_CRASH_CODES:
            pytest.fail(
                f"Attempt {attempt}/{_SUBPROCESS_ATTEMPT_BUDGET}: collection export UI "
                f"worker native crash ({desc}); versions={versions!r}; "
                f"matrix={results!r}\n"
                f"STDOUT tail:\n{proc.stdout[-2000:]}\n"
                f"STDERR tail:\n{proc.stderr[-2000:]}"
            )

    assert results, "bounded evidence matrix must record at least one attempt"
    non_zero = [(code, desc) for code, desc in results if code != 0]
    assert not non_zero, (
        "Child runs must complete without unexpected non-native failures; "
        f"versions={versions!r}; matrix={results!r}"
    )
    # Diagnostic artifact (zero-crash path): versions + matrix remain in assertion
    # context above; roadmap records cause fork R-autouse when this stays green.
    assert all(code == 0 for code, _desc in results), (
        f"diagnostic zero-crash matrix expected on restored host; "
        f"versions={versions!r}; matrix={results!r}"
    )
