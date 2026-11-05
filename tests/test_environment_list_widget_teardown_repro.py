"""Environment list widget dispose contract + red→green drivers (PYPOST-1358).

Assertion polarities (ai-tasks/PYPOST-1358/20-architecture.md):

- **A-complete**: full ``dispose_qt_root`` → desired end-state (permanent positive
  guard).
- **A-incomplete**: close-only only (no ``deleteLater`` / DeferredDelete drain) →
  residual liveness. Permanent **green** negative control. Intentionally does
  *not* mirror the product suite's full teardown: after Step 4,
  ``tests/test_environment_list_widget.py`` still has ``finally: widget.close()``
  but also registers roots and disposes via autouse ``dispose_qt_root``.
- **R-dispose** (default red→green): apply the suite dispose path
  (``dispose_qt_root``, same helper as registry autouse), then assert the
  **desired** end-state. Step 3 **RED** on close-only survivors; Step 4 wired
  dispose into the product suite → **GREEN**.
- **B**: bounded subprocess of the thirteen-node list/import suite; fails only on
  the live native-crash class; zero-crash matrix + dependency versions is an
  accepted diagnostic artifact when SIGSEGV/SIGBUS is unavailable on the host.
"""

from __future__ import annotations

import importlib.metadata
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest
import shiboken6
from PySide6.QtWidgets import QApplication

from pypost.models.models import Environment
from pypost.ui.widgets.environments.environment_list_widget import EnvironmentListWidget
from tests.helpers.qt_widget_dispose import dispose_qt_root

pytestmark = pytest.mark.timeout(60)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ENV_LIST_WIDGET = "tests/test_environment_list_widget.py"
_NATIVE_CRASH_CODES = frozenset({-11, -7, 139, 135})
_SUBPROCESS_ATTEMPT_BUDGET = 3
_SUBPROCESS_TIMEOUT_S = 120.0


def _make_list_widget() -> EnvironmentListWidget:
    """Mirror ``tests/test_environment_list_widget.py`` ``_make_widget`` construction."""
    return EnvironmentListWidget(
        [Environment(name="Dev", variables={"HOST": "dev.example.com"})],
    )


def _leftover_environment_list_roots(qapp: QApplication) -> list[EnvironmentListWidget]:
    leftovers: list[EnvironmentListWidget] = []
    for top in qapp.topLevelWidgets():
        if not shiboken6.isValid(top):
            continue
        if isinstance(top, EnvironmentListWidget):
            leftovers.append(top)
    return leftovers


def _assert_desired_list_dispose_end_state(
    qapp: QApplication,
    widget: EnvironmentListWidget,
) -> None:
    """Desired dispose contract: root destroyed; no EnvironmentListWidget leftovers."""
    assert not shiboken6.isValid(widget), (
        "EnvironmentListWidget must be destroyed after dispose "
        "(close-only / incomplete teardown still leaves a live C++ object)"
    )
    leftovers = _leftover_environment_list_roots(qapp)
    assert leftovers == [], (
        "No EnvironmentListWidget roots may remain in QApplication.topLevelWidgets() "
        f"after dispose; still live: {leftovers!r}"
    )


def _suite_close_only(widget: EnvironmentListWidget) -> None:
    """Close-only path for A-incomplete (no DeferredDelete drain).

    The product list/import suite still calls ``widget.close()`` in ``finally``,
    but that is no longer its full teardown: registry autouse also runs
    ``dispose_qt_root``. This helper isolates the incomplete close-only path.
    """
    widget.close()


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
    for dist in ("PySide6", "shiboken6"):
        try:
            versions[dist] = importlib.metadata.version(dist)
        except importlib.metadata.PackageNotFoundError:
            versions[dist] = "not-installed"
    return versions


def _run_env_list_widget_child(
    *, timeout_s: float = _SUBPROCESS_TIMEOUT_S
) -> subprocess.CompletedProcess[str]:
    """Run the environment list widget suite in an isolated offscreen subprocess."""
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
            _ENV_LIST_WIDGET,
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


def test_a_complete_environment_list_dispose_reaches_desired_end_state(
    qapp: QApplication,
) -> None:
    """A-complete: full ``dispose_qt_root`` reaches the desired end-state (positive guard)."""
    widget = _make_list_widget()
    assert shiboken6.isValid(widget)

    dispose_qt_root(widget, qapp)

    _assert_desired_list_dispose_end_state(qapp, widget)


def test_a_incomplete_environment_list_close_only_leaves_residual_liveness(
    qapp: QApplication,
) -> None:
    """A-incomplete: close-only cleanup leaves residual liveness (green negative control).

    Applies ``close()`` only — no ``deleteLater`` / DeferredDelete drain. The
    product suite's residual ``finally: widget.close()`` is the same incomplete
    step, but suite teardown also disposes via registry autouse; this member
    must not use that full path. Opposite polarity of A-complete / R-dispose.
    """
    widget = _make_list_widget()
    assert shiboken6.isValid(widget)

    try:
        _suite_close_only(widget)
        assert shiboken6.isValid(widget), (
            "incomplete close-only cleanup must leave the EnvironmentListWidget "
            "C++ object live (negative control for why full dispose is required)"
        )
        leftovers = _leftover_environment_list_roots(qapp)
        assert leftovers, (
            "incomplete close-only cleanup must leave EnvironmentListWidget roots "
            "among topLevelWidgets (residual-liveness negative control)"
        )
    finally:
        # Assert liveness *before* full dispose so Step 4 autouse cannot swallow
        # this negative control; dispose here only to avoid polluting later tests.
        dispose_qt_root(widget, qapp)


def test_r_dispose_suite_close_only_reaches_desired_end_state(
    qapp: QApplication,
) -> None:
    """R-dispose: suite teardown path must reach desired end-state (Step 4 GREEN).

    Mirrors the product list/import suite dispose helper (``dispose_qt_root``,
    also used by registry autouse in ``tests/test_environment_list_widget.py``),
    then asserts the desired dispose contract. Was RED under close-only teardown
    (Step 3); stays green as a durable suite-teardown contract guard.
    """
    widget = _make_list_widget()
    assert shiboken6.isValid(widget)

    dispose_qt_root(widget, qapp)
    _assert_desired_list_dispose_end_state(qapp, widget)


@pytest.mark.timeout(360)
def test_b_bounded_environment_list_widget_subprocess_evidence_matrix() -> None:
    """B: bounded subprocess evidence / diagnostic matrix for the list/import worker.

    Parent must survive any child native death. Fails only on historically matching
    native-crash codes (−11 / −7 / 139 / 135). Zero-crash matrix plus dependency
    versions is the accepted diagnostic artifact when the host cannot reproduce
    post-PASS SIGSEGV/SIGBUS within the bound.
    """
    versions = _dependency_versions()
    results: list[tuple[int, str]] = []

    for attempt in range(1, _SUBPROCESS_ATTEMPT_BUDGET + 1):
        try:
            proc = _run_env_list_widget_child()
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
                f"Attempt {attempt}/{_SUBPROCESS_ATTEMPT_BUDGET}: environment list "
                f"widget worker native crash ({desc}); versions={versions!r}; "
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
    assert all(code == 0 for code, _desc in results), (
        f"diagnostic zero-crash matrix expected when host cannot reproduce; "
        f"versions={versions!r}; matrix={results!r}"
    )
