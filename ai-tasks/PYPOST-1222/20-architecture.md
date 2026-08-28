# PYPOST-1222: [Libraries] Git repository clone, pull, and hybrid auth service

## Research

### 1. Git Execution Strategy: Pure Subprocess vs External CLI Wrappers

As part of parent epic [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219) (*Git-based Collection Libraries & Self-Contained Collection Format*), PyPost requires a robust, secure, and cross-platform Git service (`GitLibraryService`) to manage version-controlled collection libraries.

We evaluated three primary execution strategies for executing Git operations within Python:

| Strategy | Advantages | Disadvantages | Verdict |
| --- | --- | --- | --- |
| **Direct `subprocess.run` (Git CLI)** | Zero heavy external binary dependencies; standard library native; complete control over environment variables (`GIT_ASKPASS`, `GIT_SSH_COMMAND`), timeouts, process streams, and non-interactive isolation (`GIT_TERMINAL_PROMPT=0`); lightweight and deterministic across Linux, macOS, and Windows. | Requires custom stdout parsing for porcelain output formats. | **Selected** |
| **`GitPython`** | Pythonic wrapper around Git CLI. | Historically prone to shell injection CVEs if arguments are improperly quoted; leaks file descriptors; heavy dependency chain; poor non-interactive credential isolation for custom SSH passphrases. | **Rejected** |
| **`pygit2` / `libgit2`** | In-memory C-library Git implementation. | Requires C compiler toolchains and pre-compiled native binaries; complex distribution across multi-platform desktop environments; rigid SSH agent support differing from host OpenSSH. | **Rejected** |

#### Key Principles for Subprocess Execution:
1. **Never use `shell=True`**: All Git invocations use explicitly parameterized argument lists (`args: list[str]`), mitigating command injection risks.
2. **Strict Non-Interactive Execution**: Every command execution sets `GIT_TERMINAL_PROMPT="0"` and `GIT_FLUSH="1"`. Git will fail immediately with an authentication or configuration error rather than hanging waiting for user interaction on `stdin`.
3. **Explicit Timeout Guards**: Operations enforce strict timeouts (default 30.0s for network operations like `clone`/`fetch`/`pull`, 5.0s for local operations like `status`/`branch`). If a command hangs, `subprocess.TimeoutExpired` is caught and converted to a structured `GitDiagnosticError(code=GitDiagnosticErrorCode.TIMEOUT)`.
4. **UTF-8 Stream Decoding**: Standard output and error streams are captured with UTF-8 decoding and `errors="replace"` to ensure reliable cross-platform handling of multi-byte commit messages and filenames.

---

### 2. Transient Hybrid Authentication Injection

Engineering teams use diverse Git hosting environments and authentication protocols. The `GitLibraryService` must support three primary authentication modes without writing credentials to persistent Git configuration files (`.git/config`):

```
                                  ┌──────────────────────────┐
                                  │   Git Authentication     │
                                  └─────────────┬────────────┘
                                                │
                 ┌──────────────────────────────┼──────────────────────────────┐
                 ▼                              ▼                              ▼
      ┌────────────────────┐         ┌────────────────────┐         ┌────────────────────┐
      │     SSH Agent      │         │   HTTPS / PAT      │         │   Custom SSH Key   │
      │ (System SSH Sock)  │         │  (Personal Token)  │         │ (Identity + Pass)  │
      └──────────┬─────────┘         └──────────┬─────────┘         └──────────┬─────────┘
                 │                              │                              │
                 ▼                              ▼                              ▼
      - Ambient SSH_AUTH_SOCK        - GIT_ASKPASS transient        - GIT_SSH_COMMAND with
      - Default ~/.ssh/ identities     helper script / command        -i <key_path> & options
      - Zero injected credentials    - Injected via process env     - Passphrase via ASKPASS
```

#### A. System SSH Agent (`GitAuthMode.SSH_AGENT`)
- Uses the operating system's ambient `SSH_AUTH_SOCK` and default SSH identity files (`~/.ssh/id_rsa`, `~/.ssh/id_ed25519`).
- No credential injection is performed; the subprocess inherits the current environment safely.

