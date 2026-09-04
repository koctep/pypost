# Roadmap: PYPOST-1229

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1229/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1229/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_collection_import_cancellation_repro.py::`
    `test_worker_stops_promptly_when_interrupted_mid_parse`
  - `tests/test_collection_import_cancellation_repro.py::`
    `test_teardown_worker_stops_after_interruption`
- [x] **STEP 4: Development**
  - [x] Added `CollectionImportCancelled` exception, `parse_cancelled` Signal, and
    `isInterruptionRequested()` checks (before the parse and after each
    `_emit_progress`) in `pypost/core/qt/collection_import_parse_worker.py`;
    `run()` now catches `CollectionImportCancelled` before the generic
    `except Exception` and logs+emits `parse_cancelled` at info level.
  - [x] Connected/disconnected `parse_cancelled` in `_start_parse()`/`teardown()`
    and added `_on_parse_cancelled` (resets to IDLE, no dialog) in
    `pypost/ui/presenters/collection_import_actions.py`.
  - [x] Orchestrator independently ran full `make test`: 327 passed, 4 failed
    (5 test node ids), 6 skipped. All dedupe into the already-open PYPOST-1261
    cluster (function_expression_resolver x2, solid_audit_baseline, template_service
    x2) — no new failures from this task's diff.
  - [x] Reordered `CollectionImportActions.teardown()` to request worker
    interruption before its `wait_idle()` call, preserving the bounded join and
    reap path; added default-timeout regression coverage proving interruption is
    observed before waiting and no cancelled parse result is applied.
- [x] **STEP 5: Code Cleanup**
  - [x] Applied focused formatting and cleanup to the Step 4 source/test files:
    corrected stale cancellation wording, added test-helper typing, removed a
    redundant timeout marker, and normalized docstring wrapping.
  - [x] Created `ai-tasks/PYPOST-1229/40-code-cleanup.md` with Make validation
    results and baseline failure classification.
  - [x] `make lint` and `make typecheck` passed; `make test` cancellation tests
    passed. Remaining failures are documented non-blockers (PYPOST-1261/
    PYPOST-1262 baseline and load-sensitive environment issues).
- [x] **STEP 6: Observability**
  - Added INFO `collection_import_parse_cancelled from_state=...` at the GUI cancellation
    terminal handler and verified it with the existing caplog regression.
  - Created `ai-tasks/PYPOST-1229/50-observability.md` documenting cancellation/teardown logs,
    payload-size safety, and why no new collection-import metrics were added.
  - `make lint`, `make typecheck`, and focused cancellation `make test` passed. Full `make test`
    retained the documented PYPOST-1261 baseline failures (328 passed, 6 skipped, 3 failed
    files).
- [x] **STEP 7: Technical Debt Analysis**
  - Created `ai-tasks/PYPOST-1229/60-tech-debt.md` with implementation trade-offs, residual
    cancellation limits, missing tests, performance concerns, timeout-marker review, and
    pre-existing failure rows for PYPOST-1261/PYPOST-1262.
  - Step 7 validation completed through Make targets; the step remains `[/]` for independent
    review and blocker-gate acceptance.
  - [x] Blocker-fix loop: added the final publication interruption guard and deterministic
    presenter-path race coverage; corrected PYPOST-1261/PYPOST-1262 failure attribution in
    `60-tech-debt.md`.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/collection_import.md` with cooperative cancellation architecture,
    signal/lifecycle flow, reader and presenter extension guidance, bounded-wait behavior,
    observability, troubleshooting, and PYPOST-1261/PYPOST-1262 baseline-failure notes.
  - `make lint` passed, including Markdown and relative-link checks.
  - `make verify-ai-tasks` passed; Step 8 remains `[/]` for independent review.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1229/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1229/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1229/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1229/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1229/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
