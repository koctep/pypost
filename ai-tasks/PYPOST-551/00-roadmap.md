# Roadmap: PYPOST-551

Programming language: Python (.cursor/lsr/do-python.md)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `mcp_streamable_http.py` shared `/mcp` route + lifespan
  - [x] Migrated `MCPServerImpl` and `MetricsManager` to Streamable HTTP (SSE retained)
  - [x] Migrated `MCPClientService` and integration/routing tests
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

- `ai-tasks/PYPOST-551/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-551/20-architecture.md`

### STEP 3: Development

- `pypost/core/mcp_streamable_http.py`
- `pypost/core/mcp_server_impl.py`
- `pypost/core/metrics.py`
- `pypost/core/mcp_client_service.py`
- `tests/test_mcp_server_integration.py`
- `tests/test_mcp_server_impl.py`
- `tests/test_mcp_client_service.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-551/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-551/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-551/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/mcp_integration.md`
- `doc/dev/testing.md`
