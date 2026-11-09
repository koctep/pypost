"""Automated failing repro test suite for PYPOST-1394.

Validates the unified JSON selector path evaluation engine contracts and interfaces
designed in ai-tasks/PYPOST-1394/20-architecture.md.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

# Target import for planned unified engine in pypost.core.json_selector_engine
from pypost.core.json_selector_engine import (
    HIDDEN_PLACEHOLDER,
    CompiledPathSelector,
    JsonSelectorEngine,
)

pytestmark = pytest.mark.timeout(60)


def test_selector_normalization_and_filtering() -> None:
    """Verifies whitespace trimming, empty string filtering, and header selector exclusion."""
    raw_selectors = [
        " token ",
        "",
        "   ",
        "header:Authorization",
        "HEADER:Content-Type",
        "user.secret",
    ]
    engine = JsonSelectorEngine(raw_selectors)

    assert not engine.is_empty
    # Header selectors and blanks excluded; bare 'token' and path 'user.secret' retained
    assert engine.matches([], "token")
    assert engine.matches(["user"], "secret")
    assert not engine.matches([], "Authorization")
    assert not engine.matches([], "Content-Type")

    empty_engine = JsonSelectorEngine(["", "  ", "header:X-Api-Key"])
    assert empty_engine.is_empty
    assert not empty_engine.matches([], "key")


def test_compiled_path_selector_tokenization_and_matching() -> None:
    """Validates compile segments and the same cases on the live mask decision."""
    selector = CompiledPathSelector("items[*].secret")
    assert selector.tokens == ("items", "*", "secret")
    items = JsonSelectorEngine(["items[*].secret"])
    assert items.matches(["items", "*"], "secret")
    assert not items.matches(["items", "0"], "other")
    assert not items.matches(["items"], "secret")

    multi_wildcard = CompiledPathSelector("matrix[*][*].value")
    assert multi_wildcard.tokens == ("matrix", "*", "*", "value")
    matrix = JsonSelectorEngine(["matrix[*][*].value"])
    assert matrix.matches(["matrix", "*", "*"], "value")
    assert not matrix.matches(["matrix", "*"], "value")


def test_bare_key_matching_at_any_depth() -> None:
    """Verifies that bare keys match regardless of depth or container nesting."""
    engine = JsonSelectorEngine(["token", "password"])

    # Root level
    assert engine.matches([], "token")
    assert engine.matches([], "password")
    assert not engine.matches([], "username")
    assert not engine.matches([], "token_type")

    # Nested dictionaries
    assert engine.matches(["user", "profile"], "token")
    assert engine.matches(["auth", "deep", "nested"], "password")

    # Inside array items
    assert engine.matches(["items", "*"], "token")
    assert engine.matches(["data", "*", "attributes"], "password")


def test_hierarchical_dotted_path_matching() -> None:
    """Verifies that dotted paths match only exact ancestor hierarchies."""
    engine = JsonSelectorEngine(["user.credentials.apiKey"])

    # Exact hierarchical match
    assert engine.matches(["user", "credentials"], "apiKey")

    # Mismatches
    assert not engine.matches([], "apiKey")
    assert not engine.matches(["credentials"], "apiKey")
    assert not engine.matches(["admin", "credentials"], "apiKey")
    assert not engine.matches(["user", "other"], "apiKey")


def test_array_wildcard_matching() -> None:
    """Verifies wildcard expressions with bracket and dot notations."""
    engine = JsonSelectorEngine([
        "items[*].secret",
        "accounts.*.pin",
        "[*].root_id",
        "matrix[*][*].val",
    ])

    # Bracket wildcard
    assert engine.matches(["items", "*"], "secret")
    # Dot wildcard
    assert engine.matches(["accounts", "*"], "pin")
    # Root array wildcard
    assert engine.matches(["*"], "root_id")
    # Multi-dimensional wildcard
    assert engine.matches(["matrix", "*", "*"], "val")

    # Negative matches
    assert not engine.matches(["items"], "secret")
    assert not engine.matches(["other", "*"], "secret")
    assert not engine.matches(["matrix", "*"], "val")


def test_canonical_path_and_format_path_variants_helpers() -> None:
    """Verifies canonical path serialization and backward-compatible path variant helper."""
    assert (
        JsonSelectorEngine.canonical_path(["user", "profile"], "token")
        == "user.profile.token"
    )

    variants = JsonSelectorEngine.format_path_variants(["items", "*"], "secret")
    assert isinstance(variants, set)
    assert "secret" in variants
    assert "items.*.secret" in variants
    assert "items.secret" in variants
    assert "items[*].secret" in variants


def test_redact_tree_immutable_execution() -> None:
    """Verifies deep tree redaction without mutating the original input data structure."""
    engine = JsonSelectorEngine(["token", "user.secret", "items[*].key"])
    original_data: dict[str, Any] = {
        "status": "ok",
        "token": "sensitive_root_token",
        "user": {
            "name": "Alice",
            "secret": "hidden_nested_secret",
            "public_key": "safe_key",
        },
        "items": [
            {"id": 1, "key": "item1_secret", "label": "first"},
            {"id": 2, "key": "item2_secret", "label": "second"},
        ],
        "metadata": {
            "token": "sensitive_metadata_token",
        },
    }
    input_copy = copy.deepcopy(original_data)

    redacted, count = engine.redact_tree(original_data, placeholder=HIDDEN_PLACEHOLDER)

    # Input data must not be mutated
    assert original_data == input_copy

    # Redaction count: root token (1), user.secret (1), items[0].key (1),
    # items[1].key (1), metadata.token (1) = 5
    assert count == 5

    # Redacted values
    assert redacted["token"] == "***"
    assert redacted["user"]["secret"] == "***"
    assert redacted["items"][0]["key"] == "***"
    assert redacted["items"][1]["key"] == "***"
    assert redacted["metadata"]["token"] == "***"

    # Preserved values
    assert redacted["status"] == "ok"
    assert redacted["user"]["name"] == "Alice"
    assert redacted["user"]["public_key"] == "safe_key"
    assert redacted["items"][0]["label"] == "first"
    assert redacted["items"][1]["label"] == "second"


def test_redact_tree_edge_cases_and_resilience() -> None:
    """Verifies safe handling of empty containers, empty engines, and non-container primitives."""
    engine = JsonSelectorEngine(["token"])

    # Non-container primitives
    assert engine.redact_tree(42) == (42, 0)
    assert engine.redact_tree(3.14) == (3.14, 0)
    assert engine.redact_tree("plain string") == ("plain string", 0)
    assert engine.redact_tree(True) == (True, 0)
    assert engine.redact_tree(None) == (None, 0)

    # Empty containers
    assert engine.redact_tree({}) == ({}, 0)
    assert engine.redact_tree([]) == ([], 0)

    # Empty engine on valid dict
    empty_engine = JsonSelectorEngine([])
    sample = {"token": "secret", "user": {"token": "secret2"}}
    sample_copy = copy.deepcopy(sample)
    redacted_unmodified, count_zero = empty_engine.redact_tree(sample)
    assert count_zero == 0
    assert redacted_unmodified == sample_copy


def test_json_selector_engine_observability_and_zero_leak(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verifies structured logging emission and zero secret data leak."""
    import logging

    caplog.set_level(logging.DEBUG)
    engine = JsonSelectorEngine(["token", "items[*].secret", "header:Authorization"])

    assert any(
        "json_selector_engine_compiled" in record.message
        and "raw_count=2" in record.message
        and "bare_keys_count=1" in record.message
        and "path_selectors_count=1" in record.message
        and "trie_size=1" in record.message
        for record in caplog.records
    )

    caplog.clear()
    sample = {
        "token": "SUPER_SECRET_TOKEN_123",
        "items": [{"secret": "SUPER_SECRET_PIN_456"}],
    }
    redacted, count = engine.redact_tree(sample)
    assert count == 2

    assert any(
        "json_selector_engine_redact_tree_completed" in record.message
        and "masked_count=2" in record.message
        for record in caplog.records
    )

    # Zero sensitive data leakage check: secrets must NEVER appear in log records
    for record in caplog.records:
        assert "SUPER_SECRET_TOKEN_123" not in record.message
        assert "SUPER_SECRET_PIN_456" not in record.message
