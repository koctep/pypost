# Roadmap: PYPOST-167

**Language:** Python

**Branch (reference):** `documentation/PYPOST-167-metrics-singleton-di`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Verified `MetricsManager` has no singleton `__new__` override
  - [x] Confirmed only `main.py` instantiates `MetricsManager()` in production code
  - [x] Confirmed consumers receive injected `MetricsTrackerProtocol` (PYPOST-44/73/74)
  - [x] No source refactor required — debt resolved by PYPOST-44
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

- `ai-tasks/PYPOST-167/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-167/20-architecture.md`

### STEP 3: Development

- Verification only — no source changes (resolved by PYPOST-44)
- `tests/test_metrics_protocol.py` — protocol compliance
- `tests/test_metrics_manager.py` — facade unit tests

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-167/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-167/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-167/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/solid_audit.md`
- `doc/dev/tech-debt/PYPOST-40.md`
- `ai-tasks/PYPOST-167/70-dev-docs.md`
