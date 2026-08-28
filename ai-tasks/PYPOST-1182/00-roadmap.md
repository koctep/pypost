# Roadmap: PYPOST-1182

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1182/10-requirements.md`
  - Implementation language recorded: Python
  - Scope: Eliminate indefinite Qt / event loop waits in `tests/test_collections_import_ui.py` during `make test`
  - Zero test degradation: no skipping, xfailing, or deleting existing collection import test coverage
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1182/20-architecture.md`
  - Lifecycle synchronization design: `CollectionImportActions.wait_idle()`, `CollectionsPresenter.wait_import_idle()`
  - Failing repro test strategy for Step 3
  - Headless test dialog protection and deterministic event loop draining
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_collections_import_ui_repro.py`
- [x] **STEP 4: Development**
  - [x] Implemented `wait_idle(timeout_ms: int = 5000) -> bool` on `CollectionImportActions` in `pypost/ui/presenters/collection_import_actions.py`
  - [x] Implemented `wait_import_idle(timeout_ms: int = 5000) -> bool` delegation on `CollectionsPresenter` in `pypost/ui/presenters/collections_presenter.py`
  - [x] Updated `tests/test_collections_import_ui.py` `_wait_import` helper and test calls to deterministically drain background worker threads before widget teardown
  - [x] Verified `tests/test_collections_import_ui_repro.py` and `tests/test_collections_import_ui.py` pass without hangs or stalls
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1182/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1182/50-observability.md`
  - Structured logging for `CollectionImportActions.wait_idle()` on start, completion (`elapsed_ms`), and timeout warnings
  - Verified `caplog` test coverage in `tests/test_collections_import_ui_repro.py`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1182/60-tech-debt.md`
  - Documented shortcuts taken (synchronous event loop draining loop, default timeout parameters)
  - Evaluated code quality refactor opportunities (explicit state machine, test helper extraction)
  - Identified missing edge-case tests (concurrent triggers, early worker abort/cancellation)
  - Confirmed explicit pytest timeout markers present on all touched/new test files
  - Triaged follow-up tasks and pre-existing baseline issues
- [x] **STEP 8: Dev Docs**
  - `doc/dev/collection_import.md`
  - Documented `CollectionImportActions.wait_idle(timeout_ms)` and `CollectionsPresenter.wait_import_idle(timeout_ms)` lifecycle synchronization APIs
  - Documented deterministic worker thread draining during testing and widget teardown without Qt event loop hangs
  - Documented structured observability log events (`collection_import_wait_idle_started`, `collection_import_wait_idle_completed`, `collection_import_wait_idle_timeout`)
  - Updated troubleshooting guide for wait_idle timeout and test hang scenarios
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1182/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1182/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1182/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1182/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1182/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_import.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
