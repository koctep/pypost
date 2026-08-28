"""Git domain models and diagnostic errors for collection libraries (PYPOST-1222).

Defines configuration models for hybrid authentication, repository status snapshots,
branch descriptors, operation results, and structured diagnostic errors.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class GitAuthMode(str, Enum):
    """Supported authentication strategies for remote Git operations."""

    SSH_AGENT = "ssh_agent"
    PAT = "pat"
    CUSTOM_SSH_KEY = "custom_ssh_key"


class GitAuthConfig(BaseModel):
    """Authentication configuration for Git remote interactions."""

    model_config = ConfigDict(populate_by_name=True)

    mode: GitAuthMode = GitAuthMode.SSH_AGENT
    username: Optional[str] = None
    token: Optional[str] = None
    key_path: Optional[str] = None
    passphrase: Optional[str] = None
    strict_host_checking: bool = True

    @field_validator("key_path")
    @classmethod
    def validate_key_path(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            return None
        return v


class GitBranchInfo(BaseModel):
    """Metadata describing a local or remote Git branch."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    short_name: str
    is_remote: bool = False
    is_current: bool = False
    commit_hash: str = ""
    remote_name: Optional[str] = None


class GitRepoStatus(BaseModel):
    """Snapshot of a local collection library's Git working tree and sync state."""

    model_config = ConfigDict(populate_by_name=True)

    library_id: str
    repo_path: Path
    current_branch: Optional[str] = None
    commit_hash: Optional[str] = None
    commit_message: Optional[str] = None
    tracking_branch: Optional[str] = None
    ahead_count: int = 0
    behind_count: int = 0
    is_clean: bool = True
    dirty_files: List[str] = Field(default_factory=list)
    untracked_files: List[str] = Field(default_factory=list)


class GitOperationType(str, Enum):
    """Type of Git lifecycle operation executed."""

    CLONE = "clone"
    FETCH = "fetch"
    PULL = "pull"
    CHECKOUT = "checkout"
    STATUS = "status"
    BRANCH_LIST = "branch_list"


class GitDiagnosticErrorCode(str, Enum):
    """Standardized failure categories for Git operations."""

    AUTH_FAILED = "AUTH_FAILED"
    DIRTY_WORKING_TREE = "DIRTY_WORKING_TREE"
    REPO_NOT_FOUND = "REPO_NOT_FOUND"
    BRANCH_NOT_FOUND = "BRANCH_NOT_FOUND"
    MERGE_CONFLICT = "MERGE_CONFLICT"
    GIT_NOT_INSTALLED = "GIT_NOT_INSTALLED"
    DESTINATION_NOT_EMPTY = "DESTINATION_NOT_EMPTY"
    TIMEOUT = "TIMEOUT"
    COMMAND_FAILED = "COMMAND_FAILED"


class GitOperationResult(BaseModel):
    """Structured result returned by GitLibraryService operations."""

    model_config = ConfigDict(populate_by_name=True)

    success: bool
    operation: GitOperationType
    library_id: Optional[str] = None
    repo_path: Optional[Path] = None
    current_branch: Optional[str] = None
    output: str = ""
    error_code: Optional[GitDiagnosticErrorCode] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    manifest_path: Optional[Path] = None


class GitDiagnosticError(Exception):
    """Structured diagnostic error raised on Git operation failures."""

    def __init__(
        self,
        code: GitDiagnosticErrorCode | str,
        message: str,
        repo_path: Optional[Path | str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.code = (
            code if isinstance(code, GitDiagnosticErrorCode)
            else GitDiagnosticErrorCode(code) if code in GitDiagnosticErrorCode.__members__
            else GitDiagnosticErrorCode.COMMAND_FAILED
        )
        self.message = message
        self.repo_path = Path(repo_path) if repo_path else None
        self.details = details or {}
        repo_suffix = f" (repo: {repo_path})" if repo_path else ""
        super().__init__(f"[{self.code.value}] {message}{repo_suffix}")
