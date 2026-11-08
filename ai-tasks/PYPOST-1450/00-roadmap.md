# Roadmap: PYPOST-1450

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1450/10-requirements.md` — requirements, user stories, and acceptance criteria for dedicated discovery status UI
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research existing UI layout, widget hierarchies, and state handling
  - [x] Dedicated discovery UI design and state machine separation
  - [x] Step 3 failing repro test plan (`tests/test_discovery_status_ui_repro.py`)
  - [x] `ai-tasks/PYPOST-1450/20-architecture.md` — architectural specification and component design
- [x] **STEP 3: Failing Repro Test**
  - [x] Create automated red repro suite in `tests/test_discovery_status_ui_repro.py`
  - [x] Validate red failure against current production code via `make test`
- [x] **STEP 4: Development**
  - [x] Defined dedicated discovery and fetch widget IDs in `pypost/ui/widget_ids.py` and exported in `__all__` and `KEY_WIDGET_IDS`
  - [x] Constructed dedicated discovery containers (`discovery_container`, `discovery_error_container`) and child controls in `ImportCollectionVariablesDialog`
  - [x] Separated cancel and retry slots (`_on_cancel_discovery`, `_on_retry_discovery`, `_on_cancel_loading`, `_on_retry_fetch`)
  - [x] Decoupled manifest discovery worker events from fetch loading chrome
  - [x] Verified all 6 repro tests in `tests/test_discovery_status_ui_repro.py` pass green along with related async discovery and fault injection suites
- [x] **STEP 5: Code Cleanup**
  - [x] Run static analysis and formatting checks (verified line length <= 100 characters)
  - [x] Run `make lint` and verify zero issues in modified files
  - [x] Run `make typecheck` and verify mypy baseline OK
  - [x] Run `make check-baseline-metrics`
  - [x] Run targeted test suite (`tests/test_discovery_status_ui_repro.py`,
    `tests/test_async_manifest_discovery_repro.py`,
    `tests/test_remote_collection_fault_injection_repro.py`)
  - [x] Run `make verify-ai-tasks`
  - [x] Create `ai-tasks/PYPOST-1450/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Audit and decouple manifest discovery vs collection fetch logging in `pypost/ui/dialogs/import_collection_variables_dialog.py`
  - [x] Update discovery failure to `collection_variable_manifest_discovery_failed` (WARNING with exc context) and verify `collection_variable_manifest_discovery_retry_requested` in `_on_retry_discovery()`
  - [x] Author caplog test cases in `tests/test_discovery_status_ui_repro.py` (`test_discovery_observability_lifecycle_events`, `test_remote_fetch_observability_lifecycle_events`)
  - [x] Verify logging behavior and test pass via Make-only test target (`make test`)
  - [x] Create `ai-tasks/PYPOST-1450/50-observability.md` documenting log inventory, pipeline separation, metrics, and test coverage
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts taken, code quality, missing tests, and performance considerations
  - [x] Verify test timeouts per do-testing standards (`tests/test_discovery_status_ui_repro.py`)
  - [x] Record pre-existing issues and Jira-tracked follow-up tasks
  - [x] Create `ai-tasks/PYPOST-1450/60-tech-debt.md` documenting technical debt and resolution of PYPOST-1424 item 1
- [x] **STEP 8: Dev Docs**
  - [x] Document PYPOST-1450 dedicated discovery status UI (`discovery_container`,
    `discovery_label`, `cancel_discovery_btn`, `discovery_error_container`,
    `discovery_error_label`, `retry_discovery_btn`) completely separated from remote
    collection fetch chrome (`loading_container`, `error_container`) in
    `doc/dev/workspace_environment_variable_import.md`
  - [x] Document dedicated cancellation and retry slots (`_on_cancel_discovery` vs
    `_on_cancel_loading`, `_on_retry_discovery` vs `_on_retry_fetch`)
  - [x] Document decoupled state machines and isolated observability logging
  - [x] Add `tests/test_discovery_status_ui_repro.py` to automated testing catalog
  - [x] Validate markdown line length (<= 100 characters), formatting, and run
    `make lint-docs` and `make check-docs-links`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1450/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1450/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_discovery_status_ui_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1450/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1450/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1450/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/workspace_environment_variable_import.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
