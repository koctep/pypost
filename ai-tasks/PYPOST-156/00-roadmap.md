# Roadmap: PYPOST-156

**Language:** Python

**Suggested branch:** `refactoring/PYPOST-156-extract-legacy-sse-endpoints`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Extracted `SSEEndpoint` / `MessagesEndpoint` to `mcp_legacy_sse.py`
  - [x] Wired `MCPServerImpl` and `MetricsServer` via `build_legacy_sse_app`
  - [x] Added `tests/test_mcp_legacy_sse.py`
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

- `ai-tasks/PYPOST-156/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-156/20-architecture.md`

### STEP 3: Development

- `pypost/core/mcp_legacy_sse.py`
- `pypost/core/mcp_server_impl.py`
- `pypost/core/metrics_server.py`
- `tests/test_mcp_legacy_sse.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-156/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-156/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-156/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-156/70-dev-docs.md`
- `doc/dev/mcp_integration.md`
