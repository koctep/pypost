"""Automated failing repro test verifying decomposition and budget invariants for PYPOST-1262.

Asserts that monolithic test suites do not exceed heavy test budgets, that modular
split test files exist with bounded timeouts (<= 60s), and that all 24 original tests
from the monolithic suites are preserved.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"

MONOLITHIC_FILES = (
    TESTS_DIR / "test_makefile_lifecycle.py",
    TESTS_DIR / "test_makefile_targets.py",
)

DECOMPOSED_FILES = (
    TESTS_DIR / "test_makefile_markers.py",
    TESTS_DIR / "test_makefile_stamp_test_idempotency.py",
    TESTS_DIR / "test_makefile_stamp_otel_idempotency.py",
    TESTS_DIR / "test_makefile_install_stamp_contract.py",
    TESTS_DIR / "test_makefile_exit_behavior.py",
    TESTS_DIR / "test_makefile_target_install_test.py",
    TESTS_DIR / "test_makefile_target_filtering.py",
)

ORIGINAL_24_TEST_NAMES = frozenset(
    {
        # TestMarkerLifecycle (3)
        "test_venv_creates_version_marker",
        "test_clean_removes_venv_and_marker",
        "test_venv_is_idempotent",
        # TestVenvExtraStampIdempotency (8)
        "test_venv_test_skips_pip_when_current",
        "test_venv_otel_skips_pip_when_current",
        "test_venv_test_installs_when_stamp_missing",
        "test_venv_otel_installs_when_stamp_missing",
        "test_venv_test_installs_when_stamp_stale",
        "test_venv_otel_installs_when_stamp_stale",
        "test_venv_test_depends_on_stamp",
        "test_venv_otel_depends_on_stamp",
        # TestInstallExtraStampContract (2)
        "test_install_touches_both_extra_stamps",
        "test_install_stamps_allow_skip_pip_on_venv_test_otel",
        # TestExitBehavior (3)
        "test_clean_exits_zero_on_empty_tree",
        "test_unknown_target_exits_nonzero",
        "test_lint_succeeds_from_bare_venv_via_venv_test",
        # TestTargetExecution (8)
        "test_venv_test_installs_pytest_and_flake8",
        "test_make_test_excludes_slow_marker",
        "test_make_test_agent_e2e_selects_agent_e2e_marker",
        "test_install_succeeds_with_minimal_pyproject",
        "test_test_succeeds_from_bare_venv_via_venv_test",
        "test_test_succeeds_after_install",
        "test_pytest_args_narrows_test_run",
        "test_lint_succeeds_after_install",
    }
)


def _extract_test_function_names(path: Path) -> list[str]:
    if not path.is_file():
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            names.append(node.name)
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                    names.append(item.name)
    return names


def _resolve_numeric_value(node: ast.AST, module_tree: ast.Module) -> int | float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name):
        for stmt in module_tree.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == node.id:
                        if isinstance(stmt.value, ast.Constant) and isinstance(
                            stmt.value.value, (int, float)
                        ):
                            return stmt.value.value
    return None


def _extract_module_timeout(tree: ast.Module) -> int | float | None:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "pytestmark":
                    marks = (
                        node.value.elts
                        if isinstance(node.value, (ast.List, ast.Tuple))
                        else [node.value]
                    )
                    for mark in marks:
                        if isinstance(mark, ast.Call):
                            func = mark.func
                            is_timeout_mark = (
                                isinstance(func, ast.Attribute) and func.attr == "timeout"
                            ) or (
                                isinstance(func, ast.Name) and func.id == "timeout"
                            )
                            if is_timeout_mark:
                                if mark.args:
                                    val = _resolve_numeric_value(mark.args[0], tree)
                                    if val is not None:
                                        return val
                                for kw in mark.keywords:
                                    if kw.arg in ("seconds", "timeout"):
                                        val = _resolve_numeric_value(kw.value, tree)
                                        if val is not None:
                                            return val
    return None


@pytest.mark.timeout(30)
def test_monolithic_makefile_files_bounded() -> None:
    """Verify monolithic test files do not exceed 4 heavy test functions."""
    for path in MONOLITHIC_FILES:
        test_names = _extract_test_function_names(path)
        assert len(test_names) <= 4, (
            f"{path.name} contains {len(test_names)} tests; expected <= 4 heavy tests "
            "or decomposition into modular test files"
        )


@pytest.mark.timeout(30)
def test_decomposed_makefile_suite_files_exist() -> None:
    """Verify all 6 decomposed Makefile test suite files exist."""
    missing = [f.name for f in DECOMPOSED_FILES if not f.is_file()]
    assert not missing, f"Missing decomposed test suite files: {missing}"


@pytest.mark.timeout(30)
def test_decomposed_makefile_suite_files_declare_bounded_timeouts() -> None:
    """Verify each decomposed test file declares module pytestmark timeout <= 60s."""
    for path in DECOMPOSED_FILES:
        assert path.is_file(), f"Expected decomposed file {path.name} to exist"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        timeout = _extract_module_timeout(tree)
        assert timeout is not None, (
            f"{path.name} must declare a module-level timeout mark (pytestmark)"
        )
        assert 0 < timeout <= 60, (
            f"{path.name} timeout mark ({timeout}s) must be <= 60s"
        )


@pytest.mark.timeout(30)
def test_decomposed_makefile_suite_coverage_invariant() -> None:
    """Verify exactly 24 original tests are preserved across decomposed files."""
    collected_names: list[str] = []
    for path in DECOMPOSED_FILES:
        assert path.is_file(), f"Expected decomposed file {path.name} to exist"
        collected_names.extend(_extract_test_function_names(path))

    assert len(collected_names) == 24, (
        f"Expected exactly 24 tests across decomposed files, got {len(collected_names)}"
    )
    assert set(collected_names) == ORIGINAL_24_TEST_NAMES, (
        "Decomposed tests do not match original 24 test names from monolithic suites"
    )
