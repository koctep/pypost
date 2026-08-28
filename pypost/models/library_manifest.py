"""Library manifest models and data structures (PYPOST-1221).

Defines the core data models for library manifests, collection entries,
environment entries, local overlays, and variable resolution results.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pypost.models.collection_variable import (
    CollectionVariable,
)
from pypost.models.models import Collection


class VariableProvenance(str, Enum):
    """Source layer from which an effective variable value originated."""

    DEFAULT = "default"
    PROFILE = "profile"
    LOCAL_OVERRIDE = "local_override"
    LOCAL_SECRET = "local_secret"


# Alias for compatibility
VariableOrigin = VariableProvenance


class ResolvedVariable(BaseModel):
    """Represents a resolved variable with its effective value and provenance."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    value: Any
    origin: VariableProvenance = VariableProvenance.DEFAULT
    is_secret: bool = False


class LibraryCollectionEntry(BaseModel):
    """Reference to a collection file contained in a collection library."""

    model_config = ConfigDict(populate_by_name=True)

    path: str
    name: Optional[str] = None
    description: str = ""

    @field_validator("path")
    @classmethod
    def validate_path_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Collection path cannot be empty")
        return v.strip()


class LibraryEnvironmentEntry(BaseModel):
    """Preset environment profile configuration in a library manifest."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: str = ""
    variables: Dict[str, Any] = Field(default_factory=dict)


class LibraryManifest(BaseModel):
    """Descriptor manifest for a version-controlled collection library."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str = "1.0.0"
    description: str = ""
    collections: List[str] = Field(default_factory=list)
    variables: List[CollectionVariable] = Field(default_factory=list)
    presets: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def validate_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Library ID cannot be empty")
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Library name cannot be empty")
        return v.strip()

    @field_validator("collections")
    @classmethod
    def validate_collections_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Library must declare at least one collection file")
        cleaned = [item.strip() for item in v if item and item.strip()]
        if not cleaned:
            raise ValueError("Library collections cannot contain only empty paths")
        return cleaned


class LocalLibraryOverlay(BaseModel):
    """User-specific local overrides and secrets stored outside version control."""

    model_config = ConfigDict(populate_by_name=True)

    library_id: str
    active_profile: Optional[str] = None
    secrets: Dict[str, Any] = Field(default_factory=dict)
    overrides: Dict[str, Any] = Field(default_factory=dict)
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class VariableResolutionContext(BaseModel):
    """Input parameters for resolving effective library variables."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    manifest: LibraryManifest
    overlay: Optional[LocalLibraryOverlay] = None
    active_profile: Optional[str] = None
    collection: Optional[Collection] = None
    strict_required: bool = False


class VariableResolutionResult(BaseModel):
    """Result of effective variable resolution with provenance and validation status."""

    model_config = ConfigDict(populate_by_name=True)

    variables: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, VariableProvenance] = Field(default_factory=dict)
    missing_required: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """True if there are no missing required variables and no validation errors."""
        return len(self.missing_required) == 0 and len(self.errors) == 0


class ManifestDiagnosticError(Exception):
    """Structured diagnostic error for manifest parsing and validation issues."""

    def __init__(
        self,
        code: str,
        message: str,
        path: Optional[Path | str] = None,
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None,
        json_path: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        field_errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.code = code
        self.message = message
        self.path = Path(path) if path else None
        self.details = details or {}
        self.field = field
        self.json_path = json_path
        self.line = line
        self.column = column
        self.field_errors = field_errors or []
        path_str = f" (file: {path})" if path else ""
        field_str = f" [field: {field}]" if field else ""
        super().__init__(f"[{code}] {message}{path_str}{field_str}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert diagnostic error to a JSON-serializable dictionary."""
        return {
            "code": self.code,
            "message": self.message,
            "path": str(self.path) if self.path else None,
            "field": self.field,
            "json_path": self.json_path,
            "line": self.line,
            "column": self.column,
            "field_errors": self.field_errors,
            "details": self.details,
        }


class ManifestValidationError(ManifestDiagnosticError):
    """Exception raised when manifest validation fails."""

    def __init__(
        self,
        message: str,
        path: Optional[Path | str] = None,
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None,
        json_path: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        field_errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            code="MANIFEST_VALIDATION_ERROR",
            message=message,
            path=path,
            details=details,
            field=field,
            json_path=json_path,
            line=line,
            column=column,
            field_errors=field_errors,
        )
