"""Integration tests for root Makefile automation (PYPOST-307)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(120)

REPO_ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = REPO_ROOT / "Makefile"
PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"
MARKER_NAME = f".initialized-{PYTHON_VERSION}"
MARKER_REL = f".venv/{MARKER_NAME}"


def _run_make(
    workspace: Path,
    *targets: str,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["make", *targets],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=check,
        timeout=110,
    )


def _prerequisites(workspace: Path, target: str) -> list[str]:
    proc = subprocess.run(
        ["make", "-p", "-f", "Makefile", "-C", str(workspace)],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    prereqs: list[str] = []
    collecting = False
    prefix = f"{target}:"
    for line in proc.stdout.splitlines():
        if line.startswith(prefix):
            collecting = True
            tail = line[len(prefix) :].strip()
            if tail:
                prereqs.extend(tail.split())
            continue
        if collecting:
            if not line or line[0] in {"\t", "#"}:
                break
            if line[0] == " ":
                prereqs.extend(line.strip().split())
            else:
                break
    return prereqs


@pytest.fixture
def make_workspace(tmp_path: Path) -> Path:
    shutil.copy(MAKEFILE, tmp_path / "Makefile")
    (tmp_path / "requirements.txt").write_text("# empty fixture for make install\n", encoding="utf-8")
    return tmp_path


class TestMarkerLifecycle:
    def test_venv_creates_version_marker(self, make_workspace: Path) -> None:
        result = _run_make(make_workspace, "venv")
        assert result.returncode == 0, result.stderr
        marker = make_workspace / ".venv" / MARKER_NAME
        assert marker.is_file()

    def test_clean_removes_venv_and_marker(self, make_workspace: Path) -> None:
        _run_make(make_workspace, "venv", check=False)
        result = _run_make(make_workspace, "clean")
        assert result.returncode == 0, result.stderr
        assert not (make_workspace / ".venv").exists()

    def test_venv_is_idempotent(self, make_workspace: Path) -> None:
        first = _run_make(make_workspace, "venv")
        second = _run_make(make_workspace, "venv")
        assert first.returncode == 0, first.stderr
        assert second.returncode == 0, second.stderr
        assert (make_workspace / ".venv" / MARKER_NAME).is_file()


class TestDependencyChain:
    def test_install_depends_on_venv_test(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "install")
        assert "venv-test" in prereqs

    def test_venv_test_depends_on_marker(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "venv-test")
        assert MARKER_REL in prereqs

    @pytest.mark.parametrize("target", ["run", "test", "lint"])
    def test_runtime_targets_depend_on_marker_only(
        self,
        make_workspace: Path,
        target: str,
    ) -> None:
        prereqs = _prerequisites(make_workspace, target)
        assert MARKER_REL in prereqs
        assert "install" not in prereqs
        assert "venv-test" not in prereqs


class TestExitBehavior:
    def test_clean_exits_zero_on_empty_tree(self, make_workspace: Path) -> None:
        result = _run_make(make_workspace, "clean")
        assert result.returncode == 0, result.stderr

    def test_unknown_target_exits_nonzero(self, make_workspace: Path) -> None:
        result = _run_make(make_workspace, "not-a-real-target")
        assert result.returncode != 0

    def test_lint_fails_without_flake8_in_bare_venv(self, make_workspace: Path) -> None:
        venv_result = _run_make(make_workspace, "venv")
        assert venv_result.returncode == 0, venv_result.stderr
        lint_result = _run_make(make_workspace, "lint")
        assert lint_result.returncode != 0
