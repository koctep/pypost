"""PYPOST-1422: extreme concurrency stress for shared venv materialization.

Architecture: ai-tasks/PYPOST-1422/20-architecture.md

Validates 16+ concurrent workspace materializations under simulated disk latency
(injected tree_copier delay). Complements the 4-worker load-budget case in
tests/test_makefile_shared_readiness.py.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pytest

from tests import makefile_test_helpers as helpers
from tests.helpers.shared_venv_manager import SharedVenvManager

# Architecture constants — tune here, not scattered in test bodies.
STRESS_WORKER_COUNT = 16
SIMULATED_DISK_LATENCY_SECONDS = 0.05
STRESS_COMPLETION_BUDGET_SECONDS = 15.0

pytestmark = pytest.mark.timeout(120)


def _seed_interpreter(venv: Path) -> None:
    interpreter = venv / "bin" / "python"
    interpreter.parent.mkdir(parents=True, exist_ok=True)
    interpreter.write_text(
        f'#!/bin/sh\nexec "{sys.executable}" "$@"\n',
        encoding="utf-8",
    )
    interpreter.chmod(0o755)


def _seed_ready_skeleton(
    skeleton: Path,
    *,
    python_version: str,
    pth_target: Path,
) -> None:
    """Seed marker + interpreter + valid `_prewarmed_base.pth` for a `.skeleton`."""
    _seed_interpreter(skeleton)
    (skeleton / helpers.MARKER_NAME).touch()
    site_packages = skeleton / "lib" / f"python{python_version}" / "site-packages"
    site_packages.mkdir(parents=True, exist_ok=True)
    pth_target.mkdir(parents=True, exist_ok=True)
    (site_packages / "_prewarmed_base.pth").write_text(
        f"{pth_target}\n", encoding="utf-8",
    )


def _successful_bootstrap(
    cmd: list[str], **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    if "venv" in cmd:
        target = Path(cmd[-1])
        _seed_interpreter(target)
        (target / helpers.MARKER_NAME).touch()
    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")


def _slow_tree_copier(src: Path, dst: Path) -> None:
    """Simulate disk latency then populate with symlink-preserving copytree."""
    time.sleep(SIMULATED_DISK_LATENCY_SECONDS)
    shutil.copytree(src, dst, symlinks=True)


def test_stress_worker_count_meets_architecture_minimum() -> None:
    """Architecture requires >= 16 concurrent materialization workers."""
    assert STRESS_WORKER_COUNT >= 16


@pytest.mark.timeout(120)
def test_extreme_concurrency_materialization_under_simulated_disk_latency(
    tmp_path: Path,
) -> None:
    """16+ concurrent materializations under simulated latency must all succeed."""
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    base = tmp_path / ".venv"
    _seed_interpreter(base)
    (base / helpers.MARKER_NAME).touch()
    (base / "probe.txt").write_text("base-probe", encoding="utf-8")
    base_site = base / "lib" / f"python{python_version}" / "site-packages"
    base_site.mkdir(parents=True, exist_ok=True)

    skeleton = tmp_path / ".skeleton"
    _seed_ready_skeleton(
        skeleton, python_version=python_version, pth_target=base_site,
    )
    (skeleton / "probe.txt").write_text("skeleton-probe", encoding="utf-8")

    manager = SharedVenvManager(
        base_root=tmp_path,
        python_version=python_version,
        preparation_runner=_successful_bootstrap,
        flock=lambda *_args, **_kwargs: None,
        tree_copier=_slow_tree_copier,
    )
    assert manager.ensure_ready(preparation_budget=5) == base

    workspaces = [tmp_path / f"worker_{i}" for i in range(STRESS_WORKER_COUNT)]
    for ws in workspaces:
        ws.mkdir()

    barrier = threading.Barrier(STRESS_WORKER_COUNT)
    errors: dict[int, str] = {}
    durations: dict[int, float] = {}

    def _worker(worker_id: int) -> None:
        barrier.wait(timeout=10)
        started = time.monotonic()
        try:
            manager.materialize(workspaces[worker_id], copy_timeout=20)
        except Exception as exc:
            errors[worker_id] = repr(exc)
            return
        durations[worker_id] = time.monotonic() - started

    wall_started = time.monotonic()
    with ThreadPoolExecutor(max_workers=STRESS_WORKER_COUNT) as executor:
        futures = [
            executor.submit(_worker, worker_id)
            for worker_id in range(STRESS_WORKER_COUNT)
        ]
        for future in as_completed(futures):
            future.result()
    wall_elapsed = time.monotonic() - wall_started

    assert not errors, (
        f"materialization failures under extreme concurrency: {errors!r}"
    )
    assert len(durations) == STRESS_WORKER_COUNT, (
        f"expected {STRESS_WORKER_COUNT} durations, got {len(durations)}"
    )
    assert wall_elapsed <= STRESS_COMPLETION_BUDGET_SECONDS, (
        f"extreme concurrency wall clock {wall_elapsed:.2f}s exceeded "
        f"{STRESS_COMPLETION_BUDGET_SECONDS}s budget "
        f"(latency={SIMULATED_DISK_LATENCY_SECONDS}s workers={STRESS_WORKER_COUNT})"
    )

    for ws in workspaces:
        target = ws / ".venv"
        assert manager.is_ready(target), f"venv not ready in {ws}"
        assert (target / "probe.txt").read_text(encoding="utf-8") == "skeleton-probe"

    marker = workspaces[0] / ".venv" / "isolation_check.marker"
    marker.touch()
    for ws in workspaces[1:]:
        assert not (ws / ".venv" / "isolation_check.marker").exists()
    assert not (skeleton / "isolation_check.marker").exists()
    assert not (base / "isolation_check.marker").exists()
