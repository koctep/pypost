# Roadmap: PYPOST-36

## Task Metadata

- Programming language: Python
- Recommended branch: feature/PYPOST-36-context-menu-rename

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `RequestManager` rename APIs for request/collection/item and
    non-empty-name validation, including storage file rewrite for collection rename.
  - [x] Added unit tests for request rename, collection rename, and empty-name rejection.
  - [x] Added `Rename` action to collection tree context menu with inline rename flow for
    collection/request items and non-empty validation in UI.
  - [x] Fixed rename editor lifecycle in tree view to avoid crashes on collection rename selection.
  - [x] Refactored rename commit handling to process rename only on editor close and avoid model
    mutation during in-progress edit events.
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

- `ai-tasks/PYPOST-36/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-36/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-36/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-36/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-36/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/`
