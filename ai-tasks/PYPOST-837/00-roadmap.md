# Roadmap: PYPOST-837

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Implemented `pypost.agent.ui_wait` (poll + condition helpers + errors)
  - [x] Wired `AgentAppSession.wait_*` and package exports; lifecycle uses
    production `wait_until`
  - [x] Thin-reexported `tests.helpers.qt_wait.wait_until`
  - [x] Added async fixture + session tests (`tests/test_ui_wait.py`)
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (`.cursor/lsr/do-python.md`)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-837/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-837/20-architecture.md`

### STEP 3: Development

- `pypost/agent/ui_wait.py`
- `pypost/agent/lifecycle.py` (session helpers + ready wait)
- `pypost/agent/__init__.py` (exports)
- `tests/helpers/qt_wait.py` (re-export)
- `tests/test_ui_wait.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-837/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-837/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-837/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/ui_wait.md`
- `ai-tasks/PYPOST-837/70-dev-docs.md`
