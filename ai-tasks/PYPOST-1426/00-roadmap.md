# Roadmap: PYPOST-1426

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_remote_collection_fault_injection_repro.py`
  - [x] `tests/helpers/remote_collection_faults.py`
- [x] **STEP 4: Development**
  - [x] Fault-injection helper factories (reset, broken pipe, truncated JSON, bad schema, mid-stream abort)
  - [x] Dialog + worker suite green (10 tests); drained QueuedConnection signals in worker unit tests
  - [x] No production code changes required — existing recovery path covers fault classes
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1426/40-code-cleanup.md`; `make lint` OK
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1426/50-observability.md` (reuse existing fetch/serializer events)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1426/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/workspace_environment_variable_import.md`
  - [x] `ai-tasks/PYPOST-1426/70-dev-docs.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1426/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1426/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_remote_collection_fault_injection_repro.py`
- `tests/helpers/remote_collection_faults.py`

### STEP 4: Development

- Source code (none — characterization suite)
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1426/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1426/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1426/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/workspace_environment_variable_import.md`
- `ai-tasks/PYPOST-1426/70-dev-docs.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
