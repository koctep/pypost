"""Domain contract for environment variable keys."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping

MSG_EMPTY = "Variable name cannot be empty."
MSG_STARTS_WITH_DIGIT = "Variable name cannot start with a digit."
MSG_INVALID_CHARS = (
    "Variable name can only contain letters, numbers, and underscores."
)


class EnvironmentVariableKeyFailure(str, Enum):
    """Stable, machine-readable reasons for rejecting a variable key."""

    EMPTY = "empty"
    INVALID_SYNTAX = "invalid_syntax"
    DUPLICATE = "duplicate"


@dataclass(frozen=True)
class EnvironmentVariableKeyValidation:
    normalized_name: str
    failure: EnvironmentVariableKeyFailure | None = None
    message: str = ""

    @property
    def accepted(self) -> bool:
        return self.failure is None


class EnvironmentVariableValidationError(ValueError):
    """Raised when environment variables violate the key contract."""

    def __init__(self, validation: EnvironmentVariableKeyValidation) -> None:
        super().__init__(validation.message)
        self.validation = validation


def validate_variable_syntax(name: str) -> tuple[bool, str]:
    if not name:
        return False, MSG_EMPTY
    if name[0].isdigit():
        return False, MSG_STARTS_WITH_DIGIT
    if not all(character.isalnum() or character == "_" for character in name):
        return False, MSG_INVALID_CHARS
    return True, ""


def validate_environment_variable_key(
    name: str,
    *,
    other_names: Iterable[str] = (),
) -> EnvironmentVariableKeyValidation:
    """Normalize and validate one key against the other keys in its environment."""
    normalized = name.strip()
    is_valid, message = validate_variable_syntax(normalized)
    if not is_valid:
        failure = (
            EnvironmentVariableKeyFailure.EMPTY
            if not normalized
            else EnvironmentVariableKeyFailure.INVALID_SYNTAX
        )
        return EnvironmentVariableKeyValidation(normalized, failure, message)

    normalized_others = {other.strip() for other in other_names}
    if normalized in normalized_others:
        return EnvironmentVariableKeyValidation(
            normalized,
            EnvironmentVariableKeyFailure.DUPLICATE,
            f'Variable "{normalized}" already exists.',
        )
    return EnvironmentVariableKeyValidation(normalized)


def validate_environment_variable_keys(
    variables: Mapping[Any, Any],
) -> dict[str, object]:
    """Validate and normalize mapping keys while preserving opaque values."""
    normalized: dict[str, object] = {}
    for raw_name, raw_value in variables.items():
        validation = validate_environment_variable_key(
            str(raw_name),
            other_names=normalized,
        )
        if not validation.accepted:
            raise EnvironmentVariableValidationError(validation)
        normalized[validation.normalized_name] = raw_value
    return normalized


def normalize_environment_variables(
    variables: Mapping[Any, Any],
) -> dict[str, str]:
    """Validate a complete mapping and return its normalized string form."""
    return {
        key: str(value)
        for key, value in validate_environment_variable_keys(variables).items()
    }
