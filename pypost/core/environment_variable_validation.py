"""Application operations built on the environment variable domain contract."""
from __future__ import annotations

from typing import Any, Mapping, Protocol

from pypost.models.environment_variable import (
    EnvironmentVariableKeyFailure,
    EnvironmentVariableKeyValidation,
    EnvironmentVariableValidationError,
    normalize_environment_variables,
    validate_environment_variable_key,
    validate_environment_variable_keys,
)

__all__ = [
    "EnvironmentVariableKeyFailure",
    "EnvironmentVariableKeyValidation",
    "EnvironmentVariableValidationError",
    "apply_environment_variable_updates",
    "normalize_environment_variables",
    "validate_environment_variable_key",
    "validate_environment_variable_keys",
]


class EnvironmentVariablesTarget(Protocol):
    variables: dict[str, str]
    hidden_keys: set[str]


def apply_environment_variable_updates(
    environment: EnvironmentVariablesTarget,
    updates: Mapping[Any, Any],
) -> None:
    """Validate a batch first, then merge it into an environment atomically."""
    candidate = dict(environment.variables)
    update_names: set[str] = set()
    for raw_name, raw_value in updates.items():
        name = str(raw_name)
        normalized = name.strip()
        if normalized in update_names:
            validation = validate_environment_variable_key(
                name,
                other_names=update_names,
            )
            raise EnvironmentVariableValidationError(validation)
        other_names = [key for key in candidate if key != normalized]
        validation = validate_environment_variable_key(
            name,
            other_names=other_names,
        )
        if not validation.accepted:
            raise EnvironmentVariableValidationError(validation)
        update_names.add(validation.normalized_name)
        candidate[validation.normalized_name] = str(raw_value)

    # Validate the complete result before changing the caller-owned model.
    environment.variables = normalize_environment_variables(candidate)
    environment.hidden_keys.intersection_update(environment.variables)
