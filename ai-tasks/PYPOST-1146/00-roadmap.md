# Roadmap: PYPOST-1146

## Task Metadata

- **Implementation language**: Python 3
- **Branch name**: `refactoring/PYPOST-1146-metrics-manager-modularization`

## Step Status

- [/] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1146/10-requirements.md`
- [/] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1146/20-architecture.md`
- [/] **STEP 3: Failing Repro Test**
  - `tests/test_metrics_manager_modularization.py`
- [/] **STEP 4: Development**
  - [x] Extracted `MetricsTrackingMixin` to `pypost/core/qt/metrics_tracking.py`
  - [x] Extracted `MetricsWebSocketMixin` to `pypost/core/qt/metrics_websocket.py`
  - [x] Slimmed `MetricsManager`; removed `__getattr__` dynamic delegation
  - [x] Updated SOLID audit caps for new modules
  - [x] Regenerated `ai-tasks/PYPOST-376/baseline-metrics.md`
  - [x] Updated `test_metrics_manager_dynamic_delegation` to assert explicit methods
- [/] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1146/40-code-cleanup.md`
- [/] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1146/50-observability.md`
- [/] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1146/60-tech-debt.md`
- [/] **STEP 8: Dev Docs**
  - Updated `doc/dev/websocket_settings_session_ceiling_and_metrics.md`
- [ ] **COMMIT: Commit Changes**
  - Proposed: `refactoring(metrics): PYPOST-1146 modularize MetricsManager delegation`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1146/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1146/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_metrics_manager_modularization.py`

### STEP 4: Development

- `pypost/core/qt/metrics.py`
- `pypost/core/qt/metrics_tracking.py`
- `pypost/core/qt/metrics_websocket.py`
- `scripts/audit_baseline_metrics.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1146/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1146/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1146/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_settings_session_ceiling_and_metrics.md`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID) — not committed per task scope
