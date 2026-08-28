"""Red failing repro tests for GitLibraryService and Hybrid Auth (PYPOST-1222).

Tests the target contract before Step 4 implementation:
- Git domain models (GitAuthConfig, GitRepoStatus, GitBranchInfo, GitOperationResult, etc.)
- Transient hybrid auth environment builder (SSH agent, PAT, custom SSH key)
- GitLibraryService clone into isolated base directory
- Destination directory guards against clobbering existing directories
- Pre-pull and pre-checkout dirty check guards blocking operations when modifications exist
- Clean pull fast-forward updates
- Remote fetch & sync status inspection (ahead/behind counts, commit hash, commit message)
- Branch listing and branch checkout
- Post-clone automatic manifest discovery (pypost-library.yaml / .json)
- Configurable base directory & hermetic test isolation
- Structured Git diagnostic errors (AUTH_FAILED, REPO_NOT_FOUND, DIRTY_WORKING_TREE, etc.)
"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

import pytest

from pypost.core.git_auth import (
    GitAuthEnvironmentManager,
    transient_git_auth_env,
)
from pypost.core.git_service import GitLibraryService, sanitize_git_url
from pypost.models.git_library import (
    GitAuthConfig,
    GitAuthMode,
    GitBranchInfo,
    GitDiagnosticError,
    GitDiagnosticErrorCode,
    GitOperationResult,
    GitOperationType,
    GitRepoStatus,
)

pytestmark = pytest.mark.timeout(30)


# ============================================================================
# Helper Fixtures & Utilities for Local Git Repositories
# ============================================================================


def _run_git_cmd(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Helper to run git commands during test fixture setup."""
    env = dict(os.environ)
    env["GIT_AUTHOR_NAME"] = "PyPost Test"
    env["GIT_AUTHOR_EMAIL"] = "test@pypost.local"
    env["GIT_COMMITTER_NAME"] = "PyPost Test"
    env["GIT_COMMITTER_EMAIL"] = "test@pypost.local"
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )


@pytest.fixture
def sample_remote_git_repo(tmp_path: Path) -> Path:
    """Creates a local origin Git repository with an initial commit, a feature branch,
    and a pypost-library.yaml manifest file to serve as a remote origin for tests.
    """
    origin_dir = tmp_path / "remote_origin_repo"
    origin_dir.mkdir(parents=True)

    _run_git_cmd(["init", "-b", "main"], cwd=origin_dir)

    manifest_file = origin_dir / "pypost-library.yaml"
    manifest_file.write_text(
        """id: sample-payments-lib
name: Sample Payments Library
version: 1.0.0
collections:
  - collections/payments.yaml
""",
        encoding="utf-8",
    )

    collections_dir = origin_dir / "collections"
    collections_dir.mkdir(parents=True)
    (collections_dir / "payments.yaml").write_text(
        "id: col-payments\nname: Payments\nrequests: []\n",
        encoding="utf-8",
    )

    _run_git_cmd(["add", "."], cwd=origin_dir)
    _run_git_cmd(["commit", "-m", "Initial library commit"], cwd=origin_dir)

    # Create a feature branch
    _run_git_cmd(["checkout", "-b", "feature/v2-endpoints"], cwd=origin_dir)
    (collections_dir / "v2_payments.yaml").write_text(
        "id: col-payments-v2\nname: Payments V2\nrequests: []\n",
        encoding="utf-8",
    )
    _run_git_cmd(["add", "."], cwd=origin_dir)
    _run_git_cmd(["commit", "-m", "Add v2 payments endpoints"], cwd=origin_dir)

    # Return to main branch
    _run_git_cmd(["checkout", "main"], cwd=origin_dir)

    return origin_dir


# ============================================================================
# 1. Domain Models Validation Tests
# ============================================================================


