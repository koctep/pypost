"""PYPOST-971/1041: flat and tree DisplayRole scan share one helper owner."""

from __future__ import annotations

import ast
import io
import re
import tokenize
from dataclasses import dataclass
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


def _module_all_exports(tree: ast.AST) -> set[str]:
    """Return the string names listed in the module-level ``__all__`` assignment.

    Returns an empty set when the module declares no ``__all__`` or assigns it
    something other than a list/tuple literal, so a missing manifest fails the
    caller's subset assertion instead of raising.
    """
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in node.targets
        ):
            continue
        value = node.value
        if isinstance(value, (ast.List, ast.Tuple)):
            return {
                elt.value
                for elt in value.elts
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            }
    return set()


_FLAT_DELEGATION_DIAGNOSTIC = (
    "find_child_index_by_display_text must call display_role_equals "
    "instead of inlining DisplayRole comparison"
)
_FLAT_DUPLICATE_DIAGNOSTIC = (
    "find_child_index_by_display_text must not compare "
    "ItemDataRole.DisplayRole inline; use display_role_equals"
)
_TREE_DELEGATION_DIAGNOSTIC = (
    "find_tree_index_by_display_text must call display_role_equals "
    "instead of inlining DisplayRole comparison"
)
_TREE_DUPLICATE_DIAGNOSTIC = (
    "find_tree_index_by_display_text must not compare "
    "ItemDataRole.DisplayRole inline; use display_role_equals"
)


@dataclass(frozen=True)
class _OwnershipViolation:
    """One deterministic, test-side ownership validation result."""

    diagnostic: str
    context: str
    source_order: int


@dataclass(frozen=True)
class DiscoverabilityDiagnostic:
    """One stable diagnostic for the PYPOST-1239 source contract."""

    target: str
    code: str
    message: str


@dataclass(frozen=True)
class DiscoverabilityValidationResult:
    """Structured outcome for local DisplayRole assertion explanations."""

    valid: bool
    checked_targets: tuple[str, ...]
    diagnostics: tuple[DiscoverabilityDiagnostic, ...]


@dataclass(frozen=True)
class _DiscoverabilityTarget:
    label: str
    start_function: str
    end_function: str | None
    call_subject: str
    call_name: str
    display_subject: str
    delegated_lookup: str


_DISCOVERABILITY_TARGETS = (
    _DiscoverabilityTarget(
        "find_child",
        "_assert_flat_shared_ownership",
        "_assert_flat_no_duplicate_ownership",
        "find_child",
        "display_role_equals",
        "find_child",
        "display_role_equals",
    ),
    _DiscoverabilityTarget(
        "find_tree",
        "_assert_tree_shared_ownership",
        None,
        "find_tree",
        "display_role_equals",
        "find_tree",
        "display_role_equals",
    ),
    _DiscoverabilityTarget(
        "_select_item_view",
        "test_flat_and_tree_share_display_role_match_helper",
        None,
        "select_item",
        "find_child_index_by_display_text",
        "select_item",
        "find_child_index_by_display_text",
    ),
)
_DISCOVERABILITY_LABELS = tuple(target.label for target in _DISCOVERABILITY_TARGETS)
_LOCAL_PROXIMITY = 12
_MARKER_RE = re.compile(
    r"\bPYPOST-1239\s+(find_child|find_tree|_select_item_view)\b"
)
_DIAGNOSTIC_MEANINGS = {
    "MISSING_ASSERTION_PAIR": "both repeated DisplayRole assertions are required",
    "MISSING_EXPLANATION": (
        "local rationale is required for both repeated DisplayRole assertions"
    ),
    "MISSING_INTENTIONALITY": "local rationale must state that repetition is intentional",
    "INCOMPLETE_RATIONALE": (
        "local rationale must cover delegation, no inline ownership, and regression risk"
    ),
    "WRONG_TARGET_EXPLANATION": "local rationale names a different assertion target",
    "DETACHED_EXPLANATION": (
        "target rationale must stay local to both repeated DisplayRole assertions"
    ),
}


def _target_region(
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    target: _DiscoverabilityTarget,
) -> tuple[int, int] | None:
    start = functions.get(target.start_function)
    end = functions.get(target.end_function) if target.end_function else start
    if start is None or end is None:
        return None
    return start.lineno, end.end_lineno


