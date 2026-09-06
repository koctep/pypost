"""Typed state used by the manageable library manager surface."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LibrarySourceType(str, Enum):
    """Origin of a connected library directory."""

    CLONED = "Cloned managed copy"
    REGISTERED = "Registered local directory"


class LibrarySyncStatus(str, Enum):
    """Synchronization labels in the manager's stable attention order."""

    CHECKING = "Checking"
    UNKNOWN = "Unknown"
    LOCAL_AND_REMOTE = "Local changes and remote updates"
    LOCAL = "Local changes"
    REMOTE = "Remote updates available"
    AHEAD = "Locally ahead"
    NO_REMOTE = "No remote source"
    CURRENT = "Current"


class LibraryCondition(str, Enum):
    """Independent conditions that can be shown beside synchronization state."""

    OFFLINE = "Offline"
    UNAVAILABLE = "Unavailable"
    INVALID = "Invalid"
    ERROR = "Error"


class LibraryConnectionRecord(BaseModel):
    """Persistable, non-secret description of one connected local directory."""

    model_config = ConfigDict(populate_by_name=True)

    stable_id: str
    local_path: Path
    source_type: LibrarySourceType
    display_name: Optional[str] = None
    manifest_id: Optional[str] = None
    remote_url: Optional[str] = None

    @field_validator("stable_id")
    @classmethod
    def _stable_id_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Library connection ID cannot be empty")
        return value.strip()

    @property
    def canonical_path(self) -> Path:
        """Return the normalized path used for duplicate detection."""
        return self.local_path.expanduser().resolve(strict=False)


class LibraryStatusSnapshot(BaseModel):
    """Normalized, user-facing status that can retain known local facts."""

    model_config = ConfigDict(populate_by_name=True)

    library_id: str
    display_name: Optional[str] = None
    local_path: Optional[Path] = None
    sync_status: LibrarySyncStatus = LibrarySyncStatus.UNKNOWN
    conditions: list[LibraryCondition | str] = Field(default_factory=list)
    is_clean: Optional[bool] = None
    dirty_files: list[str] = Field(default_factory=list)
    current_branch: Optional[str] = None
    tracking_branch: Optional[str] = None
    remote_reachable: Optional[bool] = None
    ahead_count: int = 0
    behind_count: int = 0
    last_modified: Optional[datetime] = None
    last_checked_at: Optional[datetime] = None
    last_successful_check: Optional[datetime] = None
    is_stale: bool = False
    diagnostic: Optional[str] = None


class LibraryOperationGuard(BaseModel):
    """Result of checking whether a destructive Git operation is safe to start."""

    is_blocked: bool
    files: list[str] = Field(default_factory=list)
    message: str = ""


class LibraryOperationState(BaseModel):
    """Visible progress state for one connection and one operation."""

    operation: str
    active: bool = False
    diagnostic: Optional[str] = None


class LibraryListEntry(BaseModel):
    """Immutable row payload combining connection, status, and progress state."""

    model_config = ConfigDict(frozen=True)

    connection: LibraryConnectionRecord
    status: LibraryStatusSnapshot
    operation: Optional[LibraryOperationState] = None

    @property
    def stable_id(self) -> str:
        """Return the stable ID used by selection and actions."""
        return self.connection.stable_id

    @property
    def display_name(self) -> str:
        """Return a readable name with a stable-ID fallback."""
        return self.connection.display_name or self.status.display_name or self.stable_id

    @property
    def source_type(self) -> LibrarySourceType:
        """Return the source label shown in the row."""
        return self.connection.source_type

    @property
    def local_path(self) -> Path:
        """Return the user-facing exact path."""
        return self.connection.local_path

    @property
    def sync_status(self) -> LibrarySyncStatus:
        """Return the normalized synchronization label."""
        return self.status.sync_status

    @property
    def conditions(self) -> list[LibraryCondition | str]:
        """Return independent condition badges."""
        return self.status.conditions

    @property
    def is_clean(self) -> Optional[bool]:
        """Return the known local-change state."""
        return self.status.is_clean

    @property
    def last_modified(self) -> Optional[datetime]:
        """Return the most recent known local modification time."""
        return self.status.last_modified

    @property
    def is_stale(self) -> bool:
        """Return whether the local facts outlive the failed check that supplied them."""
        return self.status.is_stale

    @property
    def ahead_count(self) -> int:
        """Return the local commit count shown in the row."""
        return self.status.ahead_count

    @property
    def behind_count(self) -> int:
        """Return the remote commit count shown in the row."""
        return self.status.behind_count

    @property
    def current_branch(self) -> Optional[str]:
        """Return the active branch or the detached-HEAD label."""
        return self.status.current_branch

    @property
    def last_checked_at(self) -> Optional[datetime]:
        """Return the last status-check timestamp."""
        return self.status.last_checked_at

    @property
    def diagnostic(self) -> Optional[str]:
        """Return safe row guidance, when available."""
        return self.status.diagnostic


@dataclass(frozen=True)
class LibraryRow:
    """Typed, display-ready row consumed by the Qt model and proxy."""

    stable_id: str
    display_name: str
    source_type: str
    local_path: Optional[Path]
    sync_status: str
    conditions: list[str]
    badges: list[str]
    is_clean: Optional[bool]
    last_modified: Optional[datetime]
    last_checked_at: Optional[datetime]
    ahead_count: int
    behind_count: int
    is_stale: bool
    diagnostic: Optional[str]
    display_text: str = ""

    def __getitem__(self, field: str) -> Any:
        """Retain mapping-style access for existing lightweight UI callers."""
        return getattr(self, field)


__all__ = [
    "LibraryCondition",
    "LibraryConnectionRecord",
    "LibraryOperationGuard",
    "LibraryOperationState",
    "LibraryRow",
    "LibraryListEntry",
    "LibrarySourceType",
    "LibraryStatusSnapshot",
    "LibrarySyncStatus",
]
