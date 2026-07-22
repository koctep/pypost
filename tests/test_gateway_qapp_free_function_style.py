"""Guard: gateway/H3 stress tests use free functions with qapp (PYPOST-885)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_TESTS_DIR = Path(__file__).resolve().parent
_TARGET_MODULES = (
    "test_environment_storage_gateway.py",
    "test_collection_storage_gateway.py",
    "test_storage_gateway_h3_stress.py",
)


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _testcase_class_names(tree: ast.Module) -> list[str]:
    names: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            base_name = ""
            if isinstance(base, ast.Attribute):
                base_name = base.attr
            elif isinstance(base, ast.Name):
                base_name = base.id
            if base_name == "TestCase":
                names.append(node.name)
                break
    return names


def _has_usefixtures_qapp(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (
            isinstance(func, ast.Attribute)
            and func.attr == "usefixtures"
            and isinstance(func.value, ast.Attribute)
            and func.value.attr == "mark"
        ):
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and arg.value == "qapp":
                return True
    return False


def _test_functions_missing_qapp(tree: ast.Module) -> list[str]:
    missing: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if not node.name.startswith("test_"):
            continue
        arg_names = [a.arg for a in node.args.args]
        if "qapp" not in arg_names:
            missing.append(node.name)
    return missing


@pytest.mark.parametrize("module_name", _TARGET_MODULES)
def test_gateway_module_uses_free_functions_with_qapp(module_name: str):
    path = _TESTS_DIR / module_name
    tree = _parse(path)
    testcase_names = _testcase_class_names(tree)
    assert not testcase_names, (
        f"{module_name}: must not use unittest.TestCase "
        f"(found {testcase_names}); convert to free pytest functions with "
        "qapp param (PYPOST-885)"
    )
    assert not _has_usefixtures_qapp(tree), (
        f"{module_name}: must not use @pytest.mark.usefixtures(\"qapp\"); "
        "take qapp as a free-function parameter (PYPOST-885)"
    )
    missing = _test_functions_missing_qapp(tree)
    assert not missing, (
        f"{module_name}: test functions must accept qapp parameter "
        f"(missing on {missing})"
    )
