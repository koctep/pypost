# Roadmap: PYPOST-382

**Language:** Python 3

**Suggested branch:** `refactoring/PYPOST-382-testability-seams`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `http_client` / `mcp_client` constructor seams to `RequestService`
  - [x] Added `session` constructor seam to `HTTPClient`
  - [x] Added injection tests for RequestService, HTTPClient, MainWindow
  - [x] Created `doc/dev/testability.md`
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

- `ai-tasks/PYPOST-382/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-382/20-architecture.md`

### STEP 3: Development

- `pypost/core/request_service.py`
- `pypost/core/http_client.py`
- `tests/test_request_service.py`
- `tests/test_http_client.py`
- `tests/test_main_window.py`
- `doc/dev/testability.md`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-382/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-382/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-382/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/testability.md`
- `doc/dev/testing.md` (cross-reference)
- `doc/dev/gui_testing.md` (cross-reference)
