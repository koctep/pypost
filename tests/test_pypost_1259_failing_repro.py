"""Verification test for PYPOST-1259 demonstrating AST parser resilience.

Validates that structural markdown parsing helpers in
tests/test_pypost_1077_verification_artifacts.py resolve the fragility modes:
1. _parse_markdown_sections and _section succeed when headings are rearranged.
2. _parse_markdown_table parses rows accurately despite alignment padding.
3. _normalize_prose validates semantic claims across reflowed multi-line text.
"""

from __future__ import annotations

import pytest

from tests.test_pypost_1077_verification_artifacts import (
    _normalize_prose,
    _parse_markdown_sections,
    _parse_markdown_table,
    _section,
)


pytestmark = pytest.mark.timeout(30)


@pytest.mark.timeout(30)
def test_section_slicing_fragility_on_rearranged_headings() -> None:
    """Test 1: _parse_markdown_sections and _section succeed on rearranged headings."""
    markdown_with_rearranged_headings = (
        "# Architectural Report\n\n"
        "## SOLID Assessment by Dialog\n"
        "Content of SOLID assessment.\n\n"
        "## Module Inventory\n"
        "| Module | LOC |\n"
        "| :--- | ---: |\n"
        "| `dialog_one.py` | 100 |\n\n"
        "## Verdict\n"
        "All checks passed.\n"
    )
    # Structural parsing by title independently of heading order
    sections = _parse_markdown_sections(markdown_with_rearranged_headings)
    assert "module inventory" in sections
    assert "`dialog_one.py`" in sections["module inventory"].content

    # Backward-compatible _section helper also resolves rearranged headings
    extracted_section = _section(
        markdown_with_rearranged_headings,
        "## Module Inventory",
        "## SOLID Assessment by Dialog",
    )
    assert "`dialog_one.py`" in extracted_section


@pytest.mark.timeout(30)
def test_table_regex_fragility_on_alignment_spacing() -> None:
    """Test 2: _parse_markdown_table succeeds with extra alignment spacing."""
    table_text = (
        "| Module | LOC |\n"
        "| :--- | ---: |\n"
        "|  `module.py`  |  123  |\n"
    )
    inventory_rows = _parse_markdown_table(table_text)
    assert len(inventory_rows) == 1
    assert inventory_rows[0]["module"] == "module.py"
    assert inventory_rows[0]["loc"] == "123"


@pytest.mark.timeout(30)
def test_prose_assertion_fragility_on_reflowed_text() -> None:
    """Test 3: _normalize_prose validates semantic claims on reflowed prose."""
    reflowed_report = (
        "## Executive Summary\n\n"
        "The activity and tools dialogs are read-only, whereas the "
        "server manager supports configuration and lifecycle changes.\n"
    )
    normalized = _normalize_prose(reflowed_report)
    assert "The activity and tools dialogs are read-only" in normalized
    assert "server manager supports configuration and lifecycle changes" in normalized
