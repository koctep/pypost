"""Red failing repro tests for Collection Format v2 (PYPOST-1220).

Tests the target contract before Step 4 implementation:
- CollectionVariable model and type/default validation
- Collection model variables, presets, description, and version
- YAML and JSON serializers & deserializers
- Lossless round-trip serialization
- Backward compatibility with legacy JSON collection files
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import ValidationError

from pypost.core.collection_import import load_collection_import_candidates, plan_collection_import
from pypost.core.collection_serializer import (
    CollectionSerializationError,
    deserialize_collection_from_dict,
    deserialize_collection_from_json,
    deserialize_collection_from_yaml,
    serialize_collection_to_dict,
    serialize_collection_to_json,
    serialize_collection_to_yaml,
)
from pypost.models.collection_variable import (
    COLLECTION_VARIABLE_TYPES,
    CollectionVariable,
    validate_variable_value,
)
from pypost.models.mcp_client import McpClientConnection
from pypost.models.models import Collection, McpToolParam, RequestData
from pypost.models.retry import RetryPolicy
from pypost.models.websocket import WebSocketConnection

pytestmark = pytest.mark.timeout(30)


# ============================================================================
# 1. CollectionVariable Model & Validation Tests
# ============================================================================


def test_collection_variable_valid_types():
    """Verify CollectionVariable instantiation across all supported types."""
    assert COLLECTION_VARIABLE_TYPES == frozenset(
        {"string", "integer", "number", "boolean", "array", "object"}
    )

    var_str = CollectionVariable(
        name="base_url",
        type="string",
        default="https://api.example.com",
        description="Base URL for the API",
        required=True,
        secret=False,
    )
    assert var_str.name == "base_url"
    assert var_str.type == "string"
    assert var_str.default == "https://api.example.com"
    assert var_str.description == "Base URL for the API"
    assert var_str.required is True
    assert var_str.secret is False

    var_int = CollectionVariable(name="port", type="integer", default=8080)
    assert var_int.default == 8080

    var_num = CollectionVariable(name="timeout", type="number", default=3.5)
    assert var_num.default == 3.5

    var_bool = CollectionVariable(name="debug", type="boolean", default=True)
    assert var_bool.default is True

    var_arr = CollectionVariable(name="tags", type="array", default=["dev", "test"])
    assert var_arr.default == ["dev", "test"]

    var_obj = CollectionVariable(name="headers_map", type="object", default={"X-Custom": "val"})
    assert var_obj.default == {"X-Custom": "val"}

    # Default value of None should always be valid for any type
    var_none = CollectionVariable(name="api_token", type="string", default=None, secret=True)
    assert var_none.default is None
    assert var_none.secret is True


def test_collection_variable_rejects_empty_name():
    """Variable name must be a non-empty string."""
    with pytest.raises((ValueError, ValidationError)):
        CollectionVariable(name="", type="string")

    with pytest.raises((ValueError, ValidationError)):
        CollectionVariable(name="   ", type="string")


def test_collection_variable_rejects_unsupported_type():
    """Variable type must be in COLLECTION_VARIABLE_TYPES."""
    with pytest.raises((ValueError, ValidationError)):
        CollectionVariable(name="custom", type="unsupported_type")


@pytest.mark.parametrize(
    "var_type,invalid_default",
    [
        ("string", 123),
        ("string", True),
        ("string", ["a", "b"]),
        ("string", {"k": "v"}),
        ("integer", "123"),
        ("integer", 12.34),
        ("integer", True),  # bool is a subclass of int in Python, must be explicitly rejected
        ("integer", False),
        ("integer", [1]),
        ("number", "12.34"),
        ("number", True),
        ("number", False),
        ("number", [1.0]),
        ("boolean", "true"),
        ("boolean", 1),
        ("boolean", 0),
        ("boolean", None),  # None is valid when passed as default, but not as non-None type mismatch
        ("array", "['a', 'b']"),
        ("array", {"a": 1}),
        ("array", 123),
        ("object", "[1, 2, 3]"),
        ("object", ["a", "b"]),
        ("object", "not_a_dict"),
    ],
)
def test_collection_variable_rejects_default_type_mismatch(var_type: str, invalid_default: Any):
    """CollectionVariable must reject default values that do not match the declared type."""
    if invalid_default is None:
        # None is permitted as default
        return
    with pytest.raises((ValueError, ValidationError)):
        CollectionVariable(name="test_var", type=var_type, default=invalid_default)


def test_validate_variable_value_helper():
    """validate_variable_value helper tests type validation correctly."""
    assert validate_variable_value("hello", "string") is True
    assert validate_variable_value(123, "string") is False

    assert validate_variable_value(42, "integer") is True
    assert validate_variable_value(True, "integer") is False
    assert validate_variable_value(3.14, "integer") is False

    assert validate_variable_value(42, "number") is True
    assert validate_variable_value(3.14, "number") is True
    assert validate_variable_value(True, "number") is False

    assert validate_variable_value(True, "boolean") is True
    assert validate_variable_value(False, "boolean") is True
    assert validate_variable_value(1, "boolean") is False

    assert validate_variable_value([1, 2], "array") is True
    assert validate_variable_value((1, 2), "array") is False

    assert validate_variable_value({"key": "val"}, "object") is True
    assert validate_variable_value([1, 2], "object") is False


# ============================================================================
# 2. Collection Model Variable & Preset Integration Tests
# ============================================================================


def test_collection_model_with_variables_and_presets():
    """Collection model should accept variables, presets, description, and version."""
    variables = [
        CollectionVariable(name="base_url", type="string", default="https://api.example.com"),
        CollectionVariable(name="api_key", type="string", secret=True, required=True),
        CollectionVariable(name="timeout", type="integer", default=30),
    ]
    presets = {
        "local": {"base_url": "http://localhost:8000", "timeout": 5},
        "staging": {"base_url": "https://staging.api.example.com", "timeout": 15},
        "production": {"base_url": "https://api.example.com", "timeout": 30},
    }

    col = Collection(
        id="col-v2-1",
        name="Orders Service API",
        description="Core ordering microservice collection",
        version="2.1.0",
        variables=variables,
        presets=presets,
    )

    assert col.name == "Orders Service API"
    assert col.description == "Core ordering microservice collection"
    assert col.version == "2.1.0"
    assert len(col.variables) == 3
    assert col.variables[0].name == "base_url"
    assert col.variables[1].secret is True
    assert col.presets["local"]["timeout"] == 5


def test_collection_model_defaults_empty_variables_and_presets():
    """Collection model should initialize variables as [] and presets as {} by default."""
    col = Collection(name="Default Collection")
    assert col.description == ""
    assert col.version == "1.0.0"
    assert col.variables == []
    assert col.presets == {}
    assert col.requests == []
    assert col.websockets == []
    assert col.mcp_clients == []


# ============================================================================
# 3. YAML & JSON Round-Trip Serialization Fidelity Tests
# ============================================================================


def _create_comprehensive_collection() -> Collection:
    """Create a rich collection exercising all fields for round-trip validation."""
    return Collection(
        id="col-comprehensive-1",
        name="Payment Gateway API",
        description="Comprehensive collection with requests, websockets, and MCP tools",
        version="1.5.0",
        variables=[
            CollectionVariable(
                name="base_url",
                type="string",
                default="https://api.payments.com",
                description="Gateway URL",
                required=True,
                secret=False,
            ),
            CollectionVariable(
                name="secret_key",
                type="string",
                default=None,
                description="Merchant private key",
                required=True,
                secret=True,
            ),
            CollectionVariable(
                name="max_retries",
                type="integer",
                default=3,
                description="HTTP retry attempts",
                required=False,
                secret=False,
            ),
            CollectionVariable(
                name="rate_limit_ratio",
                type="number",
                default=0.75,
                description="Throttle multiplier",
                required=False,
                secret=False,
            ),
            CollectionVariable(
                name="enable_telemetry",
                type="boolean",
                default=True,
                description="Telemetry flag",
                required=False,
                secret=False,
            ),
            CollectionVariable(
                name="allowed_currencies",
                type="array",
                default=["USD", "EUR", "GBP"],
                description="Currencies whitelist",
                required=False,
                secret=False,
            ),
            CollectionVariable(
                name="metadata_template",
                type="object",
                default={"env": "sandbox", "version": "v1"},
                description="Default metadata payload",
                required=False,
                secret=False,
            ),
        ],
        presets={
            "sandbox": {
                "base_url": "https://sandbox.payments.com",
                "max_retries": 1,
                "enable_telemetry": False,
            },
            "production": {
                "base_url": "https://api.payments.com",
                "max_retries": 5,
                "enable_telemetry": True,
            },
        },
        requests=[
            RequestData(
                id="req-charge-1",
                name="Create Charge",
                method="POST",
                url="{{base_url}}/v1/charges",
                headers={"Authorization": "Bearer {{secret_key}}", "Content-Type": "application/json"},
                params={"idempotency_key": "abc-123"},
                body='{"amount": 5000, "currency": "USD"}',
                body_type="json",
                yaml_as_json=False,
                post_script="assert response.status_code == 200\nprint('Charge created successfully')",
                expose_as_mcp=True,
                mcp_description="Execute a payment charge",
                mcp_params={
                    "amount": McpToolParam(
                        type="integer", description="Amount in cents", required=True, default=100
                    ),
                    "currency": McpToolParam(
                        type="string", description="Currency ISO code", required=False, default="USD"
                    ),
                },
                retry_policy=RetryPolicy(
                    max_attempts=3,
                    initial_delay_sec=1.0,
                    backoff_factor=2.0,
                    retry_on_status_codes=[502, 503, 504],
                ),
            ),
            RequestData(
                id="req-refund-2",
                name="Refund Charge",
                method="DELETE",
                url="{{base_url}}/v1/charges/{{charge_id}}",
                headers={"Authorization": "Bearer {{secret_key}}"},
            ),
        ],
        websockets=[
            WebSocketConnection(
                id="ws-events-1",
                name="Payment Events Stream",
                url="wss://events.payments.com/stream",
                headers={"Authorization": "Bearer {{secret_key}}"},
                protocols=["v1.payment.events"],
            )
        ],
        mcp_clients=[
            McpClientConnection(
                id="mcp-audit-1",
                name="Audit Service MCP",
                command="npx",
                args=["-y", "@payments/audit-server"],
                env={"AUDIT_ENDPOINT": "{{base_url}}/audit"},
            )
        ],
    )


def test_yaml_round_trip_serialization():
    """Serialize collection to YAML and deserialize back, verifying full semantic equality."""
    original = _create_comprehensive_collection()
    yaml_text = serialize_collection_to_yaml(original)

    assert isinstance(yaml_text, str)
    assert "Payment Gateway API" in yaml_text
    assert "variables:" in yaml_text
    assert "presets:" in yaml_text
    assert "sandbox:" in yaml_text

    deserialized = deserialize_collection_from_yaml(yaml_text)

    assert deserialized.id == original.id
    assert deserialized.name == original.name
    assert deserialized.description == original.description
    assert deserialized.version == original.version

    # Variables equality
    assert len(deserialized.variables) == len(original.variables)
    for orig_var, des_var in zip(original.variables, deserialized.variables):
        assert des_var.name == orig_var.name
        assert des_var.type == orig_var.type
        assert des_var.default == orig_var.default
        assert des_var.description == orig_var.description
        assert des_var.required == orig_var.required
        assert des_var.secret == orig_var.secret

    # Presets equality
    assert deserialized.presets == original.presets

    # Requests equality
    assert len(deserialized.requests) == len(original.requests)
    for orig_req, des_req in zip(original.requests, deserialized.requests):
        assert des_req.id == orig_req.id
        assert des_req.name == orig_req.name
        assert des_req.method == orig_req.method
        assert des_req.url == orig_req.url
        assert des_req.headers == orig_req.headers
        assert des_req.params == orig_req.params
        assert des_req.body == orig_req.body
        assert des_req.body_type == orig_req.body_type
        assert des_req.post_script == orig_req.post_script
        assert des_req.expose_as_mcp == orig_req.expose_as_mcp
        assert des_req.mcp_description == orig_req.mcp_description
        assert len(des_req.mcp_params) == len(orig_req.mcp_params)
        if orig_req.retry_policy is not None:
            assert des_req.retry_policy is not None
            assert des_req.retry_policy.max_attempts == orig_req.retry_policy.max_attempts

    # WebSockets and MCP clients
    assert len(deserialized.websockets) == 1
    assert deserialized.websockets[0].name == "Payment Events Stream"
    assert len(deserialized.mcp_clients) == 1
    assert deserialized.mcp_clients[0].command == "npx"


def test_json_round_trip_serialization():
    """Serialize collection to JSON and deserialize back, verifying full semantic equality."""
    original = _create_comprehensive_collection()
    json_text = serialize_collection_to_json(original, indent=2)

    assert isinstance(json_text, str)
    deserialized = deserialize_collection_from_json(json_text)

    assert deserialized.id == original.id
    assert deserialized.name == original.name
    assert deserialized.description == original.description
    assert deserialized.version == original.version
    assert len(deserialized.variables) == len(original.variables)
    assert deserialized.presets == original.presets
    assert len(deserialized.requests) == len(original.requests)
    assert len(deserialized.websockets) == len(original.websockets)
    assert len(deserialized.mcp_clients) == len(original.mcp_clients)


def test_dict_serialization_helpers():
    """Test serialize_collection_to_dict and deserialize_collection_from_dict."""
    original = _create_comprehensive_collection()
    data_dict = serialize_collection_to_dict(original)
    assert isinstance(data_dict, dict)
    assert data_dict["name"] == "Payment Gateway API"
    assert len(data_dict["variables"]) == 7

    reconstructed = deserialize_collection_from_dict(data_dict)
    assert reconstructed.id == original.id
    assert reconstructed.name == original.name


def test_deserialization_error_handling():
    """Malformed YAML/JSON or invalid schema raises CollectionSerializationError."""
    with pytest.raises(CollectionSerializationError):
        deserialize_collection_from_yaml("invalid: yaml: [syntax error")

    with pytest.raises(CollectionSerializationError):
        deserialize_collection_from_json("invalid json { [")

    # Invalid variable schema within YAML
    invalid_schema_yaml = """
