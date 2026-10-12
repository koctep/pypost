"""Automated repro tests for dependency lockfile verification (PYPOST-1359).

Verifies the contract of `make check-lock-dev` under the repository toolchain.
Prior to refreshing `requirements-dev.txt`, `make check-lock-dev` must fail due to
transitive dependency drift against `requirements-dev.in`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(60)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MAKEFILE = _REPO_ROOT / "Makefile"
_REQUIREMENTS_DEV_IN = _REPO_ROOT / "requirements-dev.in"
_REQUIREMENTS_DEV_TXT = _REPO_ROOT / "requirements-dev.txt"


def _resolve_uv_binary() -> str:
    """Find uv binary in system PATH or repository .venv."""
    system_uv = shutil.which("uv")
    if system_uv:
        return system_uv
    venv_uv = _REPO_ROOT / ".venv" / "bin" / "uv"
    if venv_uv.is_file() and os.access(venv_uv, os.X_OK):
        return str(venv_uv)
    pytest.skip("uv binary not available on PATH or in .venv/bin/uv")


def test_repro_check_lock_dev_detects_no_drift() -> None:
    """Reproduction test asserting that `make check-lock-dev` passes cleanly.

    In the red state (prior to Step 4 lockfile refresh), `requirements-dev.txt` is stale
    relative to `requirements-dev.in` when compiled with the CI-pinned uv toolchain,
    causing this test to fail because `make check-lock-dev` exits with code 1.
    After Step 4 development synchronizes `requirements-dev.txt`, this test will pass.
    """
    uv_bin = _resolve_uv_binary()

    cmd = ["make", "check-lock-dev", f"UV={uv_bin}"]
    proc = subprocess.run(
        cmd,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )

    combined_output = f"{proc.stdout}\n{proc.stderr}"
    assert proc.returncode == 0, (
        f"Expected `make check-lock-dev` to pass cleanly with zero exit code, "
        f"but it failed with exit code {proc.returncode}:\n{combined_output}"
    )
    assert "stale relative to requirements-dev.in" not in combined_output, (
        f"`make check-lock-dev` reported stale lockfile:\n{combined_output}"
    )
