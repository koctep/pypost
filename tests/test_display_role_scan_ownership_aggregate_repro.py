"""PYPOST-1237: the ownership guard reports all violations together."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import tests.test_display_role_scan_ownership as ownership_suite

pytestmark = pytest.mark.timeout(10)

_FLAT = Path("flat.py")
_TREE_DUPLICATE = Path("tree_duplicate.py")
_TREE_OWNERSHIP = Path("tree_ownership.py")

_DIAGNOSTICS = (
    "find_child_index_by_display_text must call display_role_equals instead of inlining DisplayRole comparison",
    "find_tree_index_by_display_text must not compare ItemDataRole.DisplayRole inline; use display_role_equals",
    "find_tree_index_by_display_text must call display_role_equals instead of inlining DisplayRole comparison",
)

_CONTEXT_LABELS = {
    _FLAT: "flat",
    _TREE_DUPLICATE: "tree-duplicate",
    _TREE_OWNERSHIP: "tree-ownership",
}


def _fixture_source(path: Path) -> str:
    if path == _FLAT:
        return """
def find_child_index_by_display_text(model, text, parent=None):
    return str(model.index(0, 0, parent).data(Qt.ItemDataRole.DisplayRole)) == text
"""
    if path == _TREE_DUPLICATE:
        return """
def find_tree_index_by_display_text(tree, text):
    index = tree.model().index(0, 0)
    if display_role_equals(index, text):
        return str(index.data(Qt.ItemDataRole.DisplayRole)) == text
    return None
"""
    if path == _TREE_OWNERSHIP:
        return """
def find_tree_index_by_display_text(tree, text):
    return tree.model().index(0, 0)
"""
    raise AssertionError(f"unexpected fixture path: {path}")


def _patch_parser(
    monkeypatch: pytest.MonkeyPatch,
    paths: tuple[Path, ...],
    parse_calls: list[Path],
) -> None:
    fixtures = {path: _fixture_source(path) for path in paths}

    def fake_parse(path: Path) -> ast.AST:
        parse_calls.append(path)
        return ast.parse(fixtures[path], filename=str(path))

    monkeypatch.setattr(ownership_suite, "_parse", fake_parse)


def _aggregate_validator(
    entry_calls: list[tuple[Path, ...]],
    *,
    compatibility: bool = False,
) -> object:
    validator = getattr(ownership_suite, "_validate_display_role_ownership", None)
    if callable(validator):
        def invoke(paths: tuple[Path, ...]) -> object:
            entry_calls.append(paths)
            return validator(paths)

        return invoke

    if compatibility:
        def clean_compatibility(paths: tuple[Path, ...]) -> None:
            entry_calls.append(paths)
            for path in paths:
                ownership_suite._parse(path)

        return clean_compatibility

    def missing_validator(paths: tuple[Path, ...]) -> None:
        entry_calls.append(paths)
        for path in paths:
            ownership_suite._parse(path)
        raise AssertionError(
            "Step 4 must expose _validate_display_role_ownership for aggregate validation"
        )

    return missing_validator


def test_repro_reports_all_ownership_violations_in_one_stable_outcome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Multiple independent violations must be collected before one failure."""
    paths = (_FLAT, _TREE_DUPLICATE, _TREE_OWNERSHIP)
    parse_calls: list[Path] = []
    entry_calls: list[tuple[Path, ...]] = []
    _patch_parser(monkeypatch, paths, parse_calls)
    validator = _aggregate_validator(entry_calls)

    with pytest.raises(AssertionError) as raised:
        validator(paths)

    assert entry_calls == [paths]
    assert parse_calls == list(paths)
    assert [_CONTEXT_LABELS[path] for path in parse_calls] == [
        "flat",
        "tree-duplicate",
        "tree-ownership",
    ]
    message = str(raised.value)
    positions = [message.index(diagnostic) for diagnostic in _DIAGNOSTICS]
    assert positions == sorted(positions)
    assert all(message.count(diagnostic) == 1 for diagnostic in _DIAGNOSTICS)


def test_repro_single_violation_has_no_unrelated_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = (_FLAT,)
    parse_calls: list[Path] = []
    entry_calls: list[tuple[Path, ...]] = []
    _patch_parser(monkeypatch, paths, parse_calls)
    validator = _aggregate_validator(entry_calls)

    with pytest.raises(AssertionError) as raised:
        validator(paths)

    assert entry_calls == [paths]
    assert parse_calls == [_FLAT]
    assert [_CONTEXT_LABELS[path] for path in parse_calls] == ["flat"]
    assert str(raised.value).count(_DIAGNOSTICS[0]) == 1
    assert _DIAGNOSTICS[1] not in str(raised.value)
    assert _DIAGNOSTICS[2] not in str(raised.value)


def test_repro_clean_scope_completes_without_ownership_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clean = Path("clean.py")
    parse_calls: list[Path] = []
    entry_calls: list[tuple[Path, ...]] = []
    monkeypatch.setattr(
        ownership_suite,
        "_parse",
        lambda path: (
            parse_calls.append(path)
            or ast.parse(
                """
def display_role_equals(index, text):
    return True

def find_child_index_by_display_text(model, text, parent=None):
    return display_role_equals(model, text)

def find_tree_index_by_display_text(tree, text):
    return display_role_equals(tree, text)
""",
                filename=str(path),
            )
        ),
    )
    _aggregate_validator(entry_calls, compatibility=True)((clean,))
    assert entry_calls == [(clean,)]
    assert parse_calls == [clean]
