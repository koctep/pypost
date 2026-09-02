"""PYPOST-1251: bounded child-process guard for alert-reload teardown."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

pytestmark = [pytest.mark.timeout(90), pytest.mark.slow]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TARGET = "tests/test_main_window_alert_reload.py"
_ITERATIONS = 3
_CHILD_TIMEOUT_S = 20.0
_CHILD_ENV = {
    "QT_QPA_PLATFORM": "offscreen",
    "PYTHONFAULTHANDLER": "1",
}


@dataclass(frozen=True)
class _ChildOutcome:
    command: tuple[str, ...]
    environment: dict[str, str]
    duration_s: float
    classification: str
    result: subprocess.CompletedProcess[str] | None = None
    timeout: subprocess.TimeoutExpired | None = None

    def report(self) -> str:
        details = [
            f"command: {' '.join(self.command)}",
            f"environment: {self.environment}",
            f"duration: {self.duration_s:.3f}s",
            f"classification: {self.classification}",
        ]
        if self.result is not None:
            details.extend(
                [
                    f"stdout tail:\n{self.result.stdout[-2000:]}",
                    f"stderr tail:\n{self.result.stderr[-2000:]}",
                ]
            )
        if self.timeout is not None:
            details.extend(
                [
                    f"stdout tail:\n{(self.timeout.stdout or '')[-2000:]}",
                    f"stderr tail:\n{(self.timeout.stderr or '')[-2000:]}",
                ]
            )
        return "\n".join(details)


def _run_child() -> _ChildOutcome:
    command = (sys.executable, "-m", "pytest", _TARGET, "-q")
    environment = {key: _CHILD_ENV[key] for key in sorted(_CHILD_ENV)}
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=_REPO_ROOT,
            env={**os.environ, **_CHILD_ENV},
            capture_output=True,
            text=True,
            timeout=_CHILD_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return _ChildOutcome(
            command=command,
            environment=environment,
            duration_s=time.monotonic() - started,
            classification="timeout",
            timeout=exc,
        )

    classification = "normal_exit" if result.returncode == 0 else "nonzero_exit"
    if result.returncode < 0:
        classification = "signal_exit"
    return _ChildOutcome(
        command=command,
        environment=environment,
        duration_s=time.monotonic() - started,
        classification=classification,
        result=result,
    )


def _returncode_description(returncode: int) -> str:
    if returncode >= 0:
        return f"exit code {returncode}"
    signum = -returncode
    try:
        name = signal.Signals(signum).name
    except ValueError:
        name = "unknown signal"
    return f"signal {signum} ({name})"


def test_clean_control_child_completes() -> None:
    """A bounded isolated alert-reload run must produce a normal exit."""
    outcome = _run_child()
    assert outcome.classification == "normal_exit", (
        "clean control did not complete normally:\n" + outcome.report()
    )


def test_alert_reload_stays_alive_across_repeated_child_runs() -> None:
    """Detect a native crash without letting it terminate the parent runner."""
    outcomes: list[_ChildOutcome] = []
    for index in range(_ITERATIONS):
        outcomes.append(_run_child())

    failures = [
        f"child {index + 1}:\n{outcome.report()}"
        for index, outcome in enumerate(outcomes)
        if outcome.classification != "normal_exit"
    ]
    assert not failures, "alert-reload child crash/timeout evidence:\n" + "\n\n".join(
        failures
    )
