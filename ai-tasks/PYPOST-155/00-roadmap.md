# Roadmap: PYPOST-155

**Language:** Python

**Suggested branch:** `refactoring/PYPOST-155-messages-route-method-filter`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Replaced `/messages` `Mount` + manual POST/405 with `Route(..., methods=["POST"])`
  - [x] Removed redundant manual GET check on SSE endpoint (Route already filters)
  - [x] Mirrored change in `MetricsServer` legacy SSE layout
  - [x] Updated routing structure test
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

- `ai-tasks/PYPOST-155/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-155/20-architecture.md`

### STEP 3: Development

- `pypost/core/mcp_server_impl.py`
- `pypost/core/metrics_server.py`
- `tests/test_mcp_server_impl.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-155/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-155/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-155/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/mcp_integration.md`
