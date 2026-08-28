# Git Library Service & Hybrid Authentication

## Overview

As part of parent epic [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219) (*Git-based Collection Libraries & Self-Contained Collection Format*), **PYPOST-1222** delivers the Git repository management, lifecycle operations, and hybrid authentication engine for version-controlled collection libraries.

Collection libraries allow teams to store, synchronize, and version-control multiple PyPost collection files (`.yaml` / `.yml` / `.json`) inside Git repositories. The `GitLibraryService` and `GitAuthEnvironmentManager` provide safe, hermetic, and non-interactive Git operations across multiple authentication mechanisms without exposing sensitive credentials or risking working tree corruption.

### Core Capabilities

1. **Subprocess Git Lifecycle Operations**:
   - High-level operations for `clone`, `fetch`, `pull`, `checkout`, `status`, `list_branches`, and `delete_library`.
   - Manifest auto-discovery scanning for standard manifest descriptors (`pypost-library.yaml`, `pypost-library.yml`, `pypost-library.json`).
2. **Transient Hybrid Authentication**:
   - Zero-leak authentication supporting **System SSH Agent** (ambient `SSH_AUTH_SOCK`), **Personal Access Tokens (PAT)** via isolated `GIT_ASKPASS` credential helpers, and **Custom SSH Private Keys** via dynamic `GIT_SSH_COMMAND` parameters.
   - Strictly non-interactive process environment configuration (`GIT_TERMINAL_PROMPT=0`, `GIT_FLUSH=1`).
3. **Working Tree Safety Guards**:
   - Machine-readable porcelain dirty tree analysis (`git status --porcelain=v1 -uall`).
   - Pre-pull and pre-checkout safety checks preventing uncommitted local edits from being overwritten or clobbered.
4. **Storage Organization & Credential Isolation**:
   - Local Git repositories cloned into `~/.pypost/libraries/<library_id>/`.
   - Completely decoupled and isolated from local secrets and user overrides stored in `~/.pypost/libraries_data/<library_id>/overlay.json` (PYPOST-1221).
5. **Structured Error Diagnostics & Observability**:
   - Domain exception `GitDiagnosticError` mapping raw Git outputs into categorized error codes (`AUTH_FAILED`, `DIRTY_WORKING_TREE`, `REPO_NOT_FOUND`, etc.).
   - Structured key=value logging with automatic URL credential masking.

---

## Architecture & Data Models

### Module Structure

```text
pypost/
├── models/
│   ├── git_library.py           # [NEW] Git domain models, auth configuration, diagnostic errors
│   ├── library_manifest.py      # [EXISTING] Manifest & local overlay data models
│   └── __init__.py              # Re-exports Git domain models
└── core/
    ├── git_auth.py              # [NEW] GitAuthEnvironmentManager & transient_git_auth_env
    ├── git_service.py           # [NEW] GitLibraryService & sanitize_git_url
    └── library_manifest.py      # [EXISTING] Manifest parsing & candidate discovery
```

### Component Architecture

```mermaid
graph TD
    subgraph UI_or_Caller [UI / Orchestrator / API]
        CALLER[Caller / UI Actions]
    end

    subgraph ServiceLayer [pypost.core]
        GLS[GitLibraryService<br/>- clone(), fetch(), pull()<br/>- status(), list_branches()<br/>- checkout(), check_dirty()<br/>- discover_manifest()]
        GAEM[GitAuthEnvironmentManager<br/>- build_env()<br/>- transient_git_auth_env()]
    end

    subgraph SubprocessEnv [Isolated Git Subprocess Execution]
        ENV[Process Environment<br/>- GIT_TERMINAL_PROMPT=0<br/>- GIT_FLUSH=1<br/>- GIT_ASKPASS / GIT_SSH_COMMAND]
        PROMPT_SCRIPT[Ephemeral AskPass Helper<br/>chmod 0o700 / auto-cleaned]
        GIT_CLI[git CLI Subprocess]
    end

    subgraph StorageLayout [Filesystem Storage]
        REPO_DIR[~/.pypost/libraries/library-id/<br/>Cloned Git Repository]
        SECRETS_DIR[~/.pypost/libraries_data/library-id/<br/>overlay.json: Secrets & Overrides]
    end

    CALLER --> GLS
    GLS --> GAEM
    GAEM --> ENV
    GAEM --> PROMPT_SCRIPT
    GLS --> GIT_CLI
    ENV -. injected into .-> GIT_CLI
    GIT_CLI --> REPO_DIR
    SECRETS_DIR -. isolated from .-> REPO_DIR
```

