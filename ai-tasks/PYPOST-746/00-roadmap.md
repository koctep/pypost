# Roadmap: PYPOST-746

**Jira:** [PYPOST-746](https://pypost.atlassian.net/browse/PYPOST-746) — Split
metrics_registry._init_metrics

**Programming language:** Python

**Suggested branch:** `refactoring/PYPOST-746-split-metrics-registry-init`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Split `_init_metrics` into domain helpers (GUI, HTTP, MCP, encryption)
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

- `ai-tasks/PYPOST-746/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-746/20-architecture.md`

### STEP 3: Development

- `pypost/core/metrics_registry.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-746/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-746/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-746/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-746/70-dev-docs.md`
- `doc/dev/maintainability_audit.md`
- `doc/dev/mcp_integration.md`
