"""PYPOST-1040: subprocess-based stress detector for the intermittent post-PASS Qt
teardown crash in ``tests/test_agent_dialog_settle_e2e.py``.

Background (see ``ai-tasks/PYPOST-1040/20-architecture.md`` for full evidence)
--------------------------------------------------------------------------
``tests/test_agent_dialog_settle_e2e.py`` intermittently prints both of its tests
as PASSED and then the *process* exits with SIGSEGV or SIGBUS during Qt/PySide
widget teardown — specifically inside CPython's cyclic garbage collector, forced
by pytest's own ``_pytest/unraisableexception.py`` plugin at session end
(``gc_collect_harder()``: 5 rounds of ``gc.collect()``), which then triggers a
Shiboken ``QWidgetItem`` destructor use-after-free/double-free somewhere in
``SettingsDialog``'s nested ``QVBoxLayout``/``QFormLayout``/seven-section widget
subtree. Step 2's ablation confirmed the mechanism precisely:

- Disabling the forced-GC plugin (``-p no:unraisableexception``) eliminates the
  crash entirely (0/20 vs. 13/40 with it enabled) — the crash is *at* that forced
  collection, not merely correlated with it.
- Removing the Settings dialog from the exercised path (a no-dialog
  ``AgentAppSession`` smoke test, same launch/shutdown machinery) also
  eliminates the crash (0/20) — the trigger surface is specifically
  ``SettingsDialog``'s widget/layout composition, not ``AgentAppSession``
  teardown in general.

Step 2 measured a 32.5% (13/40) single-run crash rate for
``pytest tests/test_agent_dialog_settle_e2e.py`` on this exact Linux /
Python 3.13.5 / PySide6-shiboken6 6.11.1 combination (the same binding version
CI pins). This matches the upstream ``QWidgetItem``/``QLayout`` lifecycle bug
class documented in PYSIDE-665 / PYSIDE-2482 / PYSIDE-1919 — i.e. it is an
**upstream PySide6/shiboken6 defect, not a PyPost-owned defect** (no raw
``QLayoutItem``/``QWidgetItem`` reference is held anywhere in ``pypost/``, and
``AgentAppSession.shutdown()`` completes and logs success before the crash
occurs, every time).

Why this test is a *stress detector*, not a single-shot repro
---------------------------------------------------------------
The crash is a probabilistic (~1/3 per run) *native* process crash inside a
third-party C-extension's GC-time object destruction. It kills the child
interpreter before any in-process assertion could observe it, and a majority of
individual runs look completely clean. So instead of a deterministic
single-run assertion, this test spawns many independent child ``pytest``
subprocesses of the target module (each isolated so a segfault kills only the
child, never this test's own process) and asserts every child exits ``0``. At
the measured 32.5% single-run rate, ``STRESS_ITERATIONS = 25`` gives
``P(>=1 crash) = 1 - 0.675**25 ≈ 99.99%`` detection power if the defect is
still present.

Settlement outcome (PYPOST-1115 / PYPOST-1211)
-------------------------------------------------
Under epic PYPOST-1115 (mitigation evaluated in PYPOST-1209, PYPOST-1210, and
PYPOST-1211), application-side mitigations (breaking reference cycles in
``SettingsDialog``, explicit deferred delete processing upon modal dismissal,
and controlled garbage collection during ``AgentAppSession.shutdown()``) were
implemented and verified against this stress detector. The empirical crash rate
dropped to 0/25 (0.0% crashes, >99.99% detection power), fully resolving the
intermittent process teardown crash while preserving 100% green functional settle
assertions. Per the evaluation contract, the ``xfail`` marker has been removed
and the test runs as an active regression barrier under ``pytest.mark.slow``.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

# do-testing (mandatory per-test timeout) + repo convention: subprocess stress
# tests are marked slow so they are excluded from the default `-m "not slow"`
# addopts (pyproject.toml) and only run via `make test-slow` / explicit opt-in.
# 150s covers STRESS_ITERATIONS=25 children at the measured ~2s/child baseline
# (~50s) plus generous headroom for slower CI hosts and any crashing children'
# OS-level teardown overhead.
pytestmark = [
    pytest.mark.timeout(150),
    pytest.mark.slow,
]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TARGET_MODULE = "tests/test_agent_dialog_settle_e2e.py"

# Step 2 (ai-tasks/PYPOST-1040/20-architecture.md) recommended N=25 for >99.9%
# detection power at the measured 32.5% per-run crash rate. Keep this the
# committed default for this test's real/ongoing use — do not shrink it for
# convenience; a smaller N was used only for Step 3's own bounded confirmation
# run (invoked separately, outside this file, not by lowering this constant).
STRESS_ITERATIONS = 25
CHILD_TIMEOUT_S = 30.0

_LOGGER = logging.getLogger(__name__)


def _run_child(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run one isolated child ``pytest`` invocation of the target module."""
    return subprocess.run(
        [sys.executable, "-m", "pytest", _TARGET_MODULE, "-q"],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=CHILD_TIMEOUT_S,
        check=False,
    )


def _describe_returncode(returncode: int) -> str:
    """Render a subprocess return code, naming the signal for negative codes."""
    if returncode >= 0:
        return f"exit code {returncode}"
    raw_signum = -returncode
    try:
        name = signal.Signals(raw_signum).name
    except ValueError:
        name = "unknown signal"
    return f"killed by signal {raw_signum} ({name})"


def test_all_child_runs_exit_zero_under_repeated_teardown_stress() -> None:
    """Spawn STRESS_ITERATIONS independent child pytest runs of the dialog-settle
    e2e module and assert every one exits 0.

    A non-zero/negative exit (SIGSEGV=-11/139, SIGBUS=-7/135, or any other
    crash-signal-derived code) on any child is evidence of the PYPOST-1040
    upstream PySide6/shiboken6 QWidgetItem GC-teardown crash described in the
    module docstring above. Each child is a fully separate OS process so a
    crash there cannot take down this test's own process/assertions.
    """
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    failures: list[str] = []

    for index in range(STRESS_ITERATIONS):
        try:
            result = _run_child(env)
        except subprocess.TimeoutExpired as exc:
            failures.append(
                f"child #{index}: timed out after {CHILD_TIMEOUT_S}s "
                f"(hang, not a crash signal — not observed in Step 2 data)\n"
                f"stdout tail: {(exc.stdout or '')[-1000:]!r}\n"
                f"stderr tail: {(exc.stderr or '')[-500:]!r}"
            )
            continue

        if result.returncode != 0:
            failures.append(
                f"child #{index}: {_describe_returncode(result.returncode)}\n"
                f"stdout tail:\n{result.stdout[-2000:]}\n"
                f"stderr tail:\n{result.stderr[-1000:]}"
            )

    if failures:
        summary = (
            f"{len(failures)}/{STRESS_ITERATIONS} child `pytest {_TARGET_MODULE}` "
            "runs crashed or exited non-zero during Qt/PySide teardown "
            "(PYPOST-1040 upstream PySide6/shiboken6 QWidgetItem GC-teardown "
            "defect — see this file's module docstring and "
            "ai-tasks/PYPOST-1040/20-architecture.md):\n\n"
            + "\n\n".join(failures)
        )
        _LOGGER.warning(summary)
        pytest.fail(summary)
