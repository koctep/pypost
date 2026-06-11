# Roadmap: PYPOST-75

**Jira:** [PYPOST-75](https://pypost.atlassian.net/browse/PYPOST-75) — [PYPOST-44 TD-3] MetricsManager bundles counters MCP and uvicorn lifecycle

**Programming language:** Python

**Suggested branch:** `refactor/PYPOST-75-metrics-manager-split`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Extracted `MetricsRegistry` (counters + `track_*` methods)
  - [x] Extracted `MetricsServer` (MCP resources + uvicorn lifecycle)
  - [x] `MetricsManager` retained as facade for backward-compatible injection
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

- `ai-tasks/PYPOST-75/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-75/20-architecture.md`

### STEP 3: Development

- `pypost/core/metrics_registry.py`
- `pypost/core/metrics_server.py`
- `pypost/core/metrics.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-75/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-75/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-75/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-75/70-dev-docs.md`
- `doc/dev/mcp_integration.md`
- `doc/dev/testability.md`
