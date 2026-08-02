"""PYPOST-971: flat and tree DisplayRole scan share one helper owner."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_REPO = Path(__file__).resolve().parents[1]
_TREE_INDEX = _REPO / "pypost" / "agent" / "tree_index.py"
_UI_ACTIONS = _REPO / "pypost" / "agent" / "ui_actions.py"


def _parse(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _function_defs(tree: ast.AST) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _calls_name(fn: ast.AST, name: str) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == name
        for node in ast.walk(fn)
    )


def _imports_from_tree_index(tree: ast.AST, name: str) -> bool:
    return any(
        isinstance(node, ast.ImportFrom)
        and node.module == "pypost.agent.tree_index"
        and any(alias.name == name for alias in node.names)
        for node in ast.walk(tree)
    )


def _has_display_role_attr(fn: ast.AST) -> bool:
    """True if ``fn`` references ``ItemDataRole.DisplayRole`` (inline match)."""
    for node in ast.walk(fn):
        if not isinstance(node, ast.Attribute) or node.attr != "DisplayRole":
            continue
        value = node.value
        if isinstance(value, ast.Attribute) and value.attr == "ItemDataRole":
            return True
        if isinstance(value, ast.Name) and value.id == "ItemDataRole":
            return True
    return False


def test_flat_and_tree_share_display_role_match_helper() -> None:
    """AC-1: shared DisplayRole match + flat scan live in tree_index and are used."""
    assert _TREE_INDEX.is_file(), f"missing {_TREE_INDEX}"
    assert _UI_ACTIONS.is_file(), f"missing {_UI_ACTIONS}"

    tree_index_ast = _parse(_TREE_INDEX)
    ui_actions_ast = _parse(_UI_ACTIONS)
    tree_defs = _function_defs(tree_index_ast)
    ui_defs = _function_defs(ui_actions_ast)

    assert "display_role_equals" in tree_defs, (
        "pypost.agent.tree_index must define display_role_equals "
        "(shared DisplayRole exact-match policy)"
    )
    assert "find_child_index_by_display_text" in tree_defs, (
        "pypost.agent.tree_index must define find_child_index_by_display_text "
        "(flat sibling DisplayRole scan)"
    )

    find_tree = tree_defs.get("find_tree_index_by_display_text")
    assert find_tree is not None, "missing find_tree_index_by_display_text"
    assert _calls_name(find_tree, "display_role_equals"), (
        "find_tree_index_by_display_text (or nested walk) must call "
        "display_role_equals instead of inlining DisplayRole comparison"
    )
    assert not _has_display_role_attr(find_tree), (
        "find_tree_index_by_display_text must not compare ItemDataRole.DisplayRole "
        "inline; use display_role_equals"
    )

    select_item = ui_defs.get("_select_item_view")
    assert select_item is not None, "missing _select_item_view"
    assert _imports_from_tree_index(ui_actions_ast, "find_child_index_by_display_text"), (
        "_select_item_view must import find_child_index_by_display_text from "
        "pypost.agent.tree_index"
    )
    assert _calls_name(select_item, "find_child_index_by_display_text"), (
        "_select_item_view text branch must call find_child_index_by_display_text"
    )
    assert not _has_display_role_attr(select_item), (
        "_select_item_view must not access ItemDataRole.DisplayRole for text "
        "matching; delegate to find_child_index_by_display_text"
    )
