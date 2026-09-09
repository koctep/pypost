"""Domain contract tests for environment variable keys and updates."""

import pytest
from pydantic import ValidationError

from pypost.core.environment_variable_validation import (
    EnvironmentVariableKeyFailure,
    EnvironmentVariableValidationError,
    apply_environment_variable_updates,
    validate_environment_variable_key,
)
from pypost.models.models import Environment

pytestmark = pytest.mark.timeout(60)


@pytest.mark.parametrize(
    ("name", "others", "reason"),
    [
        ("   ", (), EnvironmentVariableKeyFailure.EMPTY),
        ("bad-key", (), EnvironmentVariableKeyFailure.INVALID_SYNTAX),
        (" A ", ("A",), EnvironmentVariableKeyFailure.DUPLICATE),
    ],
)
def test_validator_returns_typed_failure(name, others, reason):
    result = validate_environment_variable_key(name, other_names=others)

    assert result.accepted is False
    assert result.failure is reason


def test_environment_model_normalizes_keys_and_hidden_keys():
    environment = Environment(
        variables={" API_KEY ": 123},
        hidden_keys={" API_KEY ", "ORPHAN"},
    )

    assert environment.variables == {"API_KEY": "123"}
    assert environment.hidden_keys == {"API_KEY"}


def test_environment_model_rejects_normalized_duplicates():
    with pytest.raises(ValidationError, match="already exists"):
        Environment(variables={"A": "1", " A ": "2"})


def test_programmatic_batch_update_is_atomic_on_invalid_key():
    environment = Environment(
        variables={"A": "1", "SECRET": "old"},
        hidden_keys={"SECRET"},
    )

    with pytest.raises(EnvironmentVariableValidationError) as raised:
        apply_environment_variable_updates(
            environment,
            {"SECRET": "new", "bad-key": "value"},
        )

    assert raised.value.validation.failure is EnvironmentVariableKeyFailure.INVALID_SYNTAX
    assert environment.variables == {"A": "1", "SECRET": "old"}
    assert environment.hidden_keys == {"SECRET"}


def test_programmatic_update_normalizes_and_updates_existing_key():
    environment = Environment(variables={"A": "1"})

    apply_environment_variable_updates(environment, {" A ": "2"})

    assert environment.variables == {"A": "2"}


def test_programmatic_batch_rejects_two_names_with_same_normalized_key():
    environment = Environment(variables={"EXISTING": "safe"})

    with pytest.raises(EnvironmentVariableValidationError) as raised:
        apply_environment_variable_updates(
            environment,
            {"A": "first", " A ": "second"},
        )

    assert raised.value.validation.failure is EnvironmentVariableKeyFailure.DUPLICATE
    assert environment.variables == {"EXISTING": "safe"}


def test_environment_assignment_preserves_domain_invariant():
    environment = Environment(variables={"A": "1"})

    with pytest.raises(ValidationError):
        environment.variables = {"bad-key": "2"}

    assert environment.variables == {"A": "1"}
