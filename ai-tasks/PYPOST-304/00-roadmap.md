# Roadmap: PYPOST-304

Debt follow-up from [PYPOST-32](https://pypost.atlassian.net/browse/PYPOST-32): New-tab source normalization helper.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Normalizes caller-provided source strings at metrics API boundary
  - [x] Regression tests lock `plus_button`, `shortcut`, and `unknown` labels
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

- `ai-tasks/PYPOST-304/10-requirements.md`

### STEP 3: Development

- `pypost/metrics/metrics_registry.py`
- `tests/test_metrics_manager.py`

### STEP 6: Review

- `ai-tasks/PYPOST-304/60-tech-debt.md`
