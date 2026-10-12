"""Offline regressions for bounded shared Make fixture readiness (PYPOST-1298)."""

from __future__ import annotations

import errno
import fcntl
import multiprocessing
import os
import queue
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from tests import makefile_test_helpers as helpers

pytestmark = pytest.mark.timeout(30)


@pytest.mark.parametrize("runner_watchdog", [False, True])
@pytest.mark.parametrize("nonzero_exit", [False, True])
def test_preparation_failure_terminates_descendants(
    tmp_path: Path, runner_watchdog: bool, nonzero_exit: bool,
) -> None:
    """Exercise real subprocess cleanup without an external prerequisite service."""
    from scripts.run_parallel_tests import _run_fixture_preparation

    pid_file = tmp_path / "descendant.pid"
    command = [sys.executable, "-c", (
        "import subprocess, sys, time; from pathlib import Path; "
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'], "
        "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
        f"Path({str(pid_file)!r}).write_text(str(child.pid)); "
        + ("sys.exit(7)" if nonzero_exit else "time.sleep(30)")
    )]
    try:
        expected_error = (
            subprocess.CalledProcessError if nonzero_exit else subprocess.TimeoutExpired
        )
        with pytest.raises(expected_error) as failure:
            if runner_watchdog:
                _run_fixture_preparation(command, cwd=tmp_path, timeout=1)
            else:
                helpers._run_preparation_command(command, timeout=1)
        if nonzero_exit:
            assert failure.value.returncode == 7
        assert pid_file.is_file(), "descendant did not start before preparation failed"
        pid = int(pid_file.read_text(encoding="utf-8"))
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            state_file = Path(f"/proc/{pid}/stat")
            if not state_file.exists() or state_file.read_text().split()[2] == "Z":
                break
            time.sleep(0.05)
        else:
            pytest.fail("preparation failure left a running descendant")
    finally:
        if pid_file.is_file():
            try:
                os.kill(int(pid_file.read_text(encoding="utf-8")), 9)
            except ProcessLookupError:
                pass


