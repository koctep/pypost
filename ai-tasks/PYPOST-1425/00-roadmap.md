# Roadmap: PYPOST-1425

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_collection_fetch_transport_abort_repro.py`
- [x] **STEP 4: Development**
  - [x] Wired `CancellationTokenSource` into `CollectionFetchWorker` / `ManifestDiscoveryWorker`
  - [x] Added `call_with_cancellation_token` helper in `pypost/core/cancellation.py`
  - [x] Optional `cancellation_token` on `LibraryManagerService` list/read APIs
  - [x] Quiet `OperationCancelledError` handling; red repro green
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1425/40-code-cleanup.md`; `make lint` OK
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1425/50-observability.md` (`*_transport_aborted` DEBUG events)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1425/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/workspace_environment_variable_import.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1425/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1425/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_collection_fetch_transport_abort_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1425/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1425/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1425/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/workspace_environment_variable_import.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
