# Roadmap: PYPOST-1451

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1451/10-requirements.md` — requirements, user stories, and acceptance criteria for automated discovery failure and retry coverage
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research existing failure and retry paths across `ManifestDiscoveryWorker` and `ImportCollectionVariablesDialog`
  - [x] Design automated test architecture with Mermaid flowchart and fault injection strategies
  - [x] Specify failing repro test plan in `tests/test_async_manifest_discovery_failure_repro.py`
  - [x] `ai-tasks/PYPOST-1451/20-architecture.md` — system/test architecture, fault injection, retry lifecycle, decoupling verification, and failing repro plan
- [x] **STEP 3: Failing Repro Test**
  - [x] Author automated failing repro test suite in `tests/test_async_manifest_discovery_failure_repro.py`
  - [x] Cover network and OS faults on `list_connections` (`ConnectionResetError`, `TimeoutError`, `BrokenPipeError`, `OSError`)
  - [x] Cover mid-stream catalog traversal failure on `list_manifest_collections` and verify partial result discard
  - [x] Cover end-to-end fail-then-recover retry lifecycle and verify red repro probe (stale error label reset contract)
  - [x] Cover rapid retries and obsolete generation failure/completion discard
  - [x] Cover cooperative cancellation during fault state via `cancel_discovery_btn`
  - [x] Cover workspace collection usability and local variable import during remote discovery failure
  - [x] Cover clean background worker cancellation and thread join on dialog close / reject
  - [x] Review subagent verification of red repro test
- [x] **STEP 4: Development**
  - [x] Clear `discovery_error_label` text in `_start_manifest_discovery()` on discovery start
  - [x] Clear `discovery_error_label` text in `_on_discovery_completed()` on successful discovery completion
  - [x] Clear `discovery_error_label` text in `_on_retry_discovery()` when retry is requested
  - [x] Validate all 7 automated tests in `tests/test_async_manifest_discovery_failure_repro.py` turn green
  - [x] Verify zero regression across related test suites (`tests/test_async_manifest_discovery_repro.py`, `tests/test_discovery_status_ui_repro.py`)
  - [x] Independent subagent review of Step 4 implementation
- [x] **STEP 5: Code Cleanup**
  - [x] Run static analysis and formatting checks (verified line length <= 100 characters)
  - [x] Run `make lint` and verify zero issues in modified files
  - [x] Run `make typecheck` and verify mypy baseline OK
  - [x] Run `make check-baseline-metrics`
  - [x] Run targeted test suite (`tests/test_async_manifest_discovery_failure_repro.py`,
    `tests/test_async_manifest_discovery_repro.py`,
    `tests/test_discovery_status_ui_repro.py`)
  - [x] Run `make verify-ai-tasks`
  - [x] Create `ai-tasks/PYPOST-1451/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Audit and document worker-level events in `pypost/ui/workers/manifest_discovery_worker.py`
  - [x] Audit and document dialog-level events in `pypost/ui/dialogs/import_collection_variables_dialog.py`
  - [x] Verify caplog coverage for discovery failure, worker failure, retry requests, cancellations, and stale discards in `tests/test_async_manifest_discovery_failure_repro.py`
  - [x] Create `ai-tasks/PYPOST-1451/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Document resolution of PYPOST-1424 Tech Debt Item 2 (discovery failure + retry automated coverage)
  - [x] Audit test suite timeouts per `do-testing` rules (all 7 tests have module and function level timeouts)
  - [x] Document shortcuts taken (repeated error label string resets)
  - [x] Document code quality considerations (all-or-nothing catalog traversal)
  - [x] Document missing test scenarios (extreme multi-connection scale with concurrent network faults)
  - [x] Document performance concerns (synchronous `wait(1000)` join on UI thread during dialog teardown)
  - [x] Document follow-up tasks and pre-existing non-blockers (PYPOST-1509, PYPOST-1397, PYPOST-1413, PYPOST-1452, PYPOST-1453)
  - [x] Create `ai-tasks/PYPOST-1451/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Document automated discovery failure and retry coverage
    (`tests/test_async_manifest_discovery_failure_repro.py`) in
    `doc/dev/workspace_environment_variable_import.md`
  - [x] Document network and OS fault injection on `list_connections` (`ConnectionResetError`,
    `TimeoutError`, `BrokenPipeError`, `OSError`)
  - [x] Document mid-stream catalog traversal failure handling on `list_manifest_collections` and
    partial result discard
  - [x] Document end-to-end fail-then-recover retry lifecycle and `discovery_error_label` reset
    contract
  - [x] Document monotonic generation tracking and stale discard during rapid retries
  - [x] Document cooperative cancellation during fault state and workspace collection isolation
  - [x] Document clean worker thread termination and bounded join on dialog close
  - [x] Reference follow-up tickets (PYPOST-1515, PYPOST-1516, PYPOST-1517)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1451/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1451/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_async_manifest_discovery_failure_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1451/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1451/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1451/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/workspace_environment_variable_import.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
