"""Classify MCP tool inputSchema for a simple form, JSON, or no-arg invoke."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

__all__ = [
    "ArgFieldSpec",
    "ArgSchemaKind",
    "ArgValidationError",
    "classify_arg_schema",
    "list_arg_fields",
]

_COMPOSITION_KEYS = frozenset({"$ref", "oneOf", "anyOf", "allOf"})
_SIMPLE_TYPES = frozenset({"string", "number", "integer", "boolean"})


class ArgSchemaKind(str, Enum):
    """How the invoke column should collect arguments."""

    SIMPLE_FORM = "simple_form"
    JSON_ONLY = "json_only"
    NO_ARGS = "no_args"


class ArgValidationError(ValueError):
    """User-visible argument validation failure (do not call run)."""


@dataclass(frozen=True)
class ArgFieldSpec:
    """One flat JSON Schema property that the simple form can render."""

    name: str
    json_type: str
    required: bool
    enum_values: tuple[str, ...] | None = None


def classify_arg_schema(schema: dict[str, Any] | None) -> ArgSchemaKind:
    """Return simple_form, json_only, or no_args for an MCP inputSchema."""
    if not isinstance(schema, dict):
        return ArgSchemaKind.JSON_ONLY
    if _has_composition(schema):
        return ArgSchemaKind.JSON_ONLY
    if schema.get("type") != "object":
        return ArgSchemaKind.JSON_ONLY
    properties = schema.get("properties")
    if not properties:
        return ArgSchemaKind.NO_ARGS
    if not isinstance(properties, dict):
        return ArgSchemaKind.JSON_ONLY
    for spec in properties.values():
        if not _is_simple_property(spec):
            return ArgSchemaKind.JSON_ONLY
    return ArgSchemaKind.SIMPLE_FORM


def list_arg_fields(schema: dict[str, Any] | None) -> list[ArgFieldSpec]:
    """Field specs for a simple_form schema; empty for other kinds."""
    if classify_arg_schema(schema) != ArgSchemaKind.SIMPLE_FORM:
        return []
    if not isinstance(schema, dict):
        return []
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return []
    required = schema.get("required")
    required_names = (
        {str(item) for item in required} if isinstance(required, list) else set()
    )
    fields: list[ArgFieldSpec] = []
    for name, spec in properties.items():
        if not isinstance(name, str) or not name or not isinstance(spec, dict):
            continue
        json_type = spec.get("type")
        if json_type not in _SIMPLE_TYPES:
            continue
        enum_raw = spec.get("enum")
        enum_values: tuple[str, ...] | None = None
        if isinstance(enum_raw, list) and enum_raw:
            enum_values = tuple(str(item) for item in enum_raw)
        fields.append(
            ArgFieldSpec(
                name=name,
                json_type=str(json_type),
                required=name in required_names,
                enum_values=enum_values,
            ),
        )
    return fields


def _has_composition(node: dict[str, Any]) -> bool:
    return any(key in node for key in _COMPOSITION_KEYS)


def _is_simple_property(spec: object) -> bool:
    if not isinstance(spec, dict):
        return False
    if _has_composition(spec):
        return False
    json_type = spec.get("type")
    if json_type not in _SIMPLE_TYPES:
        return False
    enum_raw = spec.get("enum")
    if enum_raw is None:
        return True
    if not isinstance(enum_raw, list) or not enum_raw:
        return False
    if json_type != "string":
        return False
    return all(isinstance(item, str) for item in enum_raw)
