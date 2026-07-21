# Roadmap: PYPOST-827

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `tests/helpers/process_until.py` (wall-clock + posted quit)
  - [x] Wired three sibling gateway/worker modules onto shared helper
  - [x] Unified responsiveness module onto shared helper (hang-regression kept)
  - [x] Focused suite: 20 passed (responsiveness + three siblings)
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Programming language

Python 3.10+ (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

Suggested branch (reference only): `test/PYPOST-827-shared-process-until`

### STEP 1: Requirements

- `ai-tasks/PYPOST-827/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-827/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-827/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-827/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-827/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-827/70-dev-docs.md`
- `doc/dev/gui_testing.md`
- `doc/dev/testing.md`
- `doc/dev/environment_storage_async.md`
