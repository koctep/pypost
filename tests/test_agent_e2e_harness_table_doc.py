"""PYPOST-866: guard agent_e2e marks vs doc/dev/agent_e2e.md harness table."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TESTS_DIR = _REPO_ROOT / "tests"
_HARNESS_DOC = _REPO_ROOT / "doc" / "dev" / "agent_e2e.md"
_TABLE_ANCHOR = "Harness modules under the marker"
_MODULE_CELL_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|")


def _is_pytest_mark_attr(node: ast.AST, mark_name: str) -> bool:
    """True for pytest.mark.<mark_name> attribute chain."""
    if not isinstance(node, ast.Attribute) or node.attr != mark_name:
        return False
    mark = node.value
    if not isinstance(mark, ast.Attribute) or mark.attr != "mark":
        return False
    root = mark.value
    return isinstance(root, ast.Name) and root.id == "pytest"


def _is_agent_e2e_mark(node: ast.AST) -> bool:
    """True for pytest.mark.agent_e2e or @pytest.mark.agent_e2e(...)."""
    target = node.func if isinstance(node, ast.Call) else node
    return _is_pytest_mark_attr(target, "agent_e2e")


def _pytestmark_has_agent_e2e(value: ast.AST) -> bool:
    if isinstance(value, (ast.List, ast.Tuple)):
        return any(_is_agent_e2e_mark(elt) for elt in value.elts)
    return _is_agent_e2e_mark(value)


def _module_has_agent_e2e_mark(tree: ast.AST) -> bool:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(t, ast.Name) and t.id == "pytestmark" for t in node.targets
            ) and _pytestmark_has_agent_e2e(node.value):
                return True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for dec in node.decorator_list:
                if _is_agent_e2e_mark(dec):
                    return True
    return False


def _discover_marked_modules() -> frozenset[str]:
    marked: set[str] = set()
    for path in sorted(_TESTS_DIR.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if _module_has_agent_e2e_mark(tree):
            marked.add(f"tests/{path.name}")
    return frozenset(marked)


def _documented_harness_modules(text: str) -> frozenset[str]:
    assert _TABLE_ANCHOR in text, (
        f"{_HARNESS_DOC.relative_to(_REPO_ROOT)}: missing anchor "
        f"{_TABLE_ANCHOR!r}"
    )
    after = text.split(_TABLE_ANCHOR, 1)[1]
    modules: set[str] = set()
    in_table = False
    for line in after.splitlines():
        stripped = line.strip()
        if not in_table:
            if stripped.startswith("| Module |"):
                in_table = True
            continue
        if not stripped.startswith("|"):
            break
        if stripped.startswith("| ---") or stripped.startswith("|--"):
            continue
        match = _MODULE_CELL_RE.match(stripped)
        if match:
            modules.add(match.group(1))
    assert modules, (
        f"{_HARNESS_DOC.relative_to(_REPO_ROOT)}: no Module rows after "
        f"{_TABLE_ANCHOR!r}"
    )
    return frozenset(modules)


def test_agent_e2e_harness_table_matches_marked_modules() -> None:
    """Marked agent_e2e modules must equal harness table Module paths."""
    assert _HARNESS_DOC.is_file(), f"missing harness doc: {_HARNESS_DOC}"
    marked = _discover_marked_modules()
    documented = _documented_harness_modules(
        _HARNESS_DOC.read_text(encoding="utf-8"),
    )
    only_in_marks = sorted(marked - documented)
    only_in_doc = sorted(documented - marked)
    assert marked == documented, (
        "agent_e2e mark set != harness table Module paths; "
        f"only_in_marks={only_in_marks!r}; only_in_doc={only_in_doc!r}"
    )
