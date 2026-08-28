# PYPOST-1222: [Libraries] Git repository clone, pull, and hybrid auth service

## Goals

As part of parent epic [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219) (*Git-based Collection Libraries & Self-Contained Collection Format*), PyPost enables engineering teams to collaborate on version-controlled API collections stored in Git repositories.

Following the core collection schema format ([PYPOST-1220](https://pypost.atlassian.net/browse/PYPOST-1220)) and the library manifest validator with local secrets overlay ([PYPOST-1221](https://pypost.atlassian.net/browse/PYPOST-1221)), PyPost requires a robust, secure Git operations service (`GitLibraryService`) to manage the lifecycle of cloned repositories.

Managing collection repositories over Git introduces several critical operational requirements:
1. **Seamless Collection Repository Sharing**: Developers and teams need to clone shared collection repositories from diverse hosting environments (GitHub, GitLab, Bitbucket, self-hosted Git servers) directly into the local PyPost library registry (`~/.pypost/libraries/<library-id>/`).
2. **Hybrid Authentication Flexibility**: Engineering environments use varied authentication mechanisms. Some developers rely on their native system SSH agent, others require Personal Access Tokens (PATs) for HTTPS remotes, and some need dedicated custom SSH private keys (with or without passphrases). The system must seamlessly support all three authentication models without requiring global Git configuration changes.
3. **Safe Working Copy Protection (Dirty Check Guard)**: When pulling updates from an upstream remote, uncommitted or unstaged local changes must never be overwritten or clobbered. A strict dirty check guard must verify working tree cleanliness before initiating any pull or checkout operation.
4. **Immediate Manifest Discovery**: Upon completing a repository clone, PyPost must automatically locate the library manifest (`pypost-library.yaml` / `pypost-library.json`) and bind the repository to the local library ecosystem.

**Business Goal:**
Provide an autonomous, secure, and non-destructive `GitLibraryService` for cloning, fetching, pulling, branch switching, and inspecting Git-backed collection libraries. The service supports hybrid authentication (system SSH agent, HTTPS PAT, custom SSH keys) with isolated credential helpers/environment variables, prevents data loss via pre-pull dirty working tree guards, and manages cloned repositories within standard storage directories (`~/.pypost/libraries/<library-id>/`).

## Programming Language

- **Implementation language**: Python (Git library service, authentication adapters, working tree guards, repository status models, and unit tests).

## User Stories

- As a **Library Consumer (Developer / QA Engineer)**, I want to clone a remote Git repository containing collection libraries, inspect its synchronization status (ahead/behind counts, current branch), switch branches, and pull upstream updates safely without risking loss of my local uncommitted modifications.
- As a **Team Administrator / Security Lead**, I want the team to connect to private Git repositories using flexible authentication methods (system SSH agent, PAT tokens, or dedicated custom SSH keys) while ensuring sensitive credentials are never written to repository configuration files, logs, or shared workspaces.
- As an **Automation Pipeline / CI Runner**, I want to perform headless, non-interactive clone, fetch, and checkout operations using environment-supplied tokens or private keys without triggering interactive terminal prompts or hanging execution.
- As a **Downstream Feature Developer (UI & Library Manager Integration - PYPOST-1223)**, I want a well-defined `GitLibraryService` interface to query repository status, execute clone/pull/branch operations, and receive structured error diagnostics and dirty-state feedback.

## Definition of Done

This task is considered complete when:

1. Business requirements, entity definitions, and acceptance criteria for Git repository operations and hybrid authentication are fully documented.
2. A `GitLibraryService` is implemented to handle repository lifecycle operations:
   - Cloning remote repositories (HTTPS / SSH) into the standard library location (`~/.pypost/libraries/<library-id>/`).
   - Fetching remote tracking references and querying synchronization status.
   - Pulling upstream updates with fast-forward/merge handling.
   - Listing local and remote branches and checking out selected branches.
   - Inspecting repository state (current branch, commit hash, dirty status, ahead/behind counts).
3. Hybrid authentication is supported across three primary modes:
   - **System SSH Agent**: Inheriting native `ssh-agent` / system SSH environment.
   - **Personal Access Token (PAT)**: Authenticating HTTPS remotes non-interactively.
   - **Custom SSH Private Key**: Authenticating SSH remotes using a specified private key file and optional passphrase.
4. Credential isolation is enforced: authentication tokens and credentials are provided via non-interactive credential helpers or transient environment variables (`GIT_ASKPASS`, `GIT_SSH_COMMAND`) and are never written to `.git/config` remote URLs on disk.
5. A pre-pull **dirty check guard** is implemented and verified: if the working tree has unstaged modifications, staged uncommitted changes, or untracked conflicting files, pull operations are blocked with a descriptive `DIRTY_WORKING_TREE` diagnostic.
6. Automatic manifest discovery identifies `pypost-library.yaml`, `pypost-library.yml`, or `pypost-library.json` immediately following a successful clone.
7. Scope boundaries are strictly maintained: pure Git operations and authentication service without GUI components ([PYPOST-1223](https://pypost.atlassian.net/browse/PYPOST-1223)) or manifest schema validation ([PYPOST-1221](https://pypost.atlassian.net/browse/PYPOST-1221)).
8. Storage paths are configurable to allow isolated, hermetic testing fixtures without altering the user's live `~/.pypost/libraries/` directory.
9. Comprehensive test suite verifies cloning, hybrid auth strategies, dirty check guards, pull updates, branch listing/checkout, and error diagnostics under simulated Git environments.
10. Full repository quality gates pass (`make check`, `make lint`, `make typecheck`, `make test`, `make verify-ai-tasks`).

## Task Description

### Problem

API collection libraries hosted in Git repositories require full Git lifecycle management within PyPost. However, integrating Git operations directly into an API client presents several challenges:
- **Authentication Fragmentation**: Users clone repositories over HTTPS using username/PAT credentials, or over SSH using system SSH agents or specific identity files. If an application does not isolate credentials cleanly, credentials can leak into `.git/config` or trigger hanging interactive prompts.
- **Accidental Work Overwrite**: Users modifying collections locally might trigger a "Pull" or "Update" action. Without a safety guard detecting dirty working copies, a pull could result in merge conflicts, overwritten files, or loss of local work.
- **Detached Head & Branch Confusion**: Cloned repositories must track designated branches, allow switching branches, and provide clear insight into whether the local copy is ahead or behind upstream remotes.
- **Filesystem Organization**: Cloned libraries must reside in a standardized, predictable directory structure (`~/.pypost/libraries/<library-id>/`) segregated from local overlay secrets (`~/.pypost/libraries_data/<library-id>/`).

### Current State (Inventory)

- **Collection Serialization & Models** ([PYPOST-1220](https://pypost.atlassian.net/browse/PYPOST-1220)):
  - `Collection` model with variable metadata and request definitions.
  - Format-agnostic YAML/JSON collection serializers.
- **Library Manifest & Local Overlay** ([PYPOST-1221](https://pypost.atlassian.net/browse/PYPOST-1221)):
  - `LibraryManifest` model and parser for `pypost-library.yaml` / `.json`.
  - `LocalOverlayManager` storing local secrets under `~/.pypost/libraries_data/<library-id>/`.
  - Layered effective variable resolution engine.
- **Missing Capabilities (Addressed in This Task)**:
  - No Git operations service for clone, fetch, pull, status, and branch management.
  - No hybrid authentication provider supporting system SSH agent, PATs, and custom SSH keys.
  - No dirty check guard mechanism to prevent destructive updates on modified working copies.
  - No automated manifest discovery helper following a Git clone.

### Scope (This Task)

- Define core domain models for:
  - Git Authentication Configuration (Auth method, PAT token, username, SSH key path, passphrase).
  - Git Repository Status (current branch, commit hash, is_clean, dirty files list, ahead count, behind count, tracking branch).
  - Git Operation Result (success flag, operation type, output messages, error diagnostics).
  - Branch Information (branch name, is_remote, is_current, commit hash).
- Implement `GitLibraryService` supporting:
  - Cloning remote repositories to `~/.pypost/libraries/<library-id>/`.
  - Fetching updates and inspecting repository synchronization state.
  - Pulling remote changes with strict pre-pull dirty checking.
  - Listing available local and remote branches.
  - Checking out and switching branches.
- Implement hybrid authentication adapters for:
  - System SSH Agent.
  - Personal Access Token (PAT) via credential helper or `GIT_ASKPASS`.
  - Custom SSH Private Key via transient `GIT_SSH_COMMAND`.
- Implement pre-pull dirty check guard detecting uncommitted, unstaged, and untracked conflicting changes.
- Implement automatic manifest discovery post-clone.
- Provide comprehensive error categorization and diagnostics.

### Out of Scope (This Task)

- UI Library Manager panel, clone dialogs, branch dropdowns, and commit/push GUI views ([PYPOST-1223](https://pypost.atlassian.net/browse/PYPOST-1223)).
- Manifest schema parsing, local secret overlay persistence, and variable resolution ([PYPOST-1221](https://pypost.atlassian.net/browse/PYPOST-1221)).
- Example library updates and legacy fixture migrations ([PYPOST-1224](https://pypost.atlassian.net/browse/PYPOST-1224)).

### Functional Requirements

- **FR-1: Remote Repository Cloning & Target Destination Management**
  - The system shall clone remote Git repositories over HTTPS and SSH protocols into designated target directories under `~/.pypost/libraries/<library-id>/`.
  - The system shall support specifying an optional initial branch or tag during clone.
  - If the target directory already exists and is non-empty, the service shall refuse to clone and return a structured diagnostic error unless explicitly instructed.

- **FR-2: Hybrid Authentication Strategy Support**
  - The system shall support three distinct authentication strategies for Git operations:
    1. **System SSH Agent**: Utilizes the environment's active `ssh-agent` and default SSH keys without additional credentials.
    2. **Personal Access Token (PAT)**: Authenticates HTTPS remotes using a username (or token-as-username) and access token.
    3. **Custom SSH Private Key**: Authenticates SSH remotes using a specified local private key file path with an optional passphrase.
  - The system shall allow authentication strategy selection per repository operation or library profile.

- **FR-3: Non-Interactive Credential Isolation & Environment Injection**
  - The system shall execute Git operations non-interactively, never blocking or prompting on `stdin`.
  - Sensitive credentials (PAT tokens, SSH key passphrases) must be injected through transient environment variables or temporary credential helpers (e.g., `GIT_ASKPASS`, `GIT_SSH_COMMAND`).
  - The system shall never write plaintext tokens or passwords into `.git/config` remote URLs or persistent log files.

- **FR-4: Working Tree Dirty Check Guard**
  - The system shall inspect the working tree status of a local repository before executing any pull, fast-forward, or checkout operation.
  - The system shall detect:
    - Modified tracked files (staged or unstaged).
    - Deleted tracked files.
    - Untracked files that would be overwritten by incoming changes.
  - If the working tree is dirty, the system shall block the pull operation and return a structured `DIRTY_WORKING_TREE` status containing the list of dirty files.

- **FR-5: Safe Remote Pull & Synchronization**
  - When the working tree is clean, the system shall pull upstream changes from the configured tracking remote and branch.
  - The system shall handle fast-forward updates and report the outcome (e.g., updated commits range, already up-to-date).
  - If upstream changes cannot be fast-forwarded or merged cleanly, the operation shall fail safely with diagnostic conflict details without corrupting the working copy.

- **FR-6: Remote Fetch & Repository Status Inspection**
  - The system shall provide an operation to fetch updates from the remote repository without altering the working tree.
  - The system shall provide an inspection operation returning comprehensive repository status:
    - Current branch name or detached HEAD state.
    - Latest local commit hash and commit message summary.
    - Upstream tracking branch name.
    - Number of commits ahead of upstream.
    - Number of commits behind upstream.
    - Clean / dirty working tree indicator and list of modified files.

- **FR-7: Branch Discovery & Branch Checkout**
  - The system shall list all available branches (both local branches and remote-tracking branches).
  - The system shall allow checking out an existing local branch.
  - The system shall support creating and checking out a local tracking branch when switching to a remote branch that has not yet been checked out locally.
  - Branch checkout must be guarded by the dirty check to prevent losing uncommitted modifications.

- **FR-8: Automatic Manifest Discovery & Post-Clone Verification**
  - Following a successful clone operation, the system shall scan the cloned repository root for a library manifest file (`pypost-library.yaml`, `pypost-library.yml`, or `pypost-library.json`).
  - If a manifest is located, the system shall return its path and manifest summary metadata.
  - If no manifest is present at the root, the system shall report that the repository does not contain a standard manifest while still preserving the cloned repository for manual inspection.

- **FR-9: Actionable Error Diagnostics & Failure Categorization**
  - The system shall classify Git operation failures into distinct diagnostic categories:
    - `AUTH_FAILED`: Authentication failed (invalid PAT, rejected SSH key, missing permissions).
    - `DIRTY_WORKING_TREE`: Pull or checkout blocked due to uncommitted local modifications.
    - `REPO_NOT_FOUND`: Remote URL does not exist or network host unreachable.
    - `BRANCH_NOT_FOUND`: Specified branch or tag does not exist.
    - `MERGE_CONFLICT`: Pull failed due to non-trivial merge conflicts.
    - `GIT_NOT_INSTALLED`: Git executable not found in system PATH.
    - `TIMEOUT`: Operation timed out.
  - Each diagnostic error shall include a human-readable message, sanitized command summary, and contextual details.

- **FR-10: Configurable Base Directory & Test Isolation**
  - The base storage directory for libraries (`~/.pypost/libraries/`) shall be configurable across all service operations.
  - Test suites and programmatic callers must be able to specify a custom temporary directory as the library storage root to ensure hermetic, side-effect-free execution.

### Non-Functional Requirements

- **NFR-1 Security & Credential Protection**: Sensitive tokens, passwords, and private keys must never be logged, persisted in `.git/config`, or exposed in standard process error streams. All temporary credential helper artifacts must be cleaned up immediately upon command completion.
- **NFR-2 Safety & Data Loss Prevention**: Local modifications must be strictly protected. Destructive Git commands (e.g., hard reset, clean -f) must never be executed implicitly. Dirty check guards must prevent accidental overwrite of user edits.
- **NFR-3 Performance & Responsiveness**: Git status checks and fetch operations must complete within predictable timeouts (default 30 seconds for network operations, 5 seconds for local operations).
- **NFR-4 Cross-Platform Compatibility**: The service must function reliably across Linux, macOS, and Windows operating systems, correctly handling path delimiters, Git executable discovery, and SSH command invocation.
- **NFR-5 Determinism & Robust Error Recovery**: Interrupted network connections or failed Git commands must leave the local repository in a consistent state without orphan lock files (`.git/index.lock`) preventing subsequent operations.

### Constraints and Assumptions

- Python is the implementation language.
- Standard Git CLI (`git` executable) is assumed to be available on the host system.
- Cloned library repositories are stored under `~/.pypost/libraries/<library-id>/`, separate from local overlay secrets stored in `~/.pypost/libraries_data/<library-id>/`.
- Network operations depend on external connectivity and remote repository permissions.
- Pure core service implementation; GUI interactions (dialogs, progress bars, notifications) are handled in PYPOST-1223.

### Main Entities (Business Perspective)

| Entity | Description | Key Business Attributes |
| --- | --- | --- |
| **Git Auth Config** | Configuration encapsulating authentication parameters for a remote Git operation. | Auth Method (`SSH_AGENT`, `PAT`, `CUSTOM_SSH_KEY`), Username, PAT Token, Key Path, Passphrase |
| **Git Repository Status** | Snapshot of a local collection library repository's Git state. | Library ID, Root Path, Current Branch, Commit Hash, Is Clean, Dirty Files List, Ahead Count, Behind Count, Tracking Branch |
| **Branch Info** | Metadata describing an available local or remote branch. | Name, Is Remote, Is Current, Commit Hash |
| **Git Operation Result** | Structured outcome returned by any Git operation. | Success Flag, Operation Type, Result Data, Error Category, Diagnostic Message |
| **Git Library Service** | Core business service coordinating all Git repository lifecycle and safety operations. | Base Directory (`~/.pypost/libraries/`), Clone, Fetch, Pull, Status, Branch Listing, Checkout |
| **Dirty Check Guard** | Safety component evaluating working tree cleanliness before mutating operations. | Working Tree State, Unstaged Changes, Staged Changes, Untracked Collisions |

## Q&A

| Question | Answer |
| --- | --- |
| **Where are cloned Git collection libraries stored on disk?** | Cloned repositories are stored under `~/.pypost/libraries/<library-id>/`. This is strictly separate from local overlay secrets and overrides which reside under `~/.pypost/libraries_data/<library-id>/`. |
| **Why is hybrid authentication necessary?** | Teams have diverse security requirements. Corporate environments frequently use SSH agents with smart cards, cloud CI runners use Personal Access Tokens (PATs), and automated scripts often use dedicated SSH deployment keys. Supporting all three ensures compatibility with any developer workflow. |
| **How does the system ensure credentials are not saved to disk in `.git/config`?** | Credentials are supplied per-operation via isolated environment variables (`GIT_ASKPASS`, `GIT_SSH_COMMAND`) and transient credential helpers. The remote URL stored in `.git/config` remains clean (e.g., `https://github.com/org/repo.git`) without embedded credentials. |
| **What happens if a user pulls upstream changes while having uncommitted modifications?** | The pre-pull dirty check guard intercepts the operation, detects modified or untracked files, aborts the pull, and returns a structured `DIRTY_WORKING_TREE` diagnostic error listing the dirty files. |
| **Can the base library directory be overridden for unit testing?** | Yes. `GitLibraryService` accepts a configurable base storage path, allowing test fixtures to run in temporary directories without touching the user's actual `~/.pypost/libraries/` folder. |
| **Is UI or manifest parsing code included in this task?** | No. Manifest validation and overlay management are implemented in PYPOST-1221, and UI panels/dialogs are implemented in PYPOST-1223. This task focuses exclusively on the Git operations service and hybrid authentication backend. |

## References

- [PYPOST-1222](https://pypost.atlassian.net/browse/PYPOST-1222) — This task: *Git repository clone, pull, and hybrid auth service*
- [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219) — Parent Epic: *Git-based Collection Libraries & Self-Contained Collection Format*
- [PYPOST-1220](https://pypost.atlassian.net/browse/PYPOST-1220) — Preceding story: *Core schema and serializers for self-contained collection format with variable metadata*
- [PYPOST-1221](https://pypost.atlassian.net/browse/PYPOST-1221) — Sibling story: *Library manifest schema validator and local secrets overlay manager*
- [PYPOST-1223](https://pypost.atlassian.net/browse/PYPOST-1223) — Sibling story: *UI library manager panel, dirty check guards, and two-way Git commit/push flow*
- [PYPOST-1224](https://pypost.atlassian.net/browse/PYPOST-1224) — Sibling story: *Modernize examples to unified library format and preserve legacy fixtures in tests*
- `pypost/models/library_manifest.py` — Manifest domain models
- `pypost/core/library_manifest.py` — Manifest parser and auto-discovery
- `pypost/core/local_overlay_manager.py` — Local overlay persistence manager
