# Roadmap: PYPOST-430

**Programming language:** Python 3.11+

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Replaced URL `/sse` substring heuristic with Content-Type detection in `HTTPClient`
  - [x] Added unit tests for content-type path, false-positive guard, Accept-header timeout
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

- `ai-tasks/PYPOST-430/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-430/20-architecture.md`

### STEP 3: Development

- `pypost/core/http_client.py`
- `tests/test_http_client_sse_probe.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-430/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-430/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-430/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-430/70-dev-docs.md`
- `doc/dev/request_execution.md`

## Suggested branch

`refactoring/PYPOST-430-sse-content-type-detection`
