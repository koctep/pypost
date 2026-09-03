# Roadmap: PYPOST-1228

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1228/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1228/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_collections_import_ui.py::TestImportCollectionsBusyDuringApply::test_is_busy_true_while_applying_imported_collections`
- [x] **STEP 4: Development**
  - [x] Added Qt-free `pypost/core/collection_import_state.py` with
    `CollectionImportState(str, Enum)`: IDLE, PREPARING, PARSING, APPLYING (mirrors
    `ImportConflictDecision` pattern).
  - [x] In `pypost/ui/presenters/collection_import_actions.py`: replaced `_preparing` bool with
    `_state: CollectionImportState` (default IDLE); redefined `is_busy()` as
    `self._state is not CollectionImportState.IDLE`; renamed `_set_preparing(active)` to
    `_set_state(state)` with equivalent button/busy-cue/log side effects. Wired transitions:
    IDLE->PREPARING in `_start_parse()` before worker construction, PREPARING->PARSING right
    after `worker.start()`, PARSING->IDLE on `parse_failed` or empty-collections
    `parse_completed`, PARSING->APPLYING on valid `parse_completed` (set before
    `_finish_import()` is called), APPLYING->IDLE as the final statement of `_finish_import()`.
    `teardown()` forces IDLE unconditionally.
  - [x] Updated pre-existing tests that poked `_preparing`/`_set_preparing` internals directly
    to use the renamed `_state`/`_set_state` API: `tests/test_collections_import_ui.py`
    (`TestImportCollectionsBusyDuringApply`, the target failing repro — setup line only, its
    assertions unchanged), `tests/test_collection_import_teardown_repro.py`, and
    `tests/test_collection_import_async_gaps.py`. One test
    (`test_is_busy_retains_true_while_worker_instance_exists`, PYPOST-1148) asserted the
    superseded contract that a lingering `_worker` alone implies busy; rewritten as
    `test_is_busy_reflects_state_independent_of_worker_presence` to document the new,
    intentional decoupling (architecture doc: "`_worker` no longer participates in `is_busy()`
    at all"). `test_teardown_structured_logging`'s busy-worker simulation updated to set
    `_state = PARSING` (previously relied on worker-presence alone implying busy).
  - [x] Ran targeted suite (`tests/test_collections_import_ui.py`,
    `tests/test_collection_import_teardown_repro.py`, `tests/test_collection_import_async_gaps.py`)
    via `make test` — 3/3 files passed, including the target failing repro test now green.
  - [x] Ran full `make test` suite: 336 files, 323 passed, 7 failed, 6 skipped. All 7 failures
    are pre-existing and unrelated to this change (none touch `collection_import_actions.py`,
    `collection_import_state.py`, or reference `_state`/`_preparing`/`is_busy`):
    `test_collection_import_profile.py::test_plan_collection_import_large_dataset_performance`
    (flaky perf budget, 143ms vs 100ms, under parallel CPU load; module untouched by this
    ticket), `test_environment_list_widget.py` (segfault, exit code -11, unrelated
    EnvironmentListWidget import flow), `test_function_expression_resolver.py` (2 tests,
    `invalid_argument`/`invalid_arity` mismatch, template expression validation, unrelated),
    `test_solid_audit_baseline.py::test_markdown_snapshot_matches_current_metrics` (snapshot
    drift, unrelated), `test_template_service.py` (2 tests, same
    `invalid_argument`/`invalid_arity` mismatch as above). Flagged for the orchestrator per
    failing-tests-triage — not fixed here, not filed as Jira by this step.
  - [x] Orchestrator independently re-ran full `make test` twice: 324 passed/6 failed and
    323 passed/7 failed (parallel-run variance in the segfault/timeout flakes). All failures
    across both runs dedupe into the exact same pre-existing/flaky clusters already filed
    during PYPOST-1184 — PYPOST-1261 (function_expression_resolver x2, solid_audit_baseline,
    template_service x2, environment_list_widget segfault), PYPOST-1262 (makefile
    lifecycle/targets 120s worker timeout), PYPOST-1263 (collection_import_profile flaky perf).
    Confirmed all three issues still open in Jira. No new Jira issues needed.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1228/50-observability.md`
  - Added one new `DEBUG collection_import_state_changed from=%s to=%s` log line in
    `CollectionImportActions._set_state()`, naming the actual enum value on both sides of every
    transition (including the new `PARSING→APPLYING` and `APPLYING→IDLE` edges this ticket
    introduces). Existing INFO/WARNING/ERROR/DEBUG logging at all other transition points
    (parse start/completed/failed, teardown, busy-cue shown/cleared) was reviewed and left
    unchanged — it already adequately covers those events; only the binary busy-cue DEBUG log's
    inability to distinguish PREPARING/PARSING/APPLYING was a real gap. Re-ran
    `tests/test_collections_import_ui.py`, `tests/test_collection_import_teardown_repro.py`,
    `tests/test_collection_import_async_gaps.py` — 30 passed, no regressions to existing
    substring-based `caplog` assertions.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1228/60-tech-debt.md`
  - No shortcuts, no architecture deviations, no new hardcoded values. All new/changed test
    files (`test_collections_import_ui.py`, `test_collection_import_teardown_repro.py`,
    `test_collection_import_async_gaps.py`) carry module-level `pytestmark =
    pytest.mark.timeout(...)`. Two minor missing-test gaps and one pre-existing code-quality
    item noted as future follow-ups (non-blocking). Pre-existing failures
    (PYPOST-1261/1262/1263) recorded, not re-investigated.
- [x] **STEP 8: Dev Docs**
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1228/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1228/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1228/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1228/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1228/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
