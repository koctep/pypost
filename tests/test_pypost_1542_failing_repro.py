"""Automated failing repro for PYPOST-1542.

Asserts the unused selector match helpers are absent, and that the live
mask decision still returns the compiled-matcher outcomes.
"""

from __future__ import annotations

import pytest

from pypost.core.json_selector_engine import (
    CompiledPathSelector,
    JsonSelectorEngine,
    PathSelectorTrie,
)

pytestmark = pytest.mark.timeout(30)


def test_unused_match_helpers_are_absent() -> None:
    """The spare token walker and compiled matcher are not on the classes."""
    assert not hasattr(PathSelectorTrie, "matches_tokens")
    assert not hasattr(CompiledPathSelector, "matches")


def test_live_mask_decision_keeps_compiled_matcher_cases() -> None:
    """JsonSelectorEngine.matches keeps the five compiled-matcher outcomes."""
    items = JsonSelectorEngine(["items[*].secret"])
    assert items.matches(["items", "*"], "secret")
    assert not items.matches(["items", "0"], "other")
    assert not items.matches(["items"], "secret")

    matrix = JsonSelectorEngine(["matrix[*][*].value"])
    assert matrix.matches(["matrix", "*", "*"], "value")
    assert not matrix.matches(["matrix", "*"], "value")
