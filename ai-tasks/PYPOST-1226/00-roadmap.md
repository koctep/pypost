# Roadmap: PYPOST-1226

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_manifest_field_diagnostics.py`
- [x] **STEP 4: Development**
  - [x] Implemented field-level validation diagnostics, JSON path mapping, line/column number extraction, and `to_dict()` serialization on `ManifestDiagnosticError` and parser functions in `pypost/core/library_manifest.py`.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
- [x] **STEP 8: Dev Docs**
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1226/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1226/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1226/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1226/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1226/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