def _is_helper_call(
    node: ast.AST, helper: str, subject: str, name: str | None = None
) -> bool:
    expected_args = 1 if name is None else 2
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == helper
        and len(node.args) == expected_args
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == subject
        and (
            name is None
            or (
                isinstance(node.args[1], ast.Constant)
                and node.args[1].value == name
            )
        )
    )


def _assertion_lines(
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    target: _DiscoverabilityTarget,
) -> tuple[int | None, int | None]:
    region = _target_region(functions, target)
    if region is None:
        return None, None
    assertions = [
        node
        for function in functions.values()
        if region[0] <= function.lineno <= region[1]
        for node in ast.walk(function)
        if isinstance(node, ast.Assert) and region[0] <= node.lineno <= region[1]
    ]
    call_line = next(
        (
            node.lineno
            for node in assertions
            if _is_helper_call(
                node.test, "_calls_name", target.call_subject, target.call_name
            )
        ),
        None,
    )
    display_line = next(
        (
            node.lineno
            for node in assertions
            if isinstance(node.test, ast.UnaryOp)
            and isinstance(node.test.op, ast.Not)
            and _is_helper_call(
                node.test.operand, "_has_display_role_attr", target.display_subject
            )
        ),
        None,
    )
    return call_line, display_line


def _source_markers(
    lines: list[str], region: tuple[int, int] | None = None
) -> list[tuple[int, str]]:
    """Return recognized source markers, optionally restricted to a region."""
    start, end = region if region else (1, len(lines))
    markers: list[tuple[int, str]] = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO("\n".join(lines)).readline)
        for token in tokens:
            if token.type != tokenize.COMMENT:
                continue
            line_number = token.start[0]
            if not start <= line_number <= end:
                continue
            markers.extend(
                (line_number, match.group(1))
                for match in _MARKER_RE.finditer(token.string)
            )
    except tokenize.TokenError:
        pass
    return markers


def _nearby_markers(
    lines: list[str], assertion_line: int, region: tuple[int, int]
) -> list[tuple[int, str]]:
    """Find markers within the bounded nonblank-line proximity contract."""
    nonblank = [
        line_number
        for line_number in range(region[0], region[1] + 1)
        if lines[line_number - 1].strip()
    ]
    assertion_position = nonblank.index(assertion_line)
    return [
        marker
        for marker in _source_markers(lines, region)
        if abs(nonblank.index(marker[0]) - assertion_position) <= _LOCAL_PROXIMITY
    ]


def _marker_explanation(lines: list[str], marker_line: int) -> str:
    """Read the contiguous comment block attached to a source marker."""
    comment_lines = [lines[marker_line - 1]]
    for direction in (-1, 1):
        line_number = marker_line + direction
        while 1 <= line_number <= len(lines):
            line = lines[line_number - 1]
            if not line.strip() or not line.lstrip().startswith("#"):
                break
            if direction < 0:
                comment_lines.insert(0, line)
            else:
                comment_lines.append(line)
            line_number += direction
    return " ".join(comment_lines).lower()


def _has_complete_rationale(explanation: str, target: _DiscoverabilityTarget) -> bool:
    """Check the three non-intentionality rationale facts for one target."""
    delegates = "delegat" in explanation and target.delegated_lookup.lower() in explanation
    no_inline_ownership = (
        "no inline" in explanation
        and "displayrole" in explanation.replace(" ", "")
        and "ownership" in explanation
    )
    regression_risk = "regression" in explanation and any(
        word in explanation for word in ("risk", "weaken", "protect")
    )
    return delegates and no_inline_ownership and regression_risk


def _rationale_diagnostic(
    lines: list[str],
    target: _DiscoverabilityTarget,
    assertion_lines: tuple[int, int],
    region: tuple[int, int],
) -> DiscoverabilityDiagnostic | None:
    """Return the first stable rationale failure for one target."""
    all_markers = _source_markers(lines)
    for assertion_line in assertion_lines:
        nearby = _nearby_markers(lines, assertion_line, region)
        matching = [marker for marker in nearby if marker[1] == target.label]
        if matching:
            continue
        if any(marker[1] != target.label for marker in nearby):
            code = "WRONG_TARGET_EXPLANATION"
        elif any(marker[1] == target.label for marker in all_markers):
            code = "DETACHED_EXPLANATION"
        else:
            code = "MISSING_EXPLANATION"
        message = (
            f"PYPOST-1239/{target.label}/{code}: "
            f"{_DIAGNOSTIC_MEANINGS[code]}"
        )
        return DiscoverabilityDiagnostic(
            target.label, code, message
        )

    explanations = [
        _marker_explanation(lines, marker_line)
        for assertion_line in assertion_lines
        for marker_line, label in _nearby_markers(lines, assertion_line, region)
        if label == target.label
    ]
    if not all(
        "intentional" in explanation
        and ("repeated" in explanation or "repetition" in explanation)
        for explanation in explanations
    ):
        code = "MISSING_INTENTIONALITY"
    elif not all(
        _has_complete_rationale(explanation, target) for explanation in explanations
    ):
        code = "INCOMPLETE_RATIONALE"
    else:
        return None
    message = (
        f"PYPOST-1239/{target.label}/{code}: "
        f"{_DIAGNOSTIC_MEANINGS[code]}"
    )
    return DiscoverabilityDiagnostic(
        target.label, code, message
    )


