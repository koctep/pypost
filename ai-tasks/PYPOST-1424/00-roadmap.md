# Roadmap: PYPOST-1424

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1424/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1424/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_async_manifest_discovery_repro.py` — dialog init must not block on slow list_connections
- [x] **STEP 4: Development**
  - [x] Added `ManifestDiscoveryWorker` in `pypost/ui/workers/manifest_discovery_worker.py`
  - [x] Dialog starts discovery async; workspace populate stays sync; cancel/close/accept lifecycle
  - [x] Preserve combo selection after discovery appends (Qt empty-combo auto-select)
  - [x] Updated virtualization repro waits for discovery; Step 3 repro green
- [x] **STEP 5: Code Cleanup**
  - [x] `make lint` passed; `40-code-cleanup.md` written
- [x] **STEP 6: Observability**
  - [x] Discovery started/completed/cancelled/stale + worker DEBUG events (`50-observability.md`)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `60-tech-debt.md` with unticketed follow-ups (suggested SP)
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/workspace_environment_variable_import.md` for ManifestDiscoveryWorker
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1424/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1424/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_async_manifest_discovery_repro.py`

### STEP 4: Development

- `pypost/ui/workers/manifest_discovery_worker.py`
- `pypost/ui/dialogs/import_collection_variables_dialog.py`
- `tests/test_variable_import_virtualization_repro.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1424/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1424/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1424/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/workspace_environment_variable_import.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
