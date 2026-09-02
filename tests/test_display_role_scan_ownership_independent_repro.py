"""Independent tests for guarded DisplayRole ownership conditions.

The production implementation is intentionally not imported by these tests.  Each
case substitutes a small, valid ``tree_index`` source module at the ownership
suite's existing ``_parse(Path)`` seam and invokes exactly one Step 4 assertion
helper.  The Step 4 helpers now exist and these tests validate them independently.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Callable
from pathlib import Path

import pytest

import tests.test_display_role_scan_ownership as ownership_suite

pytestmark = pytest.mark.timeout(10)


_COMPLIANT_EXPORTS = """__all__ = [
    \"display_role_equals\",
    \"find_child_index_by_display_text\",
    \"find_tree_index_by_display_text\",
]"""

_SHARED_MATCHER = """def display_role_equals(index, text):
    return str(index.data(Qt.ItemDataRole.DisplayRole)) == text
"""

_COMPLIANT_FLAT = """def find_child_index_by_display_text(model, text, parent=None):
    for row in range(model.rowCount(parent)):
        index = model.index(row, 0, parent)
        if display_role_equals(index, text):
            return index
    return None
"""

_INLINE_FLAT = """def find_child_index_by_display_text(model, text, parent=None):
    for row in range(model.rowCount(parent)):
        index = model.index(row, 0, parent)
        if str(index.data(Qt.ItemDataRole.DisplayRole)) == text:
            return index
    return None
"""

_DELEGATES_AND_INLINES_FLAT = """def find_child_index_by_display_text(model, text, parent=None):
    for row in range(model.rowCount(parent)):
        index = model.index(row, 0, parent)
        if display_role_equals(index, text):
            if str(index.data(Qt.ItemDataRole.DisplayRole)) == text:
                return index
    return None
"""

_COMPLIANT_TREE = """def find_tree_index_by_display_text(tree, text):
    model = tree.model()
    if model is None:
        return None
    index = model.index(0, 0)
    return index if display_role_equals(index, text) else None
"""

_INLINED_FIND_TREE = """def find_tree_index_by_display_text(tree, text):
    model = tree.model()
    if model is None:
        return None
    index = model.index(0, 0)
    if str(index.data(Qt.ItemDataRole.DisplayRole)) == text:
        return index
    return None
"""


def _source(flat: str, tree: str) -> str:
    """Build a parseable synthetic tree_index module for one mutation."""
    return "\n\n".join(
        (
            "from PySide6.QtCore import Qt",
            _COMPLIANT_EXPORTS,
            _SHARED_MATCHER,
            flat,
            tree,
        )
    )


def _patch_tree_index_source(monkeypatch: pytest.MonkeyPatch, source: str) -> None:
    """Return the selected mutant AST only for the tree_index parse request."""
    real_parse = ownership_suite._parse

    def fake_parse(path: Path) -> ast.AST:
        if path == ownership_suite._TREE_INDEX:
            return ast.parse(source, filename=str(path))
        return real_parse(path)

    monkeypatch.setattr(ownership_suite, "_parse", fake_parse)


def _isolated_assertion(name: str) -> Callable[[], None]:
    """Return one Step 4 ownership assertion for independent validation."""
    assertion = getattr(ownership_suite, name, None)
    assert callable(assertion), (
        f"tests.test_display_role_scan_ownership must expose {name} for independent "
        "ownership coverage"
    )
    return assertion


def test_repro_flat_delegation_is_independently_pinned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-1 catches a flat finder that bypasses the shared matcher."""
    _patch_tree_index_source(monkeypatch, _source(_INLINE_FLAT, _COMPLIANT_TREE))
    assertion = _isolated_assertion("_assert_flat_shared_ownership")

    with pytest.raises(
        AssertionError,
        match=re.escape(
            "find_child_index_by_display_text must call display_role_equals "
            "instead of inlining DisplayRole comparison"
        ),
    ):
        assertion()


def test_repro_flat_duplicate_ownership_is_independently_pinned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-2 catches a second local DisplayRole comparison in the flat finder."""
    _patch_tree_index_source(
        monkeypatch,
        _source(_DELEGATES_AND_INLINES_FLAT, _COMPLIANT_TREE),
    )
    assertion = _isolated_assertion("_assert_flat_no_duplicate_ownership")

    with pytest.raises(
        AssertionError,
        match=re.escape(
            "find_child_index_by_display_text must not compare "
            "ItemDataRole.DisplayRole inline; use display_role_equals"
        ),
    ):
        assertion()


@pytest.mark.parametrize("tree_body", [_INLINED_FIND_TREE], ids=["inlined-find_tree"])
def test_repro_tree_delegation_is_independently_pinned(
    monkeypatch: pytest.MonkeyPatch,
    tree_body: str,
) -> None:
    """AC-4 catches a tree finder that bypasses the shared matcher."""
    _patch_tree_index_source(monkeypatch, _source(_COMPLIANT_FLAT, tree_body))
    assertion = _isolated_assertion("_assert_tree_shared_ownership")

    with pytest.raises(
        AssertionError,
        match=re.escape(
            "find_tree_index_by_display_text must call display_role_equals "
            "instead of inlining DisplayRole comparison"
        ),
    ):
        assertion()


def test_compliant_source_does_not_trigger_ownership_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The independent ownership checks accept compliant delegation."""
    _patch_tree_index_source(monkeypatch, _source(_COMPLIANT_FLAT, _COMPLIANT_TREE))

    _isolated_assertion("_assert_flat_shared_ownership")()
    _isolated_assertion("_assert_flat_no_duplicate_ownership")()
    _isolated_assertion("_assert_tree_shared_ownership")()