#### B. Personal Access Token (`GitAuthMode.PAT`)
- Used for HTTPS remote URLs (e.g., `https://github.com/org/repo.git`, `https://gitlab.com/org/repo.git`).
- **Security Constraint**: Credentials must never be baked directly into the remote URL (`https://user:token@github.com/...`) because URLs are persisted in `.git/config` on disk and can leak in process inspection tables (`ps aux`).
- **Mechanism**:
  - A transient credential helper or `GIT_ASKPASS` provider is injected via process environment.
  - A lightweight, self-contained Python helper script or command is supplied via `GIT_ASKPASS`.
  - The token is passed via a dedicated environment variable (e.g. `PYPOST_GIT_ASKPASS_TOKEN`) accessible only to the ephemeral subprocess.
  - When Git requests username or password, `GIT_ASKPASS` evaluates the prompt:
    - If prompting for `Username`, it returns the configured username (or a fallback like `oauth2` / `x-token-auth` / token itself).
    - If prompting for `Password`, it outputs the secret token to `stdout`.
  - The remote URL in `.git/config` remains completely clean (`https://github.com/org/repo.git`).

#### C. Custom SSH Private Key (`GitAuthMode.CUSTOM_SSH_KEY`)
- Used when a repository requires a dedicated SSH deploy key separate from the user's default SSH keys.
- **Mechanism**:
  - `GIT_SSH_COMMAND` is dynamically generated with isolated options:
    `ssh -i <escaped_key_path> -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -F /dev/null`
  - If a passphrase is required for the encrypted private key, `SSH_ASKPASS` / `GIT_ASKPASS` is combined with `setsid` / non-interactive environment variables to supply the passphrase securely without terminal prompts.

---

### 3. Dirty Status Detection & Pre-Pull Safety Guard

When pulling upstream changes or switching branches, uncommitted local modifications in a collection library must never be clobbered or silently overwritten.

#### Detection Mechanics via `git status --porcelain=v1 -uall`:
1. `git status --porcelain=v1 -uall` provides machine-readable status where each modified or untracked file is listed with a two-character prefix `XY`:
   - `X`: Status of the index (staged)
   - `Y`: Status of the work tree (unstaged)
2. Status code mapping:
   - `M ` / ` M` / `MM`: Modified tracked file (staged, unstaged, or both)
   - `A ` / `AM`: Added / newly staged file
   - `D ` / ` D`: Deleted tracked file
   - `R ` / `RM`: Renamed file
   - `C `: Copied file
   - `??`: Untracked file
   - `UU` / `AA` / `DD` / `UD` / `DU`: Unmerged merge conflicts
3. **Dirty Check Guard Algorithm**:
   - If any tracked file is modified (`M`, `A`, `D`, `R`, `C`) or if untracked files collide with incoming changes, `is_clean` is marked `False`.
   - Before executing `pull()`, the service calls `check_dirty(library_id)`.
   - If `not is_clean` and `force=False`, the pull operation is immediately aborted and raises `GitDiagnosticError(code=GitDiagnosticErrorCode.DIRTY_WORKING_TREE, message="Working tree has uncommitted modifications", details={"dirty_files": dirty_files})`.

---

### 4. Branch Parsing and Repository Synchronization Inspection

To provide full repository visibility to the caller (and UI components in PYPOST-1223):

1. **Branch Listing (`git branch --all --format="%(refname)|%(refname:short)|%(HEAD)|%(objectname)"`)**:
   - Parses local branches (`refs/heads/*`) and remote tracking branches (`refs/remotes/*`).
   - Identifies active branch (`%(HEAD)` is `*`).
2. **Ahead / Behind Counts**:
   - Upstream tracking branch resolved via `git rev-parse --abbrev-ref --symbolic-full-name @{u}`.
   - If upstream is configured, `git rev-list --left-right --count HEAD...@{u}` returns ahead/behind counts (e.g. `2 0` = 2 ahead, 0 behind).
