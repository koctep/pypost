# Roadmap: PYPOST-66

**Programming language:** Python (`.cursor/lsr/do-python.md`)

**Suggested branch:** `refactoring/PYPOST-66-main-window-signals`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Extracted presenter signal wiring to `main_window_signals.py`
  - [x] Added `tests/test_main_window_signals.py`
  - [x] Updated MainWindow test patches to `wire_presenter_signals`
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

- `ai-tasks/PYPOST-66/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-66/20-architecture.md`

### STEP 3: Development

- `pypost/ui/main_window_signals.py`
- `pypost/ui/main_window.py`
- `tests/test_main_window_signals.py`
- Test patch updates in `tests/test_*main_window*.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-66/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-66/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-66/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-66/70-dev-docs.md`
- `doc/dev/testability.md`