name: Bad Collection
variables:
  - name: count
    type: integer
    default: "not_an_integer"
"""
    with pytest.raises((CollectionSerializationError, ValidationError, ValueError)):
        deserialize_collection_from_yaml(invalid_schema_yaml)


# ============================================================================
# 4. Backward Compatibility with Legacy Collection Format
# ============================================================================


def test_deserialize_legacy_json_collection():
    """Legacy JSON files without variables, presets, description or version parse cleanly."""
    legacy_payload = {
        "id": "legacy-col-1",
        "name": "Legacy Users API",
        "requests": [
            {
                "id": "req-user-1",
                "name": "Get User",
                "method": "GET",
                "url": "https://api.example.com/users/1",
                "headers": {},
                "params": {},
                "body": "",
                "body_type": "json",
            }
        ],
        "websockets": [],
        "mcp_clients": [],
    }

    col = deserialize_collection_from_dict(legacy_payload)
    assert col.id == "legacy-col-1"
    assert col.name == "Legacy Users API"
    assert col.description == ""
    assert col.version == "1.0.0"
    assert col.variables == []
    assert col.presets == {}
    assert len(col.requests) == 1


def test_collection_import_preserves_variables_and_presets(tmp_path):
    """Collection import pipeline preserves variables, presets, version, and description."""
    col_dict = {
        "id": "import-col-1",
        "name": "Imported Service",
        "description": "Service with presets and variables",
        "version": "1.2.0",
        "variables": [
            {
                "name": "api_host",
                "type": "string",
                "default": "https://prod.service.internal",
                "description": "Host URL",
                "required": True,
                "secret": False,
            }
        ],
        "presets": {
            "dev": {"api_host": "http://localhost:5000"},
        },
        "requests": [
            {
                "id": "req-1",
                "name": "Health Check",
                "method": "GET",
                "url": "{{api_host}}/health",
            }
        ],
        "websockets": [],
        "mcp_clients": [],
    }

    file_path = tmp_path / "imported_service.json"
    file_path.write_text(json.dumps(col_dict), encoding="utf-8")

    collections, parse_errors = load_collection_import_candidates(file_path)
    assert parse_errors == []
    assert len(collections) == 1
    collection = collections[0]

    assert collection.description == "Service with presets and variables"
    assert collection.version == "1.2.0"
    assert len(collection.variables) == 1
    assert collection.variables[0].name == "api_host"
    assert collection.presets == {"dev": {"api_host": "http://localhost:5000"}}

    # Verify planning and materialization preserves variables and presets
    plan = plan_collection_import(existing=[], incoming=collections)
    assert len(plan.collections) == 1
    materialized = plan.collections[0]
    assert materialized.description == "Service with presets and variables"
    assert materialized.version == "1.2.0"
    assert len(materialized.variables) == 1
    assert materialized.variables[0].name == "api_host"
    assert materialized.presets == {"dev": {"api_host": "http://localhost:5000"}}
