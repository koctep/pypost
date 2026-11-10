"""Automated failing repro for PYPOST-1543.

Asserts the stored compiled-rule list is absent and compile DEBUG reports
trie size without a list-length field. Live mask decisions stay on the
current rules.
"""

from __future__ import annotations

import logging

import pytest

from pypost.core.json_selector_engine import JsonSelectorEngine

pytestmark = pytest.mark.timeout(30)

_ENGINE_LOGGER = "pypost.core.json_selector_engine"


def test_engine_has_no_path_selectors_attribute() -> None:
    """Hierarchical compile must not keep a second copy of the rules."""
    engine = JsonSelectorEngine(["items[*].secret"])
    assert not hasattr(engine, "_path_selectors")


def test_compile_debug_reports_trie_size_without_list_length(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Shared terminals log trie_size only, not the raw list length."""
    with caplog.at_level(logging.DEBUG, logger=_ENGINE_LOGGER):
        JsonSelectorEngine(["items[*].secret", "items.*.secret"])

    compiled = [
        record.message
        for record in caplog.records
        if record.name == _ENGINE_LOGGER
        and "json_selector_engine_compiled" in record.message
    ]
    assert len(compiled) == 1
    message = compiled[0]
    assert "trie_size=1" in message
    assert "path_selectors_count=" not in message


def test_live_mask_matches_stay_on_current_rules() -> None:
    """Bare, dotted, wildcard, shorthand, header, and empty masks."""
    bare = JsonSelectorEngine(["token"])
    assert bare.matches([], "token")

    dotted = JsonSelectorEngine(["user.secret"])
    assert dotted.matches(["user"], "secret")

    wildcard = JsonSelectorEngine(["items[*].secret"])
    assert wildcard.matches(["items", "*"], "secret")

    shorthand = JsonSelectorEngine(["items.secret"])
    assert shorthand.matches(["items", "*"], "secret")

    header = JsonSelectorEngine(["token", "header:Authorization"])
    assert not header.matches([], "Authorization")

    empty = JsonSelectorEngine([])
    assert empty.is_empty
    assert not empty.matches([], "token")
