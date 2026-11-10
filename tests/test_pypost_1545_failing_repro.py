"""Isolated catalog for the hierarchical path index (PYPOST-1545)."""

from __future__ import annotations

import pytest

from pypost.core.json_selector_engine import (
    CompiledPathSelector,
    JsonSelectorEngine,
    PathSelectorTrie,
)

pytestmark = pytest.mark.timeout(30)

_MISS = (
    ([], "secret"),
    (["items"], "secret"),
    (["items", "*"], "secret"),
    (["other"], "secret"),
)

_SHORTHAND = (
    (["items", "*"], "secret", False, True, True),
    (["other"], "secret", False, False, False),
    (["items"], "secret", True, True, True),
)

_AGREE = (
    (["user"], "apiKey", True),
    (["user"], "name", False),
)

_BARE = (
    (["other"], "secret", True),
    (["items", "*"], "secret", True),
    (["other"], "name", False),
)

_HEAVY = ("*.*.secret", "*.*.*.pin", "items.*.*.token", "*.id")

_HEAVY_ROWS = (
    (["orders", "*"], "secret", True),
    (["items", "*", "*"], "token", True),
    (["a", "b"], "secret", True),
    (["x"], "id", True),
    (["other"], "name", False),
    (["items", "*"], "token", False),
    (["items"], "secret", False),
)


def _index(*selectors: str) -> PathSelectorTrie:
    trie = PathSelectorTrie()
    for raw in selectors:
        trie.insert(CompiledPathSelector(raw).tokens)
    return trie


def test_insert_counts_distinct_complete_paths() -> None:
    trie = PathSelectorTrie()
    assert trie.size == 0
    assert trie.is_empty
    tokens = CompiledPathSelector("items.secret").tokens
    trie.insert(tokens)
    trie.insert(tokens)
    assert trie.size == 1
    trie.insert(CompiledPathSelector("items.other").tokens)
    assert trie.size == 2


@pytest.mark.parametrize(("path", "key"), _MISS)
def test_empty_index_and_empty_selector_set(path: list[str], key: str) -> None:
    trie = PathSelectorTrie()
    engine = JsonSelectorEngine([])
    assert trie.is_empty
    assert engine.is_empty
    assert not trie.matches_path_and_key(path, key)
    assert not trie.matches_shorthand_path_and_key(path, key)
    assert not engine.matches(path, key)


@pytest.mark.parametrize(
    ("path", "key", "direct", "shorthand", "public"), _SHORTHAND,
)
def test_shorthand_only_under_items_secret(
    path: list[str], key: str, direct: bool, shorthand: bool, public: bool,
) -> None:
    trie = _index("items.secret")
    engine = JsonSelectorEngine(["items.secret"])
    assert trie.matches_path_and_key(path, key) is direct
    assert trie.matches_shorthand_path_and_key(path, key) is shorthand
    assert engine.matches(path, key) is public


def test_items_star_secret_is_a_direct_hit() -> None:
    path = ["items", "*"]
    assert _index("items.*.secret").matches_path_and_key(path, "secret")
    assert JsonSelectorEngine(["items.*.secret"]).matches(path, "secret")


@pytest.mark.parametrize(("path", "key", "hidden"), _AGREE)
def test_path_and_key_agrees_with_public_check(
    path: list[str], key: str, hidden: bool,
) -> None:
    direct = _index("user.apiKey").matches_path_and_key(path, key)
    assert direct is hidden
    assert JsonSelectorEngine(["user.apiKey"]).matches(path, key) is direct


@pytest.mark.parametrize(("path", "key", "hidden"), _BARE)
def test_bare_name_hides_fields_apart_from_the_trie(
    path: list[str], key: str, hidden: bool,
) -> None:
    engine = JsonSelectorEngine(["secret"])
    assert not engine.is_empty
    assert engine.matches(path, key) is hidden


@pytest.mark.parametrize(("path", "key", "hidden"), _HEAVY_ROWS)
def test_wildcard_heavy_public_check_matches_direct_walk(
    path: list[str], key: str, hidden: bool,
) -> None:
    public = JsonSelectorEngine(_HEAVY).matches(path, key)
    assert public is hidden
    assert _index(*_HEAVY).matches_path_and_key(path, key) is public


def test_removed_match_helpers_stay_absent() -> None:
    assert not hasattr(PathSelectorTrie, "matches_tokens")
    assert not hasattr(CompiledPathSelector, "matches")