3. **Commit Hash & Message**:
   - `git rev-parse HEAD` returns current 40-character commit hash.
   - `git log -1 --pretty=format:%s` returns latest commit message summary.

---

### 5. Storage Organization & Test Isolation

1. **Storage Path Convention**:
   - Cloned collection libraries reside under `~/.pypost/libraries/<library-id>/`.
   - Local user overlay secrets reside under `~/.pypost/libraries_data/<library-id>/overlay.json` (managed by `LocalOverlayManager` from PYPOST-1221).
2. **Configurable Base Directory**:
   - `GitLibraryService(base_dir=...)` accepts an optional base directory.
   - In production, it defaults to `Path.home() / ".pypost" / "libraries"`.
   - In automated unit/integration tests, it accepts `tmp_path`, ensuring 100% hermetic test execution without side effects on user home directory.
3. **Clone Destination Guard**:
   - If the target folder `~/.pypost/libraries/<library-id>/` exists and contains files (non-empty), `clone()` refuses execution and returns `DESTINATION_NOT_EMPTY` error unless explicitly forced.

---

### 6. Post-Clone Automatic Manifest Discovery

Following a successful repository clone:
1. The service scans the root of the cloned repository for `pypost-library.yaml`, `pypost-library.yml`, or `pypost-library.json` using `find_and_read_manifest()` from `pypost.core.library_manifest` (PYPOST-1221).
2. If located, the manifest path and manifest identifier are attached to `GitOperationResult.manifest_path` and `GitOperationResult.details`.
3. If no manifest is present, the clone still succeeds and reports `manifest_found: false`, allowing developers to clone arbitrary Git repositories and create manifests subsequently.

---

### 7. Gap Analysis

| Capability | Current State | Required State (PYPOST-1222) |
| --- | --- | --- |
| **Git Domain Models** | None | `pypost/models/git_library.py` defining `GitAuthConfig`, `GitAuthMode`, `GitRepoStatus`, `GitBranchInfo`, `GitOperationResult`, `GitDiagnosticError` |
| **Hybrid Authentication Provider** | None | `pypost/core/git_auth.py` providing isolated transient environment generation for SSH agent, PAT (`GIT_ASKPASS`), and custom SSH keys (`GIT_SSH_COMMAND`) |
| **Git Operations Service** | None | `pypost/core/git_service.py` implementing `GitLibraryService` for `clone`, `fetch`, `pull`, `status`, `list_branches`, `checkout`, and `check_dirty` |
| **Dirty Check Guard** | None | Pre-pull and pre-checkout guard preventing data loss on modified working copies |
| **Post-Clone Manifest Discovery** | None | Automatic discovery of `pypost-library.yaml` / `.json` post-clone |

---

## Implementation Plan

### High-Level Execution Phases

1. **Phase 1 (Step 3): Automated Failing Repro Tests**
   - Implement `tests/test_git_library_service_repro.py` testing the complete target contract before adding production code.
   - Assert domain model serialization, hybrid auth environment generation, repository clone, dirty check guard before pull, clean pull fast-forward, branch listing/checkout, ahead/behind status inspection, manifest discovery, and structured diagnostic errors.

2. **Phase 2 (Step 4): Domain Models Definition (`pypost/models/git_library.py`)**
   - Define `GitAuthMode`, `GitAuthConfig`, `GitRepoStatus`, `GitBranchInfo`, `GitOperationType`, `GitDiagnosticErrorCode`, `GitOperationResult`, and `GitDiagnosticError`.
   - Re-export models in `pypost/models/__init__.py`.

3. **Phase 3 (Step 4): Hybrid Authentication Provider (`pypost/core/git_auth.py`)**
   - Implement `GitAuthEnvironmentManager` and context manager `transient_git_auth_env(config: Optional[GitAuthConfig])`.
   - Generate non-interactive environment dict with `GIT_TERMINAL_PROMPT=0`.
   - Handle PAT injection via `GIT_ASKPASS` helper.
   - Handle custom SSH private key and passphrase injection via `GIT_SSH_COMMAND` and `SSH_ASKPASS`.

