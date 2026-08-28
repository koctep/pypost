# Roadmap: PYPOST-1222

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1222/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1222/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_git_library_service_repro.py`
- [x] **STEP 4: Development**
  - [x] Defined domain models and diagnostic errors (`GitAuthConfig`, `GitAuthMode`, `GitBranchInfo`, `GitRepoStatus`, `GitOperationType`, `GitDiagnosticErrorCode`, `GitOperationResult`, `GitDiagnosticError`) in `pypost/models/git_library.py` and re-exported in `pypost/models/__init__.py`.
  - [x] Implemented hybrid authentication environment manager `GitAuthEnvironmentManager` and context manager `transient_git_auth_env` in `pypost/core/git_auth.py` supporting system SSH agent, PAT via isolated `GIT_ASKPASS`, and custom SSH private keys via `GIT_SSH_COMMAND`.
  - [x] Implemented `GitLibraryService` in `pypost/core/git_service.py` with clone, fetch, pull, status, list_branches, checkout, dirty tree guard, and manifest auto-discovery.
  - [x] Verified full test suite passes with green repro test `tests/test_git_library_service_repro.py` (18/18 passed) and clean quality gate via `make check`.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1222/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1222/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1222/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - `doc/dev/git_library_service.md`
  - Updated `doc/dev/README.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1222/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1222/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1222/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1222/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1222/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/git_library_service.md`
- `doc/dev/README.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
