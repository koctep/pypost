"""Library manifest parser, serializer, and validator (PYPOST-1221).

Provides multi-format parsing (YAML and JSON), discovery, disk path validation,
and structured diagnostic error reporting for library manifests.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional
import yaml
from pydantic import ValidationError

from pypost.models.library_manifest import (
    LibraryManifest,
    ManifestDiagnosticError,
    ManifestValidationError,
)

logger = logging.getLogger(__name__)

__all__ = [
    "ManifestDiagnosticError",
    "ManifestValidationError",
    "deserialize_manifest_from_dict",
    "deserialize_manifest_from_json",
    "deserialize_manifest_from_yaml",
    "find_and_read_manifest",
    "find_library_manifest",
    "read_library_manifest",
    "read_manifest_file",
    "serialize_manifest_to_dict",
    "serialize_manifest_to_json",
    "serialize_manifest_to_yaml",
    "validate_manifest_collections",
    "write_library_manifest",
    "write_manifest_file",
]

MANIFEST_CANDIDATE_NAMES = [
    "pypost-library.yaml",
    "pypost-library.yml",
    "pypost-library.json",
]


def serialize_manifest_to_dict(manifest: LibraryManifest) -> dict[str, Any]:
    """Serialize a LibraryManifest instance into a JSON-compatible dictionary."""
    return manifest.model_dump(mode="json")


def serialize_manifest_to_yaml(manifest: LibraryManifest) -> str:
    """Serialize a LibraryManifest into a human-readable YAML string."""
    data = serialize_manifest_to_dict(manifest)
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def serialize_manifest_to_json(
    manifest: LibraryManifest, indent: int = 2
) -> str:
    """Serialize a LibraryManifest into an indented JSON string."""
    return manifest.model_dump_json(indent=indent)


def deserialize_manifest_from_dict(
    data: dict[str, Any], path: Optional[Path | str] = None
) -> LibraryManifest:
    """Deserialize and validate a dictionary into a LibraryManifest instance.

    Raises:
        ManifestDiagnosticError: If validation or schema parsing fails.
    """
    if not isinstance(data, dict):
        logger.warning(
            "manifest_invalid_root type=%s", type(data).__name__
        )
        raise ManifestDiagnosticError(
            code="MANIFEST_INVALID_ROOT",
            message=f"Expected dict, got {type(data).__name__}",
            path=path,
        )
    try:
        manifest = LibraryManifest(**data)
        logger.debug(
            "manifest_deserialized_dict id=%s name=%s collections_count=%d variables_count=%d",
            manifest.id,
            manifest.name,
            len(manifest.collections),
            len(manifest.variables),
        )
        return manifest
    except (ValidationError, ValueError, TypeError) as exc:
        logger.warning("manifest_deserialization_failed reason=%s", exc)
        field_errors: list[dict[str, Any]] = []
        primary_field = None
        primary_json_path = None
        if isinstance(exc, ValidationError):
            for err in exc.errors():
                loc_parts = err.get("loc", ())
                field_str = ""
                json_path_parts = ["$"]
                for part in loc_parts:
                    if isinstance(part, int):
                        field_str = f"{field_str}[{part}]" if field_str else f"[{part}]"
                        json_path_parts.append(f"[{part}]")
                    else:
                        field_str = f"{field_str}.{part}" if field_str else str(part)
                        json_path_parts.append(f".{part}")
                json_path_str = "".join(json_path_parts)
                field_err = {
                    "field": field_str,
                    "json_path": json_path_str,
                    "message": str(err.get("msg", "Validation error")),
                    "type": str(err.get("type", "value_error")),
                }
                field_errors.append(field_err)
                if primary_field is None:
                    primary_field = field_str
                    primary_json_path = json_path_str
        raise ManifestDiagnosticError(
            code="MANIFEST_VALIDATION_ERROR",
            message=f"Failed to validate library manifest: {exc}",
            path=path,
            details={"error": str(exc)},
            field=primary_field,
            json_path=primary_json_path,
            field_errors=field_errors,
        ) from exc


def deserialize_manifest_from_yaml(
    content: str, path: Optional[Path | str] = None
) -> LibraryManifest:
    """Deserialize and validate a YAML string into a LibraryManifest instance.

    Raises:
        ManifestDiagnosticError: If YAML is malformed or validation fails.
    """
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        logger.warning("manifest_yaml_parse_failed reason=%s", exc)
        line = None
        column = None
        if hasattr(exc, "problem_mark") and exc.problem_mark is not None:
            line = exc.problem_mark.line + 1
            column = exc.problem_mark.column + 1
        raise ManifestDiagnosticError(
            code="MANIFEST_SYNTAX_ERROR",
            message=f"Invalid YAML content: {exc}",
            path=path,
            details={"error": str(exc)},
            line=line,
            column=column,
        ) from exc

    if not isinstance(data, dict):
        logger.warning("manifest_yaml_invalid_root type=%s", type(data).__name__)
        raise ManifestDiagnosticError(
            code="MANIFEST_INVALID_ROOT",
            message="YAML content root must be a mapping/object",
            path=path,
        )

    return deserialize_manifest_from_dict(data, path=path)


def deserialize_manifest_from_json(
    content: str, path: Optional[Path | str] = None
) -> LibraryManifest:
    """Deserialize and validate a JSON string into a LibraryManifest instance.

    Raises:
        ManifestDiagnosticError: If JSON is malformed or validation fails.
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.warning("manifest_json_parse_failed reason=%s", exc)
        raise ManifestDiagnosticError(
            code="MANIFEST_SYNTAX_ERROR",
            message=f"Invalid JSON content: {exc}",
            path=path,
            details={"error": str(exc)},
            line=exc.lineno,
            column=exc.colno,
        ) from exc

    if not isinstance(data, dict):
        logger.warning("manifest_json_invalid_root type=%s", type(data).__name__)
        raise ManifestDiagnosticError(
            code="MANIFEST_INVALID_ROOT",
            message="JSON content root must be an object",
            path=path,
        )

    return deserialize_manifest_from_dict(data, path=path)