4. **Phase 4 (Step 4): Git Library Service (`pypost/core/git_service.py`)**
   - Implement `GitLibraryService` with configurable `base_dir`.
   - Implement subprocess runner with timeout guards, error categorization, and diagnostic classification.
   - Implement `clone()`, `fetch()`, `pull()`, `status()`, `list_branches()`, `checkout()`, `check_dirty()`, and `discover_manifest()`.
   - Enforce pre-pull dirty check guard.

5. **Phase 5 (Step 4): Manifest Auto-Discovery Integration**
   - Connect `find_and_read_manifest` / manifest candidate discovery with `GitLibraryService.clone()`.

6. **Phase 6 (Steps 5–8): Code Cleanup, Observability, Technical Debt, and Dev Docs**
   - Run type checks (`make typecheck`), static analysis (`make lint`), and fast tests (`make test`).
   - Add structured logging events for Git operations, auth strategy application, and dirty guard triggers.
   - Author developer documentation in `doc/dev/git_library_service.md`.

---

### Mandatory — Failing Repro (Step 3 Design)

- **Test File Path**: `tests/test_git_library_service_repro.py`
- **What it Asserts**:
  1. **Domain Models & Validation**:
     - `GitAuthConfig` instantiation with `SSH_AGENT`, `PAT`, and `CUSTOM_SSH_KEY` modes.
     - `GitRepoStatus` and `GitBranchInfo` structure and defaults.
     - `GitDiagnosticError` structured codes (`AUTH_FAILED`, `DIRTY_WORKING_TREE`, `REPO_NOT_FOUND`, etc.).
  2. **Hybrid Auth Environment Generation**:
     - `SSH_AGENT`: passes environment without modifying `GIT_ASKPASS` or `GIT_SSH_COMMAND`.
     - `PAT`: sets `GIT_ASKPASS` and passes token via environment variable without writing to disk.
     - `CUSTOM_SSH_KEY`: sets `GIT_SSH_COMMAND` referencing key path with `-o IdentitiesOnly=yes`.
  3. **Repository Clone to Target Directory**:
     - Cloning a local/remote Git repository into `~/.pypost/libraries/<library-id>/`.
     - Rejecting clone into non-empty existing directory without force flag.
  4. **Dirty Check Guard Before Pull**:
     - Creating uncommitted changes (modified tracked file, staged file, untracked conflicting file).
     - Verifying `check_dirty()` returns `(True, ["modified_file.yaml"])`.
     - Verifying `pull()` is blocked and raises or returns `GitDiagnosticError` with code `DIRTY_WORKING_TREE`.
  5. **Clean Pull & Fast-Forward Updates**:
     - Pulling from upstream when working copy is clean.
     - Verifying local commits advance and status reflects up-to-date state.
  6. **Remote Fetch & Repository Status Inspection**:
     - Fetching remote refs without modifying working tree.
     - Querying `status()` to inspect `current_branch`, `commit_hash`, `commit_message`, `is_clean`, `ahead_count`, `behind_count`, and `tracking_branch`.
  7. **Branch Listing and Branch Checkout**:
     - Listing local and remote branches via `list_branches()`.
     - Checking out existing branch and creating local tracking branch for remote branch.
     - Guarding checkout against dirty working tree.
  8. **Post-Clone Manifest Auto-Discovery**:
     - Auto-discovering `pypost-library.yaml` upon clone and returning `manifest_path`.
  9. **Configurable Base Directory & Hermetic Test Isolation**:
     - Instantiating `GitLibraryService(base_dir=tmp_path)` and verifying all operations remain confined to `tmp_path`.
  10. **Error Diagnostics on Invalid Remote / Auth Failure**:
      - Attempting clone with non-existent remote URL and receiving structured `REPO_NOT_FOUND` diagnostic.
