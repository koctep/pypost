"""Repro for PYPOST-1539 — reject a broken double-dot field selector.

Current contract: ``users..email`` is rejected and ``users[*].email`` stays ok.
"""

from __future__ import annotations

import pytest

from pypost.core.field_selector_syntax import validate_field_selector

pytestmark = pytest.mark.timeout(30)


def test_double_dot_selector_is_rejected_and_wildcard_stays_ok() -> None:
    """A written ``..`` is not acceptable; a bracket wildcard path remains ok."""
    broken = validate_field_selector("users..email")
    assert broken.ok is False, (
        "users..email must not be accepted; collapse rewrites it to users.email"
    )

    wildcard = validate_field_selector("users[*].email")
    assert wildcard.ok is True
