# Roadmap: PYPOST-406

## Programming Language

Python (PySide6 / Qt), consistent with the PyPost desktop application.

## Recommended Branch

`feature/PYPOST-406-unify-left-click-deep-copy`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Deep-copy in `CollectionsPresenter._on_collection_clicked` and `TabsPresenter.add_new_tab`
  - [x] Tests: left-click emits copy; dual tabs isolated from shared source
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

- `ai-tasks/PYPOST-406/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-406/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-406/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-406/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-406/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/open_request_in_isolated_tab.md`
- `ai-tasks/PYPOST-406/70-dev-docs.md`