- **How it Fails Before Implementation**:
  - `pypost.models.git_library` does not exist (`ModuleNotFoundError`).
  - `pypost.core.git_auth` does not exist (`ModuleNotFoundError`).
  - `pypost.core.git_service` does not exist (`ModuleNotFoundError`).
- **Sequencing**:
  - Step 2: Architecture approved.
  - Step 3: Write red test `tests/test_git_library_service_repro.py` and verify all tests fail with `ModuleNotFoundError`.
  - Step 4: Implement domain models, auth environment manager, and `GitLibraryService` until all tests pass green.

---

## Architecture

### 1. System Module Breakdown & Responsibilities

```
pypost/
├── models/
│   ├── git_library.py           # [NEW] GitAuthConfig, GitAuthMode, GitRepoStatus, GitBranchInfo, GitOperationResult, GitDiagnosticError
│   ├── library_manifest.py      # [EXISTING - PYPOST-1221] LibraryManifest, LocalLibraryOverlay
│   └── __init__.py              # [UPDATED] Re-exports Git models
└── core/
    ├── git_auth.py              # [NEW] GitAuthEnvironmentManager & transient credential injection (GIT_ASKPASS, GIT_SSH_COMMAND)
    ├── git_service.py           # [NEW] GitLibraryService (clone, fetch, pull, status, list_branches, checkout, dirty guard)
    ├── library_manifest.py      # [EXISTING - PYPOST-1221] Manifest parser, validator, and candidate discovery
    └── local_overlay_manager.py # [EXISTING - PYPOST-1221] Local overlay manager for secrets
```

#### Detailed Module Responsibilities

1. **`pypost.models.git_library`**:
   - `GitAuthMode`: Enum (`SSH_AGENT`, `PAT`, `CUSTOM_SSH_KEY`).
   - `GitAuthConfig`: Value object holding authentication method and credentials (`username`, `token`, `key_path`, `passphrase`, `strict_host_checking`).
   - `GitBranchInfo`: Value object representing a Git branch (`name`, `short_name`, `is_remote`, `is_current`, `commit_hash`, `remote_name`).
   - `GitRepoStatus`: Value object representing the status of a cloned repository (`library_id`, `repo_path`, `current_branch`, `commit_hash`, `commit_message`, `tracking_branch`, `ahead_count`, `behind_count`, `is_clean`, `dirty_files`, `untracked_files`).
   - `GitOperationType`: Enum (`CLONE`, `FETCH`, `PULL`, `CHECKOUT`, `STATUS`, `BRANCH_LIST`).
   - `GitDiagnosticErrorCode`: Enum (`AUTH_FAILED`, `DIRTY_WORKING_TREE`, `REPO_NOT_FOUND`, `BRANCH_NOT_FOUND`, `MERGE_CONFLICT`, `GIT_NOT_INSTALLED`, `DESTINATION_NOT_EMPTY`, `TIMEOUT`, `COMMAND_FAILED`).
   - `GitOperationResult`: Result container holding operation success flag, output messages, error codes, and manifest discovery details.
   - `GitDiagnosticError`: Exception class for structured Git failures.

2. **`pypost.core.git_auth`**:
   - `GitAuthEnvironmentManager`:
     - Builds isolated environment dictionaries for `subprocess.run`.
     - Injects `GIT_TERMINAL_PROMPT=0` and non-interactive safeguards.
     - Sets up temporary `GIT_ASKPASS` helper scripts / environment variables for PAT authentication.
     - Sets up `GIT_SSH_COMMAND` for custom private keys.
     - Cleans up any temporary credential helper artifacts upon process termination.
   - `transient_git_auth_env(config: Optional[GitAuthConfig])`: Context manager yielding `(env_dict, cleanup_callback)`.