### Data Models (`pypost.models.git_library`)

#### `GitAuthMode`
Enum specifying the authentication strategy for remote Git operations:

| Value | Identifier | Description |
| --- | --- | --- |
| `"ssh_agent"` | `GitAuthMode.SSH_AGENT` | Uses the host system's ambient `SSH_AUTH_SOCK` and default SSH keys. |
| `"pat"` | `GitAuthMode.PAT` | Uses a Personal Access Token / Bearer Token over HTTPS via transient `GIT_ASKPASS`. |
| `"custom_ssh_key"` | `GitAuthMode.CUSTOM_SSH_KEY` | Uses a dedicated private SSH key and optional passphrase via `GIT_SSH_COMMAND`. |

#### `GitAuthConfig`
Configuration model for remote Git authentication:

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `mode` | `GitAuthMode` | `GitAuthMode.SSH_AGENT` | Authentication mode. |
| `username` | `Optional[str]` | `None` | Username for PAT or basic auth (optional fallback). |
| `token` | `Optional[str]` | `None` | Personal Access Token / password (never logged or persisted in `.git/config`). |
| `key_path` | `Optional[str]` | `None` | Path to private SSH key file. |
| `passphrase` | `Optional[str]` | `None` | Passphrase for encrypted private SSH key. |
| `strict_host_checking` | `bool` | `True` | If `True`, sets `-o StrictHostKeyChecking=accept-new`; otherwise `no`. |

#### `GitRepoStatus`
Detailed snapshot of repository synchronization and working tree status:

| Field | Type | Description |
| --- | --- | --- |
| `library_id` | `str` | Collection library identifier. |
| `repo_path` | `Path` | Absolute filesystem path to the cloned repository. |
| `current_branch` | `Optional[str]` | Active branch name or detached HEAD summary. |
| `commit_hash` | `Optional[str]` | 40-character SHA-1 commit hash of `HEAD`. |
| `commit_message` | `Optional[str]` | Subject line of the latest commit. |
| `tracking_branch` | `Optional[str]` | Upstream tracking branch name (e.g. `origin/main`). |
| `ahead_count` | `int` | Number of local commits ahead of upstream tracking branch. |
| `behind_count` | `int` | Number of commits behind upstream tracking branch. |
| `is_clean` | `bool` | `True` if working tree has no uncommitted/untracked changes. |
| `dirty_files` | `List[str]` | Paths of modified, staged, deleted, or untracked files. |
| `untracked_files` | `List[str]` | Paths of untracked files (`??`). |

#### `GitBranchInfo`
Metadata describing a local or remote Git branch:

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `name` | `str` | *required* | Full refname (e.g. `refs/heads/main` or `refs/remotes/origin/main`). |
| `short_name` | `str` | *required* | Short branch name (e.g. `main` or `origin/main`). |
| `is_remote` | `bool` | `False` | `True` if reference belongs to `refs/remotes/*`. |
| `is_current` | `bool` | `False` | `True` if this branch is currently checked out (`*` in HEAD). |
| `commit_hash` | `str` | `""` | SHA-1 commit hash for the branch tip. |
| `remote_name` | `Optional[str]` | `None` | Remote name for tracking branches (e.g. `origin`). |

#### `GitOperationResult`
Structured result returned by all mutative and lifecycle operations:

| Field | Type | Description |
| --- | --- | --- |
| `success` | `bool` | `True` if the operation succeeded. |
| `operation` | `GitOperationType` | `CLONE`, `FETCH`, `PULL`, `CHECKOUT`, `STATUS`, or `BRANCH_LIST`. |
| `library_id` | `Optional[str]` | Collection library identifier. |
| `repo_path` | `Optional[Path]` | Filesystem path to the repository directory. |
| `current_branch` | `Optional[str]` | Active branch after operation. |
| `output` | `str` | Combined standard output and error from Git. |
| `error_code` | `Optional[GitDiagnosticErrorCode]` | Categorized error code if failed. |
| `error_message` | `Optional[str]` | Human-readable failure explanation. |
| `details` | `Dict[str, Any]` | Diagnostic key/value context (e.g. `dirty_files`). |
| `manifest_path` | `Optional[Path]` | Path to discovered `pypost-library.yaml` (if present). |

#### `GitDiagnosticErrorCode` & `GitDiagnosticError`
Standardized error codes and exception class:

