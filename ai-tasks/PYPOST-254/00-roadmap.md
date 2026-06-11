# Roadmap: PYPOST-254

Debt follow-up from [PYPOST-29](https://pypost.atlassian.net/browse/PYPOST-29): New-tab metrics source validation.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Validates `plus_button`, `shortcut`, and maps unknown values to `unknown`
  - [x] Tests in `tests/test_metrics_manager.py`
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

- `ai-tasks/PYPOST-254/10-requirements.md`

### STEP 3: Development

- `pypost/metrics/metrics_registry.py`
- `tests/test_metrics_manager.py`

### STEP 6: Review

- `ai-tasks/PYPOST-254/60-tech-debt.md`