3. **`pypost.core.git_service`**:
   - `GitLibraryService`:
     - `__init__(base_dir: Optional[Path | str] = None, git_binary: str = "git", default_timeout: float = 30.0)`
     - `get_library_dir(library_id: str) -> Path`
     - `is_git_installed() -> bool`
     - `clone(url: str, library_id: str, branch: Optional[str] = None, auth: Optional[GitAuthConfig] = None, force: bool = False, timeout: Optional[float] = None) -> GitOperationResult`
     - `fetch(library_id: str, remote: str = "origin", auth: Optional[GitAuthConfig] = None, timeout: Optional[float] = None) -> GitOperationResult`
     - `pull(library_id: str, remote: str = "origin", branch: Optional[str] = None, auth: Optional[GitAuthConfig] = None, force: bool = False, timeout: Optional[float] = None) -> GitOperationResult`
     - `status(library_id: str, timeout: Optional[float] = None) -> GitRepoStatus`
     - `list_branches(library_id: str, timeout: Optional[float] = None) -> list[GitBranchInfo]`
     - `checkout(library_id: str, branch: str, create: bool = False, auth: Optional[GitAuthConfig] = None, force: bool = False, timeout: Optional[float] = None) -> GitOperationResult`
     - `check_dirty(library_id: str) -> tuple[bool, list[str]]`
     - `discover_manifest(library_id: str) -> Optional[Path]`
     - Low-level `_run_git(args: list[str], cwd: Optional[Path], auth: Optional[GitAuthConfig], timeout: float) -> tuple[int, str, str]`

---

### 2. Component Architecture Diagram (Mermaid)

```mermaid
graph TD
    subgraph UIAndCallers [Callers & Future UI - PYPOST-1223]
        LMUI[Library Manager UI / CLI]
    end

    subgraph ServiceLayer [pypost.core.git_service]
        GLS[GitLibraryService<br/>- base_dir: Path<br/>- clone()<br/>- fetch()<br/>- pull()<br/>- status()<br/>- list_branches()<br/>- checkout()<br/>- check_dirty()]
        DCG[Dirty Check Guard<br/>git status --porcelain=v1]
    end

    subgraph AuthLayer [pypost.core.git_auth]
        GAE[GitAuthEnvironmentManager<br/>transient_git_auth_env]
        ASK[Transient GIT_ASKPASS Helper]
        SSH[GIT_SSH_COMMAND Builder]
    end

    subgraph ManifestLayer [pypost.core.library_manifest]
        LMP[Manifest Auto-Discovery<br/>find_and_read_manifest]
    end

    subgraph ModelsLayer [pypost.models.git_library]
        GAC[GitAuthConfig & GitAuthMode]
        GRS[GitRepoStatus]
        GBI[GitBranchInfo]
        GOR[GitOperationResult]
        GDE[GitDiagnosticError]
    end

    subgraph OSGitFilesystem [Local Filesystem & Git Subprocess]
        GITCLI[Git Executable CLI / subprocess]
        LIBDIR[~/.pypost/libraries/<library-id>/<br/>- .git/<br/>- pypost-library.yaml<br/>- collections/]
        DATADIR[~/.pypost/libraries_data/<library-id>/<br/>- overlay.json (PYPOST-1221)]
    end

    LMUI --> GLS
    LMUI -. configures .-> GAC
    GLS --> DCG
    GLS --> GAE
    GAE --> ASK
    GAE --> SSH
    GAE --> GITCLI
    GLS --> GITCLI
    GITCLI --> LIBDIR
    GLS --> LMP
    LMP --> LIBDIR
    GLS --> GRS
    GLS --> GBI
    GLS --> GOR
    GLS -. raises .-> GDE
```

---

### 3. Data Models Specification

#### `pypost/models/git_library.py`

```python
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
        super().__init__(f"[{self.code.value}] {message}" + (f" (repo: {repo_path})" if repo_path else ""))
```

---

### 4. Dirty Check Guard Algorithm

The dirty check guard ensures that neither uncommitted changes nor untracked files are overwritten during pull or branch checkout operations:

```mermaid
flowchart TD
    Start([Execute Git Operation: pull / checkout]) --> CheckGuard{Pre-Operation Safety Check}
    CheckGuard --> RunStatus[Execute 'git status --porcelain=v1 -uall']
    RunStatus --> ParseOutput[Parse Output Lines: Staged, Unstaged, Untracked]
    ParseOutput --> Evaluate{Any Modified / Untracked Files?}
    Evaluate -- Yes --> IsCleanFalse[Set is_clean = False<br/>Populate dirty_files list]
    Evaluate -- No --> IsCleanTrue[Set is_clean = True<br/>dirty_files = empty]
    
    IsCleanFalse --> CheckForce{Is force=True?}
    CheckForce -- No --> AbortPull[Abort Operation<br/>Raise GitDiagnosticError<br/>code=DIRTY_WORKING_TREE]
    CheckForce -- Yes --> ProceedOperation[Proceed with Caution]
    
    IsCleanTrue --> ProceedOperation
    ProceedOperation --> ExecGit[Execute 'git pull' or 'git checkout']
    ExecGit --> CheckSuccess{Execution Successful?}
    CheckSuccess -- Yes --> ReturnSuccess([Return GitOperationResult: Success])
    CheckSuccess -- No --> ClassifyError[Classify Error: MERGE_CONFLICT / AUTH_FAILED]
    ClassifyError --> ReturnError([Return GitOperationResult: Failure])
    AbortPull --> ReturnError
```

#### Step-by-Step Guard Logic:
1. Before running `git pull` or `git checkout`, `GitLibraryService` runs `_run_git(["status", "--porcelain=v1", "-uall"], cwd=repo_dir)`.
2. Each line of stdout is trimmed and analyzed:
   - If line starts with `??`, file is categorized as untracked.
   - If line starts with `M`, `A`, `D`, `R`, `C`, `U`, file is categorized as dirty.
3. If dirty or untracked files are present and `force=False`:
   - Operation is prevented from invoking the remote Git command.
   - Raises `GitDiagnosticError(code=GitDiagnosticErrorCode.DIRTY_WORKING_TREE, message="Cannot pull updates into a dirty working tree", details={"dirty_files": dirty_files})`.

---

### 5. Transient Credential Injection Architecture

```mermaid
sequenceDiagram
    participant App as GitLibraryService
    participant Auth as GitAuthEnvironmentManager
    participant Env as Subprocess Environment
    participant Git as Git CLI Process
    participant Remote as Remote Git Server (GitHub / GitLab)

    App->>Auth: transient_git_auth_env(GitAuthConfig)
    alt AuthMode == PAT
        Auth->>Auth: Write ephemeral askpass script / configure python askpass
        Auth->>Env: Set GIT_ASKPASS, GIT_TERMINAL_PROMPT=0, PYPOST_GIT_ASKPASS_TOKEN
    else AuthMode == CUSTOM_SSH_KEY
        Auth->>Env: Set GIT_SSH_COMMAND="ssh -i <key> -o IdentitiesOnly=yes"
    else AuthMode == SSH_AGENT
        Auth->>Env: Set GIT_TERMINAL_PROMPT=0 (ambient SSH_AUTH_SOCK)
    end

    App->>Git: subprocess.run(['git', 'clone', ...], env=Env)
    Git->>Remote: Handshake & Auth Challenge
    alt PAT Prompt
        Remote-->>Git: Request credentials
        Git->>Env: Invoke GIT_ASKPASS
        Env-->>Git: Stream token
    end
    Remote-->>Git: Auth Succeeded / Data Transfer
    Git-->>App: Process Completed (exit_code=0)
    App->>Auth: Cleanup Context
    Auth->>Auth: Erase any temporary helper scripts & clear memory buffers
```

#### Security Safeguards:
1. **No `.git/config` Credentials**: Remote URLs in cloned repositories are stored without embedded basic authentication credentials (`https://github.com/org/repo.git`).
2. **Ephemeral ASKPASS Helper**: Helper scripts are generated inside `tempfile.TemporaryDirectory` with POSIX permissions `0o700` and deleted immediately inside a `finally:` block.
3. **No Process Table Exposure**: Passwords and tokens are never passed as command-line arguments to `git` or `ssh`.
4. **Sanitized Diagnostics**: All log messages and error messages sanitize URLs and strip potential tokens before printing to log files or returning to UI callers.

