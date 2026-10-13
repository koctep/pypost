"""Automated failing repro tests for CollectionVariable help_text attribute (PYPOST-1372).

Tests assert desired behavior for help_text on CollectionVariable before implementation:
1. Instantiation with help_text retains the string attribute.
2. Default without help_text is None (or when explicitly passed as None).
3. Serialization via model_dump() includes help_text.
4. Deserialization / validation from dictionary with "help_text" populates the field.
5. Rejection of invalid non-string types for help_text (e.g. integer, boolean, list, dict)
   raises ValidationError.
6. Stripping of leading/trailing whitespace from help_text.
7. Normalization/conversion of blank or whitespace-only help_text to None.
8. Round-trip serialization through collection serializer preserving help_text.
"""
from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import ValidationError

from pypost.core.collection_serializer import (
    deserialize_collection_from_dict,
    deserialize_collection_from_json,
    deserialize_collection_from_yaml,
    serialize_collection_to_dict,
    serialize_collection_to_json,
    serialize_collection_to_yaml,
)
from pypost.models.collection_variable import CollectionVariable
from pypost.models.models import Collection


@pytest.mark.timeout(30)
def test_collection_variable_help_text_retained_on_instantiation() -> None:
    """Instantiation with help_text retains the string attribute."""
    guidance = "Provide OAuth token acquired from Google Cloud Console."
    var = CollectionVariable(name="oauth_token", help_text=guidance)
    assert hasattr(var, "help_text")
    assert var.help_text == guidance


@pytest.mark.timeout(30)
def test_collection_variable_help_text_default_none() -> None:
    """Default without help_text or with explicit None resolves to None."""
    var_default = CollectionVariable(name="api_key")
    assert hasattr(var_default, "help_text")
    assert var_default.help_text is None

    var_explicit_none = CollectionVariable(name="api_secret", help_text=None)
    assert var_explicit_none.help_text is None


@pytest.mark.timeout(30)
def test_collection_variable_help_text_serialization_model_dump() -> None:
    """Serialization via model_dump() and model_dump_json() includes help_text."""
    guidance = "Enter your Personal Access Token with repo scope."
    var = CollectionVariable(
        name="github_pat",
        help_text=guidance,
        secret=True,
    )
    dumped = var.model_dump()
    assert "help_text" in dumped
    assert dumped["help_text"] == guidance

    json_dump = json.loads(var.model_dump_json())
    assert "help_text" in json_dump
    assert json_dump["help_text"] == guidance


@pytest.mark.timeout(30)
def test_collection_variable_help_text_deserialization_from_dict() -> None:
    """Deserialization / validation from dictionary with help_text populates the field."""
    raw_data: dict[str, Any] = {
        "name": "jira_token",
        "type": "string",
        "help_text": "Generate API token in Atlassian account settings.",
        "required": True,
    }
    var = CollectionVariable(**raw_data)
    assert hasattr(var, "help_text")
    assert var.help_text == "Generate API token in Atlassian account settings."


@pytest.mark.timeout(30)
@pytest.mark.parametrize(
    "invalid_value",
    [
        12345,
        True,
        False,
        ["instruction 1", "instruction 2"],
        {"details": "token instructions"},
        3.14159,
    ],
)
def test_collection_variable_help_text_rejects_non_string_types(invalid_value: Any) -> None:
    """Rejection of invalid non-string types for help_text raises ValidationError."""
    with pytest.raises(ValidationError):
        CollectionVariable(name="bad_token", help_text=invalid_value)


@pytest.mark.timeout(30)
def test_collection_variable_help_text_whitespace_stripping() -> None:
    """Stripping of leading/trailing boundary whitespace from help_text."""
    raw_guidance = "   \n  Paste the bearer token from auth service.   \t\n"
    var = CollectionVariable(name="bearer_token", help_text=raw_guidance)
    assert var.help_text == "Paste the bearer token from auth service."


@pytest.mark.timeout(30)
@pytest.mark.parametrize(
    "blank_guidance",
    [
        "",
        " ",
        "   ",
        "\t\t",
        "\n\n\r\n",
        " \t \n ",
    ],
)
def test_collection_variable_help_text_blank_converted_to_none(blank_guidance: str) -> None:
    """Rejection or conversion of blank/whitespace-only help_text to None."""
    var = CollectionVariable(name="blank_var", help_text=blank_guidance)
    assert var.help_text is None


@pytest.mark.timeout(30)
def test_collection_variable_help_text_collection_roundtrip_yaml_and_json() -> None:
    """Collection with help_text variables round-trips via serializer in YAML and JSON."""
    var = CollectionVariable(
        name="workspace_id",
        type="string",
        default="ws-123",
        description="Active workspace ID",
        help_text="Find this in Workspace Settings -> General -> Identifier.",
        required=True,
    )
    col = Collection(
        id="col-help-test",
        name="Collection With Variable Guidance",
        variables=[var],
    )

    # 1. Dict round-trip
    col_dict = serialize_collection_to_dict(col)
    assert col_dict["variables"][0]["help_text"] == var.help_text
    reconstructed_dict = deserialize_collection_from_dict(col_dict)
    assert reconstructed_dict.variables[0].help_text == var.help_text

    # 2. YAML round-trip
    yaml_text = serialize_collection_to_yaml(col)
    assert "help_text" in yaml_text
    reconstructed_yaml = deserialize_collection_from_yaml(yaml_text)
    assert reconstructed_yaml.variables[0].help_text == var.help_text

    # 3. JSON round-trip
    json_text = serialize_collection_to_json(col)
    assert "help_text" in json_text
    reconstructed_json = deserialize_collection_from_json(json_text)
    assert reconstructed_json.variables[0].help_text == var.help_text


@pytest.mark.timeout(30)
def test_collection_variable_help_text_legacy_collection_backward_compatibility() -> None:
    """Legacy collections lacking help_text deserialize with help_text=None."""
    legacy_dict: dict[str, Any] = {
        "id": "col-legacy",
        "name": "Legacy Collection",
        "variables": [
            {
                "name": "legacy_var",
                "type": "string",
                "default": "legacy_val",
                "description": "Legacy variable without help_text",
            }
        ],
    }
    reconstructed = deserialize_collection_from_dict(legacy_dict)
    assert len(reconstructed.variables) == 1
    assert reconstructed.variables[0].name == "legacy_var"
    assert reconstructed.variables[0].help_text is None
