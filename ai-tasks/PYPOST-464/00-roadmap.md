# Roadmap: PYPOST-464

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `tests/test_history_masking_metrics.py` with Prometheus scrape assertions for
    empty vs non-empty `hidden_keys`.
- [x] **STEP 4: Code Cleanup**
  - [x] flake8 and line-length checks on scoped test file (pass)
  - [x] `40-code-cleanup.md` created
- [x] **STEP 5: Observability**
  - [x] Documented metric counter test scope; no production observability changes
  - [x] `50-observability.md` created
- [x] **STEP 6: Review and Technical Debt**
  - [x] Tech-debt analysis completed; closes PYPOST-446 metric negative-test gap
  - [x] `60-tech-debt.md` created
- [x] **STEP 7: Dev Docs**
  - [x] Updated `doc/dev/sensitive_data_masking_policy.md` with metric test section
  - [x] Updated `ai-tasks/PYPOST-446/70-dev-docs.md` test references
  - [x] `70-dev-docs.md` created

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python 3.10+ (same as the pypost application codebase; see `.cursor/lsr/do-python.md`).

## Related Work

- Parent feature: [PYPOST-446](https://pypost.atlassian.net/browse/PYPOST-446) (hidden-variable
  masking in request history)
- Prerequisite context: [PYPOST-462](https://pypost.atlassian.net/browse/PYPOST-462) (history
  masking e2e acceptance test)
- Source debt item: [PYPOST-446 technical-debt analysis](ai-tasks/PYPOST-446/60-tech-debt.md)
- Related, separate coverage:
  - [PYPOST-463](https://pypost.atlassian.net/browse/PYPOST-463) (refactor history-recording block)
  - [PYPOST-465](https://pypost.atlassian.net/browse/PYPOST-465) (CI/local dependency provisioning)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-464/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-464/20-architecture.md`

### STEP 3: Development

- `tests/test_history_masking_metrics.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-464/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-464/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-464/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-464/70-dev-docs.md`

## Task Context

- Programming language: Python
- Jira issue: PYPOST-464
- Summary: Add explicit masking metric tests for empty vs non-empty hidden_keys
- Type: Debt (test coverage)
- Recommended branch name: `test/PYPOST-464-hidden-mask-metric-tests`
