# Roadmap: PYPOST-443

**Programming language:** Python

**Suggested branch:** `documentation/PYPOST-443-metric-rename-migration`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added deprecated `email_notification_failures_total` alias mirrored in
        `track_request_retry_exhaustion`
  - [x] Extended `tests/test_metrics_manager.py` for dual-export scrape assertion
  - [x] Added `doc/dev/metric_rename_migration.md` operator migration guide
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

- `ai-tasks/PYPOST-443/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-443/20-architecture.md`

### STEP 3: Development

- `pypost/core/metrics.py`
- `tests/test_metrics_manager.py`
- `doc/dev/metric_rename_migration.md`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-443/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-443/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-443/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/metric_rename_migration.md`
- `doc/dev/README.md`
