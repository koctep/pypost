"""Automated reproduction tests for PYPOST-1306.

Reproduces the triage failure mechanism where starved worker timeout
triggers premature timeout before pytest initializes and writes grandchild PID.
Also verifies deterministic termination with adequate timeout budget.
"""

from __future__ import annotations

import os
import signal
import time
from pathlib import Path

import pytest

from scripts.run_parallel_tests import (
    CLIParser,
    PytestArgvLayout,
    SubprocessTestExecutor,
    TestDiscovery,
)

pytestmark = pytest.mark.timeout(15)


def _setup_hang_test(tmp_path: Path) -> tuple[Path, Path]:
    """Create test harness files for grandchild process group tests."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    pid_file = tmp_path / "grandchild.pid"

    test_file = tests_dir / "test_hang_with_grandchild.py"
    test_file.write_text(
        "import subprocess\n"
        "import sys\n"
        "import time\n"
        "from pathlib import Path\n"
        "\n"
        "def test_hang():\n"
        f"    pid_file = Path({str(pid_file)!r})\n"
        "    proc = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        "    pid_file.write_text(str(proc.pid), encoding='utf-8')\n"
        "    time.sleep(30)\n",
        encoding="utf-8",
    )
    return test_file, pid_file


@pytest.mark.timeout(15)
def test_starved_worker_timeout_reproduces_premature_pid_failure(tmp_path: Path) -> None:
    """Reproduce triage failure: starved worker timeout expires before PID file write."""
    test_file, pid_file = _setup_hang_test(tmp_path)

    config = CLIParser().parse_args(
        [
            "--workers=1",
            "--worker-timeout=0.2",
            "-o",
            "addopts=",
            str(test_file),
        ],
        repo_root=tmp_path,
    )
    executor = SubprocessTestExecutor(config)
    layout = PytestArgvLayout.from_project(
        tmp_path, config.original_argv, config.runner_spans
    )
    discovery = TestDiscovery().discover(
        repo_root=tmp_path, target_records=config.target_records
    )
    assert not discovery.errors
    assert len(discovery.units) == 1

    grandchild_pid: int | None = None
    try:
        result = executor.run_dispatch_unit(
            unit=discovery.units[0],
            layout=layout,
            all_target_records=discovery.records,
            index=1,
            total=1,
            coverage_plan=None,
        )
        assert result.status == "timed_out"

        # Under starved worker timeout (0.2s), the worker times out during pytest
        # startup before test_hang writes the grandchild PID file.
        # This confirms that starving the timeout budget reproduces the exact
        # premature timeout before grandchild PID creation observed in the triage report.
        assert not pid_file.exists(), (
            "Expected starved worker timeout to prevent PID file creation; got PID"
        )
    finally:
        if grandchild_pid is not None:
            try:
                os.kill(grandchild_pid, signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass
        elif pid_file.exists():
            try:
                pid = int(pid_file.read_text(encoding="utf-8").strip())
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, OSError, ValueError):
                pass


@pytest.mark.timeout(15)
def test_sufficient_worker_timeout_terminates_grandchild_deterministically(
    tmp_path: Path,
) -> None:
    """Verify sufficient worker timeout allows test initialization and terminates group."""
    test_file, pid_file = _setup_hang_test(tmp_path)

    config = CLIParser().parse_args(
        [
            "--workers=1",
            "--worker-timeout=3.0",
            "-o",
            "addopts=",
            str(test_file),
        ],
        repo_root=tmp_path,
    )
    executor = SubprocessTestExecutor(config)
    layout = PytestArgvLayout.from_project(
        tmp_path, config.original_argv, config.runner_spans
    )
    discovery = TestDiscovery().discover(
        repo_root=tmp_path, target_records=config.target_records
    )
    assert not discovery.errors
    assert len(discovery.units) == 1

    grandchild_pid: int | None = None
    try:
        result = executor.run_dispatch_unit(
            unit=discovery.units[0],
            layout=layout,
            all_target_records=discovery.records,
            index=1,
            total=1,
            coverage_plan=None,
        )
        assert result.status == "timed_out"

        assert pid_file.exists(), (
            f"Grandchild PID file was not created; stdout={result.stdout} stderr={result.stderr}"
        )
        grandchild_pid = int(pid_file.read_text(encoding="utf-8").strip())

        deadline = time.perf_counter() + 1.0
        is_alive = True
        while time.perf_counter() < deadline:
            try:
                os.kill(grandchild_pid, 0)
                time.sleep(0.05)
            except (ProcessLookupError, OSError):
                is_alive = False
                break

        assert not is_alive, (
            f"Grandchild process {grandchild_pid} is still alive after worker timeout"
        )
    finally:
        if grandchild_pid is not None:
            try:
                os.kill(grandchild_pid, signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass
        elif pid_file.exists():
            try:
                pid = int(pid_file.read_text(encoding="utf-8").strip())
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, OSError, ValueError):
                pass
