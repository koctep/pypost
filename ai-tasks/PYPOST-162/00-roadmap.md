# Roadmap: PYPOST-162

**Language:** Python (PySide6)

**Suggested branch:** `refactoring/PYPOST-162-centralize-tab-signal-wiring`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `_create_request_tab` factory; closure wiring for save/save-as
  - [x] Removed `_find_tab_for_sender` and `_request_tab_before_dialog`
  - [x] Updated tests for explicit tab handler signatures
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

- `ai-tasks/PYPOST-162/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-162/20-architecture.md`

### STEP 3: Development

- `pypost/ui/presenters/tabs_presenter.py`
- `tests/test_tabs_presenter.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-162/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-162/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-162/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-162/70-dev-docs.md`
- `doc/dev/request_execution.md`
