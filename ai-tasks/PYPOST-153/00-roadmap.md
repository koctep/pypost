# Roadmap: PYPOST-153

**Language:** Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added shared `format_bind_error` in `server_bind.py`
  - [x] MetricsServer bind failure handling mirroring MCPServerManager
  - [x] MetricsManager `start_failed` signal with deferred UI connect
  - [x] MainWindow warning dialog on metrics bind failure
  - [x] Tests in `test_metrics_server_startup.py`
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

- `ai-tasks/PYPOST-153/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-153/20-architecture.md`

### STEP 3: Development

- `pypost/core/server_bind.py`
- `pypost/core/metrics_server.py`
- `pypost/core/metrics.py`
- `pypost/core/mcp_server.py`
- `pypost/ui/main_window.py`
- `tests/test_metrics_server_startup.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-153/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-153/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-153/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/mcp_integration.md`
- `ai-tasks/PYPOST-153/70-dev-docs.md`
