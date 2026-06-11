# Roadmap: PYPOST-386

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Debounced `StateManager` UI-state saves with QTimer coalescing (300 ms)
  - [x] `flush_pending_save()` on `MainWindow.handle_exit()`
  - [x] Tests for coalescing, flush durability, and exit flush
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (PySide6)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-386/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-386/20-architecture.md`

### STEP 3: Development

- `pypost/core/state_manager.py`
- `pypost/ui/main_window.py`
- `tests/test_settings_persistence.py`
- `tests/test_main_window_shutdown.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-386/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-386/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-386/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/architecture.md`
- `doc/dev/collection_tree_actions.md`
- `ai-tasks/PYPOST-386/70-dev-docs.md`