```python
class GitDiagnosticErrorCode(str, Enum):
    AUTH_FAILED = "AUTH_FAILED"
    DIRTY_WORKING_TREE = "DIRTY_WORKING_TREE"
    REPO_NOT_FOUND = "REPO_NOT_FOUND"
    BRANCH_NOT_FOUND = "BRANCH_NOT_FOUND"
    MERGE_CONFLICT = "MERGE_CONFLICT"
    GIT_NOT_INSTALLED = "GIT_NOT_INSTALLED"
    DESTINATION_NOT_EMPTY = "DESTINATION_NOT_EMPTY"
    TIMEOUT = "TIMEOUT"
    COMMAND_FAILED = "COMMAND_FAILED"
```

---

## Hybrid Authentication Modes & Credential Isolation

The `GitAuthEnvironmentManager` dynamically prepares isolated process execution environments per command, preventing secrets from persisting in disk configs or environment leaks.

### 1. System SSH Agent (`GitAuthMode.SSH_AGENT`)
- Default mode for developers with pre-configured SSH agent setups.
- Inherits host `SSH_AUTH_SOCK` and default SSH keys (`~/.ssh/id_rsa`, `~/.ssh/id_ed25519`).
- No credential material is generated or injected.

### 2. Personal Access Token (`GitAuthMode.PAT`)
- Used for HTTPS authentication against GitHub, GitLab, Bitbucket, Azure DevOps, or self-hosted Git servers.
- **Security Guard**: Tokens are **never** embedded in remote URLs (e.g. `https://token@github.com/...`) because URLs are saved to `.git/config` and exposed in system process listings.
- **Transient ASKPASS Mechanism**:
  1. An ephemeral executable script (`askpass.py`) is written to a temporary directory with POSIX permissions `0o700`.
  2. The script parses the Git prompt argument: returns `PYPOST_GIT_ASKPASS_USERNAME` for username prompts and `PYPOST_GIT_ASKPASS_TOKEN` for password prompts.
  3. Environment variables `GIT_ASKPASS`, `GIT_TERMINAL_PROMPT=0`, and `PYPOST_GIT_ASKPASS_TOKEN` are passed directly to `subprocess.run(..., env=env)`.
  4. The temporary directory and script are immediately removed upon completion of the operation.

```python
from pypost.core.git_auth import transient_git_auth_env
from pypost.models.git_library import GitAuthConfig, GitAuthMode

auth = GitAuthConfig(
    mode=GitAuthMode.PAT,
    username="oauth2",
    token="ghp_exampleToken1234567890",
)

with transient_git_auth_env(auth) as env:
    # Subprocess runs with GIT_ASKPASS configured; credentials never leak to disk
    pass
```

### 3. Custom SSH Private Key (`GitAuthMode.CUSTOM_SSH_KEY`)
- Used for dedicated deployment keys or repository-specific SSH keys.
- **Mechanism**:
  1. Constructs an isolated `GIT_SSH_COMMAND`:
     `ssh -i <key_path> -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -F /dev/null`
  2. If the private key is encrypted with a passphrase, creates an ephemeral `SSH_ASKPASS` helper with `SSH_ASKPASS_REQUIRE=force`.
  3. Ephemeral helpers are wiped clean immediately after execution.

---

## Core API & Usage

### Initializing the Service

```python
from pathlib import Path
from pypost.core.git_service import GitLibraryService

# Default storage location: ~/.pypost/libraries/
service = GitLibraryService()

# Or with custom base directory (e.g. in tests)
test_service = GitLibraryService(
    base_dir=Path("/tmp/pypost_test/libraries"),
    default_timeout=30.0,
)
```

### Cloning a Remote Library

```python
from pypost.models.git_library import GitAuthConfig, GitAuthMode

auth = GitAuthConfig(mode=GitAuthMode.PAT, token="ghp_secretToken")
result = service.clone(
    url="https://github.com/my-org/api-library.git",
    library_id="lib_billing_api",
    branch="main",
    auth=auth,
    force=False,
)

print(result.success)          # True
print(result.manifest_path)    # Path to ~/.pypost/libraries/lib_billing_api/pypost-library.yaml
```

### Inspecting Repository Status & Ahead/Behind Counts

```python
status = service.status(library_id="lib_billing_api")

print(f"Branch: {status.current_branch}")
print(f"Clean: {status.is_clean}")
print(f"Ahead: {status.ahead_count}, Behind: {status.behind_count}")
print(f"Dirty Files: {status.dirty_files}")
```

