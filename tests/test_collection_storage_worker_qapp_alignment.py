"""Guard: collection storage worker tests use shared qapp (PYPOST-884)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_WORKER_TEST = Path(__file__).resolve().parent / "test_collection_storage_worker.py"
_TARGET_CLASS = "TestCollectionStorageWorker"


def _class_def(tree: ast.Module, name: str) -> ast.ClassDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise AssertionError(f"class {_TARGET_CLASS!r} not found in {_WORKER_TEST.name}")


def _has_usefixtures_qapp(class_def: ast.ClassDef) -> bool:
    for dec in class_def.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        func = dec.func
        if not (
            isinstance(func, ast.Attribute)
            and func.attr == "usefixtures"
            and isinstance(func.value, ast.Attribute)
            and func.value.attr == "mark"
        ):
            continue
        for arg in dec.args:
            if isinstance(arg, ast.Constant) and arg.value == "qapp":
                return True
    return False


def _has_local_qapplication_setup(class_def: ast.ClassDef) -> bool:
    for node in class_def.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "setUpClass":
            continue
        source = ast.unparse(node)
        if "QApplication" in source:
            return True
    return False


def test_collection_storage_worker_requests_shared_qapp():
    source = _WORKER_TEST.read_text(encoding="utf-8")
    tree = ast.parse(source)
    class_def = _class_def(tree, _TARGET_CLASS)
    assert _has_usefixtures_qapp(class_def), (
        f"{_WORKER_TEST.name}: {_TARGET_CLASS} must use "
        '@pytest.mark.usefixtures("qapp") (shared suite fixture; PYPOST-884)'
    )
    assert not _has_local_qapplication_setup(class_def), (
        f"{_WORKER_TEST.name}: {_TARGET_CLASS} must not create QApplication in "
        "setUpClass; use shared tests/conftest.py qapp instead"
    )
