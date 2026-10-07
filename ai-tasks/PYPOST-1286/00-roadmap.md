# Roadmap: PYPOST-1286

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1286/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1286/20-architecture.md`
  - [x] Deep research of WebSocket stream view export thread lifecycle & timing race
  - [x] Deep research of template service strict-conversion state isolation & caching
  - [x] Architecture: export completion signals, wait_for_export sync helper, teardown
  - [x] Architecture: immutable default catalog, template cache clear, conftest reset
  - [x] Failing repro design for Step 3 (`tests/test_pypost_1286_failing_repro.py`)
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_pypost_1286_failing_repro.py`
  - Reopened: deterministic queued-completion ownership and close-timeout regressions.
  - Added queued native-thread completion tests for busy ownership and wait finalization,
    plus an Event-held worker test requiring close refusal after the join timeout.
  - Focused `make test WORKERS=1 PYTEST_ARGS='tests/test_pypost_1286_failing_repro.py -q'`
    confirms three intended failures and four passes; no production changes in this repro pass.
- [x] **STEP 4: Development**
  - [x] Source code and test stabilization iterations
  - [x] Iteration 1: immutable `_DEFAULT_CATALOG`, `TemplateService.clear_cache()`
  - [x] Iteration 2: `WebSocketStreamView` export signals, `wait_for_export`, safe `closeEvent`
  - [x] Iteration 3: test sync (`wait_for_export`) and hermetic template test teardown
  - [x] Iteration 4: review fixes: `wait_for_export` via QEventLoop (no tests import),
    `export_finished` after worker cleanup, `FunctionRegistry.reset()`, `cleanup()`
  - [x] Snapshot `ai-tasks/PYPOST-376/baseline-metrics.md` regenerated via `make baseline-metrics`
  - [x] Deviation: conftest autouse `_reset_template_service_state` omitted (not needed for DoD)
  - Reopened: native thread exit must not release ownership before queued cleanup;
    closing must refuse or defer disposal when the worker join times out.
  - [x] Iteration 5: busy ownership now lasts through queued completion and native teardown;
    completion checks worker identity before clearing ownership or scheduling deletion.
  - [x] Iteration 6: bounded, stopped wait timers; nonpositive budgets only inspect state;
    cleanup returns its result and close refuses disposal while export remains owned.
  - [x] Reviewed three red lifecycle regressions now pass; all three focused test files and
    `make lint` pass. Added timeout-budget regressions for negative, zero, and positive budgets.
  - [x] Iteration 7: review fixes — singleShot context object; architecture doc synced to
    implementation.
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1286/40-code-cleanup.md`
  - Cleanup: removed unused test import and redundant timeout markers; docstring fix.
  - `make lint` and `make typecheck` pass (181 accepted mypy baseline errors).
  - 3 full-suite parallel runs (`make check`, `make test` x2): target tests pass in all.
  - Remaining failures are pre-existing or flaky Makefile/exit-policy subprocess tests,
    with base `10ba60b7` evidence; see `40-code-cleanup.md`. NON-BLOCKER, filed as
    PYPOST-1299 (exit-policy) and PYPOST-1298 (Makefile venv `flock` timeouts).
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1286/50-observability.md`
  - [x] Restored WARNING `websocket_stream_export_worker_finish_wait_timeout` on refused close
    (`wait_ms`, `action=close_refused`)
  - [x] DEBUG `..._finalize_deferred` (once per worker), `..._finalized deferrals=N`,
    `..._finished_ignored reason=stale_worker`; `clear_cache`/`reset` intentionally unlogged
  - [x] Caplog tests: `tests/test_pypost_1286_observability.py`
  - Focused tests (4 files), `make lint`, `make typecheck` (181 baseline) pass.
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1286/60-tech-debt.md`
  - TD-1..TD-14 recorded; no BLOCKER. Medium follow-ups: TD-1 (close guard not on tab
    removal path), TD-2 (template flake root cause unproven), TD-3 (lint skips `tests/`).
  - Low follow-ups: TD-4 (unused `FunctionRegistry.reset()`), TD-5 (shared test helpers).
  - Doc drift (TD-6: architecture "50 ms delay", Step 2 "conftest reset") recorded, not
    edited, because those steps are accepted.
  - Pre-existing: PYPOST-1299, PYPOST-1298 (NON-BLOCKER). Three flaky failures seen only at
    base: one tracked by PYPOST-1263, two recorded for the orchestrator to file.
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/websocket_message_stream.md`: export lifecycle (PYPOST-1286), busy
    ownership, finalize retry, public API, close refusal, log events, testing rules
  - [x] `doc/dev/template_service.md`: `clear_cache()`, immutable `_DEFAULT_CATALOG`,
    `FunctionRegistry.reset()`, unproven strict-conversion flake cause (PYPOST-1302)
  - [x] `doc/dev/template_expression_functions.md`: read-only default catalog note
  - `doc/dev/README.md` already links both main docs; no index change needed.
  - TD-6 doc drift left as recorded (accepted Step 2 artifacts not edited).
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1286/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1286/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_pypost_1286_failing_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1286/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1286/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1286/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