### Pulling Upstream Updates (with Safety Guard)

```python
try:
    result = service.pull(library_id="lib_billing_api", auth=auth)
    print("Pull succeeded!")
except GitDiagnosticError as exc:
    if exc.code == GitDiagnosticErrorCode.DIRTY_WORKING_TREE:
        print(f"Pull blocked! Dirty files: {exc.details.get('dirty_files')}")
    else:
        print(f"Pull failed: {exc.message}")
```

### Listing Branches & Checking Out

```python
# List local and remote branches
branches = service.list_branches(library_id="lib_billing_api")
for b in branches:
    print(f"{b.short_name} (current: {b.is_current}, remote: {b.is_remote})")

# Switch branch (guarded against uncommitted local edits)
service.checkout(library_id="lib_billing_api", branch="feature/v2-endpoints")

# Create and checkout a new branch
service.checkout(library_id="lib_billing_api", branch="feature/new-apis", create=True)
```

### Manifest Discovery

```python
manifest_path = service.discover_manifest(library_id="lib_billing_api")
if manifest_path:
    print(f"Discovered manifest at: {manifest_path}")
```

---

## Safety Guards

### Pre-Pull & Pre-Checkout Dirty Working Tree Checks

To prevent accidental data loss or clobbering uncommitted developer edits:
1. `check_dirty(library_id)` executes `git status --porcelain=v1 -uall`.
2. Any modified (`M`), added (`A`), deleted (`D`), renamed (`R`), copied (`C`), or untracked (`??`) files will cause `is_clean` to be `False`.
3. `pull()` and `checkout()` evaluate working tree cleanliness before running:
   - If dirty and `force=False`, operation raises `GitDiagnosticError(code=GitDiagnosticErrorCode.DIRTY_WORKING_TREE)` and emits warning logs.
   - If `force=True`, the safety check is bypassed.

---

## Storage Layout & Credential Isolation

To maintain strict boundaries between version-controlled files and private developer credentials:

```text
~/.pypost/
├── libraries/                          # Cloned Git Repositories (Managed by GitLibraryService)
│   └── <library-id>/
│       ├── .git/                       # Clean Git metadata (NO tokens in .git/config)
│       ├── pypost-library.yaml         # Library Manifest
│       └── collections/                # Version-controlled collection files
│           ├── auth.yaml
│           └── users.json
│
└── libraries_data/                     # Local User Overrides & Secrets (Managed by LocalOverlayManager)
    └── <library-id>/
        └── overlay.json                # Mode 0o600 / Directory 0o700
                                        # Contains active_profile, sensitive secrets, local overrides
```

### Storage Isolation Rules:
- **Clean Remote Config**: URLs saved to `.git/config` are pure HTTPS/SSH URLs without credentials.
- **Zero Secrets in Worktree**: User API tokens, passwords, and private overrides are stored solely in `~/.pypost/libraries_data/` and never written to the working tree.
- **Filesystem Permissions**: Overlay data directories are restricted to `0o700` and overlay files to `0o600`.

---

## Configuration & Runtime Settings

| Setting / Variable | Default Value | Purpose |
| --- | --- | --- |
| `base_dir` | `~/.pypost/libraries` | Root directory for cloned Git repositories. |
| `git_binary` | `"git"` | Binary or executable path for Git CLI. |
| `default_timeout` | `30.0` seconds | Timeout for network-bound operations (`clone`, `fetch`, `pull`). |
| Local Operation Timeout | `5.0` seconds | Timeout for local metadata commands (`status`, `list_branches`, `rev-parse`). |
| Checkout Timeout | `10.0` seconds | Timeout for branch checkout operations. |
| `GIT_TERMINAL_PROMPT` | `"0"` | Enforces non-interactive failure instead of hanging on terminal inputs. |
| `GIT_FLUSH` | `"1"` | Ensures real-time stream flushing for subprocess outputs. |
| AskPass Directory Perms | `0o700` | POSIX permissions for transient askpass helper scripts. |

---

## Observability & Structured Logging Catalog

All log records are structured with key=value attributes and event identifiers.

### Error Events (`ERROR`)

