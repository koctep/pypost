# Roadmap: PYPOST-264

Debt follow-up from [PYPOST-29](https://pypost.atlassian.net/browse/PYPOST-29): New-tab metrics
source validation (`plus_button`, `shortcut`, `unknown`).

Suggested branch: `refactoring/PYPOST-264-new-tab-source-validation`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Verified `_normalize_new_tab_source` at metrics API boundary
  - [x] Added `collections_context` regression test for full allowed-source set
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

- `ai-tasks/PYPOST-264/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-264/20-architecture.md`

### STEP 3: Development

- `pypost/core/metrics_registry.py`
- `tests/test_metrics_manager.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-264/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-264/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-264/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/request_actions.md`
- `ai-tasks/PYPOST-264/70-dev-docs.md`
