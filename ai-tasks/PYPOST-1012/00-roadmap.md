# Roadmap: PYPOST-1012

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_collection_export.py::test_build_all_export_payload_round_trips_ordered_collections`
- [x] **STEP 4: Development**
  - [x] Implemented ordered all-collection payload serialization and JSON-list file writing.
  - [x] Added the selection-independent Export All Collections… sidebar action, destination prompt, and count-aware success/error feedback.
  - [x] Covered list fidelity, empty backups, cancellation, write failures, and existing single-export regressions.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming language

Python

## Suggested Branch Name

`feature/PYPOST-1012-export-all-collections`

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1012/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1012/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1012/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1012/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1012/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`
