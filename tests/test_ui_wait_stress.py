"""PYPOST-1152: forward-looking regression guard for ``tests/test_ui_wait.py``.

Background (see ``ai-tasks/PYPOST-1152/20-architecture.md`` for full evidence)
--------------------------------------------------------------------------
``ai-tasks/PYPOST-1149/60-tech-debt.md`` carried a tech-debt row alleging a
PySide6/Shiboken segfault in ``tests/test_ui_wait.py`` when run as an isolated
subprocess. PYPOST-1152 Steps 1 and 2 investigated that claim directly:
**47/47 clean executions** of ``tests/test_ui_wait.py`` were observed this
session (17 orchestrator pre-investigation runs + 20 additional sequential
isolated runs + 8 concurrent isolated runs + 2 final sanity re-runs while
closing Steps 2 and 3), across five invocation shapes (direct ``pytest``,
``make test PYTEST_ARGS=...``, embedded in the full 311-file suite, genuine
concurrent multi-subprocess load, and a final standalone re-run) — zero
segfaults, core dumps, or ``Fatal Python error`` output. A full code-review
pass of both ``tests/test_ui_wait.py`` and ``pypost/agent/ui_wait.py`` found
no PyPost-owned defect pattern matching any of the four documented failure
classes in ``doc/dev/testing.md`` § Failure Class Taxonomy.

**This is explicitly the opposite evidence shape from PYPOST-1040's**
``tests/test_agent_dialog_settle_teardown_stress.py``, which this file is
structurally modeled on. That test stresses a module with a *measured*,
*confirmed* 32.5% (13/40) native crash rate from its own Step 2 ablation, and
is correctly marked ``xfail(strict=False)`` to document a known, currently
outstanding upstream defect. This module has **no confirmed live defect** —
Branch C of this task's Definition of Done is non-reproduction, not a fix or
mitigation. Consequently this test ships **green, unmarked, with no
``xfail``**: it is a tripwire for a *future* regression, not a repro of a
*current* one, and if it ever goes red that is a first-class CI failure
requiring immediate triage — not a pre-excused, expected-to-fail state.

Why a stress test at all, if there is no confirmed defect?
------------------------------------------------------------
The original PYPOST-1149 filing that seeded this investigation gave no
reproduction steps, crash log, backtrace, or core dump to work backward from.
47/47 clean runs bounds a hypothetical steady per-run crash rate at roughly
<=6.5% with ~95% confidence (rule of three on a zero-event sample) — it does
not prove the rate is exactly zero, nor rule out a rarer or
environment-specific trigger. This guard exists so that *if* such a defect is
reintroduced (or was always present at a low enough rate to evade this
session's sampling), CI catches it automatically going forward, with useful
forensic evidence attached, rather than relying on another manual
investigation sprint like this one.

Why ``STRESS_ITERATIONS = 15`` (not PYPOST-1040's 25)
---------------------------------------------------------
PYPOST-1040's N=25 was sized against a *measured* 32.5% crash rate for >99.9%
detection power. This task has no measured current rate to size against —
that evidence does not exist and inventing one would misrepresent the
finding. Instead N=15 is sized against a *hypothetical future* regression: if
a code change someday reintroduces even a modest ~20%-per-run native crash
rate (an order of magnitude below PYPOST-1040's confirmed 32.5%, chosen as a
proportionate "catch it reasonably fast, don't over-invest in an unconfirmed
problem" threshold), ``P(>=1 detected in 15) = 1 - 0.80**15 ~= 96.5%``. This
keeps the ``make test-slow`` wall-clock cost proportionate to a module with
no confirmed live defect while still giving meaningful forward detection
power.

Why ``PYTHONFAULTHANDLER=1`` (new relative to the PYPOST-1040 precedent)
--------------------------------------------------------------------------
The single biggest constraint on the PYPOST-1152 investigation was that the
original filing left no forensic artifact to work backward from. Setting
``PYTHONFAULTHANDLER=1`` in every child's environment means that if this
guard ever does catch a real native crash, Python's ``faulthandler`` module
dumps a best-effort native traceback to the child's stderr at the moment of
the fault — which this test already captures (stderr tail) and surfaces in
its failure message. This closes the "no captured backtrace" gap the
original PYPOST-1149 filing suffered from, without requiring any new tooling
or a manual ``lldb -c core`` session unless the faulthandler dump proves
insufficient (``doc/dev/gui_testing.md``'s existing ELF core-dump
troubleshooting row remains the fallback for a fault outside Python's
traceback capture, e.g. a true SIGSEGV inside Qt/Shiboken C code before any
Python frame is reachable).
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

# do-testing (mandatory per-test timeout) + repo convention: subprocess stress
# tests are marked slow so they are excluded from the default `-m "not slow"`
# addopts (pyproject.toml) and only run via `make test-slow` / explicit opt-in.
# 240s covers STRESS_ITERATIONS=15 children at test_ui_wait.py's observed
# ~6-9s/child baseline (~135s worst case) plus generous headroom for slower
# hosts and any child that needs the full CHILD_TIMEOUT_S before being
# declared hung.
pytestmark = [
    pytest.mark.timeout(240),
    pytest.mark.slow,
]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TARGET_MODULE = "tests/test_ui_wait.py"

# See module docstring § "Why STRESS_ITERATIONS = 15" for the full sizing
# rationale — this is deliberately smaller than PYPOST-1040's 25 because there
# is no measured current crash rate to size detection power against; N=15
# gives ~96.5% detection power against a hypothetical future ~20%-per-run
# regression while keeping this guard's routine `make test-slow` cost modest
# for a module with no confirmed live defect.
STRESS_ITERATIONS = 15
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


def test_all_child_runs_exit_zero_under_repeated_isolated_stress() -> None:
    """Spawn STRESS_ITERATIONS independent child pytest runs of
    ``tests/test_ui_wait.py`` and assert every one exits 0.

    This is a forward-looking regression guard, not a repro: PYPOST-1152
    found no confirmed defect (47/47 clean runs across five invocation
    shapes, no PyPost-owned pattern on code review — see module docstring).
    A non-zero/negative exit (e.g. SIGSEGV=-11/139, SIGBUS=-7/135, or any
    other crash-signal-derived code) on any child here would be genuine,
    unexpected CI-blocking signal warranting an immediate, first-class
    investigation — not an expected/pre-excused outcome. Each child is a
    fully separate OS process, isolated with its own bounded timeout, so a
    crash or hang in one child cannot take down this test's own process or
    the other children.
    """
    env = {
        **os.environ,
        "QT_QPA_PLATFORM": "offscreen",
        # See module docstring § PYTHONFAULTHANDLER — captures a best-effort
        # native traceback on stderr if a child ever does crash, closing the
        # "no captured backtrace" gap left by the original PYPOST-1149 filing.
        "PYTHONFAULTHANDLER": "1",
    }
    failures: list[str] = []
    started_at = time.monotonic()

    for index in range(STRESS_ITERATIONS):
        try:
            result = _run_child(env)
        except subprocess.TimeoutExpired as exc:
            failures.append(
                f"child #{index}: timed out after {CHILD_TIMEOUT_S}s "
                f"(hang, not a crash signal — not observed in any prior "
                f"PYPOST-1152 evidence)\n"
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

    duration_s = time.monotonic() - started_at

    if failures:
        summary = (
            f"{len(failures)}/{STRESS_ITERATIONS} child `pytest "
            f"{_TARGET_MODULE}` runs crashed or exited non-zero under "
            "repeated isolated-subprocess stress. PYPOST-1152's own "
            "investigation found NO confirmed defect (47/47 clean runs "
            "across five invocation shapes, no PyPost-owned pattern on code "
            "review) — this is a genuine, unexpected regression, not an "
            "excused/known outcome. Reopen a PYPOST-1152-class investigation "
            "using the stdout/stderr (and any faulthandler traceback) below "
            "as the starting forensic evidence:\n\n" + "\n\n".join(failures)
        )
        _LOGGER.error(summary)
        pytest.fail(summary)

    # NOTICE-equivalent (stdlib logging has no NOTICE level; INFO is the
    # nearest standard level): a one-line "this guard ran and passed" summary
    # so a CI log scan sees the check executed and its outcome without
    # requiring `pytest -v`. Deliberately just counts/timing — no per-child
    # stdout/stderr on the happy path (that stays failure-only, above).
    _LOGGER.info(
        "PYPOST-1152 stress guard passed: %d/%d isolated `pytest %s` child "
        "runs exited 0 in %.1fs",
        STRESS_ITERATIONS,
        STRESS_ITERATIONS,
        _TARGET_MODULE,
        duration_s,
    )