- `git_binary_not_found`: `binary=%s error=%s` — Git executable missing from system PATH.
- `git_command_timeout`: `subcommand=%s timeout=%s` — Subprocess exceeded timeout.
- `git_clone_failed`: `url=%s code=%s stderr=%s` — Clone failed (URL credentials sanitized).
- `git_fetch_failed`: `library_id=%s code=%s stderr=%s` — Remote fetch failed.
- `git_pull_failed`: `library_id=%s code=%s stderr=%s` — Remote pull failed.
- `git_checkout_failed`: `library_id=%s branch=%s code=%s stderr=%s` — Branch checkout failed.

### Warning Events (`WARNING`)

- `git_auth_cleanup_failed`: `error=%s` — Temporary askpass directory cleanup error.
- `git_status_check_failed`: `repo=%s stderr=%s` — Porcelain status command returned non-zero.
- `git_clone_destination_not_empty`: `path=%s` — Destination directory exists and is not empty.
- `git_pull_blocked_dirty_tree`: `library_id=%s files=%s` — Pull prevented due to dirty tree.
- `git_checkout_blocked_dirty_tree`: `library_id=%s files=%s` — Checkout prevented due to dirty tree.
- `git_list_branches_failed`: `library_id=%s stderr=%s` — Branch listing returned non-zero.

### Informational Events (`INFO`)

- `git_clone_started`: `library_id=%s url=%s branch=%s force=%s`
- `git_clone_force_clearing_destination`: `path=%s`
- `git_clone_success`: `library_id=%s path=%s manifest=%s`
- `git_fetch_started` / `git_fetch_success`: `library_id=%s remote=%s`
- `git_pull_started` / `git_pull_success`: `library_id=%s remote=%s branch=%s force=%s`
- `git_checkout_started` / `git_checkout_success`: `library_id=%s branch=%s create=%s force=%s`
- `git_library_deleted`: `library_id=%s path=%s`

### Debug Events (`DEBUG`)

- `git_auth_mode_configured`: Details of active auth mode (`mode=%s username=%s has_token=%s`).
- `git_auth_askpass_created` / `git_auth_askpass_cleaned`: Lifecycle of transient helper scripts.
- `transient_git_auth_env_entered` / `transient_git_auth_env_exited`: Scope boundaries.
- `git_check_dirty_started` / `git_dirty_tree_detected` / `git_dirty_tree_clean`: Dirty check execution.
- `git_manifest_discovery_started` / `git_manifest_discovered` / `git_manifest_not_found`: Manifest discovery.
- `git_status_started` / `git_status_completed`: Detailed branch, sync, and file counts.
- `git_list_branches_started` / `git_list_branches_completed`: Branch enumeration summary.

### Credential Masking

- Personal access tokens and passphrases are **never** logged.
- `sanitize_git_url(url)` replaces basic auth credentials in remote URLs with `***:***@` before logging or attaching to error objects.

---

## Troubleshooting & Diagnostics Guide

| Diagnostic Error Code | Underlying Cause | Remediation |
| --- | --- | --- |
| `AUTH_FAILED` | Invalid PAT token, expired credentials, missing SSH deploy key, or rejected public key. | Verify the configured PAT token in `GitAuthConfig`, or ensure the SSH public key is registered with the Git provider. |
| `DIRTY_WORKING_TREE` | Local collection files or untracked modifications exist in the working tree during `pull()` or `checkout()`. | Commit or discard local changes, or pass `force=True` if you explicitly intend to bypass the guard. |
| `REPO_NOT_FOUND` | Remote repository URL is invalid, repository was deleted, or DNS resolution failed. | Check repository URL spelling, network connectivity, and access permissions. |
| `BRANCH_NOT_FOUND` | Requested branch does not exist on remote or locally. | Verify branch name with `list_branches()` or specify `create=True` when checking out a new branch. |
| `MERGE_CONFLICT` | Upstream changes conflict with uncommitted local work. | Resolve conflicts manually in the library directory or pull with `force=True`. |
| `DESTINATION_NOT_EMPTY` | Clone target directory `~/.pypost/libraries/<library-id>/` already exists and contains files. | Use a distinct `library_id`, delete the existing directory via `delete_library()`, or pass `force=True`. |
| `GIT_NOT_INSTALLED` | `git` binary cannot be located on system `PATH`. | Ensure Git is installed and available in the system PATH environment. |
| `TIMEOUT` | Git network operation exceeded timeout duration. | Check internet connectivity, proxy settings, or increase `default_timeout`. |
| `COMMAND_FAILED` | Generic unclassified Git CLI error. | Check `exc.details.get("stderr")` for specific Git CLI output. |
