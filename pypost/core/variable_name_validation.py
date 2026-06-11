"""Jinja2-compatible environment variable name validation."""

from typing import Literal

ValidationFailureReason = Literal["empty", "starts_with_digit", "invalid_chars"]


def validate_variable_name(name: str) -> tuple[bool, str]:
    """Validate a variable name for Jinja2 template compatibility.

    Rules:
    - Cannot be empty
    - Cannot start with a digit
    - Can only contain alphanumeric characters and underscore

    Returns:
        Tuple of (is_valid, error_message). error_message is empty when valid.
    """
    if not name:
        return False, "Variable name cannot be empty."

    if name[0].isdigit():
        return False, "Variable name cannot start with a digit."

    if not all(c.isalnum() or c == "_" for c in name):
        return (
            False,
            "Variable name can only contain letters, numbers, and underscores.",
        )

    return True, ""


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
