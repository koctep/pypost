"""PYPOST-1041 repro: the DisplayRole ownership suite must lock the flat finder.

Each test below was red before Step 4 and pins one gap in
``tests/test_display_role_scan_ownership.py``:

1. No AST assertion that ``find_child_index_by_display_text`` delegates to
   ``display_role_equals``.
2. No AST assertion that ``find_child_index_by_display_text`` never inlines
   ``ItemDataRole.DisplayRole``.
3. No AST assertion that ``pypost.agent.tree_index.__all__`` exports the helpers.
4. Mutation gap: a ``find_child_index_by_display_text`` that inlines DisplayRole
   passes the ownership suite.
5. Mutation gap: an empty ``__all__`` in ``tree_index`` passes the ownership suite.
6. No source-inspection repro pins the ``find_tree_index_by_display_text`` diagnostic.
7. No source-inspection repro pins the ``_select_item_view`` diagnostic.

Tests 1-3 and 6-7 inspect the ownership suite's own source; tests 4-5 run the suite against
a synthetic ``tree_index`` mutant and require it to fail.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

import pytest

import tests.test_display_role_scan_ownership as ownership_suite

pytestmark = pytest.mark.timeout(10)

_REPO = Path(__file__).resolve().parents[1]
_OWNERSHIP_TEST_FILE = _REPO / "tests" / "test_display_role_scan_ownership.py"

# Mutants are parsed, never imported: only their AST shape matters. They mirror the
# real pypost/agent/tree_index.py signatures so a reviewer can diff them by eye, and
# each varies exactly one axis of the template below (``__all__`` and the flat finder
# body) so a mutant isolates a single contract violation.
_COMPLIANT_EXPORTS = """__all__ = [
    "display_role_equals",
    "find_child_index_by_display_text",
    "find_tree_index_by_display_text",
]"""

_EMPTY_EXPORTS = "__all__ = []"

_COMPLIANT_FIND_CHILD = '''def find_child_index_by_display_text(
    model: QAbstractItemModel,
    text: str,
    parent: QModelIndex | None = None,
) -> QModelIndex | None:
    parent_index = QModelIndex() if parent is None else parent
    for row in range(model.rowCount(parent_index)):
        index = model.index(row, 0, parent_index)
        if display_role_equals(index, text):
            return index
    return None'''

_INLINED_FIND_CHILD = '''def find_child_index_by_display_text(
    model: QAbstractItemModel,
    text: str,
    parent: QModelIndex | None = None,
) -> QModelIndex | None:
    # MUTATION: inlines the DisplayRole comparison instead of calling display_role_equals.
    parent_index = QModelIndex() if parent is None else parent
    for row in range(model.rowCount(parent_index)):
        index = model.index(row, 0, parent_index)
        if str(index.data(Qt.ItemDataRole.DisplayRole)) == text:
            return index
    return None'''

_MUTANT_TREE_INDEX_TEMPLATE = '''"""Synthetic pypost.agent.tree_index stand-in."""

from __future__ import annotations

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PySide6.QtWidgets import QTreeView

{exports}


def display_role_equals(index: QModelIndex, text: str) -> bool:
    return str(index.data(Qt.ItemDataRole.DisplayRole)) == text


{find_child}


def find_tree_index_by_display_text(tree: QTreeView, text: str) -> QModelIndex | None:
    model = tree.model()
    if model is None:
        return None
    root = QModelIndex()
    for row in range(model.rowCount(root)):
        index = model.index(row, 0, root)
        if display_role_equals(index, text):
            return index
    return None
'''

_MUTANT_INLINE_DISPLAY_ROLE_CODE = _MUTANT_TREE_INDEX_TEMPLATE.format(
    exports=_COMPLIANT_EXPORTS,
    find_child=_INLINED_FIND_CHILD,
)

_MUTANT_EMPTY_ALL_EXPORTS_CODE = _MUTANT_TREE_INDEX_TEMPLATE.format(
    exports=_EMPTY_EXPORTS,
    find_child=_COMPLIANT_FIND_CHILD,
)


def _parse_file(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _calls_to(tree: ast.AST, func_name: str) -> Iterator[ast.Call]:
    """Yield every direct call to the bare name ``func_name`` inside ``tree``."""
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == func_name
        ):
            yield node


def _refers_to_find_child(arg: ast.expr) -> bool:
    """True when ``arg`` denotes the ``find_child_index_by_display_text`` AST node.

    The ownership suite may bind that node to a local (``find_child``) or pass a
    lookup expression, so accept either spelling.
    """
    if isinstance(arg, ast.Name) and "child" in arg.id.lower():
        return True
    return "find_child_index_by_display_text" in ast.dump(arg)


def _has_find_child_delegation_check(tree: ast.AST) -> bool:
    """True when the suite asserts ``find_child`` calls ``display_role_equals``."""
    for call in _calls_to(tree, "_calls_name"):
        if len(call.args) < 2:
            continue
        target_arg, called_arg = call.args[0], call.args[1]
        names_display_role_equals = (
            isinstance(called_arg, ast.Constant) and called_arg.value == "display_role_equals"
        )
        if names_display_role_equals and _refers_to_find_child(target_arg):
            return True
    return False


def _has_find_child_forbids_display_role_check(tree: ast.AST) -> bool:
    """True when the suite runs the inline-DisplayRole probe over ``find_child``."""
    return any(
        call.args and _refers_to_find_child(call.args[0])
        for call in _calls_to(tree, "_has_display_role_attr")
    )


def _has_all_exports_check(tree: ast.AST) -> bool:
    """True when the suite reads ``__all__`` and asserts the required export names.

    Requires both halves of the check: a call to the ``_module_all_exports`` helper
    and a literal collection naming the helpers that must be exported.
    """
    if next(_calls_to(tree, "_module_all_exports"), None) is None:
        return False
    required = {"display_role_equals", "find_child_index_by_display_text"}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Set, ast.List, ast.Tuple)):
            continue
        names = {
            elt.value
            for elt in node.elts
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
        }
        if required.issubset(names):
            return True
    return False


def _main_ownership_test(tree: ast.AST) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "test_flat_and_tree_share_display_role_match_helper"
        ):
            return node
    raise AssertionError(
        "tests/test_display_role_scan_ownership.py must define the main ownership test"
    )


def _main_test_assertion_message(local_name: str) -> str:
    main_test = _main_ownership_test(_parse_file(_OWNERSHIP_TEST_FILE))
    matching_assertions = [
        node
        for node in ast.walk(main_test)
        if isinstance(node, ast.Assert)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == local_name
        and node.msg is not None
    ]
    assert len(matching_assertions) == 1, (
        f"main ownership test must have one diagnostic assertion for {local_name}"
    )
    message = matching_assertions[0].msg
    assert isinstance(message, ast.Constant) and isinstance(message.value, str), (
        f"main ownership test diagnostic for {local_name} must be a string literal"
    )
    return message.value


def _patch_tree_index_source(monkeypatch: pytest.MonkeyPatch, source: str) -> None:
    """Make the ownership suite parse ``source`` in place of the real tree_index."""
    real_parse = ownership_suite._parse

    def fake_parse(path: Path) -> ast.AST:
        if path == ownership_suite._TREE_INDEX:
            return ast.parse(source, filename=str(path))
        return real_parse(path)

    monkeypatch.setattr(ownership_suite, "_parse", fake_parse)


def test_repro_ownership_suite_checks_find_child_delegation() -> None:
    """The ownership suite asserts find_child delegates to display_role_equals."""
    assert _has_find_child_delegation_check(_parse_file(_OWNERSHIP_TEST_FILE)), (
        "tests/test_display_role_scan_ownership.py must assert that "
        "find_child_index_by_display_text calls display_role_equals"
    )


def test_repro_ownership_suite_checks_find_child_forbids_inline_display_role() -> None:
    """The ownership suite forbids an inline ItemDataRole.DisplayRole in find_child."""
    assert _has_find_child_forbids_display_role_check(_parse_file(_OWNERSHIP_TEST_FILE)), (
        "tests/test_display_role_scan_ownership.py must assert that "
        "find_child_index_by_display_text does not access ItemDataRole.DisplayRole inline"
    )


def test_repro_ownership_suite_checks_tree_index_all_exports() -> None:
    """The ownership suite asserts pypost.agent.tree_index.__all__ exports the helpers."""
    assert _has_all_exports_check(_parse_file(_OWNERSHIP_TEST_FILE)), (
        "tests/test_display_role_scan_ownership.py must verify that "
        "pypost.agent.tree_index.__all__ exports display_role_equals "
        "and find_child_index_by_display_text"
    )


def test_missing_recursive_lookup_diagnostic_names_owner_and_remedy() -> None:
    """The main tree lookup diagnostic identifies its owner and repair direction."""
    message = _main_test_assertion_message("find_tree")

    assert "find_tree_index_by_display_text" in message
    assert "Tree Index" in message
    assert "restore recursive lookup" in message
    assert len(message.splitlines()) == 1, message


def test_missing_item_view_selection_diagnostic_names_owner_and_remedy() -> None:
    """The main item-view diagnostic identifies its owner and repair direction."""
    message = _main_test_assertion_message("select_item")

    assert "_select_item_view" in message
    assert "UI Actions" in message
    assert "restore item-view selection" in message
    assert len(message.splitlines()) == 1, message


def test_repro_ownership_suite_catches_inlined_display_role_mutant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A find_child that inlines DisplayRole must fail the ownership suite."""
    _patch_tree_index_source(monkeypatch, _MUTANT_INLINE_DISPLAY_ROLE_CODE)

    with pytest.raises(
        AssertionError,
        match=r"find_child_index_by_display_text.*(display_role_equals|DisplayRole)",
    ):
        ownership_suite.test_flat_and_tree_share_display_role_match_helper()


def test_repro_ownership_suite_catches_empty_all_exports_mutant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A tree_index with an empty __all__ must fail the ownership suite."""
    _patch_tree_index_source(monkeypatch, _MUTANT_EMPTY_ALL_EXPORTS_CODE)

    with pytest.raises(AssertionError, match=r"__all__.*export"):
        ownership_suite.test_flat_and_tree_share_display_role_match_helper()
