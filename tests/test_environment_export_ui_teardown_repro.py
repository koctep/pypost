"""Teardown contract for PYPOST-1315 — export UI Qt lifetime / dispose.

Asserts the desired dispose end-state from ai-tasks/PYPOST-1315/20-architecture.md:

- After disposal, ``shiboken6.isValid(root)`` is False.
- No leftover ``EnvironmentListWidget`` roots remain in ``QApplication.topLevelWidgets()``.

Step 4 wires ``dispose_qt_root`` (close → processEvents → deleteLater →
``sendPostedEvents(DeferredDelete)`` → processEvents) so these assertions stay green.

Optional bounded subprocess stress records native-crash evidence without letting a
child SIGSEGV kill the parent pytest worker.
"""

from __future__ import annotations

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
_ENV_EXPORT_UI = "tests/test_environment_export_ui.py"
# Historically observed native deaths for this worker class (SIGSEGV / SIGBUS / 128+11).
_NATIVE_CRASH_CODES = frozenset({-11, -7, 139, 135})
_SUBPROCESS_ATTEMPT_BUDGET = 5
_SUBPROCESS_TIMEOUT_S = 120.0


def _leftover_environment_list_roots(qapp: QApplication) -> list[EnvironmentListWidget]:
    leftovers: list[EnvironmentListWidget] = []
    for top in qapp.topLevelWidgets():
        if not shiboken6.isValid(top):
            continue
        if isinstance(top, EnvironmentListWidget):
            leftovers.append(top)
    return leftovers


def _describe_returncode(returncode: int) -> str:
    if returncode >= 0:
        return f"exit code {returncode}"
    raw_signum = -returncode
    try:
        name = signal.Signals(raw_signum).name
    except ValueError:
        name = "unknown signal"
    return f"killed by signal {raw_signum} ({name})"


def _run_env_export_ui_child(
    *, timeout_s: float = _SUBPROCESS_TIMEOUT_S
) -> subprocess.CompletedProcess[str]:
    """Run the environment export UI suite in an isolated offscreen subprocess."""
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
            _ENV_EXPORT_UI,
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


def test_incomplete_env_dispose_leaves_no_live_environment_list_widget(
    qapp: QApplication,
) -> None:
    """Desired dispose contract: root is invalid and absent from topLevelWidgets.

    Uses ``dispose_qt_root`` (DeferredDelete via ``sendPostedEvents``) — green once
    Step 4 disposal is wired.
    """
    widget = EnvironmentListWidget(
        [Environment(name="Dev", variables={"HOST": "dev.example.com"})],
    )
    assert shiboken6.isValid(widget)
    assert widget in qapp.topLevelWidgets() or widget.isWindow()

    dispose_qt_root(widget, qapp)

    assert not shiboken6.isValid(widget), (
        "EnvironmentListWidget must be destroyed after dispose "
        "(incomplete close/deleteLater/single processEvents still leaves a live C++ object)"
    )
    leftovers = _leftover_environment_list_roots(qapp)
    assert leftovers == [], (
        "No EnvironmentListWidget roots may remain in QApplication.topLevelWidgets() "
        f"after dispose; still live: {leftovers!r}"
    )


def test_bounded_env_export_ui_subprocess_evidence_matrix() -> None:
    """Bounded subprocess evidence for the env export UI worker (architecture §B).

    Runs a fixed attempt budget of isolated children. Parent must survive any
    child native death (returncode observed, not raised into this process).

    This test archives the return-code matrix. It fails only when a child dies
    with the historical native-crash class (desired post-fix exit is 0). When
    the host cannot reproduce SIGSEGV within the bound, all-zero results are
    accepted and contract test A remains the mandatory red gate.
    """
    results: list[tuple[int, str]] = []

    for attempt in range(1, _SUBPROCESS_ATTEMPT_BUDGET + 1):
        try:
            proc = _run_env_export_ui_child()
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or "")[-2000:]
            stderr = (exc.stderr or "")[-2000:]
            pytest.fail(
                f"Attempt {attempt}/{_SUBPROCESS_ATTEMPT_BUDGET}: child timed out "
                f"after {_SUBPROCESS_TIMEOUT_S}s\nSTDOUT tail:\n{stdout}\n"
                f"STDERR tail:\n{stderr}"
            )

        desc = _describe_returncode(proc.returncode)
        results.append((proc.returncode, desc))
        if proc.returncode in _NATIVE_CRASH_CODES:
            pytest.fail(
                f"Attempt {attempt}/{_SUBPROCESS_ATTEMPT_BUDGET}: environment export UI "
                f"worker native crash ({desc}); matrix={results!r}\n"
                f"STDOUT tail:\n{proc.stdout[-2000:]}\n"
                f"STDERR tail:\n{proc.stderr[-2000:]}"
            )

    assert results, "bounded evidence matrix must record at least one attempt"
    non_zero = [(code, desc) for code, desc in results if code != 0]
    assert not non_zero, (
        "Child runs must complete without unexpected non-native failures; "
        f"matrix={results!r}"
    )
