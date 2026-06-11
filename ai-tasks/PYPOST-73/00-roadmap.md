# Roadmap: PYPOST-73

**Jira:** [PYPOST-73](https://pypost.atlassian.net/browse/PYPOST-73) — [PYPOST-44 TD-1] No IMetricsManager protocol for metrics consumers

**Programming language:** Python

**Suggested branch:** `refactoring/PYPOST-73-metrics-tracker-protocol`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `MetricsTrackerProtocol` in `pypost/core/metrics_protocol.py`
  - [x] Updated 16 consumer modules to type-hint protocol instead of `MetricsManager`
  - [x] Added `tests/test_metrics_protocol.py`
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

- `ai-tasks/PYPOST-73/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-73/20-architecture.md`

### STEP 3: Development

- `pypost/core/metrics_protocol.py`
- Consumer type-hint updates (workers, services, presenters, widgets)
- `tests/test_metrics_protocol.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-73/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-73/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-73/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-73/70-dev-docs.md`
- `doc/dev/testability.md`
