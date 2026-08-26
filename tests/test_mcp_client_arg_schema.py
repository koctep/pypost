"""Qt-free MCP Client argument-schema classifier (PYPOST-1170)."""

from __future__ import annotations

from typing import Any

import pytest

from pypost.core.mcp_client_arg_schema import ArgSchemaKind, classify_arg_schema

pytestmark = pytest.mark.timeout(10)


def test_flat_required_string_is_simple_form() -> None:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    }
    assert classify_arg_schema(schema) is ArgSchemaKind.SIMPLE_FORM


def test_nested_object_property_is_json_only() -> None:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "payload": {
                "type": "object",
                "properties": {"k": {"type": "integer"}},
            },
        },
    }
    assert classify_arg_schema(schema) is ArgSchemaKind.JSON_ONLY


def test_empty_properties_is_no_args() -> None:
    schema: dict[str, Any] = {"type": "object", "properties": {}}
    assert classify_arg_schema(schema) is ArgSchemaKind.NO_ARGS
