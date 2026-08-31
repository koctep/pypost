"""Regression tests verifying timeout budgets and modularization for parallel execution.

Validates that Makefile test suites and exit policy test cases adhere to the
parallel execution timeout budgets and decomposition boundaries defined in
PYPOST-1234.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"
EXIT_POLICY_TEST_FILE = TESTS_DIR / "test_pytest_exit_policy.py"
MAKEFILE_TEST_FILE = TESTS_DIR / "test_makefile.py"
SPLIT_MAKEFILE_TEST_FILES = (
    TESTS_DIR / "test_makefile_recipes.py",
    TESTS_DIR / "test_makefile_lifecycle.py",
    TESTS_DIR / "test_makefile_targets.py",
)


def _find_function_def(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


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


def _extract_function_timeout(
    func_node: ast.FunctionDef, module_tree: ast.Module
) -> int | float | None:
    for dec in func_node.decorator_list:
        if isinstance(dec, ast.Call):
            func = dec.func
            is_timeout_mark = (
                isinstance(func, ast.Attribute) and func.attr == "timeout"
            ) or (
                isinstance(func, ast.Name) and func.id == "timeout"
            )
            if is_timeout_mark:
                if dec.args:
                    val = _resolve_numeric_value(dec.args[0], module_tree)
                    if val is not None:
                        return val
                for kw in dec.keywords:
                    if kw.arg in ("seconds", "timeout"):
                        val = _resolve_numeric_value(kw.value, module_tree)
                        if val is not None:
                            return val
    return None


def _extract_subprocess_timeouts(
    func_node: ast.FunctionDef, module_tree: ast.Module
) -> list[int | float]:
    timeouts: list[int | float] = []
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            is_subproc_run = (
                isinstance(node.func, ast.Attribute) and node.func.attr == "run"
            ) or (
                isinstance(node.func, ast.Name) and node.func.id == "run"
            )
            if is_subproc_run:
                for kw in node.keywords:
                    if kw.arg == "timeout":
                        val = _resolve_numeric_value(kw.value, module_tree)
                        if val is not None:
                            timeouts.append(val)
    return timeouts


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


def _count_tests_in_file(path: Path) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    count = 0
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            count += 1
        elif isinstance(node, ast.ClassDef) and (
            node.name.startswith("Test")
            or any(
                (isinstance(b, ast.Name) and b.id == "TestCase")
                or (isinstance(b, ast.Attribute) and b.attr == "TestCase")
                for b in node.bases
            )
        ):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                    count += 1
    return count


def test_pytest_exit_policy_timeout_budget() -> None:
    """Verify test_pytest_exit_policy.py defines adequate timeout budgets."""
    assert EXIT_POLICY_TEST_FILE.is_file(), f"{EXIT_POLICY_TEST_FILE} must exist"
    tree = ast.parse(EXIT_POLICY_TEST_FILE.read_text(encoding="utf-8"))
    func_node = _find_function_def(
        tree, "test_make_test_fails_with_exit_code_5_when_no_tests_collected"
    )
    assert func_node is not None, (
        "Function test_make_test_fails_with_exit_code_5_when_no_tests_collected not found in "
        f"{EXIT_POLICY_TEST_FILE}"
    )

    test_timeout = _extract_function_timeout(func_node, tree)
    assert test_timeout is not None, (
        "test_make_test_fails_with_exit_code_5_when_no_tests_collected "
        "must declare a timeout marker"
    )
    assert test_timeout >= 60, (
        f"test_make_test_fails_with_exit_code_5_when_no_tests_collected timeout ({test_timeout}s) "
        "must be at least 60s to prevent flaky timeouts under parallel contention"
    )

    subproc_timeouts = _extract_subprocess_timeouts(func_node, tree)
    assert subproc_timeouts, (
        "Expected internal subprocess.run calls with timeout in "
        "test_make_test_fails_with_exit_code_5_when_no_tests_collected"
    )
    for timeout in subproc_timeouts:
        assert timeout >= 50, (
            f"Internal subprocess timeout ({timeout}s) in "
            "test_make_test_fails_with_exit_code_5_when_no_tests_collected must be at least 50s"
        )


def test_makefile_split_files_exist_and_declare_bounded_timeouts() -> None:
    """Verify split Makefile test suite files exist and declare <= 60s timeouts."""
    for split_file in SPLIT_MAKEFILE_TEST_FILES:
        assert split_file.is_file(), f"Expected split test file {split_file.name} to exist"
        tree = ast.parse(split_file.read_text(encoding="utf-8"))
        timeout = _extract_module_timeout(tree)
        assert timeout is not None, (
            f"{split_file.name} must declare a module-level timeout mark (pytestmark)"
        )
        assert 0 < timeout <= 60, (
            f"{split_file.name} timeout mark ({timeout}s) must be <= 60s"
        )


def test_makefile_monolithic_test_count_bounded() -> None:
    """Verify tests/test_makefile.py does not contain > 35 tests."""
    if not MAKEFILE_TEST_FILE.is_file():
        # Cleanly removed in favor of modular split files
        return
    test_count = _count_tests_in_file(MAKEFILE_TEST_FILE)
    assert test_count <= 35, (
        f"tests/test_makefile.py contains {test_count} tests; expected <= 35 tests "
        "after modularization into split suite files"
    )


def test_makefile_suite_files_line_length() -> None:
    """Verify all modified/created Makefile test suite files have line length <= 100."""
    files_to_check = [
        TESTS_DIR / "makefile_test_helpers.py",
        TESTS_DIR / "test_makefile_recipes.py",
        TESTS_DIR / "test_makefile_lifecycle.py",
        TESTS_DIR / "test_makefile_targets.py",
        TESTS_DIR / "test_makefile_slow_smoke.py",
        TESTS_DIR / "test_makefile_parallel_budget.py",
        TESTS_DIR / "test_pytest_exit_policy.py",
        TESTS_DIR / "test_makefile_install_seed_contract.py",
    ]
    long_lines: list[str] = []
    for file_path in files_to_check:
        assert file_path.is_file(), f"{file_path} must exist"
        lines = file_path.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                long_lines.append(f"{file_path.name}:{i} ({len(line)} chars): {line[:80]}...")
    assert not long_lines, "Found lines exceeding 100 chars:\n" + "\n".join(long_lines)


def test_makefile_suite_files_no_debug_prints() -> None:
    """Verify absence of debug print calls in Makefile test suite files."""
    files_to_check = [
        TESTS_DIR / "makefile_test_helpers.py",
        TESTS_DIR / "test_makefile_recipes.py",
        TESTS_DIR / "test_makefile_lifecycle.py",
        TESTS_DIR / "test_makefile_targets.py",
        TESTS_DIR / "test_makefile_slow_smoke.py",
        TESTS_DIR / "test_makefile_parallel_budget.py",
        TESTS_DIR / "test_pytest_exit_policy.py",
        TESTS_DIR / "test_makefile_install_seed_contract.py",
    ]
    prints: list[str] = []
    for file_path in files_to_check:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "print":
                    prints.append(f"{file_path.name}:{node.lineno}")
    assert not prints, "Found debug print calls in:\n" + "\n".join(prints)