def validate_display_role_discoverability(
    source_text: str,
) -> DiscoverabilityValidationResult:
    """Validate local explanations for the repeated ownership assertions."""
    try:
        functions = _function_defs(ast.parse(source_text))
    except SyntaxError:
        message = (
            "PYPOST-1239/module/INVALID_SOURCE: "
            "source text must parse as Python"
        )
        diagnostic = DiscoverabilityDiagnostic(
            "module", "INVALID_SOURCE", message
        )
        return DiscoverabilityValidationResult(False, _DISCOVERABILITY_LABELS, (diagnostic,))

    lines = source_text.splitlines()
    diagnostics: list[DiscoverabilityDiagnostic] = []
    for target in _DISCOVERABILITY_TARGETS:
        region = _target_region(functions, target)
        assertion_lines = _assertion_lines(functions, target)
        if region is None or any(line is None for line in assertion_lines):
            code = "MISSING_ASSERTION_PAIR"
            message = (
                f"PYPOST-1239/{target.label}/{code}: "
                f"{_DIAGNOSTIC_MEANINGS[code]}"
            )
            diagnostics.append(
                DiscoverabilityDiagnostic(
                    target.label, code, message
                )
            )
            continue
        diagnostic = _rationale_diagnostic(
            lines, target, (assertion_lines[0], assertion_lines[1]), region
        )
        if diagnostic is not None:
            diagnostics.append(diagnostic)
    return DiscoverabilityValidationResult(
        not diagnostics, _DISCOVERABILITY_LABELS, tuple(diagnostics)
    )


def _ownership_context(path: Path) -> str:
    return {
        "flat": "flat",
        "tree_duplicate": "tree-duplicate",
        "tree_ownership": "tree-ownership",
    }.get(path.stem, path.stem)


def _collect_display_role_violations(paths: tuple[Path, ...]) -> list[_OwnershipViolation]:
    violations: list[_OwnershipViolation] = []
    for source_order, path in enumerate(paths):
        tree_defs = _function_defs(_parse(path))
        context = _ownership_context(path)
        if path.stem == "flat":
            finder = tree_defs.get("find_child_index_by_display_text")
            if finder is not None and not _calls_name(finder, "display_role_equals"):
                violations.append(
                    _OwnershipViolation(
                        _FLAT_DELEGATION_DIAGNOSTIC, context, source_order
                    )
                )
            continue

        finder = tree_defs.get("find_tree_index_by_display_text")
        if finder is None:
            continue
        if _has_display_role_attr(finder):
            violations.append(
                _OwnershipViolation(
                    _TREE_DUPLICATE_DIAGNOSTIC, context, source_order
                )
            )
        elif not _calls_name(finder, "display_role_equals"):
            violations.append(
                _OwnershipViolation(
                    _TREE_DELEGATION_DIAGNOSTIC, context, source_order
                )
            )
    return violations


def _validate_display_role_ownership(paths: tuple[Path, ...]) -> None:
    """Report every ownership violation in one stable validation outcome."""
    violations = _collect_display_role_violations(paths)
    if violations:
        raise AssertionError(
            "\n".join(
                f"[{violation.context}] {violation.diagnostic}"
                for violation in violations
            )
        )


def _tree_defs(tree_defs: dict[str, ast.AST] | None) -> dict[str, ast.AST]:
    return _function_defs(_parse(_TREE_INDEX)) if tree_defs is None else tree_defs


