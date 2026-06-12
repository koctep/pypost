# Roadmap: PYPOST-579

**Language:** Python

**Suggested branch:** `feature/PYPOST-579-otel-metrics-adapter`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `pypost/core/metrics_otel.py` with `OtelMetricsTracker`
  - [x] Added `create_otel_metrics_tracker` factory
  - [x] Added `tests/test_metrics_otel.py`
  - [x] Added `opentelemetry-api` and `opentelemetry-sdk` to `requirements.txt`
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

- `ai-tasks/PYPOST-579/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-579/20-architecture.md`

### STEP 3: Development

- `pypost/core/metrics_otel.py`
- `tests/test_metrics_otel.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-579/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-579/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-579/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-579/70-dev-docs.md`
- `doc/dev/testability.md`
- `doc/dev/mcp_integration.md`
