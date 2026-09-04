"""Regression tests for pytest exit code 5 (no tests collected) policy (PYPOST-279)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = REPO_ROOT / "Makefile"
PYTEST_EXIT_NO_TESTS = 5

_MINIMAL_PYPROJECT = """\
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "pypost"
version = "0.0.0"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8,<9",
    "flake8>=7,<8",
]
otel = []

[tool.setuptools.packages.find]
where = ["."]
include = ["pypost*"]
"""


def _seed_minimal_project(workspace: Path) -> None:
    pypost_dir = workspace / "pypost"
    pypost_dir.mkdir(exist_ok=True)
    (pypost_dir / "__init__.py").write_text("", encoding="utf-8")


def _prepare_missing_runner_workspace(tmp_path: Path) -> None:
    shutil.copy(MAKEFILE, tmp_path / "Makefile")
    (tmp_path / "pyproject.toml").write_text(_MINIMAL_PYPROJECT, encoding="utf-8")
    _seed_minimal_project(tmp_path)
    (tmp_path / "tests").mkdir()

    install = subprocess.run(
        ["make", f"PYTHON={sys.executable}", "install"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert install.returncode == 0, install.stderr


def _seed_missing_runner_coverage_files(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create root and nested coverage files for the missing-runner contract."""
    fragment = tmp_path / ".coverage.worker-1"
    fragment.write_text("disposable coverage data", encoding="utf-8")
    preserved_root_file = tmp_path / ".coverage"
    preserved_root_file.write_text("persistent coverage data", encoding="utf-8")
    nested_fragment = tmp_path / "nested" / ".coverage.worker-2"
    nested_fragment.parent.mkdir()
    nested_fragment.write_text("nested coverage data", encoding="utf-8")
    return fragment, preserved_root_file, nested_fragment


def _assert_missing_runner_failure(
    result: subprocess.CompletedProcess[str],
    *,
    target: str,
    fragment: Path,
    preserved_root_file: Path,
    nested_fragment: Path,
) -> None:
    """Check the fail-closed result and scoped coverage cleanup."""
    assert result.returncode != 0, (
        f"make {target} must fail when the parallel runner is missing; "
        f"stderr={result.stderr!r}"
    )
    assert "parallel runner unavailable" in result.stderr.lower()
    assert not fragment.exists(), f"make {target} left a root coverage fragment"
    assert preserved_root_file.exists(), f"make {target} removed the base coverage file"
    assert nested_fragment.exists(), f"make {target} removed a nested coverage fragment"


@pytest.mark.timeout(30)
def test_pytest_returns_exit_code_5_for_empty_tests_dir(tmp_path: Path) -> None:
    """pytest natively exits 5 when no tests are collected."""
    empty_tests = tmp_path / "tests"
    empty_tests.mkdir()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(empty_tests), "-q"],
        capture_output=True,
        text=True,
        timeout=25,
        check=False,
    )
    assert result.returncode == PYTEST_EXIT_NO_TESTS, (
        f"expected exit {PYTEST_EXIT_NO_TESTS}, got {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


@pytest.mark.timeout(75)
def test_make_test_fails_closed_when_parallel_runner_is_missing(tmp_path: Path) -> None:
    """make test rejects a missing runner and cleans root coverage fragments."""
    _prepare_missing_runner_workspace(tmp_path)
    fragment, preserved_root_file, nested_fragment = _seed_missing_runner_coverage_files(
        tmp_path
    )
    result = subprocess.run(
        ["make", f"PYTHON={sys.executable}", "PYTEST_ARGS=", "test"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    _assert_missing_runner_failure(
        result,
        target="test",
        fragment=fragment,
        preserved_root_file=preserved_root_file,
        nested_fragment=nested_fragment,
    )


@pytest.mark.timeout(75)
def test_make_test_cov_fails_closed_when_parallel_runner_is_missing(tmp_path: Path) -> None:
    """make test-cov rejects a missing runner and cleans root coverage fragments."""
    _prepare_missing_runner_workspace(tmp_path)
    fragment, preserved_root_file, nested_fragment = _seed_missing_runner_coverage_files(
        tmp_path
    )
    result = subprocess.run(
        ["make", f"PYTHON={sys.executable}", "PYTEST_ARGS=", "test-cov"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    _assert_missing_runner_failure(
        result,
        target="test-cov",
        fragment=fragment,
        preserved_root_file=preserved_root_file,
        nested_fragment=nested_fragment,
    )


@pytest.mark.timeout(30)
def test_pytest_rewrites_exit_code_5_to_0_when_policy_is_warn(tmp_path: Path) -> None:
    """pytest exits 0 and prints/logs warning when empty_tests_policy is warn."""
    empty_tests = tmp_path / "tests"
    empty_tests.mkdir()
    shutil.copy(REPO_ROOT / "tests" / "conftest.py", empty_tests / "conftest.py")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(empty_tests),
            "-o",
            "empty_tests_policy=warn",
            "-q",
        ],
        capture_output=True,
        text=True,
        timeout=25,
        check=False,
    )
    assert result.returncode == 0, (
        f"expected exit 0, got {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "WARNING: pytest exit code 5" in result.stderr, (
        f"expected warning message in stderr; got stderr={result.stderr!r}"
    )


@pytest.mark.timeout(30)
def test_pytest_retains_exit_code_5_when_policy_is_fail(tmp_path: Path) -> None:
    """pytest exits 5 when empty_tests_policy is fail."""
    empty_tests = tmp_path / "tests"
    empty_tests.mkdir()
    shutil.copy(REPO_ROOT / "tests" / "conftest.py", empty_tests / "conftest.py")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(empty_tests),
            "-o",
            "empty_tests_policy=fail",
            "-q",
        ],
        capture_output=True,
        text=True,
        timeout=25,
        check=False,
    )
    assert result.returncode == PYTEST_EXIT_NO_TESTS, (
        f"expected exit {PYTEST_EXIT_NO_TESTS}, got {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
