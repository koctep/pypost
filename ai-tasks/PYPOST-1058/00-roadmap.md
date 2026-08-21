# Roadmap: PYPOST-1058

## Task Metadata

- **Implementation language**: Python
- **Branch name**: fix/PYPOST-1058-durable-aligned-import-recount

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather and document business requirements for durable-aligned collection import result recount after save failure
  - [x] `ai-tasks/PYPOST-1058/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research collection import apply and result recounting
  - [x] Create `ai-tasks/PYPOST-1058/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_collection_import.py::TestRecountCollectionImportPlan`
  - [x] `tests/test_collection_import_apply.py::test_partial_save_failure_returns_failed_collection_ids`
  - [x] `tests/test_collections_import_ui.py::TestImportCollections::test_partial_save_failure_recounts_summary_to_durable_membership`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Update `apply_imported_collections` in `pypost/core/collection_import_apply.py` to return `CollectionImportApplyResult` with `failed_ids` and backwards-compatible sequence protocol
  - [x] Iteration 2: Implement pure function `recount_collection_import_plan(plan, failed_ids)` in `pypost/core/collection_import.py` to adjust counts based on durable persistence
  - [x] Iteration 3: Integrate plan recount into `CollectionImportActions._finish_import` in `pypost/ui/presenters/collection_import_actions.py` on save failures
  - [x] Iteration 4: Validate test suite across unit, apply, and UI levels (55 passed)
- [x] **STEP 5: Code Cleanup**
  - [x] Run static analysis and linting (`make lint`, `flake8`, `make typecheck`)
  - [x] Enforce formatting, line length <= 100 chars, no dead code or unused imports, no debug prints
  - [x] Ensure explicit timeout markers per `do-testing` on all test files
  - [x] Run test suite to verify green status (55 passed)
  - [x] Create `ai-tasks/PYPOST-1058/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Review collection import lifecycle observability across apply and UI presenter layers
  - [x] Document structured log events (`collection_import_save_failed`, `collection_import_reconciled`, `collection_import_applied`, `collection_import_completed`)
  - [x] Verify recount alignment in `collection_import_completed` event and test validation via caplog
  - [x] Create `ai-tasks/PYPOST-1058/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Evaluate implementation for shortcuts, code smells, missing tests, and performance concerns
  - [x] Catalog pre-existing test suite failures as non-blockers
  - [x] Produce `ai-tasks/PYPOST-1058/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Update `doc/dev/collection_import.md` with durable-aligned result recount via `recount_collection_import_plan`
  - [x] Document `CollectionImportApplyResult` structure and sequence protocol backwards compatibility
  - [x] Explain durable-aligned result summary dialog and completed logs reflecting persisted outcome
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1058/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1058/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_collection_import.py::TestRecountCollectionImportPlan`
- `tests/test_collection_import_apply.py::test_partial_save_failure_returns_failed_collection_ids`
- `tests/test_collections_import_ui.py::TestImportCollections::test_partial_save_failure_recounts_summary_to_durable_membership`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1058/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1058/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1058/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_import.md`

### COMMIT

- `63d21097` — `fix(import): PYPOST-1058 recount import result after save failure`
