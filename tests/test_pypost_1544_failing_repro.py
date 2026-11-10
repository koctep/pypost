"""Failing repro for PYPOST-1544 wildcard presence on the breadcrumb.

Mask results stay the same. ``matches`` reads breadcrumb wildcard
presence, and the redact and formatter walks push the breadcrumb.
"""

from __future__ import annotations

import inspect

import pytest

from pypost.core.json_selector_engine import JsonSelectorEngine
from pypost.ui.widgets.response_mask_controller import JsonMaskFormatter

pytestmark = pytest.mark.timeout(30)

_FULL_PATH_STAR_SCAN = 'any(str(t) == "*" for t in path)'


def test_matches_miss_path_does_not_scan_the_full_path_for_star() -> None:
    """Hierarchical miss must read breadcrumb presence, not rescan segments."""
    source = inspect.getsource(JsonSelectorEngine.matches)
    assert _FULL_PATH_STAR_SCAN not in source, (
        "matches still scans every path segment for '*'"
    )
    assert "has_wildcard" in source, "matches does not read has_wildcard"


def test_redact_node_pushes_the_breadcrumb() -> None:
    """Redaction descent must push segments so the wildcard count stays aligned."""
    source = inspect.getsource(JsonSelectorEngine._redact_node)
    assert "path.push(" in source, (
        "_redact_node still calls path.append instead of path.push"
    )


def test_format_dict_pushes_the_breadcrumb() -> None:
    """Object descent in the response viewer must push the field name."""
    source = inspect.getsource(JsonMaskFormatter._format_dict)
    assert "path.push(" in source, (
        "_format_dict still calls path.append instead of path.push"
    )


def test_format_list_pushes_the_breadcrumb() -> None:
    """List descent in the response viewer must push the star segment."""
    source = inspect.getsource(JsonMaskFormatter._format_list)
    assert "path.push(" in source, (
        "_format_list still calls path.append instead of path.push"
    )


def test_live_matches_keep_current_mask_decisions() -> None:
    """One-shot match booleans stay as they are before the breadcrumb flag."""
    bare = JsonSelectorEngine(["token"])
    assert bare.matches([], "token")
    assert bare.matches(["deep", "nest"], "token")
    assert not bare.matches([], "token_type")

    dotted = JsonSelectorEngine(["user.secret"])
    assert dotted.matches(["user"], "secret")
    assert not dotted.matches([], "secret")

    wildcard = JsonSelectorEngine(["items[*].secret"])
    assert wildcard.matches(["items", "*"], "secret")
    assert not wildcard.matches(["items"], "secret")

    shorthand = JsonSelectorEngine(["items.secret"])
    assert shorthand.matches(["items", "*"], "secret")
    assert not shorthand.matches(["other", "*"], "secret")

    header = JsonSelectorEngine(
        ["header:Authorization", "HEADER:Content-Type"]
    )
    assert header.is_empty
    assert not header.matches([], "Authorization")
    assert not header.matches([], "Content-Type")

    empty = JsonSelectorEngine([])
    assert empty.is_empty
    assert not empty.matches([], "secret")
    redacted, count = empty.redact_tree({"secret": "x"})
    assert count == 0
    assert redacted == {"secret": "x"}


def test_live_redact_keeps_masks_after_inner_list_pop() -> None:
    """Shorthand masks stay correct, including an outer star after an inner pop."""
    items = JsonSelectorEngine(["items.secret"])
    redacted_items, items_count = items.redact_tree(
        {"items": [{"secret": "x", "name": "n"}]}
    )
    assert items_count == 1
    assert redacted_items["items"][0]["secret"] == "***"
    assert redacted_items["items"][0]["name"] == "n"

    rows = JsonSelectorEngine(["rows.secret"])
    redacted_rows, rows_count = rows.redact_tree(
        {"rows": [{"cells": [1], "secret": "b"}]}
    )
    assert rows_count == 1
    assert redacted_rows["rows"][0]["secret"] == "***"
    assert redacted_rows["rows"][0]["cells"] == [1]

    wrap = JsonSelectorEngine(["wrap.secret"])
    redacted_wrap, wrap_count = wrap.redact_tree(
        {"wrap": {"*": {"secret": "z"}}}
    )
    assert wrap_count == 1
    assert redacted_wrap["wrap"]["*"]["secret"] == "***"