def test_git_auth_config_modes_and_validation():
    """Verify GitAuthConfig instantiation, defaults, and validation for all auth modes."""
    # 1. SSH Agent mode (default)
    default_config = GitAuthConfig()
    assert default_config.mode == GitAuthMode.SSH_AGENT
    assert default_config.username is None
    assert default_config.token is None
    assert default_config.key_path is None
    assert default_config.strict_host_checking is True

    # 2. PAT mode
    pat_config = GitAuthConfig(
        mode=GitAuthMode.PAT,
        username="oauth2",
        token="ghp_test_token_1234567890",
    )
    assert pat_config.mode == GitAuthMode.PAT
    assert pat_config.username == "oauth2"
    assert pat_config.token == "ghp_test_token_1234567890"

    # 3. Custom SSH Key mode
    ssh_config = GitAuthConfig(
        mode=GitAuthMode.CUSTOM_SSH_KEY,
        key_path="/path/to/id_ed25519_custom",
        passphrase="secret_passphrase",
        strict_host_checking=False,
    )
    assert ssh_config.mode == GitAuthMode.CUSTOM_SSH_KEY
    assert ssh_config.key_path == "/path/to/id_ed25519_custom"
    assert ssh_config.passphrase == "secret_passphrase"
    assert ssh_config.strict_host_checking is False

    # 4. Whitespace key path normalization
    ws_config = GitAuthConfig(key_path="   ")
    assert ws_config.key_path is None


def test_git_repo_status_and_branch_info_models(tmp_path: Path):
    """Verify GitRepoStatus and GitBranchInfo model instantiation and defaults."""
    branch = GitBranchInfo(
        name="refs/heads/main",
        short_name="main",
        is_remote=False,
        is_current=True,
        commit_hash="abc1234def567890",
        remote_name=None,
    )
    assert branch.name == "refs/heads/main"
    assert branch.short_name == "main"
    assert branch.is_current is True
    assert branch.is_remote is False

    status = GitRepoStatus(
        library_id="lib-test-1",
        repo_path=tmp_path / "lib-test-1",
        current_branch="main",
        commit_hash="abc1234def567890",
        commit_message="Add initial endpoints",
        tracking_branch="origin/main",
        ahead_count=1,
        behind_count=0,
        is_clean=False,
        dirty_files=["collections/billing.yaml"],
        untracked_files=["temp_scratch.txt"],
    )
    assert status.library_id == "lib-test-1"
    assert status.is_clean is False
    assert len(status.dirty_files) == 1
    assert len(status.untracked_files) == 1
    assert status.ahead_count == 1
    assert status.behind_count == 0


def test_git_diagnostic_error_and_codes():
    """Verify GitDiagnosticError structure, error codes, and message formatting."""
    err = GitDiagnosticError(
        code=GitDiagnosticErrorCode.DIRTY_WORKING_TREE,
        message="Cannot pull updates into a dirty working tree",
        repo_path="/home/user/.pypost/libraries/lib-1",
        details={"dirty_files": ["col1.yaml"]},
    )
    assert err.code == GitDiagnosticErrorCode.DIRTY_WORKING_TREE
    assert "DIRTY_WORKING_TREE" in str(err)
    assert err.details["dirty_files"] == ["col1.yaml"]
    assert isinstance(err, Exception)


# ============================================================================
# 2. Transient Hybrid Authentication Provider Tests
# ============================================================================


def test_auth_env_manager_ssh_agent_mode():
    """SSH Agent mode preserves ambient SSH environment and sets non-interactive guard."""
    auth_mgr = GitAuthEnvironmentManager()
    config = GitAuthConfig(mode=GitAuthMode.SSH_AGENT)

    env, cleanup = auth_mgr.build_env(config)
    try:
        assert env.get("GIT_TERMINAL_PROMPT") == "0"
        # In SSH agent mode, GIT_ASKPASS and GIT_SSH_COMMAND should not be overridden
        assert "GIT_ASKPASS" not in env or env.get("GIT_ASKPASS") is None
        assert "GIT_SSH_COMMAND" not in env or env.get("GIT_SSH_COMMAND") is None
    finally:
        if cleanup:
            cleanup()


def test_auth_env_manager_pat_mode():
    """PAT mode sets GIT_ASKPASS helper and injects token via transient environment."""
    auth_mgr = GitAuthEnvironmentManager()
    config = GitAuthConfig(
        mode=GitAuthMode.PAT,
        username="git_user",
        token="pat_secret_token_value_999",
    )

    env, cleanup = auth_mgr.build_env(config)
    try:
        assert env.get("GIT_TERMINAL_PROMPT") == "0"
        assert "GIT_ASKPASS" in env
        askpass_path = env["GIT_ASKPASS"]
        assert os.path.exists(askpass_path)
        assert env.get("PYPOST_GIT_ASKPASS_TOKEN") == "pat_secret_token_value_999"
        assert env.get("PYPOST_GIT_ASKPASS_USERNAME") == "git_user"
    finally:
        if cleanup:
            cleanup()

    # Verify askpass temporary file is cleaned up after cleanup callback
    assert not os.path.exists(askpass_path)