def read_manifest_file(path: Path | str) -> LibraryManifest:
    """Read and deserialize a library manifest file (.yaml, .yml, or .json).

    Raises:
        ManifestDiagnosticError: If the file cannot be read or parsed.
    """
    file_path = Path(path)
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning(
            "manifest_file_read_failed path=%s reason=%s", file_path, exc
        )
        raise ManifestDiagnosticError(
            code="MANIFEST_READ_ERROR",
            message=f"Could not read file {file_path}: {exc}",
            path=file_path,
            details={"error": str(exc)},
        ) from exc

    suffix = file_path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        manifest = deserialize_manifest_from_yaml(content, path=file_path)
    elif suffix == ".json":
        manifest = deserialize_manifest_from_json(content, path=file_path)
    else:
        # Unknown extension: try JSON then YAML
        try:
            manifest = deserialize_manifest_from_json(content, path=file_path)
        except ManifestDiagnosticError:
            manifest = deserialize_manifest_from_yaml(content, path=file_path)

    logger.info(
        "manifest_file_read path=%s id=%s name=%s collections=%d variables=%d",
        file_path,
        manifest.id,
        manifest.name,
        len(manifest.collections),
        len(manifest.variables),
    )
    return manifest


def read_library_manifest(path: Path | str) -> LibraryManifest:
    """Alias for read_manifest_file."""
    return read_manifest_file(path)


def write_manifest_file(
    manifest: LibraryManifest,
    path: Path | str,
    format: str = "auto",
) -> Path:
    """Write a library manifest to a file in YAML or JSON format.

    Args:
        manifest: The manifest to serialize and write.
        path: Target file path.
        format: Target format ('yaml', 'json', or 'auto' to infer from extension).

    Returns:
        The written Path.

    Raises:
        ManifestDiagnosticError: If format is unsupported or file cannot be written.
    """
    file_path = Path(path)
    target_format = format.lower()
    if target_format == "auto":
        if file_path.suffix.lower() in (".yaml", ".yml"):
            target_format = "yaml"
        else:
            target_format = "json"

    if target_format == "yaml":
        content = serialize_manifest_to_yaml(manifest)
    elif target_format == "json":
        content = serialize_manifest_to_json(manifest)
    else:
        raise ManifestDiagnosticError(
            code="UNSUPPORTED_FORMAT",
            message=f"Unsupported manifest format: {format}",
            path=file_path,
        )

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        logger.warning(
            "manifest_file_write_failed path=%s format=%s reason=%s",
            file_path,
            target_format,
            exc,
        )
        raise ManifestDiagnosticError(
            code="MANIFEST_WRITE_ERROR",
            message=f"Could not write file {file_path}: {exc}",
            path=file_path,
            details={"error": str(exc)},
        ) from exc

    logger.info(
        "manifest_file_written path=%s format=%s id=%s name=%s",
        file_path,
        target_format,
        manifest.id,
        manifest.name,
    )
    return file_path


def write_library_manifest(
    manifest: LibraryManifest,
    path: Path | str,
    format: str = "auto",
) -> Path:
    """Alias for write_manifest_file."""
    return write_manifest_file(manifest, path, format=format)


def find_and_read_manifest(
    directory: Path | str,
) -> tuple[LibraryManifest, Path]:
    """Auto-detect and read pypost-library.yaml, .yml, or .json in a directory.

    Returns:
        tuple[LibraryManifest, Path]: The loaded manifest and its file path.

    Raises:
        ManifestDiagnosticError: If no candidate manifest file exists in the directory.
    """
    dir_path = Path(directory)
    for name in MANIFEST_CANDIDATE_NAMES:
        candidate = dir_path / name
        if candidate.is_file():
            logger.debug("manifest_discovered path=%s", candidate)
            return read_manifest_file(candidate), candidate

    logger.debug("manifest_discovery_not_found dir=%s", dir_path)
    raise ManifestDiagnosticError(
        code="MANIFEST_NOT_FOUND",
        message=f"No library manifest found in directory: {dir_path}",
        path=dir_path,
    )


def find_library_manifest(
    dir_path: Path | str,
) -> tuple[LibraryManifest, Path]:
    """Alias for find_and_read_manifest."""
    return find_and_read_manifest(dir_path)


def validate_manifest_collections(
    manifest: LibraryManifest,
    manifest_dir: Optional[Path | str] = None,
    base_dir: Optional[Path | str] = None,
) -> list[str]:
    """Check if all referenced collection files exist on disk relative to manifest root.

    Args:
        manifest: The library manifest to validate.
        manifest_dir: The directory containing the manifest.
        base_dir: Alternative name for manifest_dir.

    Returns:
        list[str]: Relative paths of missing collection files (empty if all exist).
    """
    root_dir = Path(manifest_dir or base_dir or Path.cwd())
    missing: list[str] = []

    for rel_path in manifest.collections:
        target_path = root_dir / rel_path
        if not target_path.is_file():
            missing.append(rel_path)

    if missing:
        logger.warning(
            "manifest_collections_validation_failed manifest_id=%s missing_count=%d "
            "missing_paths=%s",
            manifest.id,
            len(missing),
            missing,
        )
    else:
        logger.debug(
            "manifest_collections_validation_passed manifest_id=%s total_count=%d",
            manifest.id,
            len(manifest.collections),
        )

    return missing
