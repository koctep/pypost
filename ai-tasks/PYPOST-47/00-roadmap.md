# Roadmap: PYPOST-47

## Programming Language

Python (PySide6 / Qt), consistent with the PyPost desktop application.

## Recommended Branch

`feature/PYPOST-47-unify-collection-loading`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Split `refresh_tree()` from `load_collections()` in `CollectionsPresenter`
  - [x] MainWindow startup and save wiring use `refresh_tree()` via RequestManager cache
  - [x] Tests for refresh-without-reload and MainWindow startup path
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

- `ai-tasks/PYPOST-47/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-47/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-47/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-47/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-47/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/collection_loading.md`
- `ai-tasks/PYPOST-47/70-dev-docs.md`