def test_auth_env_manager_custom_ssh_key_mode(tmp_path: Path):
    """Custom SSH key mode sets GIT_SSH_COMMAND with identity key and options."""
    key_file = tmp_path / "test_id_ed25519"
    key_file.write_text("DUMMY PRIVATE KEY", encoding="utf-8")

    auth_mgr = GitAuthEnvironmentManager()
    config = GitAuthConfig(
        mode=GitAuthMode.CUSTOM_SSH_KEY,
        key_path=str(key_file),
        passphrase="key_passphrase_123",
        strict_host_checking=False,
    )

    env, cleanup = auth_mgr.build_env(config)
    try:
        assert env.get("GIT_TERMINAL_PROMPT") == "0"
        ssh_cmd = env.get("GIT_SSH_COMMAND", "")
        assert "-i" in ssh_cmd
        assert str(key_file) in ssh_cmd
        assert "IdentitiesOnly=yes" in ssh_cmd
        assert (
            "StrictHostKeyChecking=accept-new" in ssh_cmd
            or "StrictHostKeyChecking=no" in ssh_cmd
        )
    finally:
        if cleanup:
            cleanup()


def test_transient_git_auth_env_context_manager():
    """transient_git_auth_env context manager properly generates and cleans up environment."""
    config = GitAuthConfig(
        mode=GitAuthMode.PAT,
        token="context_pat_token",
    )

    askpass_script: Optional[str] = None
    with transient_git_auth_env(config) as env:
        assert env.get("GIT_TERMINAL_PROMPT") == "0"
        askpass_script = env.get("GIT_ASKPASS")
        assert askpass_script is not None
        assert os.path.exists(askpass_script)

    # After exiting context manager, ephemeral askpass script is removed
    assert askpass_script is not None
    assert not os.path.exists(askpass_script)


# ============================================================================
# 3. GitLibraryService Clone & Destination Guards Tests
# ============================================================================


def test_git_library_service_clone_and_manifest_discovery(
    tmp_path: Path,
    sample_remote_git_repo: Path,
):
    """Clone remote repository into isolated base directory and auto-discover manifest."""
    base_dir = tmp_path / "pypost_libraries"
    service = GitLibraryService(base_dir=base_dir)

    result = service.clone(
        url=str(sample_remote_git_repo),
        library_id="lib-payments-clone",
    )

    assert result.success is True
    assert result.operation == GitOperationType.CLONE
    assert result.library_id == "lib-payments-clone"
    assert result.repo_path == base_dir / "lib-payments-clone"
    assert (base_dir / "lib-payments-clone" / ".git").exists()
    assert (base_dir / "lib-payments-clone" / "pypost-library.yaml").exists()

    # Verify manifest was auto-discovered
    assert result.manifest_path == base_dir / "lib-payments-clone" / "pypost-library.yaml"


def test_git_library_service_clone_specific_branch(
    tmp_path: Path,
    sample_remote_git_repo: Path,
):
    """Clone remote repository with specific initial branch."""
    base_dir = tmp_path / "pypost_libraries"
    service = GitLibraryService(base_dir=base_dir)

    result = service.clone(
        url=str(sample_remote_git_repo),
        library_id="lib-payments-branch",
        branch="feature/v2-endpoints",
    )

    assert result.success is True
    repo_status = service.status("lib-payments-branch")
    assert repo_status.current_branch == "feature/v2-endpoints"
    assert (base_dir / "lib-payments-branch" / "collections" / "v2_payments.yaml").exists()