@pytest.fixture
def private_shared_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Never prepare, invalidate, or delete the real shared environment."""
    monkeypatch.setattr(helpers.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(helpers, "_SHARED_BASE_VENV", None)
    return tmp_path / f"pypost_shared_base_venv_{helpers.PYTHON_VERSION}" / ".venv"


def _seed_interpreter(venv: Path) -> None:
    interpreter = venv / "bin" / "python"
    interpreter.parent.mkdir(parents=True, exist_ok=True)
    interpreter.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8")
    interpreter.chmod(0o755)


def _successful_command(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    if "venv" in cmd:
        _seed_interpreter(Path(cmd[-1]))
    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")


def _hold_lock(path: str, ready: Any, release: Any) -> None:
    with open(path, "w", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ready.set()
        if not release.wait(timeout=5):
            raise RuntimeError("test lock owner was not released")


def test_unrelated_lock_error_propagates_without_polling(
    private_shared_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(lock: Any, operation: int) -> None:
        raise OSError(errno.EIO, "lock filesystem unavailable")

    monkeypatch.setattr(helpers.fcntl, "flock", fail)
    with pytest.raises(OSError, match="lock filesystem unavailable"):
        helpers._get_shared_base_venv()
    assert not (private_shared_root / helpers.MARKER_NAME).exists()


def test_lock_contention_expires_without_blocking_operation(
    private_shared_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = multiprocessing.get_context("fork")
    ready, release = ctx.Event(), ctx.Event()
    lock_path = private_shared_root.parent.with_suffix(".lock")
    owner = ctx.Process(target=_hold_lock, args=(str(lock_path), ready, release))
    owner.start()
    now = [0.0]
    attempts: list[int] = []
    real_flock = fcntl.flock

    def bounded_flock(lock: Any, operation: int) -> None:
        attempts.append(operation)
        if operation == fcntl.LOCK_EX:
            raise RuntimeError("unbounded blocking flock attempted")
        real_flock(lock, operation)

    def sleep(seconds: float) -> None:
        assert 0 < seconds <= 0.05
        now[0] += seconds

    monkeypatch.setattr(helpers.fcntl, "flock", bounded_flock)
    monkeypatch.setattr(helpers, "time", SimpleNamespace(monotonic=lambda: now[0], sleep=sleep))
    try:
        assert ready.wait(timeout=2), "lock owner did not become ready"
        with pytest.raises(RuntimeError, match=r"(?i)lock.*(deadline|budget|timeout|timed out)"):
            helpers._get_shared_base_venv()
        assert fcntl.LOCK_EX not in attempts
        assert 20 <= now[0] <= 20.05
        assert not (private_shared_root / helpers.MARKER_NAME).exists()
    finally:
        release.set()
        owner.join(timeout=2)
        if owner.is_alive():
            owner.terminate()
            owner.join(timeout=2)
        assert not owner.is_alive()


def test_stale_process_cache_requires_published_readiness(
    private_shared_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_shared_root.mkdir(parents=True)
    monkeypatch.setattr(helpers, "_SHARED_BASE_VENV", private_shared_root)
    monkeypatch.setattr(helpers, "_run_preparation_command", _successful_command)
    result = helpers._get_shared_base_venv()
    assert (result / helpers.MARKER_NAME).is_file(), "incomplete cached directory was returned"
    assert (result / "bin" / "python").is_file()


def test_marker_without_interpreter_is_not_ready(
    private_shared_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_shared_root.mkdir(parents=True)
    (private_shared_root / helpers.MARKER_NAME).touch()
    monkeypatch.setattr(helpers, "_run_preparation_command", _successful_command)
    assert (helpers._get_shared_base_venv() / "bin" / "python").is_file()


def test_bootstrap_commands_share_one_remaining_budget(
    private_shared_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = [0.0]
    budgets: list[float | None] = []
    commands: list[list[str]] = []

    def run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        commands.append(cmd)
        budgets.append(kwargs.get("timeout"))
        now[0] += 3
        return _successful_command(cmd, **kwargs)

    clock = SimpleNamespace(monotonic=lambda: now[0], sleep=lambda _: None)
    monkeypatch.setattr(helpers, "time", clock)
    monkeypatch.setattr(helpers, "_run_preparation_command", run)
    result = helpers._get_shared_base_venv()
    assert len(budgets) >= 3, "bootstrap must validate imports before publishing readiness"
    assert any("pytest" in " ".join(cmd) and "flake8" in " ".join(cmd)
               and "import" in " ".join(cmd) for cmd in commands)
    assert all(budget is not None and 0 < budget <= 20 for budget in budgets)
    assert all(later < earlier for earlier, later in zip(budgets, budgets[1:]))
    assert (result / helpers.MARKER_NAME).is_file()


@pytest.mark.parametrize("failure", ["timeout", "nonzero"])
def test_failed_bootstrap_releases_lock_and_allows_clean_retry(
    private_shared_root: Path, monkeypatch: pytest.MonkeyPatch, failure: str,
) -> None:
    budgets: list[float | None] = []

    def fail(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        budgets.append(kwargs.get("timeout"))
        private_shared_root.mkdir(parents=True, exist_ok=True)
        (private_shared_root / "partial-install").touch()
        if failure == "timeout":
            raise subprocess.TimeoutExpired(cmd, 1, output="bootstrap stalled")
        raise subprocess.CalledProcessError(1, cmd, stderr="bootstrap rejected")

    monkeypatch.setattr(helpers, "_run_preparation_command", fail)
    with pytest.raises(Exception) as error:
        helpers._get_shared_base_venv()
    assert not (private_shared_root / helpers.MARKER_NAME).exists()
    assert helpers._SHARED_BASE_VENV is None
    with open(private_shared_root.parent.with_suffix(".lock"), "w", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(lock, fcntl.LOCK_UN)
    monkeypatch.setattr(helpers, "_run_preparation_command", _successful_command)
    result = helpers._get_shared_base_venv()
    assert (result / helpers.MARKER_NAME).is_file()
    assert not (result / "partial-install").exists(), "retry retained incomplete bootstrap state"
    assert all(budget is not None and 0 < budget <= 20 for budget in budgets)
    assert "venv" in str(error.value).lower()


def test_materialization_failure_is_bounded_and_retry_removes_partial_workspace(
    private_shared_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_interpreter(private_shared_root)
    (private_shared_root / helpers.MARKER_NAME).touch()
    monkeypatch.setattr(helpers, "_SHARED_BASE_VENV", private_shared_root)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    budgets: list[float | None] = []

    def fail(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        budgets.append(kwargs.get("timeout"))
        Path(cmd[-1]).mkdir()
        (Path(cmd[-1]) / "partial-copy").touch()
        raise subprocess.TimeoutExpired(cmd, 1)

    monkeypatch.setattr(helpers, "_run_preparation_command", fail)
    with pytest.raises(Exception):
        helpers._materialize_prewarmed_venv(workspace)

    def copy(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        budgets.append(kwargs.get("timeout"))
        shutil.copytree(Path(cmd[-2]), Path(cmd[-1]))
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(helpers, "_run_preparation_command", copy)
    helpers._materialize_prewarmed_venv(workspace)
    assert (workspace / ".venv" / helpers.MARKER_NAME).is_file()
    assert not (workspace / ".venv" / "partial-copy").exists()
    assert len(budgets) == 2 and all(budget is not None and 0 < budget <= 20 for budget in budgets)


def test_parallel_consumers_wait_for_one_builder_and_receive_ready_workspaces(
    private_shared_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = multiprocessing.get_context("fork")
    building, release = ctx.Event(), ctx.Event()
    results, commands = ctx.Queue(), ctx.Queue()
    real_run = subprocess.run

    def run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if "venv" in cmd:
            commands.put("build")
            building.set()
            if not release.wait(timeout=5):
                raise RuntimeError("builder not released")
        if cmd[0] == "cp":
            shutil.copytree(Path(cmd[-2]), Path(cmd[-1]))
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        return _successful_command(cmd, **kwargs)

    def consume(index: int) -> None:
        try:
            workspace = tmp_path / f"consumer-{index}"
            workspace.mkdir()
            helpers._materialize_prewarmed_venv(workspace)
            target = workspace / ".venv"
            results.put((str(target), (target / helpers.MARKER_NAME).is_file(), None))
        except Exception as error:
            results.put(("", False, repr(error)))

    monkeypatch.setattr(helpers, "_run_preparation_command", run)
    processes = [ctx.Process(target=consume, args=(index,)) for index in range(3)]
    try:
        processes[0].start()
        assert building.wait(timeout=2)
        for process in processes[1:]:
            process.start()
        with pytest.raises(queue.Empty):
            results.get(timeout=0.1)
        release.set()
        received = [results.get(timeout=5) for _ in processes]
        assert all(marker and error is None for _, marker, error in received), received
        paths = [Path(path) for path, _, _ in received]
        assert len(set(paths)) == 3
        assert commands.get(timeout=1) == "build"
        with pytest.raises(queue.Empty):
            commands.get(timeout=0.1)
        (paths[0] / "consumer-only").touch()
        assert not any((path / "consumer-only").exists() for path in paths[1:])
        assert all((path / "bin" / "python").is_file() for path in paths)
        usable = real_run(
            [str(paths[0] / "bin" / "python"), "-c", "print('ready')"],
            capture_output=True, text=True, check=True, timeout=2,
        )
        assert usable.stdout.strip() == "ready"
    finally:
        release.set()
        for process in processes:
            if process.pid is not None:
                process.join(timeout=2)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=2)
                assert not process.is_alive()
        results.close()
        commands.close()
