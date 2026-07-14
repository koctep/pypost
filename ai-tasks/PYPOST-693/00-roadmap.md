# Roadmap: PYPOST-693

**Programming language:** Python

**Suggested branch:** `refactoring/PYPOST-693-resolve-qt-in-core`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Create `pypost/core/qt/` subpackage with boundary contract
  - [x] Move 9 PySide6 modules to `core/qt/`
  - [x] Update production and test import sites (~35 files)
  - [x] Update log allowlist and audit scripts for new logger paths
  - [x] `make check` passes; PySide6 confined to `core/qt/`
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-693/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-693/20-architecture.md`

### STEP 3: Development

- `pypost/core/qt/` (9 modules + `__init__.py`)
- Production import updates (`main.py`, presenters, widgets)
- Test import updates (~25 files)
- `tests/expected_log_allowlist.yaml`
- `scripts/parse_test_log_inventory.py`, `scripts/audit_baseline_metrics.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-693/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-693/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-693/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-693/70-dev-docs.md`
- `doc/dev/architecture.md`
- `doc/dev/architecture_audit.md`
- `doc/dev/testability.md`
- `doc/dev/testing.md`
- `doc/dev/sensitive_data_masking_policy.md`