def test_git_library_service_clone_rejects_non_empty_destination(
    tmp_path: Path,
    sample_remote_git_repo: Path,
):
    """Clone refuses to overwrite existing non-empty directory unless forced."""
    base_dir = tmp_path / "pypost_libraries"
    dest_dir = base_dir / "lib-existing"
    dest_dir.mkdir(parents=True)
    (dest_dir / "untracked_file.txt").write_text("existing contents", encoding="utf-8")

    service = GitLibraryService(base_dir=base_dir)

    # Clone without force should fail
    with pytest.raises(GitDiagnosticError) as exc_info:
        service.clone(
            url=str(sample_remote_git_repo),
            library_id="lib-existing",
            force=False,
        )

    assert exc_info.value.code == GitDiagnosticErrorCode.DESTINATION_NOT_EMPTY


# ============================================================================
# 4. Dirty Check Guard & Safe Pull Tests
# ============================================================================


def test_git_library_service_check_dirty_detection(
    tmp_path: Path,
    sample_remote_git_repo: Path,
):
    """check_dirty detects unstaged, staged, and untracked modifications."""
    base_dir = tmp_path / "pypost_libraries"
    service = GitLibraryService(base_dir=base_dir)
    service.clone(url=str(sample_remote_git_repo), library_id="lib-dirty-check")

    # 1. Clean working tree initially
    is_dirty, dirty_files = service.check_dirty("lib-dirty-check")
    assert is_dirty is False
    assert dirty_files == []

    # 2. Modify an existing tracked file (unstaged)
    tracked_file = base_dir / "lib-dirty-check" / "pypost-library.yaml"
    tracked_file.write_text("modified content", encoding="utf-8")

    is_dirty, dirty_files = service.check_dirty("lib-dirty-check")
    assert is_dirty is True
    assert any("pypost-library.yaml" in f for f in dirty_files)

    # 3. Stage the change
    _run_git_cmd(["add", "pypost-library.yaml"], cwd=base_dir / "lib-dirty-check")
    is_dirty, dirty_files = service.check_dirty("lib-dirty-check")
    assert is_dirty is True

    # 4. Add an untracked file
    untracked = base_dir / "lib-dirty-check" / "collections" / "new_untracked.yaml"
    untracked.write_text("name: Untracked", encoding="utf-8")

    is_dirty, dirty_files = service.check_dirty("lib-dirty-check")
    assert is_dirty is True
    assert any("new_untracked.yaml" in f for f in dirty_files)


def test_git_library_service_pull_blocked_by_dirty_guard(
    tmp_path: Path,
    sample_remote_git_repo: Path,
):
    """Pull is blocked and raises DIRTY_WORKING_TREE error when local edits exist."""
    base_dir = tmp_path / "pypost_libraries"
    service = GitLibraryService(base_dir=base_dir)
    service.clone(url=str(sample_remote_git_repo), library_id="lib-pull-guard")

    # Introduce local uncommitted edit
    tracked_file = base_dir / "lib-pull-guard" / "collections" / "payments.yaml"
    tracked_file.write_text("modified local payments content", encoding="utf-8")

    # Attempt pull without force -> MUST raise DIRTY_WORKING_TREE
    with pytest.raises(GitDiagnosticError) as exc_info:
        service.pull("lib-pull-guard")

    assert exc_info.value.code == GitDiagnosticErrorCode.DIRTY_WORKING_TREE
    assert "payments.yaml" in str(exc_info.value.details)


def test_git_library_service_clean_pull_fast_forward(
    tmp_path: Path,
    sample_remote_git_repo: Path,
):
    """Clean working copy successfully pulls upstream commits and fast-forwards."""
    base_dir = tmp_path / "pypost_libraries"
    service = GitLibraryService(base_dir=base_dir)
    service.clone(url=str(sample_remote_git_repo), library_id="lib-clean-pull")

    # Push a new commit to the origin repository
    (sample_remote_git_repo / "collections" / "refunds.yaml").write_text(
        "id: col-refunds\nname: Refunds\nrequests: []\n",
        encoding="utf-8",
    )
    _run_git_cmd(["add", "."], cwd=sample_remote_git_repo)
    _run_git_cmd(["commit", "-m", "Add refunds collection upstream"], cwd=sample_remote_git_repo)

    # Pull changes
    result = service.pull("lib-clean-pull")
    assert result.success is True
    assert result.operation == GitOperationType.PULL

    # Verify new file exists in local clone
    assert (base_dir / "lib-clean-pull" / "collections" / "refunds.yaml").exists()

    # Status shows clean state and matches latest commit
    status = service.status("lib-clean-pull")
    assert status.is_clean is True
    assert status.behind_count == 0


