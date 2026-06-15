"""Integration tests for root Makefile automation (PYPOST-274, PYPOST-277)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(120)

REPO_ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = REPO_ROOT / "Makefile"
REQUIREMENTS = REPO_ROOT / "requirements.txt"
PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"
MARKER_NAME = f".initialized-{PYTHON_VERSION}"
MARKER_REL = f".venv/{MARKER_NAME}"


def _run_make(
    workspace: Path,
    *targets: str,
    check: bool = False,
    timeout: int = 110,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["make", f"PYTHON={sys.executable}", *targets],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=check,
        timeout=timeout,
    )


def _prerequisites(workspace: Path, target: str) -> list[str]:
    proc = subprocess.run(
        [
            "make",
            f"PYTHON={sys.executable}",
            "-p",
            "-f",
            "Makefile",
            "-C",
            str(workspace),
        ],
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
            tail = line[len(prefix):].strip()
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


def _seed_minimal_project(workspace: Path) -> None:
    tests_dir = workspace / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_noop.py").write_text(
        "import pytest\n\npytestmark = pytest.mark.timeout(10)\n\n"
        "def test_noop() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    pypost_dir = workspace / "pypost"
    pypost_dir.mkdir(exist_ok=True)
    (pypost_dir / "__init__.py").write_text("", encoding="utf-8")


@pytest.fixture
def make_workspace(tmp_path: Path) -> Path:
    shutil.copy(MAKEFILE, tmp_path / "Makefile")
    (tmp_path / "requirements.txt").write_text(
        "# empty fixture for make install\n",
        encoding="utf-8",
    )
    _seed_minimal_project(tmp_path)
    return tmp_path


@pytest.fixture
def make_workspace_full_deps(tmp_path: Path) -> Path:
    shutil.copy(MAKEFILE, tmp_path / "Makefile")
    shutil.copy(REQUIREMENTS, tmp_path / "requirements.txt")
    _seed_minimal_project(tmp_path)
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
    def test_install_depends_on_venv_test_and_marker(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "install")
        assert "venv-test" in prereqs
        assert MARKER_REL in prereqs

    def test_test_cov_depends_on_venv_test_and_marker(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "test-cov")
        assert "venv-test" in prereqs
        assert MARKER_REL in prereqs

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


class TestTargetExecution:
    def test_venv_test_installs_pytest_and_flake8(self, make_workspace: Path) -> None:
        venv_result = _run_make(make_workspace, "venv")
        assert venv_result.returncode == 0, venv_result.stderr
        venv_test_result = _run_make(make_workspace, "venv-test")
        assert venv_test_result.returncode == 0, venv_test_result.stderr
        bin_python = make_workspace / ".venv" / "bin" / "python"
        proc = subprocess.run(
            [str(bin_python), "-c", "import pytest, flake8"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr

    def test_make_test_excludes_slow_marker(self, make_workspace: Path) -> None:
        slow_test = make_workspace / "tests" / "test_slow_fail.py"
        slow_test.write_text(
            "import pytest\n\npytestmark = pytest.mark.timeout(10)\n\n"
            "@pytest.mark.slow\n"
            "def test_would_fail_if_run() -> None:\n"
            "    assert False\n",
            encoding="utf-8",
        )
        install_result = _run_make(make_workspace, "install")
        assert install_result.returncode == 0, install_result.stderr
        test_result = _run_make(make_workspace, "test")
        assert test_result.returncode == 0, test_result.stderr

    def test_install_succeeds_with_empty_requirements(self, make_workspace: Path) -> None:
        result = _run_make(make_workspace, "install")
        assert result.returncode == 0, result.stderr

    def test_test_fails_without_pytest_in_bare_venv(self, make_workspace: Path) -> None:
        venv_result = _run_make(make_workspace, "venv")
        assert venv_result.returncode == 0, venv_result.stderr
        test_result = _run_make(make_workspace, "test")
        assert test_result.returncode != 0

    def test_test_succeeds_after_install(self, make_workspace: Path) -> None:
        install_result = _run_make(make_workspace, "install")
        assert install_result.returncode == 0, install_result.stderr
        test_result = _run_make(make_workspace, "test")
        assert test_result.returncode == 0, test_result.stderr

    def test_lint_succeeds_after_install(self, make_workspace: Path) -> None:
        install_result = _run_make(make_workspace, "install")
        assert install_result.returncode == 0, install_result.stderr
        lint_result = _run_make(make_workspace, "lint")
        assert lint_result.returncode == 0, lint_result.stderr


@pytest.mark.slow
@pytest.mark.timeout(180)
class TestSlowInstallSmoke:
    def test_install_succeeds_with_project_requirements(
        self,
        make_workspace_full_deps: Path,
    ) -> None:
        result = _run_make(
            make_workspace_full_deps,
            "install",
            timeout=170,
        )
        assert result.returncode == 0, result.stderr
        bin_python = make_workspace_full_deps / ".venv" / "bin" / "python"
        assert bin_python.is_file()
        proc = subprocess.run(
            [str(bin_python), "-c", "import pydantic"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
