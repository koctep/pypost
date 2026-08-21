"""Unit tests for FakeStorageManager.deserialize_environment_records helper (PYPOST-1060)."""

import pytest

from pypost.core.storage import EnvironmentLoadFailure
from pypost.models.models import Environment
from tests.helpers import FakeStorageManager

pytestmark = pytest.mark.timeout(60)


def test_deserialize_valid_environment_records():
    """Valid environment dictionaries deserialize into Environment models without failures."""
    storage = FakeStorageManager()
    records = [
        {
            "id": "env-1",
            "name": "Development",
            "variables": {"BASE_URL": "http://localhost:8000", "API_KEY": "dev-key"},
            "hidden_keys": ["API_KEY"],
            "enable_mcp": True,
        },
        {
            "id": "env-2",
            "name": "Staging",
            "variables": {"BASE_URL": "https://staging.example.com"},
            "hidden_keys": [],
            "enable_mcp": False,
        },
    ]

    environments, failures = storage.deserialize_environment_records(records)

    assert failures == ()
    assert len(environments) == 2
    assert isinstance(environments[0], Environment)
    assert environments[0].id == "env-1"
    assert environments[0].name == "Development"
    assert environments[0].variables == {"BASE_URL": "http://localhost:8000", "API_KEY": "dev-key"}
    assert environments[0].hidden_keys == {"API_KEY"}
    assert environments[0].enable_mcp is True

    assert isinstance(environments[1], Environment)
    assert environments[1].id == "env-2"
    assert environments[1].name == "Staging"
    assert environments[1].variables == {"BASE_URL": "https://staging.example.com"}
    assert environments[1].hidden_keys == set()
    assert environments[1].enable_mcp is False


def test_deserialize_empty_records():
    """Empty list returns empty environments list and empty failures tuple."""
    storage = FakeStorageManager()
    environments, failures = storage.deserialize_environment_records([])
    assert environments == []
    assert failures == ()


def test_deserialize_invalid_records_returns_failures():
    """Malformed records with invalid types produce EnvironmentLoadFailure instances."""
    storage = FakeStorageManager()
    records = [
        {
            "id": "bad-env-1",
            "name": "Bad Variables",
            "variables": "not-a-dict",  # variables must be a dict
        },
        {
            "id": "bad-env-2",
            "name": "Bad MCP Type",
            "variables": {},
            "enable_mcp": "not-a-bool-valid-coercion-fails-or-invalid",
        },
    ]

    environments, failures = storage.deserialize_environment_records(records)

    assert environments == []
    assert len(failures) == 2
    assert all(isinstance(f, EnvironmentLoadFailure) for f in failures)
    assert failures[0].name == "Bad Variables"
    assert failures[0].environment_id == "bad-env-1"
    assert len(failures[0].reason) > 0

    assert failures[1].name == "Bad MCP Type"
    assert failures[1].environment_id == "bad-env-2"
    assert len(failures[1].reason) > 0


def test_deserialize_mixed_valid_and_invalid_records():
    """Batch with both valid and invalid records parses valid ones and reports failures."""
    storage = FakeStorageManager()
    records = [
        {
            "id": "valid-1",
            "name": "Valid Env",
            "variables": {"KEY": "VALUE"},
        },
        {
            "id": "invalid-1",
            "name": "Invalid Env",
            "variables": ["not", "a", "dict"],
        },
    ]

    environments, failures = storage.deserialize_environment_records(records)

    assert len(environments) == 1
    assert environments[0].id == "valid-1"
    assert environments[0].name == "Valid Env"
    assert environments[0].variables == {"KEY": "VALUE"}

    assert len(failures) == 1
    assert isinstance(failures[0], EnvironmentLoadFailure)
    assert failures[0].name == "Invalid Env"
    assert failures[0].environment_id == "invalid-1"


def test_deserialize_non_mapping_record_returns_failure():
    """Non-mapping entries (integers, strings, None) produce failures safely."""
    storage = FakeStorageManager()
    records = [
        "not-a-dict",
        12345,
        None,
    ]

    environments, failures = storage.deserialize_environment_records(records)

    assert environments == []
    assert len(failures) == 3
    for failure in failures:
        assert isinstance(failure, EnvironmentLoadFailure)
        assert failure.name == "unknown"
        assert failure.environment_id is None
        assert "not a mapping" in failure.reason.lower() or len(failure.reason) > 0


def test_deserialize_preserves_custom_id_or_generates_default():
    """Record without explicit id gets auto id, and record with id preserves it."""
    storage = FakeStorageManager()
    records = [
        {
            "name": "Auto ID Env",
            "variables": {"FOO": "bar"},
        },
        {
            "id": "custom-explicit-id",
            "name": "Custom ID Env",
            "variables": {"BAZ": "qux"},
        },
    ]

    environments, failures = storage.deserialize_environment_records(records)

    assert failures == ()
    assert len(environments) == 2
    assert environments[0].id is not None
    assert len(environments[0].id) > 0
    assert environments[0].name == "Auto ID Env"

    assert environments[1].id == "custom-explicit-id"
    assert environments[1].name == "Custom ID Env"


def test_round_trip_with_serialize_environment_records():
    """Serializing environments and deserializing them produces equivalent Environment objects."""
    storage = FakeStorageManager()
    original_envs = [
        Environment(
            id="env-roundtrip-1",
            name="Prod",
            variables={"ENDPOINT": "https://api.prod.com"},
            hidden_keys={"ENDPOINT"},
            enable_mcp=True,
        ),
        Environment(
            id="env-roundtrip-2",
            name="Local",
            variables={"ENDPOINT": "http://127.0.0.1:8080"},
            hidden_keys=set(),
            enable_mcp=False,
        ),
    ]

    serialized_records = storage.serialize_environment_records(original_envs)
    assert isinstance(serialized_records, list)
    assert len(serialized_records) == 2

    deserialized_envs, failures = storage.deserialize_environment_records(serialized_records)
    assert failures == ()
    assert len(deserialized_envs) == 2
    assert deserialized_envs[0] == original_envs[0]
    assert deserialized_envs[1] == original_envs[1]
