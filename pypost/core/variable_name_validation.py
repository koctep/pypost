"""Jinja2-compatible environment variable name validation."""
from __future__ import annotations

from typing import Literal

from pypost.models.environment_variable import (
    MSG_EMPTY as MSG_EMPTY,
    MSG_INVALID_CHARS as MSG_INVALID_CHARS,
    MSG_STARTS_WITH_DIGIT as MSG_STARTS_WITH_DIGIT,
    validate_variable_syntax,
)

ValidationFailureReason = Literal["empty", "starts_with_digit", "invalid_chars"]

__all__ = [
    "MSG_EMPTY",
    "MSG_INVALID_CHARS",
    "MSG_STARTS_WITH_DIGIT",
    "ValidationFailureReason",
    "validate_variable_name",
    "validation_failure_reason",
]


def validate_variable_name(name: str) -> tuple[bool, str]:
    """Validate a variable name for Jinja2 template compatibility.

    Rules:
    - Cannot be empty
    - Cannot start with a digit
    - Can only contain alphanumeric characters and underscore

    Returns:
        Tuple of (is_valid, error_message). error_message is empty when valid.
    """
    return validate_variable_syntax(name)


def validation_failure_reason(name: str) -> ValidationFailureReason | None:
    """Return the failure reason for an invalid name, or None when valid."""
    is_valid, _ = validate_variable_name(name)
    if is_valid:
        return None
    if not name:
        return "empty"
    if name[0].isdigit():
        return "starts_with_digit"
    return "invalid_chars"
