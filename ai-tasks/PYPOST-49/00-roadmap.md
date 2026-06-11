# Roadmap: PYPOST-49

## Programming Language

Python (PySide6 / Qt), consistent with the PyPost desktop application.

## Recommended Branch

`refactoring/PYPOST-49-metrics-registry-server-split`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Verified split delivered in PYPOST-75 (`MetricsRegistry`, `MetricsServer`, facade)
  - [x] Confirmed metric names, labels, routes, and injection API unchanged
  - [x] Ran metrics unit tests (25 passed)
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

- `ai-tasks/PYPOST-49/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-49/20-architecture.md`

### STEP 3: Development

- Source code (implemented in PYPOST-75; verified in this task)
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-49/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-49/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-49/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/tech-debt/PYPOST-40.md`
- `doc/dev/architecture.md`
- `doc/dev/solid_audit.md`
- `ai-tasks/PYPOST-49/70-dev-docs.md`
