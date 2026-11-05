"""SharedVenvManager lifecycle ownership and DI-isolated stage tests.

Architecture: ai-tasks/PYPOST-1419/20-architecture.md
Failing repro (in-process materialization): ai-tasks/PYPOST-1420/20-architecture.md
Failing repro (deep .pth readiness): ai-tasks/PYPOST-1421/20-architecture.md
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


def test_materialize_timeout_cleans_partial_target_and_identifies_stage(
    tmp_path: Path,
) -> None:
    """FR5: materialization failure yields stage-aware error and cleans partials."""
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}"
    )
    base = tmp_path / ".venv"
    _seed_interpreter(base)
    (base / helpers.MARKER_NAME).touch()
    base_site = base / "lib" / f"python{python_version}" / "site-packages"
    base_site.mkdir(parents=True, exist_ok=True)
    skeleton = tmp_path / ".skeleton"
    _seed_ready_skeleton(
        skeleton, python_version=python_version, pth_target=base_site,
    )

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    def fail_copy(src: Path, dst: Path) -> None:
        dst.mkdir(parents=True, exist_ok=True)
        (dst / "partial-copy").touch()
        raise TimeoutError("simulated materialization timeout")

    manager = SharedVenvManager(
        base_root=tmp_path,
        preparation_runner=_successful_bootstrap,
        flock=lambda *_args, **_kwargs: None,
        tree_copier=fail_copy,
    )
    # On-disk base+skeleton are already ready; ensure_ready should adopt them.
    assert manager.ensure_ready(preparation_budget=5) == base

    with pytest.raises(RuntimeError, match=r"(?i)materialization"):
        manager.materialize(workspace, copy_timeout=1)

    target = workspace / ".venv"
    assert not target.exists() or not (target / "partial-copy").exists()


def test_materialize_populates_without_preparation_runner_or_cp(
    tmp_path: Path,
) -> None:
    """FR1/FR2: materialize yields a ready isolated .venv without preparation_runner/cp."""
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}"
    )
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

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    runner_calls: list[list[str]] = []

    def spy_runner(
        cmd: list[str], **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        runner_calls.append(list(cmd))
        return _successful_bootstrap(cmd, **kwargs)

    manager = SharedVenvManager(
        base_root=tmp_path,
        preparation_runner=spy_runner,
        flock=lambda *_args, **_kwargs: None,
    )

    manager.materialize(workspace)

    target = workspace / ".venv"
    assert manager.is_ready(target)
    assert (target / "probe.txt").read_text(encoding="utf-8") == "skeleton-probe"

    cp_calls = [call for call in runner_calls if call and call[0] == "cp"]
    assert not cp_calls, (
        "materialize must not populate via preparation_runner/cp; "
        f"saw: {cp_calls!r}"
    )
    assert runner_calls == [], (
        "with a ready shared base, materialize must not invoke preparation_runner "
        f"for population; saw: {runner_calls!r}"
    )

    (target / "probe.txt").write_text("mutated-workspace", encoding="utf-8")
    assert (skeleton / "probe.txt").read_text(encoding="utf-8") == "skeleton-probe"
    assert (base / "probe.txt").read_text(encoding="utf-8") == "base-probe"


def test_is_ready_rejects_skeleton_without_prewarmed_base_pth(tmp_path: Path) -> None:
    """PYPOST-1421: skeleton missing _prewarmed_base.pth must not be ready."""
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}"
    )
    skeleton = tmp_path / ".skeleton"
    _seed_interpreter(skeleton)
    (skeleton / helpers.MARKER_NAME).touch()
    (
        skeleton / "lib" / f"python{python_version}" / "site-packages"
    ).mkdir(parents=True, exist_ok=True)

    manager = SharedVenvManager(base_root=tmp_path, python_version=python_version)

    assert not manager.is_ready(skeleton)
    assert not helpers._venv_ready(skeleton)


def test_is_ready_rejects_skeleton_with_invalid_prewarmed_base_pth_target(
    tmp_path: Path,
) -> None:
    """PYPOST-1421: .pth pointing at a non-directory must fail readiness."""
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}"
    )
    skeleton = tmp_path / ".skeleton"
    _seed_interpreter(skeleton)
    (skeleton / helpers.MARKER_NAME).touch()
    site_packages = (
        skeleton / "lib" / f"python{python_version}" / "site-packages"
    )
    site_packages.mkdir(parents=True, exist_ok=True)
    missing_target = tmp_path / "does-not-exist-site-packages"
    (site_packages / "_prewarmed_base.pth").write_text(
        f"{missing_target}\n", encoding="utf-8",
    )

    manager = SharedVenvManager(base_root=tmp_path, python_version=python_version)

    assert not manager.is_ready(skeleton)
    assert not helpers._venv_ready(skeleton)


def test_is_ready_accepts_skeleton_with_valid_prewarmed_base_pth(
    tmp_path: Path,
) -> None:
    """PYPOST-1421: marker + interpreter + readable .pth target => ready."""
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}"
    )
    base_site = tmp_path / "base-site-packages"
    skeleton = tmp_path / ".skeleton"
    _seed_ready_skeleton(
        skeleton, python_version=python_version, pth_target=base_site,
    )

    manager = SharedVenvManager(base_root=tmp_path, python_version=python_version)

    assert manager.is_ready(skeleton)
    assert helpers._venv_ready(skeleton)
