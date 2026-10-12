"""Offline missing-runner preparation contracts for PYPOST-1299."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

import tests.test_pytest_exit_policy as exit_policy

pytestmark = pytest.mark.timeout(20)


@pytest.mark.parametrize("target", ["test", "test-cov"])
def test_missing_runner_check_prepares_offline(
    target: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run original assertions without permitting installation or venv bootstrap."""
    real_run = subprocess.run
    delegated: list[subprocess.CompletedProcess[str]] = []

    def run_target_only(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert command[0] == "make" and command[-1] == target, (
            "missing-runner preparation must be offline; unexpected preparation "
            f"subprocess: {command!r}"
        )
        assert all("=" in argument for argument in command[1:-1]), (
            f"only the isolated make {target} target may run: {command!r}"
        )
        assert Path(kwargs["cwd"]) == tmp_path
        assert 0 < kwargs["timeout"] <= 60
        assert not (tmp_path / "scripts" / "run_parallel_tests.py").exists()

        # Check prerequisites before delegation so an incomplete fixture cannot
        # launch Make's venv/pip recipes and contact the network.
        version = f"{sys.version_info.major}.{sys.version_info.minor}"
        venv = tmp_path / ".venv"
        marker = venv / f".initialized-{version}"
        metadata = tmp_path / "pyproject.toml"
        assert (venv / "bin" / "python").exists(), "offline interpreter is missing"
        assert marker.exists(), "offline initialization stamp is missing"
        for extra in ("test", "otel"):
            stamp = venv / f".venv-{extra}-{version}"
            assert stamp.exists(), f"offline {extra} stamp is missing"
            assert stamp.stat().st_mtime_ns >= max(
                marker.stat().st_mtime_ns, metadata.stat().st_mtime_ns
            ), f"offline {extra} stamp would trigger dependency installation"

        # Keep the real target and its diagnostics; cap this regression test's
        # subprocess wait independently of the original check's timeout budget.
        kwargs["timeout"] = 10
        result = real_run(command, **kwargs)
        delegated.append(result)
        return result

    monkeypatch.setattr(exit_policy.subprocess, "run", run_target_only)
    check = (
        exit_policy.test_make_test_fails_closed_when_parallel_runner_is_missing
        if target == "test"
        else exit_policy.test_make_test_cov_fails_closed_when_parallel_runner_is_missing
    )
    started = time.monotonic()
    check(tmp_path)
    assert time.monotonic() - started < 10, "offline negative check exceeded its budget"
    assert len(delegated) == 1, "negative check must delegate exactly one real Make target"
    output = delegated[0].stdout + delegated[0].stderr
    assert "pip install" not in output.lower(), "negative check attempted installation"
    assert "-m venv" not in output.lower(), "negative check attempted venv creation"
    assert not (tmp_path / "scripts" / "run_parallel_tests.py").exists()
