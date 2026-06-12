# Roadmap: PYPOST-48

**Programming language:** Python

**Suggested branch:** `refactoring/PYPOST-48-item-type-strategy`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Add `collection_item_strategies.py` registry
  - [x] Wire `RequestManager` delete/rename dispatch through registry
  - [x] Add strategy registry tests
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

- `ai-tasks/PYPOST-48/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-48/20-architecture.md`

### STEP 3: Development

- `pypost/core/collection_item_strategies.py`
- `pypost/core/request_manager.py`
- `tests/test_collection_item_strategies.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-48/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-48/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-48/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-48/70-dev-docs.md`
- `doc/dev/testability.md`
