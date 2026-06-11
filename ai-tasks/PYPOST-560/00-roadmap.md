# Roadmap: PYPOST-560

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Replaced `asyncio.run` + `asyncio.wait_for` with `anyio.run` + `anyio.fail_after` in `MCPClientService.run`.
  - [x] Used `ClientSession` as async context manager for clean teardown.
  - [x] Added regression test `test_mcp_client_service_list_tools_over_live_streamable_http` in `tests/test_mcp_server_integration.py`.
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (pypost application codebase).

## Suggested Branch

`fix/PYPOST-560-mcp-client-service-anyio-run-hang`

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-560/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-560/20-architecture.md`

### STEP 3: Development

- `pypost/core/mcp_client_service.py`
- `tests/test_mcp_client_service.py`
- `tests/test_mcp_server_integration.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-560/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-560/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-560/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-560/70-dev-docs.md`
- `doc/dev/testing.md`
