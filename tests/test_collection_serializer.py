"""Unit tests for Collection Serializer and CollectionVariable (PYPOST-1220).

Tests YAML/JSON serialization, deserialization, file I/O operations,
error handling, and collection variable validation.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from pypost.core.collection_serializer import (
    CollectionFormatError,
    CollectionSerializationError,
    deserialize_collection_from_dict,
    deserialize_collection_from_json,
    deserialize_collection_from_yaml,
    read_collection_file,
    serialize_collection_to_dict,
    serialize_collection_to_json,
    serialize_collection_to_legacy_dict,
    serialize_collection_to_yaml,
    write_collection_file,
)
from pypost.models.collection_variable import (
    CollectionVariable,
    validate_variable_value,
)
from pypost.models.models import Collection, RequestData
from pypost.models.websocket import WebSocketConnection

pytestmark = pytest.mark.timeout(30)


def test_collection_variable_properties_and_aliases():
    """Verify CollectionVariable default_value alias and property."""
    var1 = CollectionVariable(name="host", default="localhost")
    assert var1.default == "localhost"
    assert var1.default_value == "localhost"

    var2 = CollectionVariable(name="port", default_value=9000, type="integer")
    assert var2.default == 9000
    assert var2.default_value == 9000


def test_validate_variable_value_all_types():
    """Verify validate_variable_value handling all type names."""
    assert validate_variable_value("test", "string") is True
    assert validate_variable_value(123, "integer") is True
    assert validate_variable_value(123, "number") is True
    assert validate_variable_value(12.34, "number") is True
    assert validate_variable_value(True, "boolean") is True
    assert validate_variable_value([1, 2], "array") is True
    assert validate_variable_value({"a": 1}, "object") is True

    # Invalid cases
    assert validate_variable_value(None, "string") is False
    assert validate_variable_value("not_type", "unknown_type") is False


def test_serialize_and_deserialize_helpers():
    """Verify serialize_collection_to_legacy_dict and deserialize_collection_from_dict."""
    col = Collection(
        id="col-legacy-1",
        name="Legacy Col",
        requests=[RequestData(name="Ping", url="https://example.com/ping")],
    )
    legacy_dict = serialize_collection_to_legacy_dict(col)
    assert legacy_dict["name"] == "Legacy Col"
    assert legacy_dict["id"] == "col-legacy-1"

    reconstructed = deserialize_collection_from_dict(legacy_dict)
    assert reconstructed.name == col.name
    assert reconstructed.id == col.id

    with pytest.raises(CollectionFormatError):
        deserialize_collection_from_dict("not a dict")  # type: ignore


def test_read_and_write_collection_file_yaml(tmp_path: Path):
    """Verify write_collection_file and read_collection_file with YAML."""
    col = Collection(
        name="YAML Test Collection",
        description="Testing YAML serialization to disk",
        variables=[
            CollectionVariable(name="api_host", type="string", default="https://api.test.com"),
            CollectionVariable(name="port", type="integer", default=443),
        ],
        presets={
            "dev": {"api_host": "https://dev.test.com", "port": 8443},
        },
        requests=[
            RequestData(name="Get Status", method="GET", url="{{api_host}}:{{port}}/status"),
        ],
        websockets=[
            WebSocketConnection(name="WS Status", url="wss://{{api_host}}:{{port}}/stream"),
        ],
    )

    yaml_path = tmp_path / "test_col.yaml"
    result_path = write_collection_file(col, yaml_path)
    assert result_path == yaml_path
    assert yaml_path.exists()

    loaded_col = read_collection_file(yaml_path)
    assert loaded_col.name == col.name
    assert loaded_col.description == col.description
    assert len(loaded_col.variables) == 2
    assert loaded_col.presets["dev"]["port"] == 8443
    assert len(loaded_col.requests) == 1
    assert len(loaded_col.websockets) == 1


def test_read_and_write_collection_file_json(tmp_path: Path):
    """Verify write_collection_file and read_collection_file with JSON."""
    col = Collection(
        name="JSON Test Collection",
        description="Testing JSON serialization to disk",
        variables=[CollectionVariable(name="env", type="string", default="prod")],
        presets={"prod": {"env": "prod"}},
    )

    json_path = tmp_path / "test_col.json"
    write_collection_file(col, json_path, format="json")
    assert json_path.exists()

    loaded_col = read_collection_file(json_path)
    assert loaded_col.name == col.name
    assert loaded_col.description == col.description
    assert len(loaded_col.variables) == 1
    assert loaded_col.presets == {"prod": {"env": "prod"}}


def test_read_collection_file_unknown_extension_and_errors(tmp_path: Path):
    """Verify reading collection from file with non-standard extension or missing file."""
    col = Collection(name="Custom Ext Collection")
    custom_path = tmp_path / "collection.pypost"
    write_collection_file(col, custom_path, format="json")

    loaded_col = read_collection_file(custom_path)
    assert loaded_col.name == "Custom Ext Collection"

    # Non-existent file
    missing_path = tmp_path / "non_existent.yaml"
    with pytest.raises(CollectionSerializationError):
        read_collection_file(missing_path)

    # Unsupported format in write_collection_file
    with pytest.raises(CollectionSerializationError):
        write_collection_file(col, tmp_path / "out.txt", format="invalid_format")


def test_deserialize_yaml_non_dict_root():
    """Verify deserialize_collection_from_yaml raises on non-dict YAML."""
    with pytest.raises(CollectionSerializationError):
        deserialize_collection_from_yaml("- item 1\n- item 2\n")

    with pytest.raises(CollectionSerializationError):
        deserialize_collection_from_yaml("just a plain string")


def test_deserialize_json_non_dict_root():
    """Verify deserialize_collection_from_json raises on non-dict JSON."""
    with pytest.raises(CollectionSerializationError):
        deserialize_collection_from_json('["item1", "item2"]')

    with pytest.raises(CollectionSerializationError):
        deserialize_collection_from_json('"just a string"')
