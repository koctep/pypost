"""Library presenter coordinating UI actions with GitLibraryService and manifests (PYPOST-1223).

Manages library discovery, status polling, dirty tree checks, branch switching,
two-way commit/push flows, cloning, and error mapping for desktop UI views.
"""
from __future__ import annotations

import logging
from hashlib import sha256
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, cast

from PySide6.QtCore import QObject, Signal

from pypost.core.git_service import GitLibraryService
from pypost.core.library_connection_store import LibraryConnectionStore
from pypost.core.library_manager_service import LibraryManagerService
from pypost.core.library_manifest import find_and_read_manifest
from pypost.core.library_status import LibraryStatusResolver
from pypost.core.local_overlay_manager import LocalOverlayManager
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.qt.library_operation_worker import LibraryOperationWorker
from pypost.models.git_library import (
    GitAuthConfig,
    GitBranchInfo,
    GitDiagnosticError,
    GitDiagnosticErrorCode,
    GitOperationResult,
    GitRepoStatus,
)
from pypost.models.library_manifest import LibraryManifest, ManifestDiagnosticError
from pypost.models.library_manager import (
    LibraryCondition,
    LibraryConnectionRecord,
    LibraryListEntry,
    LibraryOperationGuard,
    LibraryOperationState,
    LibrarySourceType,
    LibraryStatusSnapshot,
)

logger = logging.getLogger(__name__)

ERROR_MESSAGES: Dict[GitDiagnosticErrorCode, Tuple[str, str]] = {
    GitDiagnosticErrorCode.AUTH_FAILED: (
        "Authentication Failed",
        "Could not authenticate with the remote Git repository. Please verify your "
        "Personal Access Token, SSH key, or SSH agent credentials.",
    ),
    GitDiagnosticErrorCode.DIRTY_WORKING_TREE: (
        "Uncommitted Changes Detected",
        "The operation was blocked because you have uncommitted changes in your local "
        "library. Please commit or stash your changes before pulling or switching branches.",
    ),
    GitDiagnosticErrorCode.REPO_NOT_FOUND: (
        "Repository Not Found",
        "The remote repository could not be found or reached. Please verify the repository "
        "URL and your network connection.",
    ),
    GitDiagnosticErrorCode.BRANCH_NOT_FOUND: (
        "Branch Not Found",
        "The specified branch does not exist on the remote or local repository.",
    ),
    GitDiagnosticErrorCode.MERGE_CONFLICT: (
        "Merge Conflict",
        "Automatic merge failed due to conflicting changes. Please resolve merge conflicts "
        "using Git before syncing.",
    ),
    GitDiagnosticErrorCode.GIT_NOT_INSTALLED: (
        "Git Not Found",
        "Git executable was not found on system PATH. Install Git to use collection libraries.",
    ),
    GitDiagnosticErrorCode.DESTINATION_NOT_EMPTY: (
        "Directory Already Exists",
        "A library with this ID or folder name already exists in your local library storage.",
    ),
    GitDiagnosticErrorCode.TIMEOUT: (
        "Operation Timed Out",
        "The Git operation timed out. Please check your network connection and try again.",
    ),
    GitDiagnosticErrorCode.COMMAND_FAILED: (
        "Git Operation Failed",
        "The Git command encountered an unexpected error.",
    ),
}


