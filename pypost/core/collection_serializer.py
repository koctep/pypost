"""Serializers and deserializers for self-contained collection format v2 (PYPOST-1220).

Provides YAML and JSON round-trip serialization and deserialization for Collection
models including variable metadata schemas and preset profiles.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import ValidationError
import yaml

from pypost.models.models import Collection

logger = logging.getLogger(__name__)

__all__ = [
    "CollectionFormatError",
    "CollectionSerializationError",
    "deserialize_collection_from_dict",
    "deserialize_collection_from_json",
    "deserialize_collection_from_yaml",
    "read_collection_file",
    "serialize_collection_to_dict",
    "serialize_collection_to_json",
    "serialize_collection_to_legacy_dict",
    "serialize_collection_to_yaml",
    "write_collection_file",
]


class CollectionSerializationError(Exception):
    """Raised when serialization or deserialization of a collection fails."""


class CollectionFormatError(CollectionSerializationError):
    """Raised when the collection file format or root structure is invalid."""


def serialize_collection_to_dict(collection: Collection) -> dict[str, Any]:
    """Serialize a Collection instance into a JSON-compatible dictionary."""
    return collection.model_dump(mode="json")


def serialize_collection_to_legacy_dict(collection: Collection) -> dict[str, Any]:
    """Serialize a Collection instance into a legacy format dictionary."""
    return collection.model_dump(mode="json")


def deserialize_collection_from_dict(data: dict[str, Any]) -> Collection:
    """Deserialize and validate a dictionary into a Collection instance.

    Raises:
        CollectionSerializationError: If validation or schema parsing fails.
    """
    if not isinstance(data, dict):
        raise CollectionFormatError(f"Expected dict, got {type(data).__name__}")
    try:
        return Collection(**data)
    except (ValidationError, ValueError, TypeError) as exc:
        logger.warning("collection_deserialization_failed reason=%s", exc)
        raise CollectionSerializationError(f"Failed to validate collection schema: {exc}") from exc


def serialize_collection_to_yaml(collection: Collection) -> str:
    """Serialize a collection into a human-readable YAML string."""
    data = serialize_collection_to_dict(collection)
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def deserialize_collection_from_yaml(content: str) -> Collection:
    """Deserialize and validate a YAML string into a Collection instance.

    Raises:
        CollectionSerializationError: If YAML is malformed or validation fails.
    """
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        logger.warning("collection_yaml_parse_failed reason=%s", exc)
        raise CollectionSerializationError(f"Invalid YAML content: {exc}") from exc

    if not isinstance(data, dict):
        logger.warning("collection_yaml_invalid_root type=%s", type(data).__name__)
        raise CollectionSerializationError("YAML content root must be a mapping/object")

    return deserialize_collection_from_dict(data)


def serialize_collection_to_json(collection: Collection, indent: int = 2) -> str:
    """Serialize a collection into an indented JSON string."""
    return collection.model_dump_json(indent=indent)


def deserialize_collection_from_json(content: str) -> Collection:
    """Deserialize and validate a JSON string into a Collection instance.

    Raises:
        CollectionSerializationError: If JSON is malformed or validation fails.
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.warning("collection_json_parse_failed reason=%s", exc)
        raise CollectionSerializationError(f"Invalid JSON content: {exc}") from exc

    if not isinstance(data, dict):
        logger.warning("collection_json_invalid_root type=%s", type(data).__name__)
        raise CollectionSerializationError("JSON content root must be an object")

    return deserialize_collection_from_dict(data)


def read_collection_file(path: Path | str) -> Collection:
    """Read and deserialize a collection file (.yaml, .yml, or .json).

    Raises:
        CollectionSerializationError: If the file cannot be read or parsed.
    """
    file_path = Path(path)
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("collection_file_read_failed path=%s reason=%s", file_path, exc)
        raise CollectionSerializationError(f"Could not read file {file_path}: {exc}") from exc

    suffix = file_path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        collection = deserialize_collection_from_yaml(content)
    elif suffix == ".json":
        collection = deserialize_collection_from_json(content)
    else:
        # Unknown extension: try JSON then YAML
        try:
            collection = deserialize_collection_from_json(content)
        except CollectionSerializationError:
            collection = deserialize_collection_from_yaml(content)

    logger.info(
        "collection_file_read path=%s format=%s requests=%d variables=%d presets=%d",
        file_path,
        suffix.lstrip(".") or "auto",
        len(collection.requests),
        len(getattr(collection, "variables", [])),
        len(getattr(collection, "presets", {})),
    )
    return collection


def write_collection_file(
    collection: Collection,
    path: Path | str,
    format: str = "auto",
) -> Path:
    """Write a collection to a file in YAML or JSON format.

    Args:
        collection: The collection to serialize and write.
        path: Target file path.
        format: Target format ('yaml', 'json', or 'auto' to infer from extension).

    Returns:
        The written Path.

    Raises:
        CollectionSerializationError: If format is unsupported or file cannot be written.
    """
    file_path = Path(path)
    target_format = format.lower()
    if target_format == "auto":
        if file_path.suffix.lower() in (".yaml", ".yml"):
            target_format = "yaml"
        else:
            target_format = "json"

    if target_format == "yaml":
        content = serialize_collection_to_yaml(collection)
    elif target_format == "json":
        content = serialize_collection_to_json(collection)
    else:
        raise CollectionSerializationError(f"Unsupported collection format: {format}")

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        logger.warning(
            "collection_file_write_failed path=%s format=%s reason=%s",
            file_path,
            target_format,
            exc,
        )
        raise CollectionSerializationError(f"Could not write file {file_path}: {exc}") from exc

    logger.info(
        "collection_file_written path=%s format=%s request_count=%d "
        "variable_count=%d preset_count=%d",
        file_path,
        target_format,
        len(collection.requests),
        len(getattr(collection, "variables", [])),
        len(getattr(collection, "presets", {})),
    )
    return file_path
