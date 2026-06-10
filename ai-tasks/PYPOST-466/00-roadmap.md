# Roadmap: PYPOST-466

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Implemented `_on_vars_table_context_menu` changes to include "Move Up" and "Move Down" actions.
  - [x] Added `_move_variable_at_row` to support swapping ordered dictionary items and updating the UI model.
  - [x] Updated tests in `tests/test_env_dialog.py` to cover variable reordering and logging.
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (pypost application codebase; see `.cursor/lsr/do-python.md`).

## Recommended Branch

`feature/PYPOST-466-manual-variables-order`

## Sprint Context

Sprint 235 — **Environment Management UX** (starts 2026-06-09).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-466/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-466/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-466/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-466/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-466/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/`
