"""PYPOST-1239: local explanations for repeated ownership assertions."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import tests.test_display_role_scan_ownership as ownership_suite

pytestmark = pytest.mark.timeout(10)

_REPO = Path(__file__).resolve().parents[1]
_OWNERSHIP_SOURCE = _REPO / "tests" / "test_display_role_scan_ownership.py"


_TARGETS = (
    {
        "label": "find_child",
        "start": "def _assert_flat_shared_ownership",
        "end": "def _assert_tree_shared_ownership",
        "calls": r"assert\s+_calls_name\s*\(\s*find_child\s*,\s*['\"]display_role_equals['\"]",
        "display_role": r"assert\s+not\s+_has_display_role_attr\s*\(\s*find_child\s*\)",
    },
    {
        "label": "find_tree",
        "start": "def _assert_tree_shared_ownership",
        "end": "def test_flat_and_tree_share_display_role_match_helper",
        "calls": r"assert\s+_calls_name\s*\(\s*find_tree\s*,\s*['\"]display_role_equals['\"]",
        "display_role": r"assert\s+not\s+_has_display_role_attr\s*\(\s*find_tree\s*\)",
    },
    {
        "label": "_select_item_view",
        "start": "def test_flat_and_tree_share_display_role_match_helper",
        "end": None,
        "calls": (
            r"assert\s+_calls_name\s*\(\s*select_item\s*,\s*"
            r"['\"]find_child_index_by_display_text['\"]"
        ),
        "display_role": r"assert\s+not\s+_has_display_role_attr\s*\(\s*select_item\s*\)",
    },
)

_LOCAL_PROXIMITY = 12


def _region(
    lines: list[str], start: str, end: str | None
) -> tuple[int, int]:
    """Return the bounded source region for one target assertion group."""
    start_line = next(index for index, line in enumerate(lines) if start in line)
    if end is None:
        end_line = next(
            (
                index
                for index in range(start_line + 1, len(lines))
                if re.match(r"^(?:async )?def ", lines[index])
            ),
            len(lines),
        )
    else:
        end_line = next(
            index
            for index in range(start_line + 1, len(lines))
            if end in lines[index]
        )
    return start_line, end_line


def _assertion_line(
    lines: list[str], start_line: int, end_line: int, pattern: str
) -> int | None:
    """Find one target-specific assertion without importing the ownership suite."""
    return next(
        (
            index
            for index in range(start_line, end_line)
            if re.search(pattern, lines[index])
        ),
        None,
    )


def _has_nearby_target_marker(
    lines: list[str], assertion_line: int, label: str
) -> bool:
    """Check for the target marker within twelve nonblank source lines."""
    nonblank_lines = [
        index for index, line in enumerate(lines) if line.strip()
    ]
    assertion_position = nonblank_lines.index(assertion_line)
    marker = f"PYPOST-1239 {label}"
    return any(
        abs(position - assertion_position) <= _LOCAL_PROXIMITY
        and marker in lines[index]
        for position, index in enumerate(nonblank_lines)
    )


def test_real_source_has_display_role_explanations() -> None:
    """Require target-specific rationale beside each repeated assertion pair."""
    lines = _OWNERSHIP_SOURCE.read_text(encoding="utf-8").splitlines()
    diagnostics: list[str] = []

    for target in _TARGETS:
        start_line, end_line = _region(lines, target["start"], target["end"])
        assertion_lines = (
            _assertion_line(lines, start_line, end_line, target["calls"]),
            _assertion_line(lines, start_line, end_line, target["display_role"]),
        )
        if any(line is None for line in assertion_lines):
            diagnostics.append(
                f"PYPOST-1239/{target['label']}/MISSING_ASSERTION_PAIR: "
                "both repeated DisplayRole assertions are required"
            )
            continue

        if not all(
            _has_nearby_target_marker(lines, line, target["label"])
            for line in assertion_lines
            if line is not None
        ):
            diagnostics.append(
                f"PYPOST-1239/{target['label']}/MISSING_EXPLANATION: "
                "local rationale is required for both repeated DisplayRole assertions"
            )

    assert not diagnostics, "\n".join(diagnostics)


def _rationale_pattern(label: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?m)^[ \t]*# PYPOST-1239 {re.escape(label)}:.*\n"
        r"(?:^[ \t]*#.*\n)*"
    )


def _mutate_source(source: str, label: str, mutation: str) -> str:
    if mutation == "missing":
        return re.sub(
            rf"(?m)^[ \t]*# PYPOST-1239 {re.escape(label)}:.*\n"
            r"(?:^[ \t]*#.*\n)*",
            "",
            source,
        )
    if mutation == "detached":
        blocks = list(_rationale_pattern(label).finditer(source))
        assert blocks, f"missing rationale blocks for {label}"
        remaining = source
        for block in reversed(blocks):
            remaining = remaining[: block.start()] + remaining[block.end() :]
        return f"{remaining}\n{''.join(block.group(0) for block in blocks)}"
    if mutation == "wrong-target":
        other = "find_tree" if label != "find_tree" else "find_child"
        return source.replace(f"PYPOST-1239 {label}", f"PYPOST-1239 {other}")
    if mutation == "missing-intentionality":
        return _rationale_pattern(label).sub(
            lambda match: match.group(0).replace(
                "assertions are intentionally repeated", "assertions are repeated"
            ),
            source,
        )
    if mutation == "incomplete-rationale":
        return _rationale_pattern(label).sub(
            lambda match: match.group(0).replace(
                "regression protection", "ownership protection"
            ),
            source,
        )
    raise AssertionError(f"unknown mutation: {mutation}")


@pytest.mark.parametrize("label", ("find_child", "find_tree", "_select_item_view"))
@pytest.mark.parametrize(
    "mutation",
    (
        "missing",
        "detached",
        "wrong-target",
        "missing-intentionality",
        "incomplete-rationale",
    ),
)
def test_validator_reports_targeted_rationale_failures(label: str, mutation: str) -> None:
    source = _OWNERSHIP_SOURCE.read_text(encoding="utf-8")
    result = ownership_suite.validate_display_role_discoverability(
        _mutate_source(source, label, mutation)
    )

    expected_code = {
        "missing": "MISSING_EXPLANATION",
        "detached": "DETACHED_EXPLANATION",
        "wrong-target": "WRONG_TARGET_EXPLANATION",
        "missing-intentionality": "MISSING_INTENTIONALITY",
        "incomplete-rationale": "INCOMPLETE_RATIONALE",
    }[mutation]
    assert not result.valid
    assert [diagnostic.target for diagnostic in result.diagnostics] == [label]
    diagnostic = result.diagnostics[0]
    assert diagnostic.code == expected_code
    assert diagnostic.message.startswith(f"PYPOST-1239/{label}/{expected_code}:")


def test_validator_accepts_compliant_real_source() -> None:
    source = _OWNERSHIP_SOURCE.read_text(encoding="utf-8")
    result = ownership_suite.validate_display_role_discoverability(source)

    assert result.valid
    assert result.checked_targets == ("find_child", "find_tree", "_select_item_view")
    assert result.diagnostics == ()


def test_validator_aggregates_missing_rationales_in_target_order() -> None:
    source = _OWNERSHIP_SOURCE.read_text(encoding="utf-8")
    mutated = source
    for label in ("find_child", "find_tree", "_select_item_view"):
        mutated = _mutate_source(mutated, label, "missing")

    first = ownership_suite.validate_display_role_discoverability(mutated)
    second = ownership_suite.validate_display_role_discoverability(mutated)
    expected = [
        ("find_child", "MISSING_EXPLANATION"),
        ("find_tree", "MISSING_EXPLANATION"),
        ("_select_item_view", "MISSING_EXPLANATION"),
    ]

    assert not first.valid
    assert [
        (diagnostic.target, diagnostic.code) for diagnostic in first.diagnostics
    ] == expected
    assert first.diagnostics == second.diagnostics


def test_validator_ignores_marker_text_in_string_literals() -> None:
    source = _mutate_source(
        _OWNERSHIP_SOURCE.read_text(encoding="utf-8"), "find_child", "missing"
    )
    literal = (
        '    marker_text = "PYPOST-1239 find_child: These assertions are intentionally '
        'repeated because this helper delegates to display_role_equals and has no inline '
        'DisplayRole ownership. Combining or simplifying them risks weakening ownership '
        'regression protection."\n'
    )
    source = source.replace(
        "    assert _calls_name(find_child, \"display_role_equals\"),",
        literal + "    assert _calls_name(find_child, \"display_role_equals\"),",
    )

    result = ownership_suite.validate_display_role_discoverability(source)

    assert [(diagnostic.target, diagnostic.code) for diagnostic in result.diagnostics] == [
        ("find_child", "MISSING_EXPLANATION")
    ]


@pytest.mark.timeout(10)
def test_validator_rejects_fake_multiline_string_rationale() -> None:
    source = _mutate_source(
        _OWNERSHIP_SOURCE.read_text(encoding="utf-8"), "find_child", "missing"
    )
    fake_rationale = '''    fake_rationale = """
# PYPOST-1239 find_child: These assertions are intentionally repeated because this
# helper delegates to display_role_equals and has no inline DisplayRole ownership.
# Combining or simplifying them risks weakening ownership regression protection.
"""
'''
    source = source.replace(
        "    assert _calls_name(find_child, \"display_role_equals\"),",
        fake_rationale + "    assert _calls_name(find_child, \"display_role_equals\"),",
    )

    result = ownership_suite.validate_display_role_discoverability(source)

    assert not result.valid
    assert [(diagnostic.target, diagnostic.code) for diagnostic in result.diagnostics] == [
        ("find_child", "MISSING_EXPLANATION")
    ]
    assert result.diagnostics[0].message == (
        "PYPOST-1239/find_child/MISSING_EXPLANATION: "
        "local rationale is required for both repeated DisplayRole assertions"
    )
