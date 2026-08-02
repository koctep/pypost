# Roadmap: PYPOST-973

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_qt_item_view_teardown.py` —
    `test_close_isolated_tree_actions_detaches_model`,
    `test_isolated_tree_actions_context_manager_detaches_model`
- [x] **STEP 4: Development**
  - [x] Added `close_isolated_tree_actions` + `isolated_tree_actions`
    using shared `detach_item_view_model`
  - [x] Migrated all isolated harness call sites to `addCleanup`
  - [x] Focused suite green (32 passed)
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (PySide6 / pytest helpers)

## Suggested branch name (reference only)

`chore/PYPOST-973-collections-tree-qt-teardown`

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-973/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-973/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_qt_item_view_teardown.py` (new cases)

### STEP 4: Development

- `tests/helpers/collections_tree.py`
- Consumer test modules under `tests/test_collection_tree_*.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-973/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-973/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-973/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md`
- `ai-tasks/PYPOST-973/70-dev-docs.md`
