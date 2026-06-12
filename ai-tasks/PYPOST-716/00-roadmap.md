# Roadmap: PYPOST-716

**Programming language:** Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Patched "uvicorn.Server.serve" in test cases in tests/test_mcp_server_manager.py and tests/test_metrics_server_startup.py to avoid native macOS crashes.
  - [x] Removed socket-blocking/occupy_port setup logic from port busy tests.
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**
  - [x] Documented the macOS stabilization of port-busy test cases in `doc/dev/testing.md` and created `70-dev-docs.md`.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-716/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-716/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-716/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-716/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-716/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/`

## Related Work

- Test Audit: [PYPOST-686](../PYPOST-686/00-roadmap.md)
- Qt segfault investigation: [PYPOST-429](../PYPOST-429/00-roadmap.md)
