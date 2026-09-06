"""Business facade for safe collection-library management operations."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional, cast

from pypost.core.git_service import GitLibraryService, sanitize_git_url
from pypost.core.library_connection_store import LibraryConnectionStore
from pypost.core.library_manifest import find_and_read_manifest, validate_manifest_collections
from pypost.core.library_status import LibraryStatusResolver
from pypost.core.local_overlay_manager import LocalOverlayManager
from pypost.models.git_library import GitAuthConfig, GitOperationResult
from pypost.models.library_manifest import ManifestDiagnosticError
from pypost.models.library_manager import (
    LibraryCondition,
    LibraryConnectionRecord,
    LibrarySourceType,
    LibraryStatusSnapshot,
    LibrarySyncStatus,
)

logger = logging.getLogger(__name__)


class LibraryManagerService:
    """Resolve connection records and delegate Git work without exposing UI concerns."""

    def __init__(
        self,
        git_service: Optional[GitLibraryService] = None,
        connection_store: Optional[LibraryConnectionStore] = None,
        overlay_manager: Optional[LocalOverlayManager] = None,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self.git_service = git_service or GitLibraryService()
        self.connection_store = connection_store or LibraryConnectionStore()
        self.overlay_manager = overlay_manager or LocalOverlayManager()
        self.connection_store.legacy_base_dir = self.git_service.base_dir
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    @property
    def base_dir(self) -> Path:
        """Expose the managed clone root for compatibility with existing callers."""
        return self.git_service.base_dir

    def list_connections(self) -> list[LibraryConnectionRecord]:
        """Load explicit registrations and discover legacy managed clones."""
        return self.connection_store.load(legacy_base_dir=self.git_service.base_dir)

    def get_connection(self, stable_id: str) -> Optional[LibraryConnectionRecord]:
        """Return the authoritative current record for one connection."""
        return next(
            (record for record in self.list_connections() if record.stable_id == stable_id),
            None,
        )

    def resolve_path(self, record: LibraryConnectionRecord) -> Path:
        """Return the record's exact local path without treating it as a library ID."""
        return record.local_path

    def inspect(self, record: LibraryConnectionRecord) -> LibraryStatusSnapshot:
        """Read a manifest and status snapshot for one connection."""
        path = self.resolve_path(record)
        checked_at = self.clock()
        if not path.is_dir():
            return self._condition_snapshot(
                record,
                LibraryCondition.UNAVAILABLE,
                "The local library path is unavailable. Check the path and retry.",
                checked_at,
            )
        try:
            manifest, _ = find_and_read_manifest(path)
        except ManifestDiagnosticError as error:
            condition = (
                LibraryCondition.UNAVAILABLE
                if error.code == "MANIFEST_READ_ERROR"
                else LibraryCondition.INVALID
            )
            return self._condition_snapshot(
                record,
                condition,
                (
                    "The library manifest could not be read. Check permissions and retry."
                    if condition == LibraryCondition.UNAVAILABLE
                    else "The library manifest is missing or invalid. Check the manifest and retry."
                ),
                checked_at,
            )
        except OSError:
            return self._condition_snapshot(
                record,
                LibraryCondition.UNAVAILABLE,
                "The library manifest could not be read. Check permissions and retry.",
                checked_at,
            )
        try:
            missing = validate_manifest_collections(manifest, manifest_dir=path)
        except OSError:
            return self._condition_snapshot(
                record,
                LibraryCondition.UNAVAILABLE,
                "The library collections could not be read. Check permissions and retry.",
                checked_at,
            ).model_copy(update={"display_name": manifest.name})
        if missing:
            return self._condition_snapshot(
                record,
                LibraryCondition.INVALID,
                "The library is missing declared collection files. Restore them and retry.",
                checked_at,
            ).model_copy(update={"display_name": manifest.name})
        if (path / ".git").exists():
            raw = self._git_call("status", record)
            snapshot = LibraryStatusResolver.successful(raw, checked_at=checked_at)
        else:
            snapshot = LibraryStatusSnapshot(
                library_id=record.stable_id,
                sync_status=LibrarySyncStatus.NO_REMOTE,
                is_clean=True,
                current_branch="No active branch",
                last_checked_at=checked_at,
                last_successful_check=checked_at,
            )
        return snapshot.model_copy(
            update={
                "display_name": manifest.name,
                "local_path": path,
                "last_modified": self._last_modified(path),
            }
        )

    def _condition_snapshot(
        self,
        record: LibraryConnectionRecord,
        condition: LibraryCondition,
        diagnostic: str,
        checked_at: datetime,
    ) -> LibraryStatusSnapshot:
        """Build a safe status for a readable but unusable connection."""
        return LibraryStatusSnapshot(
            library_id=record.stable_id,
            display_name=record.display_name,
            local_path=record.local_path,
            sync_status=LibrarySyncStatus.UNKNOWN,
            conditions=[condition],
            last_checked_at=checked_at,
            diagnostic=diagnostic,
        )

    @staticmethod
    def _last_modified(path: Path) -> Optional[datetime]:
        """Return the newest accessible content timestamp, excluding Git internals."""
        try:
            paths = (item for item in path.rglob("*") if ".git" not in item.parts)
            timestamps = [item.stat().st_mtime for item in paths if item.is_file()]
        except OSError:
            return None
        if not timestamps:
            return None
        return datetime.fromtimestamp(max(timestamps), tz=timezone.utc)

    def status(self, stable_id: str) -> LibraryStatusSnapshot:
        """Inspect a connection by its stable ID."""
        record = self.get_connection(stable_id)
        if record is None:
            raise ValueError("The selected library is no longer connected.")
        return self.inspect(record)

    def connect_local_directory(self, local_path: Path | str) -> LibraryConnectionRecord:
        """Validate and persist an in-place directory registration."""
        path = Path(local_path)
        manifest, _ = find_and_read_manifest(path)
        missing = validate_manifest_collections(manifest, manifest_dir=path)
        if missing:
            raise ValueError("The library is missing declared collection files.")
        return self.connection_store.add(
            LibraryConnectionRecord(
                stable_id=manifest.id,
                manifest_id=manifest.id,
                display_name=manifest.name,
                local_path=path,
                source_type=LibrarySourceType.REGISTERED,
            )
        )

    def clone(
        self,
        url: str,
        library_id: str,
        branch: Optional[str] = None,
        auth: Optional[GitAuthConfig] = None,
    ) -> GitOperationResult:
        """Clone, validate, and durably register a managed library."""
        result = self.git_service.clone(url, library_id=library_id, branch=branch, auth=auth)
        clone_id = result.library_id or library_id
        path = self.git_service.get_library_dir(clone_id)
        try:
            manifest, _ = find_and_read_manifest(path)
            missing = validate_manifest_collections(manifest, manifest_dir=path)
            if missing:
                raise ValueError("The cloned library is missing declared collection files.")
            self.connection_store.add(
                LibraryConnectionRecord(
                    stable_id=clone_id,
                    manifest_id=manifest.id,
                    display_name=manifest.name,
                    local_path=path,
                    source_type=LibrarySourceType.CLONED,
                    remote_url=sanitize_git_url(url),
                )
            )
        except Exception:
            delete_at = getattr(self.git_service, "delete_library_at", None)
            if callable(delete_at):
                try:
                    if not delete_at(path, clone_id):
                        logger.warning(
                            "library_clone_cleanup_skipped library_id=%s", clone_id
                        )
                except Exception as cleanup_error:
                    logger.error(
                        "library_clone_cleanup_failed library_id=%s error_type=%s",
                        clone_id,
                        type(cleanup_error).__name__,
                    )
            raise
        return result

    def check_dirty(self, record: LibraryConnectionRecord) -> tuple[bool, list[str]]:
        """Read dirty files using the record-aware Git boundary."""
        return cast(tuple[bool, list[str]], self._git_call("check_dirty", record))

    def list_branches(
        self,
        record: LibraryConnectionRecord,
        remote: bool = True,
        auth: Optional[GitAuthConfig] = None,
    ) -> list[Any]:
        """List branches through the record-aware Git boundary."""
        if record.source_type == LibrarySourceType.REGISTERED:
            path_method = getattr(self.git_service, "list_branches_at", None)
            if callable(path_method):
                return cast(list[Any], path_method(record.local_path, record.stable_id))
            raise ValueError(
                "Registered libraries require a path-aware branch listing operation."
            )
        return cast(list[Any], self.git_service.list_branches(record.stable_id))

    def pull(
        self,
        record: LibraryConnectionRecord,
        auth: Optional[GitAuthConfig] = None,
    ) -> GitOperationResult:
        """Pull a clean connection from its configured remote source."""
        return cast(GitOperationResult, self._git_call("pull", record, auth=auth))

    def commit(
        self,
        record: LibraryConnectionRecord,
        message: str,
        files: Optional[list[str]] = None,
        auth: Optional[GitAuthConfig] = None,
    ) -> GitOperationResult:
        """Commit changes through the connection's resolved local path."""
        return cast(
            GitOperationResult,
            self._git_call("commit", record, message=message, files=files, auth=auth),
        )

    def push(
        self,
        record: LibraryConnectionRecord,
        remote: str = "origin",
        branch: Optional[str] = None,
        auth: Optional[GitAuthConfig] = None,
    ) -> GitOperationResult:
        """Push changes through the connection's resolved local path."""
        return cast(
            GitOperationResult,
            self._git_call(
                "push", record, remote=remote, branch=branch, auth=auth
            ),
        )

    def switch_branch(
        self,
        record: LibraryConnectionRecord,
        branch: str,
        auth: Optional[GitAuthConfig] = None,
    ) -> GitOperationResult:
        """Switch a clean connection to a requested branch."""
        return cast(
            GitOperationResult,
            self._git_call("checkout", record, branch=branch, auth=auth),
        )

    def disconnect(self, stable_id: str) -> bool:
        """Forget a connection while preserving its directory and overlay data."""
        return self.connection_store.remove(stable_id)

    def delete(
        self, record: LibraryConnectionRecord, confirmed: bool = False
    ) -> bool:
        """Delete only confirmed clones contained by the managed clone root."""
        authoritative = self.get_connection(record.stable_id)
        if (
            not confirmed
            or authoritative is None
            or authoritative.source_type != LibrarySourceType.CLONED
        ):
            return False
        path = authoritative.canonical_path
        root = self.git_service.base_dir.resolve(strict=False)
        try:
            path.relative_to(root)
        except ValueError:
            return False
        if path == root:
            return False
        delete_at = getattr(self.git_service, "delete_library_at", None)
        if not callable(delete_at):
            return False
        deleted = bool(delete_at(path, authoritative.stable_id))
        if deleted:
            self.overlay_manager.delete_overlay(authoritative.stable_id)
            self.connection_store.remove(authoritative.stable_id)
        return deleted

    def _git_call(self, method_name: str, record: LibraryConnectionRecord, **kwargs: Any) -> Any:
        """Call a path-aware method for registrations and ID-based methods for clones."""
        if record.source_type == LibrarySourceType.REGISTERED:
            path_method = getattr(self.git_service, f"{method_name}_at", None)
            if callable(path_method):
                return path_method(record.local_path, library_id=record.stable_id, **kwargs)
            raise ValueError(
                f"Registered libraries require a path-aware {method_name} operation."
            )
        return getattr(self.git_service, method_name)(record.stable_id, **kwargs)


__all__ = ["LibraryManagerService"]
