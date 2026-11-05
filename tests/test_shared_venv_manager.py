"""SharedVenvManager lifecycle ownership and DI-isolated stage tests (PYPOST-1419).

Architecture: ai-tasks/PYPOST-1419/20-architecture.md
"""

from __future__ import annotations

import errno
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from tests import makefile_test_helpers as helpers
from tests.helpers.shared_venv_manager import SharedVenvManager

pytestmark = pytest.mark.timeout(30)


def _seed_interpreter(venv: Path) -> None:
    interpreter = venv / "bin" / "python"
    interpreter.parent.mkdir(parents=True, exist_ok=True)
    interpreter.write_text(
        f'#!/bin/sh\nexec "{sys.executable}" "$@"\n',
        encoding="utf-8",
    )
    interpreter.chmod(0o755)


def _successful_bootstrap(
    cmd: list[str], **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    if "venv" in cmd:
        target = Path(cmd[-1])
        _seed_interpreter(target)
        (target / helpers.MARKER_NAME).touch()
    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")


def test_shared_venv_manager_owns_readiness_not_module_path_cache(
    tmp_path: Path,
) -> None:
    """Readiness lives on the manager; helpers must not keep a path-cache SoT."""
    manager = SharedVenvManager(base_root=tmp_path)
    assert hasattr(manager, "resolved_base")
    assert hasattr(manager, "ensure_ready")
    assert hasattr(manager, "materialize")
    assert hasattr(manager, "clear_readiness")
    assert manager.resolved_base is None

    assert not hasattr(helpers, "_SHARED_BASE_VENV"), (
        "module-level mutable shared-base path cache must not remain the source of truth"
    )


def test_ensure_ready_lock_contention_expires_with_injected_clock_and_flock(
    tmp_path: Path,
) -> None:
    """FR3: lock deadline path is exercisable via constructor-injected clock/flock."""
    now = [0.0]
    sleep_calls: list[float] = []

    def always_busy(_lock: Any, _operation: int) -> None:
        raise OSError(errno.EAGAIN, "resource temporarily unavailable")

    def sleep(seconds: float) -> None:
        sleep_calls.append(seconds)
        now[0] += seconds

    clock = SimpleNamespace(monotonic=lambda: now[0], sleep=sleep)
    manager = SharedVenvManager(
        base_root=tmp_path,
        clock=clock,
        flock=always_busy,
        preparation_runner=_successful_bootstrap,
    )

    with pytest.raises(RuntimeError, match=r"(?i)lock.*(deadline|budget|timeout|timed out)"):
        manager.ensure_ready(preparation_budget=0.2)

    assert sleep_calls, "manager must poll/sleep while lock is contended"
    assert manager.resolved_base is None


def test_ensure_ready_recovers_incomplete_base_via_injected_runner(
    tmp_path: Path,
) -> None:
    """FR2/FR3: incomplete on-disk base is rebuilt; readiness is manager-owned."""
    base = tmp_path / ".venv"
    base.mkdir(parents=True)
    (base / "stale-incomplete").touch()

    manager = SharedVenvManager(
        base_root=tmp_path,
        preparation_runner=_successful_bootstrap,
        flock=lambda *_args, **_kwargs: None,
    )
    result = manager.ensure_ready(preparation_budget=5)

    assert result == manager.resolved_base
    assert (result / helpers.MARKER_NAME).is_file()
    assert (result / "bin" / "python").is_file()
    assert not (result / "stale-incomplete").exists()


def test_materialize_timeout_cleans_partial_target_and_identifies_stage(
    tmp_path: Path,
) -> None:
    """FR5: materialization TimeoutExpired yields stage-aware error and cleans partials."""
    base = tmp_path / ".venv"
    _seed_interpreter(base)
    (base / helpers.MARKER_NAME).touch()
    skeleton = tmp_path / ".skeleton"
    _seed_interpreter(skeleton)
    (skeleton / helpers.MARKER_NAME).touch()

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    def fail_copy(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if cmd and cmd[0] == "cp":
            target = Path(cmd[-1])
            target.mkdir(parents=True, exist_ok=True)
            (target / "partial-copy").touch()
            raise subprocess.TimeoutExpired(cmd, 1)
        return _successful_bootstrap(cmd, **kwargs)

    manager = SharedVenvManager(
        base_root=tmp_path,
        preparation_runner=fail_copy,
        flock=lambda *_args, **_kwargs: None,
    )
    # On-disk base+skeleton are already ready; ensure_ready should adopt them.
    assert manager.ensure_ready(preparation_budget=5) == base

    with pytest.raises(RuntimeError, match=r"(?i)materialization"):
        manager.materialize(workspace, copy_timeout=1)

    target = workspace / ".venv"
    assert not target.exists() or not (target / "partial-copy").exists()
