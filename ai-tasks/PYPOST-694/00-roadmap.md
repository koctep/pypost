# Roadmap: PYPOST-694

**Branch (reference):** current working branch

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] `HistoryManager` created in `main.py` composition root
  - [x] Optional `history_manager` injection on `MainWindow` (fallback for tests)
  - [x] Updated ~10 MainWindow test helpers to inject mock instead of patch
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**
  - [x] `doc/dev/testability.md` composition-root table
  - [x] `doc/dev/architecture.md` partial composition-root note

## Programming language

Python (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-694/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-694/20-architecture.md`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-694/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-694/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-694/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/testability.md`
- `doc/dev/architecture.md`
- `ai-tasks/PYPOST-694/70-dev-docs.md`
