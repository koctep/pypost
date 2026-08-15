# Roadmap: PYPOST-1009

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_environment_export.py` —
    `test_write_encrypted_export_file_round_trips_through_import`
- [x] **STEP 4: Development**
  - [x] Confirmed Step 3 locking test green — no production change required.
    Export already writes Hidden values as Fernet envelopes via
    `build_export_payload` / `StorageManager.serialize_environment_records`.
    Targeted `make test PYTEST_ARGS='tests/test_environment_export.py'`:
    12 passed, including
    `test_write_encrypted_export_file_round_trips_through_import`.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (verification/testing debt within the existing Python codebase; no new
language or stack introduced).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1009/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1009/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_environment_export.py` —
  `test_write_encrypted_export_file_round_trips_through_import`
- Result: green against current production (Export already writes Hidden
  envelopes). Verification lock added; no production fix in this step.

### STEP 4: Development

- No production source change (verification debt already green)
- Existing lock: `tests/test_environment_export.py` —
  `test_write_encrypted_export_file_round_trips_through_import`
- Targeted re-run: 12 passed, 0 failed

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1009/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1009/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1009/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/environment_encryption_at_rest.md`
- `doc/dev/environments_dialog.md`

## Suggested branch name

`test/PYPOST-1009-encrypted-export-round-trip`