# ============================================================================
# 5. Fetch, Status Inspection, and Branch Management Tests
# ============================================================================


def test_git_library_service_fetch_and_status_inspection(
    tmp_path: Path,
    sample_remote_git_repo: Path,
):
    """Fetch updates remote refs and status inspection calculates behind count correctly."""
    base_dir = tmp_path / "pypost_libraries"
    service = GitLibraryService(base_dir=base_dir)
    service.clone(url=str(sample_remote_git_repo), library_id="lib-sync-test")

    # Add commit to origin
    (sample_remote_git_repo / "new_remote_note.txt").write_text("remote update", encoding="utf-8")
    _run_git_cmd(["add", "."], cwd=sample_remote_git_repo)
    _run_git_cmd(["commit", "-m", "Remote upstream commit"], cwd=sample_remote_git_repo)

    # Fetch without pulling
    fetch_result = service.fetch("lib-sync-test")
    assert fetch_result.success is True
    assert fetch_result.operation == GitOperationType.FETCH

    # Check status: behind_count should now be 1
    status = service.status("lib-sync-test")
    assert status.behind_count == 1
    assert status.ahead_count == 0
    assert status.current_branch == "main"
    assert status.is_clean is True


def test_git_library_service_list_branches_and_checkout(
    tmp_path: Path,
    sample_remote_git_repo: Path,
):
    """list_branches returns local and remote branches; checkout switches branches."""
    base_dir = tmp_path / "pypost_libraries"
    service = GitLibraryService(base_dir=base_dir)
    service.clone(url=str(sample_remote_git_repo), library_id="lib-branches-test")

    branches = service.list_branches("lib-branches-test")
    branch_names = [b.short_name for b in branches]
    assert "main" in branch_names
    assert any(
        "feature/v2-endpoints" in b.short_name or "feature/v2-endpoints" in b.name
        for b in branches
    )

    # Checkout remote tracking branch
    checkout_result = service.checkout(
        "lib-branches-test",
        branch="feature/v2-endpoints",
    )
    assert checkout_result.success is True
    assert checkout_result.operation == GitOperationType.CHECKOUT

    status = service.status("lib-branches-test")
    assert status.current_branch == "feature/v2-endpoints"
    assert (base_dir / "lib-branches-test" / "collections" / "v2_payments.yaml").exists()


def test_git_library_service_checkout_guard_blocks_on_dirty(
    tmp_path: Path,
    sample_remote_git_repo: Path,
):
    """Checkout is blocked by dirty check guard when local uncommitted changes exist."""
    base_dir = tmp_path / "pypost_libraries"
    service = GitLibraryService(base_dir=base_dir)
    service.clone(url=str(sample_remote_git_repo), library_id="lib-checkout-guard")

    # Introduce local uncommitted change
    guard_file = base_dir / "lib-checkout-guard" / "pypost-library.yaml"
    guard_file.write_text("dirty edits", encoding="utf-8")

    with pytest.raises(GitDiagnosticError) as exc_info:
        service.checkout("lib-checkout-guard", branch="feature/v2-endpoints", force=False)

    assert exc_info.value.code == GitDiagnosticErrorCode.DIRTY_WORKING_TREE


# ============================================================================
# 6. Manifest Discovery & Diagnostics Tests
# ============================================================================


def test_git_library_service_discover_manifest(
    tmp_path: Path,
    sample_remote_git_repo: Path,
):
    """discover_manifest finds pypost-library.yaml in cloned repository."""
    base_dir = tmp_path / "pypost_libraries"
    service = GitLibraryService(base_dir=base_dir)
    service.clone(url=str(sample_remote_git_repo), library_id="lib-disc")

    manifest_path = service.discover_manifest("lib-disc")
    assert manifest_path is not None
    assert manifest_path.name == "pypost-library.yaml"
    assert manifest_path.exists()


