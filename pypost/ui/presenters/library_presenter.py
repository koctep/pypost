"""Library presenter coordinating UI actions with GitLibraryService and manifests (PYPOST-1223).

Manages library discovery, status polling, dirty tree checks, branch switching,
two-way commit/push flows, cloning, and error mapping for desktop UI views.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QObject, Signal

from pypost.core.git_service import GitLibraryService
from pypost.core.library_manifest import find_and_read_manifest
from pypost.core.local_overlay_manager import LocalOverlayManager
from pypost.models.git_library import (
    GitAuthConfig,
    GitBranchInfo,
    GitDiagnosticError,
    GitDiagnosticErrorCode,
    GitOperationResult,
    GitRepoStatus,
)
from pypost.models.library_manifest import LibraryManifest

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

    def __init__(
        self,
        service: Optional[GitLibraryService] = None,
        overlay_manager: Optional[LocalOverlayManager] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        """Initialize LibraryPresenter.

        Args:
            service: Optional GitLibraryService instance.
            overlay_manager: Optional LocalOverlayManager instance.
            parent: Optional Qt parent object.
        """
        super().__init__(parent)
        self.service = service or GitLibraryService()
        self.overlay_manager = overlay_manager or LocalOverlayManager()
        self._selected_library_id: Optional[str] = None
        self._cached_status: Optional[GitRepoStatus] = None
        self._cached_manifest: Optional[LibraryManifest] = None
        self._libraries: List[str] = []

    @property
    def selected_library_id(self) -> Optional[str]:
        """Return the currently selected library ID."""
        return self._selected_library_id

    @property
    def cached_status(self) -> Optional[GitRepoStatus]:
        """Return the latest cached status for the selected library."""
        return self._cached_status

    @property
    def cached_manifest(self) -> Optional[LibraryManifest]:
        """Return the latest cached manifest for the selected library."""
        return self._cached_manifest

    def load_libraries(self) -> List[str]:
        """Scan base directory for connected Git libraries and emit libraries_loaded."""
        base_dir = self.service.base_dir
        libs: List[str] = []
        if base_dir.exists() and base_dir.is_dir():
            for child in sorted(base_dir.iterdir()):
                if child.is_dir() and not child.name.startswith("."):
                    has_git = (child / ".git").exists()
                    has_yaml = (child / "pypost-library.yaml").exists()
                    has_json = (child / "pypost-library.json").exists()
                    if has_git or has_yaml or has_json:
                        libs.append(child.name)
        self._libraries = libs
        self.libraries_loaded.emit(libs)
        return libs

    def select_library(self, library_id: Optional[str]) -> Optional[GitRepoStatus]:
        """Select a library, refresh its status and manifest, and emit update signals."""
        self._selected_library_id = library_id
        if not library_id:
            self._cached_status = None
            self._cached_manifest = None
            self.status_updated.emit(None)
            self.manifest_loaded.emit(None)
            return None

        self.library_selected.emit(library_id)
        status = self.refresh_status(library_id)
        self.refresh_manifest(library_id)
        return status

    def refresh_status(self, library_id: Optional[str] = None) -> Optional[GitRepoStatus]:
        """Query Git status for library and emit status_updated."""
        lib_id = library_id or self._selected_library_id
        if not lib_id:
            self._cached_status = None
            self.status_updated.emit(None)
            return None

        try:
            status = self.service.status(lib_id)
            if lib_id == self._selected_library_id:
                self._cached_status = status
            self.status_updated.emit(status)
            return status
        except Exception as ex:
            logger.warning("library_status_refresh_failed library_id=%s error=%s", lib_id, ex)
            if lib_id == self._selected_library_id:
                self._cached_status = None
            self.status_updated.emit(None)
            return None

    def refresh_manifest(self, library_id: Optional[str] = None) -> Optional[LibraryManifest]:
        """Load manifest from library directory and emit manifest_loaded."""
        lib_id = library_id or self._selected_library_id
        if not lib_id:
            self._cached_manifest = None
            self.manifest_loaded.emit(None)
            return None

        repo_dir = self.service.get_library_dir(lib_id)
        manifest: Optional[LibraryManifest] = None
        try:
            manifest, _ = find_and_read_manifest(repo_dir)
        except Exception:
            pass
        if lib_id == self._selected_library_id:
            self._cached_manifest = manifest
        self.manifest_loaded.emit(manifest)
        return manifest

    def check_dirty(self, library_id: Optional[str] = None) -> Tuple[bool, List[str]]:
        """Check if the library working tree is dirty."""
        lib_id = library_id or self._selected_library_id
        if not lib_id:
            return False, []
        return self.service.check_dirty(lib_id)

    def pull_library(
        self,
        library_id: Optional[str] = None,
        auth: Optional[GitAuthConfig] = None,
    ) -> GitOperationResult:
        """Pull upstream changes into local library with safety guards."""
        lib_id = library_id or self._selected_library_id
        if not lib_id:
            raise ValueError("No library selected for pull")

        self.operation_started.emit("pull")
        try:
            result = self.service.pull(lib_id, auth=auth)
            self.refresh_status(lib_id)
            self.refresh_manifest(lib_id)
            self.operation_completed.emit(result)
            return result
        except Exception as ex:
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
            raise ValueError("No library selected for commit")

        self.operation_started.emit("commit")
        try:
            result = self.service.commit(lib_id, message=message, files=files, auth=auth)
            self.refresh_status(lib_id)
            self.operation_completed.emit(result)
            return result
        except Exception as ex:
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
            raise ValueError("No library selected for push")

        self.operation_started.emit("push")
        try:
            result = self.service.push(lib_id, remote=remote, branch=branch, auth=auth)
            self.refresh_status(lib_id)
            self.operation_completed.emit(result)
            return result
        except Exception as ex:
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
        return res_commit, res_push

    def clone_library(
        self,
        url: str,
        library_id: Optional[str] = None,
        branch: Optional[str] = None,
        auth: Optional[GitAuthConfig] = None,
    ) -> GitOperationResult:
        """Clone a remote repository and register it in the library list."""
        target_lib_id = library_id or url.rstrip("/").split("/")[-1].removesuffix(".git")
        self.operation_started.emit("clone")
        try:
            result = self.service.clone(url, library_id=target_lib_id, branch=branch, auth=auth)
            self.load_libraries()
            target_id = result.library_id or target_lib_id
            if target_id:
                self.select_library(target_id)
            self.operation_completed.emit(result)
            return result
        except Exception as ex:
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
            raise ValueError("No library selected for checkout")

        self.operation_started.emit("checkout")
        try:
            result = self.service.checkout(lib_id, branch=branch, auth=auth)
            self.refresh_status(lib_id)
            self.refresh_manifest(lib_id)
            self.operation_completed.emit(result)
            return result
        except Exception as ex:
            self.operation_failed.emit(ex)
            raise

    def list_branches(
        self,
        library_id: Optional[str] = None,
        remote: bool = True,
        auth: Optional[GitAuthConfig] = None,
    ) -> List[GitBranchInfo]:
        """List branches for the library."""
        lib_id = library_id or self._selected_library_id
        if not lib_id:
            return []
        return self.service.list_branches(lib_id)

    def delete_library(self, library_id: Optional[str] = None) -> bool:
        """Delete local library repository and its local overlay."""
        lib_id = library_id or self._selected_library_id
        if not lib_id:
            return False

        deleted = self.service.delete_library(lib_id)
        if self.overlay_manager:
            try:
                self.overlay_manager.delete_overlay(lib_id)
            except Exception:
                pass

        if lib_id == self._selected_library_id:
            self.select_library(None)
        self.load_libraries()
        return deleted

    @staticmethod
    def get_diagnostic_message(error: Exception) -> Tuple[str, str]:
        """Map a Git exception to user-friendly title and description."""
        if isinstance(error, GitDiagnosticError):
            title, desc = ERROR_MESSAGES.get(
                error.code,
                ("Git Error", str(error)),
            )
            if error.code == GitDiagnosticErrorCode.COMMAND_FAILED and error.message:
                return title, f"{desc}\n\nDetails: {error.message}"
            return title, desc
        return "Unexpected Error", str(error)
