"""Regression suite for PYPOST-1388 (efficient selector evaluation).

Semantic-lock tests pin match / redact / format outcomes. Efficiency tests lock
FR-2 / FR-3 bounds: hierarchical lookup must stay depth-bounded (not linear over
``_path_selectors``), and redact/format descent must reuse one path breadcrumb list.
"""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest

from pypost.core.json_selector_engine import (
    HIDDEN_PLACEHOLDER,
    JsonSelectorEngine,
)
from pypost.ui.widgets.response_mask_controller import format_masked_json

pytestmark = pytest.mark.timeout(30)

# ---------------------------------------------------------------------------
# Semantic lock (match / redact / format parity)
# ---------------------------------------------------------------------------


def test_semantic_lock_bare_keys_dotted_paths_and_wildcards() -> None:
    """FR-4: bare keys, dotted paths, bracket/dot wildcards, nested wildcards."""
    engine = JsonSelectorEngine(
        [
            "token",
            "user.credentials.apiKey",
            "items[*].secret",
            "accounts.*.pin",
            "matrix[*][*].val",
        ]
    )

    assert engine.matches([], "token")
    assert engine.matches(["deep", "nest"], "token")
    assert not engine.matches([], "token_type")

    assert engine.matches(["user", "credentials"], "apiKey")
    assert not engine.matches([], "apiKey")
    assert not engine.matches(["admin", "credentials"], "apiKey")

    assert engine.matches(["items", "*"], "secret")
    assert engine.matches(["accounts", "*"], "pin")
    assert engine.matches(["matrix", "*", "*"], "val")
    assert not engine.matches(["items"], "secret")
    assert not engine.matches(["matrix", "*"], "val")


def test_semantic_lock_shorthand_fallback_and_header_ignore() -> None:
    """FR-4: shorthand ``items.secret`` vs array path; ``header:`` body-ignored."""
    engine = JsonSelectorEngine(
        [
            "items.secret",
            "header:Authorization",
            "HEADER:Content-Type",
            "",
            "   ",
        ]
    )

    assert engine.matches(["items", "*"], "secret")
    assert engine.matches(["items"], "secret")
    assert not engine.matches([], "Authorization")
    assert not engine.matches([], "Content-Type")
    assert not engine.is_empty

    emptyish = JsonSelectorEngine(["", "  ", "header:X-Api-Key"])
    assert emptyish.is_empty


def test_semantic_lock_redact_tree_and_format_masked_json_parity() -> None:
    """FR-4 / FR-5: redact_tree + format_masked_json agree; input not mutated."""
    selectors = ["token", "user.secret", "items[*].key"]
    payload: dict[str, Any] = {
        "status": "ok",
        "token": "sensitive_root",
        "user": {"name": "Alice", "secret": "nested_secret"},
        "items": [
            {"id": 1, "key": "item1", "label": "first"},
            {"id": 2, "key": "item2", "label": "second"},
        ],
    }
    original = copy.deepcopy(payload)

    engine = JsonSelectorEngine(selectors)
    redacted, count = engine.redact_tree(payload, placeholder=HIDDEN_PLACEHOLDER)

    assert payload == original
    assert count == 4
    assert redacted["token"] == HIDDEN_PLACEHOLDER
    assert redacted["user"]["secret"] == HIDDEN_PLACEHOLDER
    assert redacted["items"][0]["key"] == HIDDEN_PLACEHOLDER
    assert redacted["items"][1]["key"] == HIDDEN_PLACEHOLDER
    assert redacted["status"] == "ok"
    assert redacted["user"]["name"] == "Alice"
    assert redacted["items"][0]["label"] == "first"

    text, spans = format_masked_json(json.dumps(original), selectors)
    assert payload == original
    assert '"***"' in text
    paths = {span.path for span in spans}
    assert "token" in paths
    assert "user.secret" in paths
    assert "items.*.key" in paths
    assert len(spans) == 4


def test_semantic_lock_empty_engine_short_circuit() -> None:
    """FR-6: empty / header-only engines skip body work."""
    engine = JsonSelectorEngine([])
    sample = {"token": "x", "nested": {"token": "y"}}
    redacted, count = engine.redact_tree(sample)
    assert count == 0
    assert redacted == sample
    assert engine.is_empty
    assert not engine.matches([], "token")


# ---------------------------------------------------------------------------
# Efficiency locks (depth-bounded lookup + reusable path breadcrumbs)
# ---------------------------------------------------------------------------


class _CountingPathSelectors:
    """Sequence wrapper that counts every rule yield during linear scans."""

    def __init__(self, rules: list[Any]) -> None:
        self._rules = list(rules)
        self.item_reads = 0

    def __iter__(self):
        for rule in self._rules:
            self.item_reads += 1
            yield rule

    def __bool__(self) -> bool:
        return bool(self._rules)

    def __len__(self) -> int:
        return len(self._rules)

    def __getitem__(self, index: int) -> Any:
        return self._rules[index]