---

### 6. Error Classification Engine

When a Git subprocess fails (`returncode != 0`), `GitLibraryService` classifies the failure based on `stderr` and `stdout` patterns:

| Error Code | Detection Pattern | Remediation Message |
| --- | --- | --- |
| `AUTH_FAILED` | `Authentication failed`, `Permission denied (publickey)`, `fatal: could not read Username`, `Invalid username or password` | Verify access token permissions or SSH key configuration. |
| `REPO_NOT_FOUND` | `Repository not found`, `fatal: remote error:`, `Could not resolve host`, `does not exist` | Verify the remote repository URL and network connectivity. |
| `BRANCH_NOT_FOUND` | `Remote branch ... not found`, `pathspec ... did not match any file(s)` | Verify that the specified branch or tag exists on remote. |
| `MERGE_CONFLICT` | `Automatic merge failed; fix conflicts and then commit`, `error: Your local changes to the following files would be overwritten by merge` | Local modifications conflict with upstream changes. Resolve conflicts or stash changes. |
| `DIRTY_WORKING_TREE` | Triggered by pre-pull / pre-checkout guard | Working tree contains uncommitted modifications. Commit or stash changes before updating. |
| `DESTINATION_NOT_EMPTY` | Destination directory exists and contains files/directories | Target folder already exists and is non-empty. |
| `GIT_NOT_INSTALLED` | `FileNotFoundError` when invoking `git` | Git CLI is not found on system PATH. Install Git to enable library operations. |
| `TIMEOUT` | `subprocess.TimeoutExpired` | Git operation timed out. Check network connection and remote server status. |

---

## Q&A

- **Q: How does `GitLibraryService` prevent hanging interactive prompts when Git asks for a username or password?**
  - **A:** All subprocess executions explicitly include `GIT_TERMINAL_PROMPT="0"` in the process environment. When a required credential is missing, Git immediately aborts with exit code 128 instead of waiting on `stdin`.

- **Q: How does the service authenticate over HTTPS using Personal Access Tokens without storing the token in `.git/config`?**
  - **A:** The service uses a transient `GIT_ASKPASS` helper and injects the token into the subprocess environment (`PYPOST_GIT_ASKPASS_TOKEN`). Git calls `GIT_ASKPASS` during the HTTPS handshake, receives the token on stdout, and completes the transfer. The remote URL on disk remains `https://github.com/org/repo.git`.

- **Q: What happens if a user tries to pull updates when they have unstaged modifications in a collection file?**
  - **A:** The pre-pull dirty check guard executes `git status --porcelain=v1` before invoking `git pull`. It detects the modified file, halts execution, and raises `GitDiagnosticError` with code `DIRTY_WORKING_TREE` containing the list of dirty files. Local work is never overwritten.

- **Q: How does the service support custom SSH private keys with passphrases?**
  - **A:** For custom private keys, `GIT_SSH_COMMAND` is set to `ssh -i <key_path> -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new`. If a passphrase is provided in `GitAuthConfig`, `SSH_ASKPASS` / `GIT_ASKPASS` supplies the passphrase to the SSH subprocess.

- **Q: How are test suites isolated from the user's real `~/.pypost/libraries/` folder?**
  - **A:** `GitLibraryService` accepts an optional `base_dir` constructor argument. Tests pass a pytest `tmp_path` fixture, completely isolating all clone, pull, and branch operations to the temporary testing directory.

- **Q: Does `GitLibraryService` automatically discover library manifests after cloning?**
  - **A:** Yes. After a successful clone, `GitLibraryService` inspects the repository root for `pypost-library.yaml`, `pypost-library.yml`, and `pypost-library.json` using `find_and_read_manifest()`. If found, `GitOperationResult.manifest_path` is populated.
