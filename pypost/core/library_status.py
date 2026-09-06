"""Normalize raw Git snapshots into truthful Library Manager status."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pypost.models.library_manager import (
    LibraryCondition,
    LibraryStatusSnapshot,
    LibrarySyncStatus,
)

STATUS_ORDER = (
    LibrarySyncStatus.CHECKING.value,
    LibrarySyncStatus.UNKNOWN.value,
    LibrarySyncStatus.LOCAL_AND_REMOTE.value,
    LibrarySyncStatus.LOCAL.value,
    LibrarySyncStatus.REMOTE.value,
    LibrarySyncStatus.AHEAD.value,
    LibrarySyncStatus.NO_REMOTE.value,
    LibrarySyncStatus.CURRENT.value,
)


def _value(source: object, name: str, default: Any = None) -> Any:
    """Read an optional attribute from both model and fake status objects."""
    return getattr(source, name, default)


def _timestamp(value: object, fallback: Optional[datetime] = None) -> Optional[datetime]:
    """Return a timezone-aware timestamp or the supplied fallback."""
    if value is None:
        value = fallback
    if value is None:
        return None
    timestamp = value if isinstance(value, datetime) else None
    if timestamp is None:
        return None
    return timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)


class LibraryStatusResolver:
    """Pure status mapping and stale-state construction."""

    @staticmethod
    def failure_condition(error: Exception) -> LibraryCondition:
        """Classify local readability failures separately from remote outages."""
        message = str(error).casefold()
        if getattr(error, "code", None) == "MANIFEST_READ_ERROR":
            return LibraryCondition.UNAVAILABLE
        if str(getattr(error, "code", "")).startswith("MANIFEST_"):
            return LibraryCondition.INVALID
        if isinstance(error, (FileNotFoundError, PermissionError, IsADirectoryError)):
            return LibraryCondition.UNAVAILABLE
        if any(
            marker in message
            for marker in ("network", "offline", "connection", "remote", "timed out")
        ):
            return LibraryCondition.OFFLINE
        if isinstance(error, OSError):
            return LibraryCondition.UNAVAILABLE
        return LibraryCondition.ERROR

    @staticmethod
    def sync_status(raw: object) -> LibrarySyncStatus:
        """Map Git ahead/behind and working-tree facts to the exact vocabulary."""
        clean = bool(_value(raw, "is_clean", True))
        ahead = int(_value(raw, "ahead_count", 0) or 0)
        behind = int(_value(raw, "behind_count", 0) or 0)
        remote_reachable = _value(raw, "remote_reachable")
        remote_configured = _value(raw, "remote_configured")
        if remote_configured is None:
            remote_configured = bool(_value(raw, "tracking_branch"))
        if remote_configured and remote_reachable is False:
            return LibrarySyncStatus.UNKNOWN
        if not clean and behind > 0:
            return LibrarySyncStatus.LOCAL_AND_REMOTE
        if not clean:
            return LibrarySyncStatus.LOCAL
        if behind > 0:
            return LibrarySyncStatus.REMOTE
        if ahead > 0:
            return LibrarySyncStatus.AHEAD
        if not _value(raw, "tracking_branch"):
            return LibrarySyncStatus.NO_REMOTE
        return LibrarySyncStatus.CURRENT

    @classmethod
    def successful(
        cls, raw: object, checked_at: Optional[datetime] = None
    ) -> LibraryStatusSnapshot:
        """Build a normalized snapshot from a successful raw status read."""
        checked_at = checked_at or datetime.now(timezone.utc)
        library_id = str(_value(raw, "library_id", ""))
        path = _value(raw, "local_path", _value(raw, "repo_path"))
        remote_configured = _value(raw, "remote_configured")
        if remote_configured is None:
            remote_configured = bool(_value(raw, "tracking_branch"))
        remote_offline = remote_configured and _value(raw, "remote_reachable") is False
        return LibraryStatusSnapshot(
            library_id=library_id,
            display_name=_value(raw, "display_name"),
            local_path=path,
            sync_status=cls.sync_status(raw),
            tracking_branch=_value(raw, "tracking_branch"),
            remote_reachable=_value(raw, "remote_reachable"),
            is_clean=_value(raw, "is_clean"),
            dirty_files=list(_value(raw, "dirty_files", []) or []),
            current_branch=_value(raw, "current_branch") or "No active branch",
            ahead_count=int(_value(raw, "ahead_count", 0) or 0),
            behind_count=int(_value(raw, "behind_count", 0) or 0),
            last_modified=_timestamp(_value(raw, "last_modified")),
            last_checked_at=_timestamp(_value(raw, "last_checked_at"), checked_at),
            last_successful_check=(
                _timestamp(_value(raw, "last_successful_check"), checked_at)
                if _value(raw, "remote_reachable") is not False
                else _timestamp(_value(raw, "last_successful_check"))
            ),
            conditions=(
                [LibraryCondition.OFFLINE]
                if remote_offline
                else []
            ),
            is_stale=bool(remote_offline),
            diagnostic=(
                "The remote source is unavailable. Local information is stale; "
                "check connectivity and retry."
                if remote_offline
                else None
            ),
        )

    @classmethod
    def failed(
        cls,
        library_id: str,
        previous: Optional[object],
        error: Exception,
        condition: Optional[LibraryCondition] = None,
        checked_at: Optional[datetime] = None,
    ) -> LibraryStatusSnapshot:
        """Retain known local facts while making a failed check visibly stale."""
        condition = condition or cls.failure_condition(error)
        checked_at = checked_at or datetime.now(timezone.utc)
        path = _value(previous, "local_path", _value(previous, "repo_path"))
        return LibraryStatusSnapshot(
            library_id=library_id,
            display_name=_value(previous, "display_name"),
            local_path=path,
            sync_status=LibrarySyncStatus.UNKNOWN,
            conditions=[condition, "Stale"],
            is_clean=_value(previous, "is_clean"),
            dirty_files=list(_value(previous, "dirty_files", []) or []),
            current_branch=_value(previous, "current_branch") or "No active branch",
            ahead_count=int(_value(previous, "ahead_count", 0) or 0),
            behind_count=int(_value(previous, "behind_count", 0) or 0),
            last_modified=_timestamp(_value(previous, "last_modified")),
            last_checked_at=checked_at,
            last_successful_check=_timestamp(_value(previous, "last_successful_check")),
            is_stale=True,
            diagnostic="Refresh could not complete. Check connectivity and retry.",
        )


__all__ = ["LibraryStatusResolver", "STATUS_ORDER"]