def test_git_library_service_diagnostic_on_invalid_remote_url(tmp_path: Path):
    """Cloning an invalid or non-existent remote URL yields REPO_NOT_FOUND error."""
    base_dir = tmp_path / "pypost_libraries"
    service = GitLibraryService(base_dir=base_dir)

    with pytest.raises(GitDiagnosticError) as exc_info:
        service.clone(
            url="https://invalid.example.com/nonexistent/repo.git",
            library_id="lib-invalid-url",
        )

    assert exc_info.value.code in (
        GitDiagnosticErrorCode.REPO_NOT_FOUND,
        GitDiagnosticErrorCode.AUTH_FAILED,
        GitDiagnosticErrorCode.COMMAND_FAILED,
    )


# ============================================================================
# 7. Observability & Credential Masking Tests (Step 6)
# ============================================================================


def test_sanitize_git_url_masks_credentials():
    """Verify that embedded tokens and passwords are masked from URLs."""
    assert (
        sanitize_git_url("https://user:secretpass@github.com/org/repo.git")
        == "https://***:***@github.com/org/repo.git"
    )
    assert (
        sanitize_git_url("https://ghp_secrettoken123@github.com/org/repo.git")
        == "https://***:***@github.com/org/repo.git"
    )
    assert (
        sanitize_git_url("git@github.com:org/repo.git")
        == "git@github.com:org/repo.git"
    )
    assert (
        sanitize_git_url("https://github.com/org/repo.git")
        == "https://github.com/org/repo.git"
    )
    assert sanitize_git_url("") == ""


def test_git_auth_logging_masks_credentials_and_logs_events(caplog: pytest.LogCaptureFixture):
    """Verify that auth manager logs structured lifecycle events without leaking credentials."""
    secret_token = "ghp_super_secret_pat_99999"
    config = GitAuthConfig(
        mode=GitAuthMode.PAT,
        username="gituser",
        token=secret_token,
    )

    with caplog.at_level(logging.DEBUG, logger="pypost.core.git_auth"):
        with transient_git_auth_env(config) as env:
            assert env.get("GIT_TERMINAL_PROMPT") == "0"

    messages = [r.message for r in caplog.records]
    assert any("git_auth_askpass_created" in m for m in messages)
    assert any("git_auth_mode_configured" in m for m in messages)
    assert any("git_auth_askpass_cleaned" in m for m in messages)
    assert any("transient_git_auth_env_entered" in m for m in messages)
    assert any("transient_git_auth_env_exited" in m for m in messages)

    # CRITICAL: ensure secret token was NEVER logged
    for m in messages:
        assert secret_token not in m


def test_git_service_logging_masks_credentials_and_records_lifecycle(
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
    sample_remote_git_repo: Path,
):
    """Verify GitLibraryService logs structured events and masks embedded credentials."""
    base_dir = tmp_path / "pypost_libraries_obs"
    service = GitLibraryService(base_dir=base_dir)

    secret_url = f"https://myuser:mysecretpass@localhost/repo.git"

    with caplog.at_level(logging.DEBUG, logger="pypost.core.git_service"):
        service.clone(
            url=str(sample_remote_git_repo),
            library_id="lib-obs-test",
        )
        service.status("lib-obs-test")
        service.check_dirty("lib-obs-test")
        service.list_branches("lib-obs-test")
        service.discover_manifest("lib-obs-test")
        service.delete_library("lib-obs-test")

    messages = [r.message for r in caplog.records]
    assert any("git_clone_started" in m for m in messages)
    assert any("git_clone_success" in m for m in messages)
    assert any("git_status_started" in m for m in messages)
    assert any("git_status_completed" in m for m in messages)
    assert any("git_check_dirty_started" in m for m in messages)
    assert any("git_list_branches_started" in m for m in messages)
    assert any("git_manifest_discovery_started" in m for m in messages)
    assert any("git_library_deleted" in m for m in messages)

    # Test error logging masks sensitive url
    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger="pypost.core.git_service"):
        with pytest.raises(GitDiagnosticError):
            service.clone(url=secret_url, library_id="lib-obs-fail")

    err_messages = [r.message for r in caplog.records]
    assert any("git_clone_failed" in m for m in err_messages)
    # Ensure raw secret credentials never appear
    for m in err_messages:
        assert "mysecretpass" not in m
        assert "myuser:mysecretpass" not in m

