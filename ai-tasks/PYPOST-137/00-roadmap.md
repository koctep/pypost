# Roadmap: PYPOST-137

Suggested branch: `documentation/PYPOST-137-mcp-active-env-binding`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Document active-environment binding for MCP
  - [x] Log/metric when env identity changes while MCP running
  - [x] Verify per-call variable supplier (existing tests)
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

- `ai-tasks/PYPOST-137/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-137/20-architecture.md`

### STEP 3: Development

- `pypost/ui/presenters/env_presenter.py`
- `pypost/core/metrics*.py`
- `tests/test_env_presenter.py`
- `tests/test_metrics_registry.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-137/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-137/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-137/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/mcp_integration.md`
- `doc/mcp_integration.md`
- `ai-tasks/PYPOST-137/70-dev-docs.md`
