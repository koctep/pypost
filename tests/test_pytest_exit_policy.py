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


@pytest.mark.timeout(30)
def test_make_test_fails_with_exit_code_5_when_no_tests_collected(tmp_path: Path) -> None:
    """make test must propagate pytest exit 5 — zero collection is a failure."""
    shutil.copy(MAKEFILE, tmp_path / "Makefile")
    (tmp_path / "requirements.txt").write_text(
        "# empty fixture for make install\n",
        encoding="utf-8",
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    install = subprocess.run(
        ["make", f"PYTHON={sys.executable}", "install"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=25,
        check=False,
    )
    assert install.returncode == 0, install.stderr

    test_result = subprocess.run(
        ["make", f"PYTHON={sys.executable}", "PYTEST_ARGS=", "test"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=25,
        check=False,
    )
    assert test_result.returncode != 0, (
        f"make test must fail when no tests are collected; got exit "
        f"{test_result.returncode}; stderr={test_result.stderr!r}"
    )
    assert f"Error {PYTEST_EXIT_NO_TESTS}" in test_result.stderr, (
        f"make must report pytest exit {PYTEST_EXIT_NO_TESTS}; stderr="
        f"{test_result.stderr!r}"
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

