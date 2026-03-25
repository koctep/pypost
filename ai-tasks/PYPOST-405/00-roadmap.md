# Roadmap: PYPOST-405

## Implementation

- **Programming language:** Python (PySide6 / Qt), same stack as the PyPost desktop app.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `open_request_in_isolated_tab` signal and `New tab` context menu in `CollectionsPresenter`.
  - [x] Wired the new signal in `MainWindow`.
  - [x] Passed deep copy of RequestData into `TabsPresenter.add_new_tab` for restore.
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

- `ai-tasks/PYPOST-405/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-405/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-405/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-405/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-405/60-review.md` (per `scripts/agent-do.sh`; tech debt lives there)

### STEP 7: Dev Docs

- `doc/dev/`
