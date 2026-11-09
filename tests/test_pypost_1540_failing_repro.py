"""Repro for PYPOST-1540 — name the unsupported field-selector kind.

A JSONPath dollar, a numeric index, and a filter each need their own
explanation. Today all three share the generic unsupported warning.
"""

from __future__ import annotations

import pytest

from pypost.core.field_selector_syntax import validate_field_selector

pytestmark = pytest.mark.timeout(30)

_GENERIC_UNSUPPORTED = (
    "Unsupported or invalid field selector syntax. "
    "This expression is not accepted by response masking."
)

_DOLLAR_MESSAGE = (
    "This field selector uses a JSONPath dollar. "
    "A dollar sign is not a supported field name."
)
_INDEX_MESSAGE = (
    "This field selector uses a numeric index. "
    "A number in brackets is not a supported field name."
)
_FILTER_MESSAGE = (
    "This field selector uses a filter. "
    "A condition in brackets is not a supported field name."
)


def test_unsupported_kinds_explain_themselves() -> None:
    """Dollar, index, and filter drafts name their kind; a plain key stays quiet."""
    dollar = validate_field_selector("$.token")
    index = validate_field_selector("users[0].email")
    filtered = validate_field_selector("users[?(@.active)].email")

    assert dollar.ok is False
    assert index.ok is False
    assert filtered.ok is False

    messages = (dollar.message, index.message, filtered.message)
    assert len(set(messages)) == 3 and _GENERIC_UNSUPPORTED not in messages, (
        "the three invalid messages are the same generic warning: "
        f"{messages!r}"
    )
    assert messages == (_DOLLAR_MESSAGE, _INDEX_MESSAGE, _FILTER_MESSAGE)

    plain = validate_field_selector("token")
    assert plain.ok is True
    assert plain.message == ""
