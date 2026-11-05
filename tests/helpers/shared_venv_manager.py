"""Shared virtualenv lifecycle for Makefile test workspaces.

Owns bootstrap, lock coordination, skeleton publication, readiness state,
and workspace materialization for pre-warmed Make fixtures.

Jira: PYPOST-1419
Architecture: ai-tasks/PYPOST-1419/20-architecture.md
"""

from __future__ import annotations

import errno
import fcntl
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

PreparationRunner = Callable[..., subprocess.CompletedProcess[str]]


class _Clock(Protocol):
    def monotonic(self) -> float:
        ...

    def sleep(self, seconds: float) -> None:
        ...


class _DefaultClock:
    """Wall-clock collaborator using the stdlib ``time`` module."""

    def monotonic(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


def _default_flock(lock: object, operation: int) -> None:
    fcntl.flock(lock, operation)  # type: ignore[arg-type]


class SharedVenvManager:
    """Own shared-base bootstrap, locking, skeleton publish, and workspace materialization."""

    def __init__(
        self,
        *,
        python_version: str | None = None,
        base_root: Path | None = None,
        marker_name: str | None = None,
        python_executable: str | None = None,
        preparation_runner: PreparationRunner | None = None,
        clock: _Clock | None = None,
        flock: Callable[..., None] | None = None,
        tempdir_fn: Callable[[], str] | None = None,
    ) -> None:
        """Construct a manager with optional collaborator overrides for tests."""
        self._python_version = python_version or (
            f"{sys.version_info.major}.{sys.version_info.minor}"
        )
        self._base_root = base_root
        self._marker_name = marker_name or f".initialized-{self._python_version}"
        self._python_executable = python_executable or sys.executable
        self._preparation_runner = preparation_runner
        self._clock = clock or _DefaultClock()
        self._flock = flock or _default_flock
        self._tempdir_fn = tempdir_fn or tempfile.gettempdir
        self._resolved_base: Path | None = None

    @property
    def resolved_base(self) -> Path | None:
        """Return owned readiness path, or None if not yet validated/published."""
        return self._resolved_base

    def clear_readiness(self) -> None:
        """Drop owned readiness so the next ensure_ready re-validates on disk."""
        self._resolved_base = None

    def is_ready(self, venv: Path) -> bool:
        """True when the initialization marker and ``bin/python`` both exist."""
        return (
            (venv / self._marker_name).is_file()
            and (venv / "bin" / "python").is_file()
        )

    def build_skeleton(self, venv_dir: Path, skeleton_dir: Path) -> None:
        """Publish a lightweight ``.skeleton`` template from a ready base venv."""
        if skeleton_dir.exists():
            shutil.rmtree(skeleton_dir)
        tmp_skeleton = skeleton_dir.with_name(f"{skeleton_dir.name}.tmp")
        if tmp_skeleton.exists():
            shutil.rmtree(tmp_skeleton)
        try:
            tmp_skeleton.mkdir(parents=True, exist_ok=True)
            cfg_src = venv_dir / "pyvenv.cfg"
            if cfg_src.is_file():
                shutil.copy2(cfg_src, tmp_skeleton / "pyvenv.cfg")
            else:
                (tmp_skeleton / "pyvenv.cfg").write_text(
                    "home = /usr/bin\n", encoding="utf-8",
                )

            bin_dir = tmp_skeleton / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            base_bin = venv_dir / "bin"
            if base_bin.is_dir():
                for item in base_bin.iterdir():
                    (bin_dir / item.name).symlink_to(item)

            site_packages = (
                tmp_skeleton / "lib" / f"python{self._python_version}" / "site-packages"
            )
            site_packages.mkdir(parents=True, exist_ok=True)
            base_site_packages = (
                venv_dir / "lib" / f"python{self._python_version}" / "site-packages"
            )
            (site_packages / "_prewarmed_base.pth").write_text(
                f"{base_site_packages}\n", encoding="utf-8",
            )
            (tmp_skeleton / self._marker_name).touch()
            if skeleton_dir.exists():
                shutil.rmtree(skeleton_dir)
            tmp_skeleton.replace(skeleton_dir)
        finally:
            if tmp_skeleton.exists():
                shutil.rmtree(tmp_skeleton)

    def _shared_base_dir(self) -> Path:
        if self._base_root is not None:
            return self._base_root
        return Path(self._tempdir_fn()) / f"pypost_shared_base_venv_{self._python_version}"

    def _run(self, cmd: list[str], *, timeout: float, cleanup_budget: float = 5) -> (
        subprocess.CompletedProcess[str]
    ):
        if self._preparation_runner is None:
            raise RuntimeError("shared venv preparation_runner is not configured")
        return self._preparation_runner(cmd, timeout=timeout, cleanup_budget=cleanup_budget)

    def ensure_ready(self, *, preparation_budget: float = 20) -> Path:
        """Serialize bootstrap under flock; return ready shared base .venv path."""
        deadline = self._clock.monotonic() + preparation_budget
        if self._resolved_base is not None and self.is_ready(self._resolved_base):
            return self._resolved_base
        self._resolved_base = None

        base_dir = self._shared_base_dir()
        venv_dir = base_dir / ".venv"
        skeleton_dir = base_dir / ".skeleton"
        marker = venv_dir / self._marker_name
        if self.is_ready(venv_dir) and self.is_ready(skeleton_dir):
            self._resolved_base = venv_dir
            return self._resolved_base

        lock_file = base_dir.with_suffix(".lock")
        lock_file.parent.mkdir(parents=True, exist_ok=True)

        def remaining(stage: str) -> float:
            budget = deadline - self._clock.monotonic()
            if budget <= 0:
                raise RuntimeError(
                    f"shared venv {stage} deadline exceeded: {venv_dir} "
                    f"({preparation_budget}s preparation budget)"
                )
            return budget

        with open(lock_file, "w", encoding="utf-8") as lock:
            while True:
                remaining("lock")
                try:
                    self._flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError as error:
                    if error.errno not in (errno.EACCES, errno.EAGAIN):
                        raise
                    self._clock.sleep(min(0.05, remaining("lock")))
            try:
                if not self.is_ready(venv_dir):
                    if venv_dir.exists():
                        shutil.rmtree(venv_dir)
                    if skeleton_dir.exists():
                        shutil.rmtree(skeleton_dir)
                    base_dir.mkdir(parents=True, exist_ok=True)
                    commands = [
                        (
                            "creation",
                            [self._python_executable, "-m", "venv", str(venv_dir)],
                        ),
                        (
                            "installation",
                            [
                                str(venv_dir / "bin" / "python"), "-m", "pip", "install",
                                "--quiet", "pytest>=8,<9", "flake8>=7,<8",
                            ],
                        ),
                        (
                            "validation",
                            [
                                str(venv_dir / "bin" / "python"), "-c",
                                "import pytest, flake8",
                            ],
                        ),
                    ]
                    for stage, command in commands:
                        try:
                            self._run(command, timeout=remaining(stage))
                        except (subprocess.SubprocessError, OSError) as error:
                            detail = (
                                getattr(error, "stderr", None)
                                or getattr(error, "output", None)
                            )
                            raise RuntimeError(
                                f"shared venv {stage} failed: {venv_dir} "
                                f"({preparation_budget}s preparation budget): "
                                f"{error}; {detail or ''}"
                            ) from error
                    remaining("publication")
                    if not (venv_dir / "bin" / "python").is_file():
                        raise RuntimeError(
                            f"shared venv validation missing interpreter: {venv_dir}"
                        )
                    marker.touch()
                if not self.is_ready(skeleton_dir):
                    self.build_skeleton(venv_dir, skeleton_dir)
            finally:
                self._flock(lock, fcntl.LOCK_UN)

        self._resolved_base = venv_dir
        return self._resolved_base

    def materialize(self, workspace: Path, *, copy_timeout: float = 20) -> None:
        """Materialize workspace/.venv from skeleton (fallback: base); bounded failure."""
        base = self.ensure_ready()
        target = workspace / ".venv"
        if self.is_ready(target):
            return
        if target.exists():
            shutil.rmtree(target)
        skeleton = base.parent / ".skeleton"
        source = skeleton if self.is_ready(skeleton) else base
        try:
            self._run(
                ["cp", "-a", str(source), str(target)],
                timeout=copy_timeout,
                cleanup_budget=1,
            )
        except (subprocess.SubprocessError, OSError) as error:
            if target.exists():
                shutil.rmtree(target)
            raise RuntimeError(
                f"shared venv materialization failed: {target}: {error}"
            ) from error
