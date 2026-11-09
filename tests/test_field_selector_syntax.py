"""Unit suite for PYPOST-1387 field selector syntax validation.

Asserts the ``validate_field_selector`` contract from
``ai-tasks/PYPOST-1387/20-architecture.md``.
"""

from __future__ import annotations

import pytest

from pypost.core.field_selector_syntax import (
    FieldSelectorSyntaxResult,
    validate_field_selector,
)

pytestmark = pytest.mark.timeout(10)

# Supported example families that invalid guidance must mention at least one of.
_SUPPORTED_EXAMPLE_SNIPPETS = (
    "token",
    "auth.token",
    "users[*].email",
    "header:Authorization",
    "simple key",
    "dot",
    "wildcard",
    "header",
)


def _assert_ok(result: FieldSelectorSyntaxResult, *, is_empty: bool = False) -> None:
    assert isinstance(result, FieldSelectorSyntaxResult)
    assert result.ok is True
    assert result.is_empty is is_empty
    assert result.message == ""


def _assert_invalid(result: FieldSelectorSyntaxResult) -> None:
    assert isinstance(result, FieldSelectorSyntaxResult)
    assert result.ok is False
    assert result.is_empty is False
    assert result.message.strip(), "invalid selectors must include a plain-language reason"
    guidance = f"{result.message} {result.suggestions}".lower()
    assert any(snippet.lower() in guidance for snippet in _SUPPORTED_EXAMPLE_SNIPPETS), (
        "invalid guidance must include at least one supported-form example; "
        f"got message={result.message!r} suggestions={result.suggestions!r}"
    )


@pytest.mark.parametrize(
    "selector",
    [
        "token",
        "api_key",
        "auth.token",
        "users.email",
        "users[*].email",
        "[*].id",
        "header:Authorization",
    ],
)
def test_validate_field_selector_accepts_supported_forms(selector: str) -> None:
    """Supported simple key, path, wildcard, and header forms must validate as ok."""
    _assert_ok(validate_field_selector(selector), is_empty=False)


@pytest.mark.parametrize(
    "selector",
    [
        "$.users[0].name",
        "users[0].name",
        "[?(@.x)]",
        "header:",
        "header:   ",
    ],
)
def test_validate_field_selector_rejects_unsupported_forms(selector: str) -> None:
    """JSONPath / numeric index / filter / empty header forms must be invalid with guidance."""
    _assert_invalid(validate_field_selector(selector))


@pytest.mark.parametrize("selector", ["", "   ", "\t"])
def test_validate_field_selector_empty_or_whitespace_is_ok(selector: str) -> None:
    """Empty and whitespace-only input is empty/ok with no error messaging."""
    _assert_ok(validate_field_selector(selector), is_empty=True)
    result = validate_field_selector(selector)
    assert result.suggestions == ""
