"""Guard: suite Qt tests use shared conftest qapp (PYPOST-886)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(30)

_TESTS_DIR = Path(__file__).resolve().parent

# Priority batches from the ticket (workers → presenters → editors), plus the
# remaining suite modules that were also aligned in PYPOST-886.
_PRIORITY_MODULES = (
    # Workers
    "test_request_save_orchestrator.py",
    "test_worker_race.py",
    # Presenters
    "test_collections_presenter.py",
    "test_env_presenter.py",
    "test_tabs_presenter.py",
    "test_presenter_font_inheritance.py",
    # Editors
    "test_code_editor.py",
    "test_code_editor_folding.py",
    "test_code_editor_validation.py",
    "test_json_highlighter.py",
    "test_tab_header.py",
    "test_request_editor_gui_metrics.py",
    "test_request_editor_variable_propagation.py",
    "test_request_editor_body_validation.py",
    "test_request_editor_body_format.py",
    "test_request_editor_body_gutter.py",
    "test_request_editor_mcp_params.py",
    "test_request_editor_method_tab_switch.py",
)

def _all_test_modules() -> list[str]:
    return sorted(
        p.name
        for p in _TESTS_DIR.glob("test_*.py")
        if p.name != "test_suite_qapp_alignment.py"
    )

def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))

def _is_usefixtures_qapp(decorator: ast.AST) -> bool:
    if not isinstance(decorator, ast.Call):
        return False
    func = decorator.func
    if not (
        isinstance(func, ast.Attribute)
        and func.attr == "usefixtures"
        and isinstance(func.value, ast.Attribute)
        and func.value.attr == "mark"
    ):
        return False
    return any(
        isinstance(arg, ast.Constant) and arg.value == "qapp"
        for arg in decorator.args
    )

def _class_has_usefixtures_qapp(class_def: ast.ClassDef) -> bool:
    return any(_is_usefixtures_qapp(dec) for dec in class_def.decorator_list)

def _setUpClass_creates_qapplication(class_def: ast.ClassDef) -> bool:
    for node in class_def.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "setUpClass":
            continue
        if "QApplication" in ast.unparse(node):
            return True
    return False

def _module_defines_local_qapp(tree: ast.Module) -> bool:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "qapp":
            return True
    return False

def _module_defines_get_app_helper(tree: ast.Module) -> bool:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_get_app":
            return True
    return False

def _qt_testcase_classes(tree: ast.Module) -> list[ast.ClassDef]:
    results: list[ast.ClassDef] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        base_names = []
        for base in node.bases:
            if isinstance(base, ast.Attribute):
                base_names.append(base.attr)
            elif isinstance(base, ast.Name):
                base_names.append(base.id)
        if "TestCase" not in base_names:
            continue
        if _setUpClass_creates_qapplication(node) or _class_has_usefixtures_qapp(node):
            results.append(node)
    return results

@pytest.mark.parametrize("module_name", _PRIORITY_MODULES)

def test_priority_module_aligned_to_shared_qapp(module_name: str):
    path = _TESTS_DIR / module_name
    assert path.is_file(), f"missing priority module {module_name}"
    tree = _parse(path)

    assert not _module_defines_local_qapp(tree), (
        f"{module_name}: must not define local def qapp(); use "
        "tests/conftest.py shared qapp (PYPOST-886)"
    )
    assert not _module_defines_get_app_helper(tree), (
        f"{module_name}: must not define _get_app() lazy QApplication; use "
        '@pytest.mark.usefixtures("qapp") (PYPOST-886)'
    )

    for class_def in _qt_testcase_classes(tree):
        assert not _setUpClass_creates_qapplication(class_def), (
            f"{module_name}: {class_def.name} must not create QApplication in "
            "setUpClass; use shared tests/conftest.py qapp (PYPOST-886)"
        )
        assert _class_has_usefixtures_qapp(class_def), (
            f"{module_name}: {class_def.name} must use "
            '@pytest.mark.usefixtures("qapp") (shared suite fixture; PYPOST-886)'
        )

def test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication():
    """Suite-wide inventory: no duplicate local qapp / setUpClass QApplication."""
    offenders_local: list[str] = []
    offenders_setup: list[str] = []
    offenders_get_app: list[str] = []
    for module_name in _all_test_modules():
        path = _TESTS_DIR / module_name
        tree = _parse(path)
        if _module_defines_local_qapp(tree):
            offenders_local.append(module_name)
        if _module_defines_get_app_helper(tree):
            offenders_get_app.append(module_name)
        for class_def in tree.body:
            if not isinstance(class_def, ast.ClassDef):
                continue
            if _setUpClass_creates_qapplication(class_def):
                offenders_setup.append(f"{module_name}:{class_def.name}")

    assert not offenders_local, (
        "local def qapp() still present (use conftest qapp): "
        + ", ".join(offenders_local)
    )
    assert not offenders_get_app, (
        "_get_app() helpers still present: " + ", ".join(offenders_get_app)
    )
    assert not offenders_setup, (
        "setUpClass still creates QApplication: " + ", ".join(offenders_setup)
    )
