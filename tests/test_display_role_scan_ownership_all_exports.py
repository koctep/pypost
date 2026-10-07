"""PYPOST-1235 repro: the ownership suite must read every literal ``__all__`` spelling.

Before the fix, ``_module_all_exports`` in ``tests/test_display_role_scan_ownership.py``
read only the plain ``__all__ = [...]`` spelling and returned ``set()`` for everything
else. That gave a false red on an annotated literal (``__all__: list[str] = [...]``) and
a misleading ``found []`` diagnostic when no literal manifest could be read at all.

The end-to-end tests run the ownership test against a synthetic ``tree_index`` through
the PYPOST-1041 source-substitution seam. The unit tests call the reader directly; its
contract is ``set[str] | None``, where ``None`` means "no statically readable literal
``__all__``" and ``set()`` means a literal empty manifest.
"""

from __future__ import annotations

import ast

import pytest

import tests.test_display_role_scan_ownership as ownership_suite
from tests.test_display_role_scan_ownership_repro import (
    _COMPLIANT_FIND_CHILD,
    _MUTANT_TREE_INDEX_TEMPLATE,
    _patch_tree_index_source,
)

pytestmark = pytest.mark.timeout(10)

_ANNOTATED_LIST_EXPORTS = """__all__: list[str] = [
    "display_role_equals",
    "find_child_index_by_display_text",
    "find_tree_index_by_display_text",
]"""

_ANNOTATED_TUPLE_EXPORTS = """__all__: tuple[str, ...] = (
    "display_role_equals",
    "find_child_index_by_display_text",
    "find_tree_index_by_display_text",
)"""

_ANNOTATED_MISSING_NAME_EXPORTS = """__all__: list[str] = [
    "display_role_equals",
    "find_child_index_by_display_text",
]"""

_BARE_ANNOTATION_EXPORTS = "__all__: list[str]"

_COMPUTED_EXPORTS = """_PUBLIC = (
    "display_role_equals",
    "find_child_index_by_display_text",
    "find_tree_index_by_display_text",
)
__all__ = list(_PUBLIC)"""

_ABSENT_EXPORTS = "# no __all__ manifest"

_EMPTY_LITERAL_EXPORTS = "__all__ = []"


def _tree_index_with(exports: str) -> str:
    """Render a compliant synthetic ``tree_index`` source with the given ``__all__`` block."""
    return _MUTANT_TREE_INDEX_TEMPLATE.format(
        exports=exports,
        find_child=_COMPLIANT_FIND_CHILD,
    )


# --- End-to-end: ownership test against a synthetic tree_index -----------------------


@pytest.mark.parametrize(
    "exports",
    [
        pytest.param(_ANNOTATED_LIST_EXPORTS, id="annotated-list"),
        pytest.param(_ANNOTATED_TUPLE_EXPORTS, id="annotated-tuple"),
    ],
)
def test_ownership_suite_accepts_annotated_literal_all(
    monkeypatch: pytest.MonkeyPatch,
    exports: str,
) -> None:
    """An annotated literal ``__all__`` with the three helpers passes the ownership test."""
    _patch_tree_index_source(monkeypatch, _tree_index_with(exports))

    ownership_suite.test_flat_and_tree_share_display_role_match_helper()


def test_ownership_suite_lists_present_names_for_annotated_literal_missing_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An annotated literal lacking a helper fails with the names it actually lists."""
    _patch_tree_index_source(monkeypatch, _tree_index_with(_ANNOTATED_MISSING_NAME_EXPORTS))

    with pytest.raises(
        AssertionError,
        match=r"__all__ must export .*; "
        r"found \['display_role_equals', 'find_child_index_by_display_text'\]",
    ):
        ownership_suite.test_flat_and_tree_share_display_role_match_helper()


@pytest.mark.parametrize(
    "exports",
    [
        pytest.param(_BARE_ANNOTATION_EXPORTS, id="bare-annotation"),
        pytest.param(_COMPUTED_EXPORTS, id="computed"),
        pytest.param(_ABSENT_EXPORTS, id="absent"),
    ],
)
def test_ownership_suite_reports_unreadable_all_distinctly(
    monkeypatch: pytest.MonkeyPatch,
    exports: str,
) -> None:
    """An unreadable manifest says so instead of reporting ``found []``."""
    _patch_tree_index_source(monkeypatch, _tree_index_with(exports))

    with pytest.raises(
        AssertionError,
        match=r"__all__.*no statically readable literal __all__",
    ) as exc_info:
        ownership_suite.test_flat_and_tree_share_display_role_match_helper()

    message = str(exc_info.value)
    assert "found []" not in message, message


def test_ownership_suite_keeps_found_empty_for_empty_literal_all(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression guard: a literal empty ``__all__`` keeps the ``found []`` diagnostic."""
    _patch_tree_index_source(monkeypatch, _tree_index_with(_EMPTY_LITERAL_EXPORTS))

    with pytest.raises(AssertionError, match=r"__all__ must export .*; found \[\]"):
        ownership_suite.test_flat_and_tree_share_display_role_match_helper()


# --- Unit: the manifest reader ---------------------------------------------------------


@pytest.mark.parametrize(
    ("snippet", "expected"),
    [
        pytest.param('__all__ = ["a", "b"]', {"a", "b"}, id="plain-list"),
        pytest.param('__all__ = ("a", "b")', {"a", "b"}, id="plain-tuple"),
        pytest.param('__all__: list[str] = ["a", "b"]', {"a", "b"}, id="annotated-list"),
        pytest.param('__all__: tuple[str, ...] = ("a",)', {"a"}, id="annotated-tuple"),
        pytest.param("__all__ = list(_PUBLIC)", None, id="computed"),
        pytest.param("__all__: list[str]", None, id="bare-annotation"),
        pytest.param("__all__ = []", set(), id="empty-literal"),
        pytest.param("x = 1", None, id="absent"),
        pytest.param(
            '__all__: list[str]\n__all__ = ["a"]',
            {"a"},
            id="bare-then-literal",
        ),
    ],
)
def test_module_all_exports_reads_manifest_spelling(
    snippet: str,
    expected: set[str] | None,
) -> None:
    """The reader returns the listed names, ``set()`` for empty, ``None`` if unreadable."""
    result = ownership_suite._module_all_exports(ast.parse(snippet))

    assert result == expected, f"{snippet!r}: expected {expected!r}, got {result!r}"
