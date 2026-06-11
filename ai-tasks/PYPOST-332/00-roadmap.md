# Roadmap: PYPOST-332

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added unit tests for `TabsPresenter.close_tabs_for_request_ids` edge cases.
  - [x] Added integration tests wiring `requests_deleted` → `close_tabs_for_request_ids`.
  - [x] Verified existing `CollectionsPresenter.requests_deleted` signal tests.
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**
  - [x] Documented test coverage in `doc/dev/collection_item_delete.md`.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-332/10-requirements.md`
- Programming Language: Python 3.10+

### STEP 2: Architecture

- `ai-tasks/PYPOST-332/20-architecture.md`

### STEP 3: Development

- `tests/test_tabs_presenter.py`
- `tests/test_delete_open_tabs_integration.py`
- `tests/test_collections_presenter.py` (existing signal tests)

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-332/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-332/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-332/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-332/70-dev-docs.md`
- `doc/dev/collection_item_delete.md`

## Recommended Branch

`test/PYPOST-332-delete-open-tab-tests`
