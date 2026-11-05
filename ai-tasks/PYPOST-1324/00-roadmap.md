# Roadmap: PYPOST-1324

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1324/10-requirements.md` — business goals, user stories, DoD,
    scope, entities, and Q&A for cooperative cancellation of connected-library
    background work so collection-import teardown can stop a stuck library
    operation within a bounded wait instead of burning the remaining budget
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1324/20-architecture.md` — cooperative interrupt for
    `LibraryOperationWorker` (CTS + `cancel` + `operation_cancelled`), cancel
    checkpoints on `list_entries` / `resolve_entries`, teardown P0 library interrupt
    and P3 interrupt-then-`bounded(final_join_ms)` join; Step 3 red-repro design
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_library_operation_interrupt_repro.py`
    - `test_teardown_calls_library_cancel_then_bounded_final_join` (Test A)
    - `test_cancel_aware_library_op_stops_cleanly_within_bounded_teardown` (Test B)
    - `test_cancel_ignoring_library_op_teardown_stays_within_caller_budget` (unclean guard)
- [x] **STEP 4: Development**
  - [x] `LibraryOperationWorker`: CTS + `cancel()` + `operation_cancelled`;
    `run()` uses `call_with_cancellation_token`
  - [x] Teardown P0/P3 call library `cancel()`; P3 `bounded(final_join_ms)`;
    wire `operation_cancelled` → IDLE; resolution start-site accepts token
  - [x] `list_entries` / `resolve_entries` / `_resolve_library_candidates`
    optional `cancellation_token` checkpoints
  - [x] Update teardown arithmetic / spy tests for P3 == `min(final_join, remaining)`
  - [x] Step 3 reds green (`test_library_operation_interrupt_repro.py`);
    suite failures triaged as pre-existing/flaky (see `60-tech-debt.md`)
  - [x] Review-gap fix: budget Test A/B assert library `cancel()` + P3
    `<= final_join_ms`; main-window shutdown repro asserts `cancels >= 1`
    (not join-only)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1324/40-code-cleanup.md`
  - Stale “failing/red” wording removed from interrupt / budget / shutdown repros
  - Budget repro `_FINAL_JOIN_MS` tied to lifecycle policy
  - `make lint` OK; focused 4-file suite passed; `make typecheck` baseline OK
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1324/50-observability.md`
  - Library cancel logs: `phase=p0` / `phase=p3`; honored join
    `wait_ms` / `elapsed_ms`; metrics outcome `cancelled`
  - Caplog/metrics coverage in `tests/test_collection_import_teardown_policy.py`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1324/60-tech-debt.md` — full Step 7 rewrite (replaced
    Step 4 triage-only draft)
  - No BLOCKER debt; timeout markers present on all touched test modules
  - Follow-up candidates TD-1..TD-5 (Phase D tickets new items); TD-6/TD-7
    accepted; pre-existing suite failures retained with existing Jira keys
  - Docs drift (TD-2) deferred to Step 8 of this task
- [x] **STEP 8: Dev Docs**
  - `doc/dev/collection_import.md` — interrupt-then-bounded library P3
    (`cancel()` + `final_join_ms`); retired Risk 4 / join-only wording;
    documented `phase=p0|p3`, cancelled join fields, metrics `cancelled` (TD-2)
  - `ai-tasks/PYPOST-1324/60-tech-debt.md` — TD-2 marked addressed by Step 8
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1324/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1324/20-architecture.md` — modules, teardown phase changes,
  interfaces, patterns, risks, and mandatory failing-repro plan for Step 3

### STEP 3: Failing Repro

- `tests/test_library_operation_interrupt_repro.py` (Test A/B + unclean guard; left `[/]` pending review)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1324/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1324/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1324/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_import.md` (library interrupt / P3 / observability updates)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