def _assert_flat_shared_ownership(tree_defs: dict[str, ast.AST] | None = None) -> None:
    tree_defs = _tree_defs(tree_defs)
    find_child = tree_defs.get("find_child_index_by_display_text")
    assert find_child is not None, "missing find_child_index_by_display_text"
    # PYPOST-1239 find_child: These assertions are intentionally repeated because this
    # helper delegates to display_role_equals and has no inline DisplayRole ownership.
    # Combining or simplifying them risks weakening ownership regression protection.
    assert _calls_name(find_child, "display_role_equals"), _FLAT_DELEGATION_DIAGNOSTIC


def _assert_flat_no_duplicate_ownership(tree_defs: dict[str, ast.AST] | None = None) -> None:
    tree_defs = _tree_defs(tree_defs)
    find_child = tree_defs.get("find_child_index_by_display_text")
    assert find_child is not None, "missing find_child_index_by_display_text"
    # PYPOST-1239 find_child: These assertions are intentionally repeated because this
    # helper delegates to display_role_equals and has no inline DisplayRole ownership.
    # Combining or simplifying them risks weakening ownership regression protection.
    assert not _has_display_role_attr(find_child), _FLAT_DUPLICATE_DIAGNOSTIC


def _assert_tree_shared_ownership(tree_defs: dict[str, ast.AST] | None = None) -> None:
    tree_defs = _tree_defs(tree_defs)
    find_tree = tree_defs.get("find_tree_index_by_display_text")
    assert find_tree is not None, "missing find_tree_index_by_display_text"
    # PYPOST-1239 find_tree: These assertions are intentionally repeated because this
    # helper delegates to display_role_equals and has no inline DisplayRole ownership.
    # Combining or simplifying them risks weakening ownership regression protection.
    assert _calls_name(find_tree, "display_role_equals"), _TREE_DELEGATION_DIAGNOSTIC
    assert not _has_display_role_attr(find_tree), _TREE_DUPLICATE_DIAGNOSTIC


def test_flat_and_tree_share_display_role_match_helper() -> None:
    """Ownership contract for the shared DisplayRole match and flat sibling scan.

    AC-1: ``find_child_index_by_display_text`` delegates matching to ``display_role_equals``.
    AC-2: it never inlines an ``ItemDataRole.DisplayRole`` comparison of its own.
    AC-3: ``pypost.agent.tree_index.__all__`` names the three public helpers.
    AC-4: the pre-existing ``find_tree_index_by_display_text`` and ``_select_item_view``
    assertions stay intact.
    """
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
    find_child = tree_defs.get("find_child_index_by_display_text")
    assert find_child is not None, (
        "pypost.agent.tree_index must define find_child_index_by_display_text "
        "(flat sibling DisplayRole scan)"
    )
    _assert_flat_shared_ownership(tree_defs)
    _assert_flat_no_duplicate_ownership(tree_defs)

    tree_exports = _module_all_exports(tree_index_ast)
    expected_exports = {
        "display_role_equals",
        "find_child_index_by_display_text",
        "find_tree_index_by_display_text",
    }
    assert expected_exports.issubset(tree_exports), (
        f"pypost.agent.tree_index.__all__ must export {sorted(expected_exports)}; "
        f"found {sorted(tree_exports)}"
    )

    find_tree = tree_defs.get("find_tree_index_by_display_text")
    assert find_tree is not None, (
        "missing find_tree_index_by_display_text recursive/tree lookup responsibility "
        "in Tree Index module; restore recursive lookup"
    )
    _assert_tree_shared_ownership(tree_defs)

    select_item = ui_defs.get("_select_item_view")
    assert select_item is not None, (
        "missing _select_item_view item-view selection responsibility in UI Actions "
        "module; restore item-view selection"
    )
    assert _imports_from_tree_index(ui_actions_ast, "find_child_index_by_display_text"), (
        "_select_item_view must import find_child_index_by_display_text from "
        "pypost.agent.tree_index"
    )
    assert _calls_name(select_item, "find_child_index_by_display_text"), (
        "_select_item_view text branch must call find_child_index_by_display_text"
    )
    # PYPOST-1239 _select_item_view: These assertions are intentionally repeated because
    # this helper delegates to find_child_index_by_display_text, the flat lookup, and
    # has no inline DisplayRole ownership.
    # Combining or simplifying them risks weakening ownership regression protection.
    assert not _has_display_role_attr(select_item), (
        "_select_item_view must not access ItemDataRole.DisplayRole for text "
        "matching; delegate to find_child_index_by_display_text"
    )