def test_hierarchical_lookup_scaling_bounded_by_depth_not_rule_count() -> None:
    """FR-2: hierarchical match must not scan all R path rules per visited key.

    Segment-trie evaluation must stay near O(depth) per key; wrapping
    ``_path_selectors`` detects any regression to a linear rule scan.
    """
    rule_count = 400
    selectors = [f"catalog{i}.branch{i}.leaf{i}" for i in range(rule_count)]
    engine = JsonSelectorEngine(selectors)
    counter = _CountingPathSelectors(engine._path_selectors)
    engine._path_selectors = counter  # type: ignore[assignment]

    # Medium body: many keys that miss the catalog (forces hierarchical probes).
    body: dict[str, Any] = {
        f"obj{i}": {f"field{j}": f"value-{i}-{j}" for j in range(8)}
        for i in range(25)
    }
    match_calls = 0
    max_depth = 0
    original_matches = engine.matches

    def counting_matches(path: Any, key: str) -> bool:
        nonlocal match_calls, max_depth
        match_calls += 1
        max_depth = max(max_depth, len(path) + 1)
        return original_matches(path, key)

    engine.matches = counting_matches  # type: ignore[method-assign]

    engine.redact_tree(body)

    assert match_calls > 0
    # Trie / depth-bounded budget with modest wildcard slack — not O(R × visits).
    budget = match_calls * max(max_depth, 1) * 4
    assert counter.item_reads <= budget, (
        f"hierarchical rule examinations={counter.item_reads} exceed depth-bounded "
        f"budget={budget} (match_calls={match_calls}, max_depth={max_depth}, "
        f"R={rule_count}); linear _path_selectors scan still in use"
    )


def test_redact_tree_reuses_single_path_breadcrumb_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-3: ``redact_tree`` descent must reuse one mutable path list (push/pop).

    Every recursive depth must share one path list identity (no ``path + [seg]``).
    """
    engine = JsonSelectorEngine(["a.b.c.d.secret"])
    path_ids: set[int] = set()
    original = JsonSelectorEngine._redact_node

    def spy(
        self: JsonSelectorEngine,
        node: Any,
        path: list[str],
        placeholder: str,
        masked_count: list[int],
    ) -> Any:
        path_ids.add(id(path))
        return original(self, node, path, placeholder, masked_count)

    monkeypatch.setattr(JsonSelectorEngine, "_redact_node", spy)

    nested: dict[str, Any] = {
        "a": {"b": {"c": {"d": {"secret": "hidden", "keep": 1}}}},
        "sibling": {"x": 2},
    }
    redacted, count = engine.redact_tree(nested)

    assert count == 1
    assert redacted["a"]["b"]["c"]["d"]["secret"] == HIDDEN_PLACEHOLDER
    assert redacted["a"]["b"]["c"]["d"]["keep"] == 1
    assert len(path_ids) == 1, (
        f"expected a single reusable path breadcrumb list across depths, "
        f"found {len(path_ids)} distinct list identities (path + [seg] still used)"
    )


def test_json_mask_formatter_reuses_single_path_breadcrumb_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-3 / FR-5: GUI formatter descent must also reuse one path breadcrumb list."""
    from pypost.ui.widgets.response_mask_controller import JsonMaskFormatter

    formatter = JsonMaskFormatter(["a.b.c.leaf"])
    path_ids: set[int] = set()
    original_value = JsonMaskFormatter._format_value
    original_dict = JsonMaskFormatter._format_dict
    original_list = JsonMaskFormatter._format_list

    def spy_value(
        self: JsonMaskFormatter, node: Any, path: list[str], depth: int
    ) -> None:
        path_ids.add(id(path))
        return original_value(self, node, path, depth)

    def spy_dict(
        self: JsonMaskFormatter, node: dict[str, Any], path: list[str], depth: int
    ) -> None:
        path_ids.add(id(path))
        return original_dict(self, node, path, depth)

    def spy_list(
        self: JsonMaskFormatter, node: list[Any], path: list[str], depth: int
    ) -> None:
        path_ids.add(id(path))
        return original_list(self, node, path, depth)

    monkeypatch.setattr(JsonMaskFormatter, "_format_value", spy_value)
    monkeypatch.setattr(JsonMaskFormatter, "_format_dict", spy_dict)
    monkeypatch.setattr(JsonMaskFormatter, "_format_list", spy_list)

    payload = {"a": {"b": {"c": {"leaf": "secret", "ok": True}}}, "other": [1, 2]}
    text, spans = formatter.format(payload)

    assert '"***"' in text
    assert any(span.path == "a.b.c.leaf" for span in spans)
    assert len(path_ids) == 1, (
        f"expected a single reusable formatter path breadcrumb, "
        f"found {len(path_ids)} distinct list identities (path + [seg] still used)"
    )
