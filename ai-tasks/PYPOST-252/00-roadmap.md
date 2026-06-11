# Roadmap: PYPOST-252

Debt follow-up from [PYPOST-29](https://pypost.atlassian.net/browse/PYPOST-29) /
[PYPOST-251](https://pypost.atlassian.net/browse/PYPOST-251): pytest infrastructure and unit
tests for `RequestManager` and `StateManager`.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Verified existing pytest infrastructure (`pytest.ini`, `Makefile`, `tests/conftest.py`)
  - [x] Audited `RequestManager` and `StateManager` test coverage
  - [x] Added edge-case unit tests for uncovered branches
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (pytest + unittest)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-252/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-252/20-architecture.md`

### STEP 3: Development

- `tests/test_request_manager.py`
- `tests/test_request_manager_delete.py`
- `tests/test_settings_persistence.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-252/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-252/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-252/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/testing.md`
- `ai-tasks/PYPOST-252/70-dev-docs.md`

## Summary

Infrastructure was already in place (PYPOST-88, PYPOST-307, PYPOST-371, PYPOST-125). This task
closed the debt gap by documenting the satisfied state, mapping test modules to manager APIs,
and adding small edge-case tests to reach ~100% line coverage on both managers.
