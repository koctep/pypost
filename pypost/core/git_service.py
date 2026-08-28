"""Git operations service for collection libraries (PYPOST-1222).

Manages repository lifecycle operations including clone, fetch, pull, status,
branch management, working tree dirty guards, and manifest discovery.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

from pypost.core.git_auth import GitAuthEnvironmentManager, transient_git_auth_env
from pypost.core.library_manifest import MANIFEST_CANDIDATE_NAMES
from pypost.models.git_library import (
    GitAuthConfig,
    GitBranchInfo,
    GitDiagnosticError,
    GitDiagnosticErrorCode,
    GitOperationResult,
    GitOperationType,
    GitRepoStatus,
)

logger = logging.getLogger(__name__)

__all__ = ["GitLibraryService", "sanitize_git_url"]


def sanitize_git_url(url: str) -> str:
    """Mask embedded credentials in git remote URL for safe logging and diagnostics.

    Args:
        url: Raw Git remote URL.

    Returns:
        str: Sanitized URL with username/password masked.
    """
    if not url:
        return ""
    try:
        parts = urlsplit(url)
        if parts.username or parts.password:
            netloc = parts.netloc
            if "@" in netloc:
                _, host = netloc.rsplit("@", 1)
                netloc = f"***:***@{host}"
            return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        pass
    return url


class GitLibraryService:
    """Service providing Git repository lifecycle management and safety guards."""

    def __init__(
        self,
        base_dir: Optional[Path | str] = None,
        git_binary: str = "git",
        default_timeout: float = 30.0,
    ) -> None:
        """Initialize GitLibraryService.

        Args:
            base_dir: Directory where cloned libraries reside. Defaults to ~/.pypost/libraries.
            git_binary: Path or command name for git executable.
            default_timeout: Default timeout in seconds for network Git operations.
        """
        if base_dir is not None:
            self.base_dir = Path(base_dir).expanduser().resolve()
        else:
            self.base_dir = (Path.home() / ".pypost" / "libraries").resolve()

        self.git_binary = git_binary
        self.default_timeout = default_timeout
        self.auth_manager = GitAuthEnvironmentManager()

    def get_library_dir(self, library_id: str) -> Path:
        """Get the filesystem path for a specific collection library repository."""
        return self.base_dir / library_id

    def is_git_installed(self) -> bool:
        """Check whether git executable is available on system PATH."""
        return shutil.which(self.git_binary) is not None

    def _run_git(
        self,
        args: list[str],
        cwd: Optional[Path] = None,
        auth: Optional[GitAuthConfig] = None,
        timeout: Optional[float] = None,
    ) -> tuple[int, str, str]:
        """Execute a git command within an isolated environment.

        Args:
            args: Command line arguments to pass to git.
            cwd: Working directory for command execution.
            auth: Optional GitAuthConfig for transient credential injection.
            timeout: Timeout in seconds.

        Returns:
            tuple[int, str, str]: (returncode, stdout, stderr)

        Raises:
            GitDiagnosticError: If git executable is missing or operation times out.
        """
        t = timeout if timeout is not None else self.default_timeout
        cmd = [self.git_binary] + args

        with transient_git_auth_env(auth) as env:
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    errors="replace",
                    env=env,
                    timeout=t,
                )
                return proc.returncode, proc.stdout, proc.stderr
            except FileNotFoundError as exc:
                logger.error("git_binary_not_found binary=%s error=%s", self.git_binary, exc)
                raise GitDiagnosticError(
                    code=GitDiagnosticErrorCode.GIT_NOT_INSTALLED,
                    message=f"Git executable '{self.git_binary}' not found on system PATH",
                    repo_path=cwd,
                ) from exc
            except subprocess.TimeoutExpired as exc:
                subcommand = args[0] if args else "unknown"
                logger.error("git_command_timeout subcommand=%s timeout=%s", subcommand, t)
                raise GitDiagnosticError(
                    code=GitDiagnosticErrorCode.TIMEOUT,
                    message=f"Git command '{' '.join(args)}' timed out after {t}s",
                    repo_path=cwd,
                ) from exc

    def _classify_git_error(
        self,
        stderr: str,
        stdout: str,
        default_code: GitDiagnosticErrorCode = GitDiagnosticErrorCode.COMMAND_FAILED,
    ) -> GitDiagnosticErrorCode:
        """Classify git failure output into a structured diagnostic error code."""
        combined = f"{stdout}\n{stderr}".lower()
        if (
            "authentication failed" in combined
            or "permission denied (publickey)" in combined
            or "fatal: could not read username" in combined
            or "could not read password" in combined
            or "invalid username or password" in combined
        ):
            return GitDiagnosticErrorCode.AUTH_FAILED

        if (
            "repository not found" in combined
            or "remote error" in combined
            or "could not resolve host" in combined
            or "does not exist" in combined
            or "not found" in combined
        ):
            return GitDiagnosticErrorCode.REPO_NOT_FOUND

        if (
            "remote branch" in combined
            or "pathspec" in combined
            or "did not match any file" in combined
        ):
            return GitDiagnosticErrorCode.BRANCH_NOT_FOUND

        if (
            "automatic merge failed" in combined
            or "fix conflicts" in combined
            or "merge conflict" in combined
        ):
            return GitDiagnosticErrorCode.MERGE_CONFLICT

        if (
            "would be overwritten by merge" in combined
            or "your local changes to the following files would be overwritten" in combined
        ):
            return GitDiagnosticErrorCode.DIRTY_WORKING_TREE

        return default_code

    def check_dirty(self, library_id: str) -> tuple[bool, list[str]]:
        """Check whether repository working tree has uncommitted or untracked modifications.

        Args:
            library_id: Collection library identifier.

        Returns:
            tuple[bool, list[str]]: (is_dirty, list of modified/untracked file paths)
        """
        logger.debug("git_check_dirty_started library_id=%s", library_id)
        repo_dir = self.get_library_dir(library_id)
        if not repo_dir.exists() or not (repo_dir / ".git").exists():
            logger.debug("git_check_dirty_skipped_no_repo library_id=%s", library_id)
            return False, []

        ret, stdout, stderr = self._run_git(
            ["status", "--porcelain=v1", "-uall"],
            cwd=repo_dir,
            timeout=5.0,
        )
        if ret != 0:
            logger.warning("git_status_check_failed repo=%s stderr=%s", repo_dir, stderr)
            return True, ["<status_check_failed>"]

        dirty_files: list[str] = []
        for line in stdout.splitlines():
            line = line.rstrip()
            if not line:
                continue
            # First 2 chars are status codes, 3rd is space, 4th onwards is filepath
            filepath = line[3:].strip()
            if filepath:
                dirty_files.append(filepath)

        is_dirty = len(dirty_files) > 0
        if is_dirty:
            logger.debug(
                "git_dirty_tree_detected library_id=%s count=%d files=%s",
                library_id,
                len(dirty_files),
                dirty_files,
            )
        else:
            logger.debug("git_dirty_tree_clean library_id=%s", library_id)
        return is_dirty, dirty_files

    def discover_manifest(self, library_id: str) -> Optional[Path]:
        """Auto-discover library manifest file in the cloned repository root."""
        logger.debug("git_manifest_discovery_started library_id=%s", library_id)
        repo_dir = self.get_library_dir(library_id)
        if not repo_dir.exists():
            logger.debug("git_manifest_not_found library_id=%s reason=no_repo_dir", library_id)
            return None

        for name in MANIFEST_CANDIDATE_NAMES:
            candidate = repo_dir / name
            if candidate.is_file():
                logger.debug(
                    "git_manifest_discovered library_id=%s path=%s",
                    library_id,
                    candidate,
                )
                return candidate
        logger.debug("git_manifest_not_found library_id=%s", library_id)
        return None

    def clone(
        self,
        url: str,
        library_id: str,
        branch: Optional[str] = None,
        auth: Optional[GitAuthConfig] = None,
        force: bool = False,
        timeout: Optional[float] = None,
    ) -> GitOperationResult:
        """Clone a remote repository into the library storage directory.

        Args:
            url: Remote repository URL.
            library_id: Unique library identifier.
            branch: Optional initial branch to checkout.
            auth: Optional authentication configuration.
            force: If True, overwrite existing destination directory.
            timeout: Optional operation timeout in seconds.

        Returns:
            GitOperationResult: Structured operation result.

        Raises:
            GitDiagnosticError: If destination is not empty, clone fails, or auth fails.
        """
        dest_dir = self.get_library_dir(library_id)
        sanitized_url = sanitize_git_url(url)
        logger.info(
            "git_clone_started library_id=%s url=%s branch=%s force=%s",
            library_id,
            sanitized_url,
            branch,
            force,
        )

        if dest_dir.exists() and any(dest_dir.iterdir()):
            if not force:
                logger.warning("git_clone_destination_not_empty path=%s", dest_dir)
                raise GitDiagnosticError(
                    code=GitDiagnosticErrorCode.DESTINATION_NOT_EMPTY,
                    message=f"Destination directory '{dest_dir}' already exists and is not empty",
                    repo_path=dest_dir,
                )
            logger.info("git_clone_force_clearing_destination path=%s", dest_dir)
            shutil.rmtree(dest_dir, ignore_errors=True)

        dest_dir.parent.mkdir(parents=True, exist_ok=True)

        args = ["clone", url, str(dest_dir)]
        if branch:
            args.extend(["-b", branch])

        ret, stdout, stderr = self._run_git(
            args,
            cwd=None,
            auth=auth,
            timeout=timeout or self.default_timeout,
        )

        if ret != 0:
            # Clean up destination directory if clone failed partially
            if dest_dir.exists() and not any(dest_dir.iterdir()):
                shutil.rmtree(dest_dir, ignore_errors=True)

            err_code = self._classify_git_error(
                stderr, stdout, default_code=GitDiagnosticErrorCode.COMMAND_FAILED
            )
            logger.error(
                "git_clone_failed url=%s code=%s stderr=%s",
                sanitized_url,
                err_code,
                stderr,
            )
            raise GitDiagnosticError(
                code=err_code,
                message=f"Git clone failed: {stderr.strip() or stdout.strip()}",
                repo_path=dest_dir,
                details={"stdout": stdout, "stderr": stderr, "url": sanitized_url},
            )

        manifest_path = self.discover_manifest(library_id)
        logger.info(
            "git_clone_success library_id=%s path=%s manifest=%s",
            library_id,
            dest_dir,
            manifest_path,
        )

        return GitOperationResult(
            success=True,
            operation=GitOperationType.CLONE,
            library_id=library_id,
            repo_path=dest_dir,
            output=stdout + stderr,
            manifest_path=manifest_path,
        )

    def fetch(
        self,
        library_id: str,
        remote: str = "origin",
        auth: Optional[GitAuthConfig] = None,
        timeout: Optional[float] = None,
    ) -> GitOperationResult:
        """Fetch references from remote repository.

        Args:
            library_id: Collection library identifier.
            remote: Remote name (default 'origin').
            auth: Optional authentication configuration.
            timeout: Optional operation timeout in seconds.

        Returns:
            GitOperationResult: Structured operation result.

        Raises:
            GitDiagnosticError: If fetch fails.
        """
        logger.info("git_fetch_started library_id=%s remote=%s", library_id, remote)
        repo_dir = self.get_library_dir(library_id)
        ret, stdout, stderr = self._run_git(
            ["fetch", remote],
            cwd=repo_dir,
            auth=auth,
            timeout=timeout or self.default_timeout,
        )

        if ret != 0:
            err_code = self._classify_git_error(stderr, stdout)
            logger.error(
                "git_fetch_failed library_id=%s code=%s stderr=%s",
                library_id,
                err_code,
                stderr,
            )
            raise GitDiagnosticError(
                code=err_code,
                message=f"Git fetch failed: {stderr.strip() or stdout.strip()}",
                repo_path=repo_dir,
                details={"stdout": stdout, "stderr": stderr},
            )

        logger.info("git_fetch_success library_id=%s remote=%s", library_id, remote)
        return GitOperationResult(
            success=True,
            operation=GitOperationType.FETCH,
            library_id=library_id,
            repo_path=repo_dir,
            output=stdout + stderr,
        )

    def pull(
        self,
        library_id: str,
        remote: str = "origin",
        branch: Optional[str] = None,
        auth: Optional[GitAuthConfig] = None,
        force: bool = False,
        timeout: Optional[float] = None,
    ) -> GitOperationResult:
        """Pull updates from remote repository with dirty check guard.

        Args:
            library_id: Collection library identifier.
            remote: Remote name (default 'origin').
            branch: Optional branch name to pull.
            auth: Optional authentication configuration.
            force: If True, bypasses dirty tree safety guard.
            timeout: Optional operation timeout in seconds.

        Returns:
            GitOperationResult: Structured operation result.

        Raises:
            GitDiagnosticError: If working tree is dirty or pull fails.
        """
        logger.info(
            "git_pull_started library_id=%s remote=%s branch=%s force=%s",
            library_id,
            remote,
            branch,
            force,
        )
        repo_dir = self.get_library_dir(library_id)

        # Pre-pull dirty check guard
        if not force:
            is_dirty, dirty_files = self.check_dirty(library_id)
            if is_dirty:
                logger.warning(
                    "git_pull_blocked_dirty_tree library_id=%s files=%s",
                    library_id,
                    dirty_files,
                )
                raise GitDiagnosticError(
                    code=GitDiagnosticErrorCode.DIRTY_WORKING_TREE,
                    message="Cannot pull updates into a dirty working tree",
                    repo_path=repo_dir,
                    details={"dirty_files": dirty_files},
                )

        args = ["pull", remote]
        if branch:
            args.append(branch)

        ret, stdout, stderr = self._run_git(
            args,
            cwd=repo_dir,
            auth=auth,
            timeout=timeout or self.default_timeout,
        )

        if ret != 0:
            err_code = self._classify_git_error(stderr, stdout)
            logger.error(
                "git_pull_failed library_id=%s code=%s stderr=%s",
                library_id,
                err_code,
                stderr,
            )
            raise GitDiagnosticError(
                code=err_code,
                message=f"Git pull failed: {stderr.strip() or stdout.strip()}",
                repo_path=repo_dir,
                details={"stdout": stdout, "stderr": stderr},
            )

        logger.info("git_pull_success library_id=%s remote=%s", library_id, remote)
        return GitOperationResult(
            success=True,
            operation=GitOperationType.PULL,
            library_id=library_id,
            repo_path=repo_dir,
            output=stdout + stderr,
        )

    def status(self, library_id: str, timeout: Optional[float] = None) -> GitRepoStatus:
        """Inspect repository status, active branch, commit details, and sync state.

        Args:
            library_id: Collection library identifier.
            timeout: Optional operation timeout in seconds.

        Returns:
            GitRepoStatus: Snapshot of repository status.
        """
        logger.debug("git_status_started library_id=%s", library_id)
        repo_dir = self.get_library_dir(library_id)

        # Get current branch
        _, stdout_br, _ = self._run_git(
            ["branch", "--show-current"], cwd=repo_dir, timeout=5.0
        )
        current_branch = stdout_br.strip() or None

        if not current_branch:
            _, stdout_short, _ = self._run_git(
                ["rev-parse", "--short", "HEAD"], cwd=repo_dir, timeout=5.0
            )
            if stdout_short.strip():
                current_branch = f"HEAD ({stdout_short.strip()})"

        # Get latest commit hash
        _, stdout_hash, _ = self._run_git(
            ["rev-parse", "HEAD"], cwd=repo_dir, timeout=5.0
        )
        commit_hash = stdout_hash.strip() or None

        # Get latest commit message
        _, stdout_msg, _ = self._run_git(
            ["log", "-1", "--pretty=format:%s"], cwd=repo_dir, timeout=5.0
        )
        commit_message = stdout_msg.strip() or None

        # Get upstream tracking branch
        ret_track, stdout_track, _ = self._run_git(
            ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
            cwd=repo_dir,
            timeout=5.0,
        )
        tracking_branch = (
            stdout_track.strip() if ret_track == 0 and stdout_track.strip() else None
        )

        # Calculate ahead/behind counts
        ahead_count = 0
        behind_count = 0
        if tracking_branch:
            ret_cnt, stdout_cnt, _ = self._run_git(
                ["rev-list", "--left-right", "--count", "HEAD...@{u}"],
                cwd=repo_dir,
                timeout=5.0,
            )
            if ret_cnt == 0 and stdout_cnt.strip():
                parts = stdout_cnt.strip().split()
                if len(parts) >= 2:
                    try:
                        ahead_count = int(parts[0])
                        behind_count = int(parts[1])
                    except ValueError:
                        pass

        # Dirty & untracked status
        _, stdout_status, _ = self._run_git(
            ["status", "--porcelain=v1", "-uall"],
            cwd=repo_dir,
            timeout=5.0,
        )
        dirty_files: list[str] = []
        untracked_files: list[str] = []
        for line in stdout_status.splitlines():
            line = line.rstrip()
            if not line:
                continue
            prefix = line[:2]
            filepath = line[3:].strip()
            if prefix == "??":
                untracked_files.append(filepath)
                dirty_files.append(filepath)
            elif filepath:
                dirty_files.append(filepath)

        is_clean = len(dirty_files) == 0

        logger.debug(
            "git_status_completed library_id=%s branch=%s clean=%s "
            "ahead=%d behind=%d dirty_count=%d untracked_count=%d",
            library_id,
            current_branch,
            is_clean,
            ahead_count,
            behind_count,
            len(dirty_files),
            len(untracked_files),
        )

        return GitRepoStatus(
            library_id=library_id,
            repo_path=repo_dir,
            current_branch=current_branch,
            commit_hash=commit_hash,
            commit_message=commit_message,
            tracking_branch=tracking_branch,
            ahead_count=ahead_count,
            behind_count=behind_count,
            is_clean=is_clean,
            dirty_files=dirty_files,
            untracked_files=untracked_files,
        )

    def list_branches(
        self, library_id: str, timeout: Optional[float] = None
    ) -> list[GitBranchInfo]:
        """List all local and remote tracking branches for the library.

        Args:
            library_id: Collection library identifier.
            timeout: Optional operation timeout in seconds.

        Returns:
            list[GitBranchInfo]: List of branch metadata objects.
        """
        logger.debug("git_list_branches_started library_id=%s", library_id)
        repo_dir = self.get_library_dir(library_id)
        ret, stdout, stderr = self._run_git(
            ["branch", "--all", "--format=%(refname)|%(refname:short)|%(HEAD)|%(objectname)"],
            cwd=repo_dir,
            timeout=timeout or 5.0,
        )
        if ret != 0:
            logger.warning("git_list_branches_failed library_id=%s stderr=%s", library_id, stderr)
            return []

        branches: list[GitBranchInfo] = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            if len(parts) >= 4:
                refname, short_name, head_marker, obj_name = (
                    parts[0],
                    parts[1],
                    parts[2],
                    parts[3],
                )
                is_current = head_marker.strip() == "*"
                is_remote = refname.startswith("refs/remotes/")
                remote_name: Optional[str] = None
                if is_remote:
                    sub = refname[len("refs/remotes/"):]
                    remote_name = sub.split("/")[0] if "/" in sub else None

                branches.append(
                    GitBranchInfo(
                        name=refname,
                        short_name=short_name,
                        is_remote=is_remote,
                        is_current=is_current,
                        commit_hash=obj_name,
                        remote_name=remote_name,
                    )
                )

        logger.debug(
            "git_list_branches_completed library_id=%s count=%d",
            library_id,
            len(branches),
        )
        return branches

    def checkout(
        self,
        library_id: str,
        branch: str,
        create: bool = False,
        auth: Optional[GitAuthConfig] = None,
        force: bool = False,
        timeout: Optional[float] = None,
    ) -> GitOperationResult:
        """Checkout a branch with dirty tree safety guard.

        Args:
            library_id: Collection library identifier.
            branch: Branch name to checkout.
            create: If True, creates a new branch (-b).
            auth: Optional authentication configuration.
            force: If True, bypasses dirty check guard.
            timeout: Optional operation timeout in seconds.

        Returns:
            GitOperationResult: Structured operation result.

        Raises:
            GitDiagnosticError: If working tree is dirty or checkout fails.
        """
        logger.info(
            "git_checkout_started library_id=%s branch=%s create=%s force=%s",
            library_id,
            branch,
            create,
            force,
        )
        repo_dir = self.get_library_dir(library_id)

        # Pre-checkout dirty check guard
        if not force:
            is_dirty, dirty_files = self.check_dirty(library_id)
            if is_dirty:
                logger.warning(
                    "git_checkout_blocked_dirty_tree library_id=%s files=%s",
                    library_id,
                    dirty_files,
                )
                raise GitDiagnosticError(
                    code=GitDiagnosticErrorCode.DIRTY_WORKING_TREE,
                    message="Cannot checkout branch in a dirty working tree",
                    repo_path=repo_dir,
                    details={"dirty_files": dirty_files},
                )

        args = ["checkout"]
        if create:
            args.extend(["-b", branch])
        else:
            args.append(branch)

        ret, stdout, stderr = self._run_git(
            args,
            cwd=repo_dir,
            auth=auth,
            timeout=timeout or 10.0,
        )

        if ret != 0:
            err_code = self._classify_git_error(stderr, stdout)
            logger.error(
                "git_checkout_failed library_id=%s branch=%s code=%s stderr=%s",
                library_id,
                branch,
                err_code,
                stderr,
            )
            raise GitDiagnosticError(
                code=err_code,
                message=f"Git checkout failed: {stderr.strip() or stdout.strip()}",
                repo_path=repo_dir,
                details={"stdout": stdout, "stderr": stderr},
            )

        logger.info("git_checkout_success library_id=%s branch=%s", library_id, branch)
        return GitOperationResult(
            success=True,
            operation=GitOperationType.CHECKOUT,
            library_id=library_id,
            repo_path=repo_dir,
            current_branch=branch,
            output=stdout + stderr,
        )

    def delete_library(self, library_id: str) -> bool:
        """Delete a local collection library directory from disk.

        Args:
            library_id: Collection library identifier.

        Returns:
            bool: True if directory existed and was deleted, False otherwise.
        """
        repo_dir = self.get_library_dir(library_id)
        if repo_dir.exists():
            shutil.rmtree(repo_dir, ignore_errors=True)
            logger.info("git_library_deleted library_id=%s path=%s", library_id, repo_dir)
            return True
        logger.debug(
            "git_library_delete_skipped_not_found library_id=%s path=%s",
            library_id,
            repo_dir,
        )
        return False
