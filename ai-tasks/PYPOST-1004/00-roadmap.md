# Roadmap: PYPOST-1004

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *`tests/test_collection_import_apply.py::test_mid_write_save_failure_reconciles_memory_to_durable_storage` — greened by Step 4*
- [x] **STEP 4: Development**
  - [x] *Approach C: `apply_imported_collections` calls `reload_collections()` when save failures are non-empty*
  - [x] *Happy-path regression: `test_successful_multi_collection_import_does_not_reload`*
  - [x] *Dialog option B unchanged (plan counts + unsuccessful + failure lines via existing UI)*
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (hardening within the existing Python codebase; no new language or stack
introduced).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1004/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1004/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1004/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1004/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1004/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

## Suggested branch

`fix/PYPOST-1004-atomic-collection-import-or-recovery`
