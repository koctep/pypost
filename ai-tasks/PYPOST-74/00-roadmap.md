# Roadmap: PYPOST-74

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `NullMetrics`, `NULL_METRICS`, and `resolve_metrics()` to `metrics_protocol.py`
  - [x] Removed all `if self._metrics:` guards across services, MCP, and UI call sites
  - [x] Extended `tests/test_metrics_protocol.py` for NullMetrics and resolve helper
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Suggested branch name

`refactoring/PYPOST-74-null-metrics-no-op`