class LibraryPresenter(QObject):
    """Coordinates UI events with GitLibraryService, manifest loader, and overlay manager."""

    libraries_loaded = Signal(list)  # list of library_id str
    library_selected = Signal(str)  # selected library_id str
    status_updated = Signal(object)  # GitRepoStatus | None
    manifest_loaded = Signal(object)  # LibraryManifest | None
    operation_started = Signal(str)  # operation name
    operation_completed = Signal(object)  # GitOperationResult
    operation_failed = Signal(object)  # GitDiagnosticError | Exception
    operation_state_changed = Signal(str, str, bool)  # library ID, operation, active
    entries_loaded = Signal(list)
    entry_updated = Signal(str, object)
    operation_completed_for_library = Signal(str, str, object)
    operation_failed_for_library = Signal(str, str, object)
    operation_blocked = Signal(str, str, object)
    branches_loaded = Signal(str, list)
    dirty_files_loaded = Signal(str, list)

    def __init__(
        self,
        service: Optional[GitLibraryService | LibraryManagerService] = None,
        overlay_manager: Optional[LocalOverlayManager] = None,
        parent: Optional[QObject] = None,
        connection_store: Optional[LibraryConnectionStore] = None,
        metrics: MetricsTrackerProtocol | None = None,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        """Initialize LibraryPresenter.

        Args:
            service: Optional GitLibraryService instance.
            overlay_manager: Optional LocalOverlayManager instance.
            parent: Optional Qt parent object.
        """
        super().__init__(parent)
        if service is None:
            self.manager_service: Optional[LibraryManagerService] = LibraryManagerService(
                overlay_manager=overlay_manager,
                connection_store=connection_store,
            )
            self.service: GitLibraryService | LibraryManagerService = self.manager_service
        elif isinstance(service, LibraryManagerService):
            self.manager_service = service
            self.service = service
        else:
            self.manager_service = None
            self.service = service
        self.overlay_manager: LocalOverlayManager = overlay_manager or (
            self.manager_service.overlay_manager
            if self.manager_service is not None
            else LocalOverlayManager()
        )
        self.connection_store = connection_store or getattr(
            self.manager_service, "connection_store", None
        )
        self._metrics = resolve_metrics(metrics)
        self._clock: Callable[[], datetime] = clock or cast(
            Callable[[], datetime],
            getattr(self.manager_service, "clock", lambda: datetime.now(timezone.utc)),
        )
        self._selected_library_id: Optional[str] = None
        self._cached_status: Optional[GitRepoStatus | LibraryStatusSnapshot] = None
        self._cached_manifest: Optional[LibraryManifest] = None
        self._libraries: List[str] = []
        self._connection_records: Dict[str, LibraryConnectionRecord] = {}
        self._active_operations: set[tuple[str, str]] = set()
        self._workers: Dict[tuple[str, str], LibraryOperationWorker] = {}
        self._status_cache: Dict[str, object] = {}

    @property
    def selected_library_id(self) -> Optional[str]:
        """Return the currently selected library ID."""
        return self._selected_library_id

    def get_connection_record(
        self, library_id: Optional[str] = None
    ) -> Optional[LibraryConnectionRecord]:
        """Return connection metadata for UI action and confirmation decisions."""
        connection_id = library_id or self._selected_library_id or ""
        if self.manager_service is not None:
            record = self.manager_service.get_connection(connection_id)
            if record is not None:
                self._connection_records[connection_id] = record
            return record
        return self._connection_records.get(connection_id)

    def get_local_path(self, library_id: Optional[str] = None) -> Optional[Path]:
        """Return the exact path for a connection without exposing service unions to views."""
        connection_id = library_id or self._selected_library_id
        if not connection_id:
            return None
        record = self.get_connection_record(connection_id)
        if record is not None:
            return record.local_path
        if self.manager_service is not None:
            return None
        get_library_dir = cast(
            Callable[[str], Path], getattr(self.service, "get_library_dir")
        )
        return get_library_dir(connection_id)

    def _require_connection_record(self, library_id: str) -> LibraryConnectionRecord:
        """Resolve the current durable record required by manager-service operations."""
        record = self.get_connection_record(library_id)
        if record is None:
            raise ValueError("The selected library is no longer connected.")
        return record

    def list_entries(self) -> List[LibraryListEntry]:
        """Return projected rows without performing disk or Git I/O."""
        entries: List[LibraryListEntry] = []
        for record in self._connection_records.values():
            status = self._snapshot_for(record)
            operation = next(
                (
                    LibraryOperationState(operation=name, active=True)
                    for item_id, name in self._active_operations
                    if item_id == record.stable_id
                ),
                None,
            )
            entries.append(
                LibraryListEntry(connection=record, status=status, operation=operation)
            )
        return entries

    def _snapshot_for(self, record: LibraryConnectionRecord) -> LibraryStatusSnapshot:
        """Return cached status or a truthful initial unknown snapshot."""
        cached = self._status_cache.get(record.stable_id)
        if isinstance(cached, LibraryStatusSnapshot):
            return cached
        if isinstance(cached, GitRepoStatus):
            return LibraryStatusResolver.successful(cached)
        return LibraryStatusSnapshot(
            library_id=record.stable_id,
            display_name=record.display_name,
            local_path=record.local_path,
        )

    def _apply_status(self, library_id: str, status: object) -> LibraryStatusSnapshot:
        """Normalize and cache a status while preserving the connection path."""
        record = self._connection_records.get(library_id)
        snapshot = (
            status
            if isinstance(status, LibraryStatusSnapshot)
            else LibraryStatusResolver.successful(status)
        )
        if record:
            snapshot = snapshot.model_copy(
                update={
                    "library_id": record.stable_id,
                    "display_name": snapshot.display_name or record.display_name,
                    "local_path": snapshot.local_path or record.local_path,
                }
            )
        previous = self._status_cache.get(library_id)
        previous_snapshot: Optional[LibraryStatusSnapshot] = None
        if isinstance(previous, LibraryStatusSnapshot):
            previous_snapshot = previous
        elif previous is not None:
            previous_snapshot = LibraryStatusResolver.successful(previous)
        condition_values = {
            str(getattr(condition, "value", condition))
            for condition in snapshot.conditions
        }
        if previous_snapshot is not None and (
            snapshot.is_stale
            or bool(
                condition_values
                & {LibraryCondition.OFFLINE.value, LibraryCondition.UNAVAILABLE.value}
            )
        ):
            updates: dict[str, object] = {}
            for field in (
                "display_name",
                "local_path",
                "is_clean",
                "dirty_files",
                "current_branch",
                "tracking_branch",
                "ahead_count",
                "behind_count",
                "last_modified",
                "last_successful_check",
            ):
                if getattr(snapshot, field) in (None, [], ""):
                    previous_value = getattr(previous_snapshot, field)
                    if previous_value not in (None, [], ""):
                        updates[field] = previous_value
            if updates:
                snapshot = snapshot.model_copy(update=updates)
        self._status_cache[library_id] = snapshot
        if library_id == self._selected_library_id:
            self._cached_status = snapshot
        self.status_updated.emit(snapshot)
        self.entry_updated.emit(library_id, snapshot)
        return snapshot

    @property
    def cached_status(self) -> Optional[GitRepoStatus | LibraryStatusSnapshot]:
        """Return the latest cached status for the selected library."""
        return self._cached_status

    @property
    def cached_manifest(self) -> Optional[LibraryManifest]:
        """Return the latest cached manifest for the selected library."""
        return self._cached_manifest

    def load_libraries(self) -> List[str]:
        """Scan base directory for connected Git libraries and emit libraries_loaded."""
        base_dir = self.service.base_dir
        if self.manager_service is not None:
            records = self.manager_service.list_connections()
            self._connection_records = {record.stable_id: record for record in records}
            self._libraries = [record.stable_id for record in records]
            self.entries_loaded.emit(self.list_entries())
            self.libraries_loaded.emit(list(self._libraries))
            for record in records:
                self.refresh_status_async(record.stable_id)
            return list(self._libraries)
        if self.connection_store is not None:
            records = self.connection_store.load(legacy_base_dir=base_dir)
            self._connection_records = {record.stable_id: record for record in records}
            self._libraries = [record.stable_id for record in records]
            self.entries_loaded.emit(self.list_entries())
            self.libraries_loaded.emit(list(self._libraries))
            return list(self._libraries)
        libs: List[str] = []
        if base_dir.exists() and base_dir.is_dir():
            for child in sorted(base_dir.iterdir()):
                if child.is_dir() and not child.name.startswith("."):
                    has_git = (child / ".git").exists()
                    has_yaml = (child / "pypost-library.yaml").exists()
                    has_yml = (child / "pypost-library.yml").exists()
                    has_json = (child / "pypost-library.json").exists()
                    if has_git or has_yaml or has_yml or has_json:
                        libs.append(child.name)
        get_library_dir = cast(Callable[[str], Path], getattr(self.service, "get_library_dir"))
        self._connection_records = {
            library_id: LibraryConnectionRecord(
                stable_id=library_id,
                local_path=get_library_dir(library_id),
                source_type=LibrarySourceType.CLONED,
            )
            for library_id in libs
        }
        self._libraries = libs
        self.entries_loaded.emit(self.list_entries())
        self.libraries_loaded.emit(libs)
        return libs

    def select_library(
        self, library_id: Optional[str], refresh: bool = True
    ) -> Optional[GitRepoStatus | LibraryStatusSnapshot]:
        """Select a library, refresh its status and manifest, and emit update signals."""
        self._selected_library_id = library_id
        if not library_id:
            self._cached_status = None
            self._cached_manifest = None
            self.status_updated.emit(None)
            self.manifest_loaded.emit(None)
            return None

        self.library_selected.emit(library_id)
        status: Optional[GitRepoStatus | LibraryStatusSnapshot]
        if refresh:
            status = self.refresh_status(library_id)
        else:
            status = cast(
                Optional[GitRepoStatus | LibraryStatusSnapshot],
                self._status_cache.get(library_id),
            )
            self._cached_status = (
                status
                if isinstance(status, (GitRepoStatus, LibraryStatusSnapshot))
                else None
            )
        self.refresh_manifest(library_id)
        return status if isinstance(status, (GitRepoStatus, LibraryStatusSnapshot)) else None

    def refresh_status(
        self, library_id: Optional[str] = None
    ) -> Optional[GitRepoStatus | LibraryStatusSnapshot]:
        """Query Git status for library and emit status_updated."""
        lib_id = library_id or self._selected_library_id
        if not lib_id:
            self._operation_rejected("none", "refresh")
            self._cached_status = None
            self.status_updated.emit(None)
            return None

        self._operation_started(lib_id, "refresh")
        try:
            status = self._status_for_library(lib_id)
            if self.manager_service is not None:
                result = self._apply_status(lib_id, status)
                self._operation_completed(lib_id, "refresh")
                return result
            if getattr(status, "remote_reachable", None) is False:
                result = self._apply_status(lib_id, status)
                self._operation_completed(lib_id, "refresh")
                return result
            self._status_cache[lib_id] = status
            if lib_id == self._selected_library_id:
                self._cached_status = status
            self.status_updated.emit(status)
            self._operation_completed(lib_id, "refresh")
            return status
        except Exception as ex:
            self._operation_failed(lib_id, "refresh", ex)
            logger.warning(
                "library_status_refresh_failed library_id=%s error_type=%s",
                self._safe_operation_id(lib_id),
                type(ex).__name__,
            )
            stale_status = LibraryStatusResolver.failed(
                lib_id,
                self._status_cache.get(lib_id, self._cached_status),
                ex,
                checked_at=self._clock(),
            )
            self._status_cache[lib_id] = stale_status
            if lib_id == self._selected_library_id:
                self._cached_status = stale_status
            self.status_updated.emit(stale_status)
            self.entry_updated.emit(lib_id, stale_status)
            return stale_status

    def refresh_manifest(self, library_id: Optional[str] = None) -> Optional[LibraryManifest]:
        """Load manifest from library directory and emit manifest_loaded."""
        lib_id = library_id or self._selected_library_id
        if not lib_id:
            self._cached_manifest = None
            self.manifest_loaded.emit(None)
            return None

        repo_dir = self.get_local_path(lib_id)
        if repo_dir is None:
            self.manifest_loaded.emit(None)
            return None
        manifest: Optional[LibraryManifest] = None
        try:
            manifest, _ = find_and_read_manifest(repo_dir)
        except Exception:
            pass
        if lib_id == self._selected_library_id:
            self._cached_manifest = manifest
        self.manifest_loaded.emit(manifest)
        return manifest

    def _status_for_library(self, library_id: str) -> GitRepoStatus | LibraryStatusSnapshot:
        """Read one library through its authoritative connection path."""
        if self.manager_service is not None:
            return self.manager_service.status(library_id)
        record = self._connection_records.get(library_id)
        status_at = getattr(self.service, "status_at", None)
        if record is not None and callable(status_at):
            return cast(Callable[..., GitRepoStatus], status_at)(
                record.local_path, library_id=library_id
            )
        return cast(Callable[[str], GitRepoStatus], getattr(self.service, "status"))(
            library_id
        )

    def _pull_for_library(
        self,
        library_id: str,
        auth: Optional[GitAuthConfig] = None,
    ) -> GitOperationResult:
        """Pull through the manager facade or the path-aware legacy Git seam."""
        if self.manager_service is not None:
            return self.manager_service.pull(self._require_connection_record(library_id), auth=auth)
        record = self._connection_records.get(library_id)
        pull_at = getattr(self.service, "pull_at", None)
        if record is not None and callable(pull_at):
            return cast(Callable[..., GitOperationResult], pull_at)(
                record.local_path, library_id=library_id, auth=auth
            )
        if record is not None and record.source_type == LibrarySourceType.REGISTERED:
            raise ValueError("Registered libraries require a path-aware pull operation.")
        return cast(Callable[..., GitOperationResult], getattr(self.service, "pull"))(
            library_id, auth=auth
        )

    def check_dirty(self, library_id: Optional[str] = None) -> Tuple[bool, List[str]]:
        """Check if the library working tree is dirty."""
        lib_id = library_id or self._selected_library_id
        if not lib_id:
            self._operation_rejected("none", "check_dirty")
            return False, []
        self._operation_started(lib_id, "check_dirty")
        try:
            result = self._check_dirty_for_library(lib_id)
            self._operation_completed(lib_id, "check_dirty")
            return result
        except Exception as error:
            self._operation_failed(lib_id, "check_dirty", error)
            raise

    def _check_dirty_for_library(self, lib_id: str) -> Tuple[bool, List[str]]:
        """Read dirty files without adding a second event inside guarded workers."""
        if self.manager_service is not None:
            return self.manager_service.check_dirty(self._require_connection_record(lib_id))
        record = self._connection_records.get(lib_id)
        check_dirty_at = getattr(self.service, "check_dirty_at", None)
        if record and callable(check_dirty_at):
            return cast(Callable[..., Tuple[bool, List[str]]], check_dirty_at)(
                record.local_path, library_id=lib_id
            )
        if record is not None and record.source_type == LibrarySourceType.REGISTERED:
            raise ValueError("Registered libraries require a path-aware dirty check.")
        return cast(
            Callable[[str], Tuple[bool, List[str]]], getattr(self.service, "check_dirty")
        )(lib_id)

    def pull_library(
        self,
        library_id: Optional[str] = None,
        auth: Optional[GitAuthConfig] = None,
    ) -> GitOperationResult:
        """Pull upstream changes into local library with safety guards."""
        lib_id = library_id or self._selected_library_id
        if not lib_id:
            self._operation_rejected("none", "pull")
            raise ValueError("No library selected for pull")

        self._operation_started(lib_id, "pull")
        self.operation_started.emit("pull")
        try:
            result = self._pull_for_library(lib_id, auth)
            self.refresh_status(lib_id)
            self.refresh_manifest(lib_id)
            self._operation_completed(lib_id, "pull")
            self.operation_completed.emit(result)
            return result
        except Exception as ex:
            self._operation_failed(lib_id, "pull", ex)
            self.operation_failed.emit(ex)
            raise

    def commit_library(
        self,
        library_id: Optional[str] = None,
        message: str = "",
        files: Optional[List[str]] = None,
        auth: Optional[GitAuthConfig] = None,
    ) -> GitOperationResult:
        """Create a Git commit in the local library."""
        lib_id = library_id or self._selected_library_id
        if not lib_id:
            self._operation_rejected("none", "commit")
            raise ValueError("No library selected for commit")

        self._operation_started(lib_id, "commit")
        self.operation_started.emit("commit")
        try:
            if self.manager_service is not None:
                result = self.manager_service.commit(
                    self._require_connection_record(lib_id),
                    message=message,
                    files=files,
                    auth=auth,
                )
            else:
                if (
                    self._connection_records.get(lib_id) is not None
                    and self._connection_records[lib_id].source_type
                    == LibrarySourceType.REGISTERED
                ):
                    raise ValueError("Registered libraries require a path-aware commit operation.")
                result = cast(
                    Callable[..., GitOperationResult], getattr(self.service, "commit")
                )(lib_id, message=message, files=files, auth=auth)
            self.refresh_status(lib_id)
            self._operation_completed(lib_id, "commit")
            self.operation_completed.emit(result)
            return result
        except Exception as ex:
            self._operation_failed(lib_id, "commit", ex)
            self.operation_failed.emit(ex)
            raise

    def push_library(
        self,
        library_id: Optional[str] = None,
        remote: str = "origin",
        branch: Optional[str] = None,
        auth: Optional[GitAuthConfig] = None,
    ) -> GitOperationResult:
        """Push local commits to remote upstream tracking branch."""
        lib_id = library_id or self._selected_library_id
        if not lib_id:
            self._operation_rejected("none", "push")
            raise ValueError("No library selected for push")

        self._operation_started(lib_id, "push")
        self.operation_started.emit("push")
        try:
            if self.manager_service is not None:
                result = self.manager_service.push(
                    self._require_connection_record(lib_id),
                    remote=remote,
                    branch=branch,
                    auth=auth,
                )
            else:
                if (
                    self._connection_records.get(lib_id) is not None
                    and self._connection_records[lib_id].source_type
                    == LibrarySourceType.REGISTERED
                ):
                    raise ValueError("Registered libraries require a path-aware push operation.")
                result = cast(
                    Callable[..., GitOperationResult], getattr(self.service, "push")
                )(lib_id, remote=remote, branch=branch, auth=auth)
            self.refresh_status(lib_id)
            self._operation_completed(lib_id, "push")
            self.operation_completed.emit(result)
            return result
        except Exception as ex:
            self._operation_failed(lib_id, "push", ex)
            self.operation_failed.emit(ex)
            raise

    def commit_and_push(
        self,
        library_id: Optional[str] = None,
        message: str = "",
        files: Optional[List[str]] = None,
        remote: str = "origin",
        branch: Optional[str] = None,
        auth: Optional[GitAuthConfig] = None,
    ) -> Tuple[GitOperationResult, GitOperationResult]:
        """Execute commit followed by push."""
        lib_id = library_id or self._selected_library_id
        if not lib_id:
            self._operation_rejected("none", "commit_and_push")
            raise ValueError("No library selected for commit and push")
        self._operation_started(lib_id, "commit_and_push")
        try:
            res_commit = self.commit_library(
                library_id=library_id,
                message=message,
                files=files,
                auth=auth,
            )
            res_push = self.push_library(
                library_id=library_id,
                remote=remote,
                branch=branch,
                auth=auth,
            )
            self._operation_completed(lib_id, "commit_and_push")
            return res_commit, res_push
        except Exception as error:
            self._operation_failed(lib_id, "commit_and_push", error)
            raise

    def clone_library(
        self,
        url: str,
        library_id: Optional[str] = None,
        branch: Optional[str] = None,
        auth: Optional[GitAuthConfig] = None,
    ) -> GitOperationResult:
        """Clone a remote repository and register it in the library list."""
        target_lib_id = library_id or url.rstrip("/").split("/")[-1].removesuffix(".git")
        safe_operation_id = self._safe_operation_id(target_lib_id)
        self._operation_started(safe_operation_id, "clone")
        self.operation_started.emit("clone")
        try:
            if self.manager_service is not None:
                result = self.manager_service.clone(
                    url, library_id=target_lib_id, branch=branch, auth=auth
                )
            else:
                result = self.service.clone(
                    url, library_id=target_lib_id, branch=branch, auth=auth
                )
            self.load_libraries()
            target_id = result.library_id or target_lib_id
            if target_id:
                self.select_library(target_id)
            self._operation_completed(safe_operation_id, "clone")
            self.operation_completed.emit(result)
            return result
        except Exception as ex:
            self._operation_failed(safe_operation_id, "clone", ex)
            self.operation_failed.emit(ex)
            raise

    def switch_branch(
        self,
        library_id: Optional[str] = None,
        branch: str = "",
        auth: Optional[GitAuthConfig] = None,
    ) -> GitOperationResult:
        """Switch active Git branch for the library."""
        lib_id = library_id or self._selected_library_id
        if not lib_id:
            self._operation_rejected("none", "switch_branch")
            raise ValueError("No library selected for checkout")

        self._operation_started(lib_id, "switch_branch")
        self.operation_started.emit("checkout")
        try:
            result = self._switch_for_library(lib_id, branch, auth)
            self.refresh_status(lib_id)
            self.refresh_manifest(lib_id)
            self._operation_completed(lib_id, "switch_branch")
            self.operation_completed.emit(result)
            return result
        except Exception as ex:
            self._operation_failed(lib_id, "switch_branch", ex)
            self.operation_failed.emit(ex)
            raise

    def _switch_for_library(
        self,
        library_id: str,
        branch: str,
        auth: Optional[GitAuthConfig] = None,
    ) -> GitOperationResult:
        """Switch branches through the manager facade or path-aware Git seam."""
        if self.manager_service is not None:
            return self.manager_service.switch_branch(
                self._require_connection_record(library_id), branch=branch, auth=auth
            )
        record = self._connection_records.get(library_id)
        checkout_at = getattr(self.service, "checkout_at", None)
        if record is not None and callable(checkout_at):
            return cast(Callable[..., GitOperationResult], checkout_at)(
                record.local_path, library_id=library_id, branch=branch, auth=auth
            )
        if record is not None and record.source_type == LibrarySourceType.REGISTERED:
            raise ValueError("Registered libraries require a path-aware checkout operation.")
        return cast(Callable[..., GitOperationResult], getattr(self.service, "checkout"))(
            library_id, branch=branch, auth=auth
        )

    def list_branches(
        self,
        library_id: Optional[str] = None,
        remote: bool = True,
        auth: Optional[GitAuthConfig] = None,
    ) -> List[GitBranchInfo]:
        """List branches for the library."""
        lib_id = library_id or self._selected_library_id
        if not lib_id:
            self._operation_rejected("none", "list_branches")
            return []
        self._operation_started(lib_id, "list_branches")
        try:
            result = self._list_branches_for_library(lib_id, remote=remote, auth=auth)
            self._operation_completed(lib_id, "list_branches")
            return result
        except Exception as error:
            self._operation_failed(lib_id, "list_branches", error)
            raise

    def _list_branches_for_library(
        self,
        lib_id: str,
        remote: bool = True,
        auth: Optional[GitAuthConfig] = None,
    ) -> List[GitBranchInfo]:
        """List branches without adding a second event inside a worker."""
        if self.manager_service is not None:
            return cast(
                List[GitBranchInfo],
                self.manager_service.list_branches(
                    self._require_connection_record(lib_id), remote=remote, auth=auth
                ),
            )
        record = self._connection_records.get(lib_id)
        list_branches_at = getattr(self.service, "list_branches_at", None)
        if record is not None and callable(list_branches_at):
            return cast(List[GitBranchInfo], list_branches_at(record.local_path, lib_id))
        if record is not None and record.source_type == LibrarySourceType.REGISTERED:
            raise ValueError("Registered libraries require a path-aware branch listing operation.")
        return cast(
            Callable[[str], List[GitBranchInfo]], getattr(self.service, "list_branches")
        )(lib_id)

    @staticmethod
    def _safe_operation_id(value: str) -> str:
        """Return a bounded identifier that cannot expose a local path or URL."""
        raw = str(value)
        if len(raw) > 80 or any(marker in raw for marker in ("/", "\\", "?", "#", "@")):
            digest = sha256(raw.encode("utf-8")).hexdigest()[:16]
            return f"opaque-{digest}"
        return raw

    def _operation_started(self, library_id: str, operation: str) -> None:
        """Record the start of one synchronous or asynchronous operation."""
        safe_id = self._safe_operation_id(library_id)
        self._metrics.track_gui_library_operation(operation, "started")
        logger.info(
            "library_operation_started library_id=%s operation=%s", safe_id, operation
        )

    def _operation_completed(self, library_id: str, operation: str) -> None:
        """Record a successful operation without logging result payloads."""
        safe_id = self._safe_operation_id(library_id)
        self._metrics.track_gui_library_operation(operation, "success")
        logger.info(
            "library_operation_completed library_id=%s operation=%s", safe_id, operation
        )

    def _operation_failed(self, library_id: str, operation: str, error: object) -> None:
        """Record an operation failure with only its exception type."""
        safe_id = self._safe_operation_id(library_id)
        self._metrics.track_gui_library_operation(operation, "failure")
        logger.error(
            "library_operation_failed library_id=%s operation=%s error_type=%s",
            safe_id,
            operation,
            type(error).__name__,
        )

    def _operation_rejected(self, library_id: str, operation: str) -> None:
        """Record a rejected operation without exposing rejection details."""
        safe_id = self._safe_operation_id(library_id)
        self._metrics.track_gui_library_operation(operation, "rejected")
        logger.warning(
            "library_operation_rejected library_id=%s operation=%s", safe_id, operation
        )

    def _operation_blocked(self, library_id: str, operation: str) -> None:
        """Record an operation blocked by a user-safety guard."""
        safe_id = self._safe_operation_id(library_id)
        self._metrics.track_gui_library_operation(operation, "blocked")
        logger.info(
            "library_operation_blocked library_id=%s operation=%s", safe_id, operation
        )

    def request_operation(self, library_id: str, operation: str) -> bool:
        """Admit one operation per library and operation until it is finished."""
        key = (library_id, operation)
        if key in self._active_operations:
            return False
        self._active_operations.add(key)
        return True

    def finish_operation(self, library_id: str, operation: str) -> None:
        """Release operation admission after success or failure."""
        self._active_operations.discard((library_id, operation))
        self.operation_state_changed.emit(library_id, operation, False)

    def run_operation_async(
        self,
        library_id: str,
        operation: str,
        callback: Callable[..., object],
        *args: object,
        **kwargs: object,
    ) -> bool:
        """Run one admitted operation in a worker and report completion on the GUI thread."""
        if not self.request_operation(library_id, operation):
            self._operation_rejected(library_id, operation)
            return False
        key = (library_id, operation)
        worker = LibraryOperationWorker(callback, *args, **kwargs)
        self._workers[key] = worker
        self._operation_started(library_id, operation)
        self.operation_started.emit(operation)
        self.operation_state_changed.emit(library_id, operation, True)
        worker.operation_completed.connect(
            lambda result: self._worker_succeeded(key, result)
        )
        worker.operation_failed.connect(lambda error: self._worker_failed(key, error))
        worker.finished.connect(lambda: self._workers.pop(key, None))
        worker.start()
        return True

    def _worker_succeeded(self, key: tuple[str, str], result: object) -> None:
        self.finish_operation(*key)
        library_id, operation = key
        if isinstance(result, LibraryOperationGuard) and result.is_blocked:
            self._operation_blocked(library_id, operation)
            self.operation_blocked.emit(library_id, operation, result)
            return
        if operation in {"disconnect", "delete"} and result is False:
            error = RuntimeError(f"{operation} did not complete")
            self._operation_failed(library_id, operation, error)
            self._mark_operation_error(library_id, error)
            self.operation_failed.emit(error)
            self.operation_failed_for_library.emit(library_id, operation, error)
            return
        if operation == "refresh":
            self._apply_status(library_id, result)
        elif operation == "check_dirty":
            dirty, files = cast(Tuple[bool, List[str]], result)
            self.dirty_files_loaded.emit(library_id, files if dirty else [])
        elif operation == "list_branches":
            self.branches_loaded.emit(library_id, cast(List[GitBranchInfo], result))
        elif operation in {"pull", "switch_branch", "commit", "push", "commit_and_push"}:
            self.refresh_status_async(library_id)
        elif operation == "clone":
            self.load_libraries()
            target_id = getattr(result, "library_id", None) or library_id
            if target_id:
                self.select_library(target_id, refresh=False)
        elif operation == "connect" and isinstance(result, LibraryConnectionRecord):
            self._add_connection_record(result)
        elif operation in {"disconnect", "delete"} and result is True:
            self._remove_connection_record(library_id)
        self._operation_completed(library_id, operation)
        self.operation_completed.emit(result)
        self.operation_completed_for_library.emit(library_id, operation, result)

    def _worker_failed(self, key: tuple[str, str], error: object) -> None:
        self.finish_operation(*key)
        self._operation_failed(key[0], key[1], error)
        self._mark_operation_error(key[0], error)
        self.operation_failed.emit(error)
        self.operation_failed_for_library.emit(key[0], key[1], error)

    def refresh_status_async(self, library_id: str) -> bool:
        """Inspect one connection away from the GUI thread."""
        return self.run_operation_async(
            library_id, "refresh", self._refresh_status_worker, library_id
        )

    def check_dirty_async(self, library_id: str) -> bool:
        """Read dirty files in a worker before opening a commit dialog."""
        return self.run_operation_async(
            library_id, "check_dirty", self._check_dirty_for_library, library_id
        )

    def _refresh_status_worker(self, library_id: str) -> object:
        """Read status through the configured manager or legacy Git service."""
        return self._status_for_library(library_id)

    def pull_library_async(
        self, library_id: str, auth: Optional[GitAuthConfig] = None
    ) -> bool:
        """Guard and pull a library in one admitted worker operation."""
        return self.run_operation_async(
            library_id, "pull", self._pull_worker, library_id, auth
        )

    def commit_library_async(
        self,
        library_id: str,
        message: str,
        files: Optional[List[str]] = None,
        auth: Optional[GitAuthConfig] = None,
    ) -> bool:
        """Commit changes in a worker with per-library operation admission."""
        return self.run_operation_async(
            library_id, "commit", self._commit_worker, library_id, message, files, auth
        )

    def _commit_worker(
        self,
        library_id: str,
        message: str,
        files: Optional[List[str]],
        auth: Optional[GitAuthConfig],
    ) -> GitOperationResult:
        """Execute one commit through the configured service boundary."""
        if self.manager_service is not None:
            return self.manager_service.commit(
                self._require_connection_record(library_id),
                message=message,
                files=files,
                auth=auth,
            )
        record = self._connection_records.get(library_id)
        commit_at = getattr(self.service, "commit_at", None)
        if record is not None and callable(commit_at):
            return cast(Callable[..., GitOperationResult], commit_at)(
                record.local_path, library_id=library_id, message=message, files=files, auth=auth
            )
        return cast(Callable[..., GitOperationResult], getattr(self.service, "commit"))(
            library_id, message=message, files=files, auth=auth
        )

    def push_library_async(
        self,
        library_id: str,
        remote: str = "origin",
        branch: Optional[str] = None,
        auth: Optional[GitAuthConfig] = None,
    ) -> bool:
        """Push changes in a worker with per-library operation admission."""
        return self.run_operation_async(
            library_id, "push", self._push_worker, library_id, remote, branch, auth
        )

    def _push_worker(
        self,
        library_id: str,
        remote: str,
        branch: Optional[str],
        auth: Optional[GitAuthConfig],
    ) -> GitOperationResult:
        """Execute one push through the configured service boundary."""
        if self.manager_service is not None:
            return self.manager_service.push(
                self._require_connection_record(library_id),
                remote=remote,
                branch=branch,
                auth=auth,
            )
        record = self._connection_records.get(library_id)
        push_at = getattr(self.service, "push_at", None)
        if record is not None and callable(push_at):
            return cast(Callable[..., GitOperationResult], push_at)(
                record.local_path,
                library_id=library_id,
                remote=remote,
                branch=branch,
                auth=auth,
            )
        return cast(Callable[..., GitOperationResult], getattr(self.service, "push"))(
            library_id, remote=remote, branch=branch, auth=auth
        )

    def commit_and_push_async(
        self,
        library_id: str,
        message: str,
        files: Optional[List[str]] = None,
        remote: str = "origin",
        branch: Optional[str] = None,
        auth: Optional[GitAuthConfig] = None,
    ) -> bool:
        """Commit and push sequentially inside one admitted worker operation."""
        return self.run_operation_async(
            library_id,
            "commit_and_push",
            self._commit_and_push_worker,
            library_id,
            message,
            files,
            remote,
            branch,
            auth,
        )

    def _commit_and_push_worker(
        self,
        library_id: str,
        message: str,
        files: Optional[List[str]],
        remote: str,
        branch: Optional[str],
        auth: Optional[GitAuthConfig],
    ) -> Tuple[GitOperationResult, GitOperationResult]:
        """Commit, then push, without returning to the GUI thread between operations."""
        commit_result = self._commit_worker(library_id, message, files, auth)
        push_result = self._push_worker(library_id, remote, branch, auth)
        return commit_result, push_result

    def clone_library_async(
        self,
        url: str,
        library_id: Optional[str] = None,
        branch: Optional[str] = None,
        auth: Optional[GitAuthConfig] = None,
    ) -> bool:
        """Clone and register a library in a worker."""
        target_id = library_id or url.rstrip("/").split("/")[-1].removesuffix(".git")
        return self.run_operation_async(
            target_id, "clone", self._clone_worker, url, target_id, branch, auth
        )

    def _clone_worker(
        self,
        url: str,
        library_id: str,
        branch: Optional[str],
        auth: Optional[GitAuthConfig],
    ) -> GitOperationResult:
        """Execute clone through the configured service boundary."""
        if self.manager_service is not None:
            return self.manager_service.clone(url, library_id, branch=branch, auth=auth)
        return cast(Callable[..., GitOperationResult], getattr(self.service, "clone"))(
            url, library_id=library_id, branch=branch, auth=auth
        )

    def _pull_worker(
        self, library_id: str, auth: Optional[GitAuthConfig]
    ) -> GitOperationResult | LibraryOperationGuard:
        guard = self.guard_operation(library_id, "pull")
        if guard.is_blocked:
            return guard
        return self._pull_for_library(library_id, auth)

    def switch_branch_async(
        self,
        library_id: str,
        branch: str,
        auth: Optional[GitAuthConfig] = None,
    ) -> bool:
        """Guard and switch a library branch in one admitted worker operation."""
        return self.run_operation_async(
            library_id,
            "switch_branch",
            self._switch_branch_worker,
            library_id,
            branch,
            auth,
        )

    def list_branches_async(self, library_id: str, remote: bool = True) -> bool:
        """List branches away from the GUI thread with per-library admission."""
        return self.run_operation_async(
            library_id,
            "list_branches",
            self._list_branches_worker,
            library_id,
            remote,
        )

    def connect_local_library_async(self, local_path: Path | str) -> bool:
        """Validate and register a local directory in a worker."""
        operation_id = self._safe_operation_id(
            str(Path(local_path).expanduser().resolve(strict=False))
        )
        return self.run_operation_async(
            operation_id, "connect", self._connect_library_worker, Path(local_path)
        )

    def _connect_library_worker(self, local_path: Path) -> LibraryConnectionRecord:
        """Perform local-library validation without emitting GUI signals."""
        return self._connect_local_library_record(local_path)

    def disconnect_library_async(self, library_id: str) -> bool:
        """Disconnect one connection through the manager-service worker boundary."""
        return self.run_operation_async(
            library_id, "disconnect", self._disconnect_library_worker, library_id
        )

    def _disconnect_library_worker(self, library_id: str) -> bool:
        """Remove only connection metadata in the worker thread."""
        if self.manager_service is not None:
            return self.manager_service.disconnect(library_id)
        if self.connection_store is not None:
            return self.connection_store.remove(library_id)
        disconnect = getattr(self.service, "disconnect_library", None)
        return bool(disconnect(library_id)) if callable(disconnect) else True

    def delete_library_async(self, library_id: str, confirmed: bool = False) -> bool:
        """Delete a confirmed clone through the authoritative service in a worker."""
        record = self.get_connection_record(library_id)
        if record is None or record.source_type == LibrarySourceType.REGISTERED or not confirmed:
            self._operation_rejected(library_id, "delete")
            return False
        return self.run_operation_async(
            library_id,
            "delete",
            self._delete_library_worker,
            record,
            confirmed,
        )

    def _delete_library_worker(
        self, record: LibraryConnectionRecord, confirmed: bool
    ) -> bool:
        """Ask the manager service to recheck source and path before deletion."""
        if self.manager_service is not None:
            return self.manager_service.delete(record, confirmed=confirmed)
        if record.source_type == LibrarySourceType.REGISTERED:
            return False
        deleted = bool(
            cast(Callable[[str], bool], getattr(self.service, "delete_library"))(
                record.stable_id
            )
        )
        if deleted and self.connection_store is not None:
            self.connection_store.remove(record.stable_id)
        if deleted:
            self.overlay_manager.delete_overlay(record.stable_id)
        return deleted

    def _list_branches_worker(self, library_id: str, remote: bool) -> List[GitBranchInfo]:
        """Read branch metadata through the configured service boundary."""
        return self._list_branches_for_library(library_id, remote=remote)

    def _switch_branch_worker(
        self,
        library_id: str,
        branch: str,
        auth: Optional[GitAuthConfig],
    ) -> GitOperationResult | LibraryOperationGuard:
        guard = self.guard_operation(library_id, "switch branch")
        if guard.is_blocked:
            return guard
        return self._switch_for_library(library_id, branch, auth)

    def _mark_operation_error(
        self,
        library_id: str,
        error: object,
        condition: Optional[LibraryCondition] = None,
    ) -> None:
        """Keep the affected row in a safe Error state after worker failure."""
        previous = self._status_cache.get(library_id)
        exception = error if isinstance(error, Exception) else RuntimeError("operation failed")
        snapshot = LibraryStatusResolver.failed(
            library_id,
            previous,
            exception,
            condition=condition or LibraryStatusResolver.failure_condition(exception),
            checked_at=self._clock(),
        ).model_copy(update={"diagnostic": self.get_diagnostic_message(exception)[1]})
        self._status_cache[library_id] = snapshot
        if library_id == self._selected_library_id:
            self._cached_status = snapshot
        self.status_updated.emit(snapshot)
        self.entry_updated.emit(library_id, snapshot)

    def guard_operation(self, library_id: str, operation: str) -> LibraryOperationGuard:
        """Check local changes before an operation that can discard them."""
        try:
            result = self.check_dirty(library_id)
        except Exception:
            return LibraryOperationGuard(
                is_blocked=True,
                files=["<file list unavailable>"],
                message=f"Cannot safely {operation}: the local status could not be read.",
            )
        if not isinstance(result, tuple) or len(result) != 2:
            return LibraryOperationGuard(is_blocked=False)
        is_dirty, dirty_files = result
        if not is_dirty:
            return LibraryOperationGuard(is_blocked=False)
        files = list(dirty_files or ["<file list unavailable>"])
        return LibraryOperationGuard(
            is_blocked=True,
            files=files,
            message="Local changes must be committed or stashed before this operation.",
        )

    def connect_local_library(self, local_path: Path | str) -> LibraryConnectionRecord:
        """Validate and register a local library without changing its directory."""
        operation_id = self._safe_operation_id(
            str(Path(local_path).expanduser().resolve(strict=False))
        )
        self._operation_started(operation_id, "connect")
        try:
            record = self._connect_local_library_record(Path(local_path))
            self._add_connection_record(record)
            self._operation_completed(operation_id, "connect")
            return record
        except Exception as error:
            self._operation_failed(operation_id, "connect", error)
            raise

    def _connect_local_library_record(self, path: Path) -> LibraryConnectionRecord:
        """Build and persist a local connection without touching the GUI model."""
        if self.manager_service is not None:
            return self.manager_service.connect_local_directory(path)
        manifest, _ = find_and_read_manifest(path)
        missing = self._validate_manifest_files(manifest, path)
        if missing:
            raise ValueError(f"Library is missing collection files: {', '.join(missing)}")
        canonical = path.expanduser().resolve(strict=False)
        if any(record.canonical_path == canonical for record in self._connection_records.values()):
            raise ValueError("This local directory is already connected.")
        if any(record.manifest_id == manifest.id for record in self._connection_records.values()):
            raise ValueError("A library with this identity is already connected.")
        record = LibraryConnectionRecord(
            stable_id=manifest.id,
            manifest_id=manifest.id,
            display_name=manifest.name,
            local_path=path,
            source_type=LibrarySourceType.REGISTERED,
        )
        if self.connection_store is not None:
            self.connection_store.add(record)
        return record

    def _add_connection_record(self, record: LibraryConnectionRecord) -> None:
        """Add a completed connection and publish the projected rows on the GUI thread."""
        self._connection_records[record.stable_id] = record
        if record.stable_id not in self._libraries:
            self._libraries.append(record.stable_id)
        self.entries_loaded.emit(self.list_entries())
        self.libraries_loaded.emit(list(self._libraries))

    @staticmethod
    def _validate_manifest_files(manifest: LibraryManifest, root: Path) -> List[str]:
        """Return manifest collection references that are absent from a local directory."""
        return [
            collection_path
            for collection_path in manifest.collections
            if not (root / collection_path).is_file()
        ]

    def disconnect_library(self, library_id: Optional[str] = None) -> bool:
        """Remove only the connection record and retain all local files."""
        lib_id = library_id or self._selected_library_id
        if not lib_id:
            self._operation_rejected("none", "disconnect")
            return False
        self._operation_started(lib_id, "disconnect")
        try:
            if self.manager_service is not None:
                result = self.manager_service.disconnect(lib_id)
            elif self.connection_store is not None:
                result = self.connection_store.remove(lib_id)
            else:
                disconnect = getattr(self.service, "disconnect_library", None)
                result = bool(disconnect(lib_id)) if callable(disconnect) else True
            if result:
                self._remove_connection_record(lib_id)
                self._operation_completed(lib_id, "disconnect")
            else:
                self._operation_failed(
                    lib_id, "disconnect", RuntimeError("disconnect did not complete")
                )
            return result
        except Exception as error:
            self._operation_failed(lib_id, "disconnect", error)
            raise

    def _remove_connection_record(self, library_id: str) -> None:
        """Remove one completed connection from the in-memory projection."""
        self._connection_records.pop(library_id, None)
        self._status_cache.pop(library_id, None)
        self._libraries = [item for item in self._libraries if item != library_id]
        if library_id == self._selected_library_id:
            self.select_library(None)
        self.entries_loaded.emit(self.list_entries())
        self.libraries_loaded.emit(list(self._libraries))

    def delete_library(
        self,
        library_id: Optional[str] = None,
        source_type: Optional[str] = None,
        confirmed: bool = False,
    ) -> bool:
        """Delete only a confirmed cloned library and its local overlay."""
        lib_id = library_id or self._selected_library_id
        if not lib_id or not confirmed:
            self._operation_rejected(lib_id or "none", "delete")
            return False
        record = self.get_connection_record(lib_id)
        if record is None:
            # The legacy API has no registry record, so require its caller to state
            # the clone-only source explicitly. Registry-backed paths never use this
            # compatibility branch and an unknown source is never inferred.
            if self.manager_service is not None or self.connection_store is not None:
                self._operation_rejected(lib_id, "delete")
                return False
            if source_type != LibrarySourceType.CLONED.value:
                self._operation_rejected(lib_id, "delete")
                return False
            self._operation_started(lib_id, "delete")
            try:
                deleted = bool(
                    cast(Callable[[str], bool], getattr(self.service, "delete_library"))(lib_id)
                )
                if deleted:
                    self.overlay_manager.delete_overlay(lib_id)
                    self._operation_completed(lib_id, "delete")
                else:
                    self._operation_failed(
                        lib_id, "delete", RuntimeError("delete did not complete")
                    )
                return deleted
            except Exception as error:
                self._operation_failed(lib_id, "delete", error)
                raise
        source = record.source_type
        if source == LibrarySourceType.REGISTERED:
            self._operation_rejected(lib_id, "delete")
            return False

        self._operation_started(lib_id, "delete")
        try:
            if self.manager_service is not None:
                deleted = self.manager_service.delete(record, confirmed=confirmed)
            else:
                deleted = bool(
                    cast(Callable[[str], bool], getattr(self.service, "delete_library"))(lib_id)
                )
                if deleted and self.connection_store is not None:
                    self.connection_store.remove(lib_id)
                if deleted:
                    try:
                        self.overlay_manager.delete_overlay(lib_id)
                    except Exception:
                        logger.warning(
                            "library_overlay_delete_failed library_id=%s",
                            self._safe_operation_id(lib_id),
                        )

            if deleted:
                self._connection_records.pop(lib_id, None)
                if lib_id == self._selected_library_id:
                    self.select_library(None)
                self.load_libraries()
                self._operation_completed(lib_id, "delete")
            else:
                self._operation_failed(lib_id, "delete", RuntimeError("delete did not complete"))
            return deleted
        except Exception as error:
            self._operation_failed(lib_id, "delete", error)
            raise

    @staticmethod
    def get_diagnostic_message(error: Exception) -> Tuple[str, str]:
        """Map a Git exception to user-friendly title and description."""
        if isinstance(error, GitDiagnosticError):
            title, desc = ERROR_MESSAGES.get(
                error.code,
                ("Git Error", "The Git operation could not be completed. Please retry."),
            )
            return title, desc
        if isinstance(error, ManifestDiagnosticError):
            if error.code == "MANIFEST_READ_ERROR":
                return (
                    "Library Unavailable",
                    "The library manifest could not be read. Check permissions and retry.",
                )
            return (
                "Invalid Library",
                "The library manifest is malformed. Check the manifest and retry.",
            )
        if isinstance(error, ValueError):
            message = str(error).casefold()
            if "already connected" in message or "identity" in message:
                return (
                    "Already Connected",
                    "This library is already connected. Choose another library.",
                )
            if "missing" in message and "collection" in message:
                return (
                    "Invalid Library",
                    "The library is missing one or more declared collection files.",
                )
            if "no longer connected" in message:
                return (
                    "Library Unavailable",
                    "This library is no longer connected. Refresh the list.",
                )
            if "no library selected" in message:
                return "No Library Selected", "Select a library and retry the operation."
            return "Invalid Library", "The library information is invalid. Check it and retry."
        return "Unexpected Error", "The library operation could not be completed. Please retry."
