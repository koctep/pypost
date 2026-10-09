# Roadmap: PYPOST-1265

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Independent requirements review passed; orchestrator accepted Step 1.
  - Created `10-requirements.md` from the assigned issue and PYPOST-1229 debt follow-up 3,
    reconciled with PYPOST-1266 (`0345e88c`), PYPOST-1267 (`6c39e40f`) and PYPOST-1264
    (`2703575a`, debt shortcut 2: cancellation repro in-flight margin).
  - Built a coverage map of every ticket item against current tests: real JSON record-level
    cancellation, legacy-reader rejection and large-file JSON/YAML decode cancellation are
    already covered; the "supported legacy reader" contract is obsolete (now rejected).
  - Remaining gaps scoped as acceptance criteria: pre-start interruption, real YAML
    record-level cancellation, exact outcome counts in the PYPOST-1229 worker/teardown
    regressions, and an in-flight proof independent of runner speed.
  - Implementation language: Python (test-only change expected; no design recorded).
  - Open question for Step 2: reaching the worker's pre-read interruption check reliably
    (Qt may reset the interruption flag on thread start).
  - `make verify-ai-tasks` passed: 396 completed tasks; 2 grandfathered legacy gaps.
  - Acceptance remains with the autonomous orchestrator after independent review.
- [x] **STEP 2: High-Level Architecture Design**
  - Independent architecture review passed; orchestrator accepted Step 2. Two optional review
    notes (patch result dialog in teardown test; mutation table clarity) carried into Step 3.
  - Created `20-architecture.md`. The design is test-only, with no production changes.
  - Open question resolved: a `requestInterruption()` made before `start()` is ignored
    because the thread is not running. This is documented in Qt 6, and a throwaway probe
    (Qt/PySide6 6.11.1, run via `make test WORKERS=1`, then deleted) confirmed it. The
    pre-start branch is reachable only between `start()` and the first check in `run()`.
  - Gap 1: a `_GatedWorker` subclass holds `run()` before calling the unmodified
    `super().run()`. This gives legitimate branch coverage at worker and presenter
    (teardown) level. The proof is that the reader is never called.
  - Gap 2: new `test_production_yaml_reader_contract[None/1/2]` in the reader-contract
    module, reusing `_run_reader`.
  - Gaps 3 and 4: an event-held `_HeldReader` replaces the sleep-based `_slow_reader`.
    DirectConnection outcome counts. Each test asserts `processed == [1, 2] < total` and
    that the reader observed `CollectionImportCancelled`. The 300 ms wall-clock threshold
    is replaced by a structural check.
  - Step 3 red: mutation red in a throwaway scratch worktree (four mutations mapped to
    gaps). There is no natural red because behavior does not change.
  - Risks: the existing 1000 ms explicit teardown budget under oversubscription (not
    widened). PYPOST-1320 is not triggered (no `exc_info` path, no new `process_until`).
  - `make verify-ai-tasks` passed: 396 completed tasks; 2 grandfathered legacy gaps.
- [x] **STEP 3: Failing Repro Test**
  - Independent repro review passed (mutation red accepted); orchestrator accepted Step 3.
  - Mutation red (no natural red: test-only task, production unchanged). Changed tests:
    `tests/test_collection_import_cancellation_repro.py` and
    `tests/test_collection_import_reader_contract.py`. No production file touched.
  - New node ids: `test_worker_pre_start_interruption_skips_reader`,
    `test_teardown_pre_start_interruption_applies_nothing` (gap 1, `_GatedWorker` +
    `_RecordingReader`); `test_production_yaml_reader_contract[None|1|2]` (gap 2, reuses
    `_run_reader`).
  - Changed node ids (gaps 3/4): `test_worker_stops_promptly_when_interrupted_mid_parse`,
    `test_teardown_worker_stops_after_interruption`,
    `test_default_teardown_requests_interruption_before_wait_and_discards_result`. They use
    `_HeldReader(hold_at=1)` released by `_release_on_interrupt` after the real
    `requestInterruption()`, `_OutcomeRecorder` (DirectConnection) exact counts,
    `processed == [1, 2] < total` and `observed == ["CollectionImportCancelled"]`. The 300 ms
    assert, `_slow_reader`, `_RECORD_DELAY_S` and `_WAIT_AFTER_INTERRUPT_MS` are removed.
    `process_until` waits are replaced by bounded `Event.wait`. The explicit-budget test now
    patches `show_collection_import_result` and asserts it is not called (Step 2 review
    note 1), and asserts one presenter `collection_import_parse_cancelled` log.
  - Unmodified production:
    `make test WORKERS=1 PYTEST_ARGS='tests/test_collection_import_cancellation_repro.py
    tests/test_collection_import_reader_contract.py'` passed, 6 + 19 = 25 tests.
  - Mutation worktree: `git worktree add --detach <scratchpad>/mut1265 HEAD` with the changed
    tests copied in. Its `.venv` held symlinks to `/home/src/.venv` (bin/lib/include/pyvenv.cfg)
    plus fresh stamp files, so `make -C` did not reinstall. A throwaway probe test showed that
    `pypost.__file__` resolved to the worktree (`pythonpath = "."`). Baseline in the worktree:
    25 passed. "Old" = HEAD's original `test_collection_import_cancellation_repro.py`, run
    against the same mutation.

    | Mutation (one at a time, reverted after) | New/changed tests red (assertion failures) | Old tests still green |
    | --- | --- | --- |
    | M1: delete pre-start `isInterruptionRequested()` check in `run()` | both pre-start tests: `reader calls=[PosixPath('/dummy/import-cancellation.json')]` vs `[]` | all other 23 tests green (no prior coverage) |
    | M2 (YAML-specific, distinct from M4): record `on_progress` exceptions swallowed for `.yaml/.yml` in `load_collection_import_candidates` | YAML `[1]`: `[(1,3),(2,3),(3,3)] == [(1,3)]`; YAML `[2]`: `... == [(1,3),(2,3)]` | JSON contract `[None/1/2]` and YAML `[None]` green (no prior YAML record coverage) |
    | M3: emit `parse_cancelled` twice | 3 PYPOST-1229 tests + 2 pre-start tests: `exactly one parse_cancelled emission`, `[True, True] == [True]`; existing exact-count tests (final guard, reader contract with cancel) also red | old HEAD repro: worker, explicit-teardown and default-teardown tests pass (only the unchanged final-guard test fails) |
    | M4: `_emit_progress` ignores interruption for `done > 0` (post-read guard still cancels) | 3 PYPOST-1229 tests: `processed=[1..40]` vs `[1, 2]`; YAML/JSON `[1/2]`, opaque and `shapes[1-*]` also red (overlap with M2 on YAML, stated) | old HEAD repro: default-teardown test green (gap); old worker test red only via the 300 ms wall clock; old explicit teardown red only via budget timeout |
  - Worktree removed (`git worktree remove --force`); `git worktree list` shows only `/home/src`.
- [x] **STEP 4: Development**
  - Independent implementation review passed (test-only, no production change); orchestrator
    accepted Step 4.
  - [x] No production change needed (test-only design). `git diff --stat -- pypost/` is empty.
    The reviewed Step 3 tests are unchanged and are already green. Only the two test modules
    are modified.
  - [x] Acceptance criteria to covering node ids (all in `tests/`):
    - DoD 1 (pre-start):
      `test_collection_import_cancellation_repro.py::test_worker_pre_start_interruption_skips_reader`,
      `::test_teardown_pre_start_interruption_applies_nothing`.
    - DoD 2 (real YAML record-level):
      `test_collection_import_reader_contract.py::test_production_yaml_reader_contract[None|1|2]`.
    - DoD 3 (exact outcome counts) and DoD 4 (in-flight proof, `processed == [1, 2] < total`):
      `test_collection_import_cancellation_repro.py::test_worker_stops_promptly_when_interrupted_mid_parse`,
      `::test_teardown_worker_stops_after_interruption` (1000 ms budget),
      `::test_default_teardown_requests_interruption_before_wait_and_discards_result`
      (5000 ms default budget).
    - DoD 5 (no regressions): every `tests/test_collection_import*.py` module passed in all
      runs below.
    - DoD 6 (timeouts and bounded waits): module `pytestmark = pytest.mark.timeout(30)` in both
      modules. Gate and hold waits are bounded `Event.wait(timeout=_GATE_S)`. Worker waits are
      `wait(_WORKER_WAIT_MS)`. `_stop_worker` runs in `finally`.
    - DoD 7: `make test` and `make verify-ai-tasks` results below.
  - [x] Serial run: `make test WORKERS=1 PYTEST_ARGS='tests/test_collection_import_cancellation_repro.py
    tests/test_collection_import_reader_contract.py'` gave 2/2 files passed (25 tests), 2.89 s.
  - [x] Oversubscribed parallel runs (default WORKERS=8 on 6 CPUs), 5 times:
    `make test PYTEST_ARGS='tests/test_collection_import_cancellation_repro.py
    tests/test_collection_import_reader_contract.py tests/test_collection_import*.py'`.
    Runs 1-5 all PASS: 17 passed, 0 failed, 1 skipped (`test_collection_import_teardown_latency.py`,
    exit 5, no tests selected). Wall clock 14.1-15.2 s, about 7x speedup.
  - [x] Full `make test` run 1: 369 passed, 3 failed, 7 skipped (294 s). All 3 are known
    pre-existing issues:
    - `tests/test_env_persistence_e2e.py::test_presenter_load_shows_no_env_when_key_missing_for_encrypted_data`:
      `OSError: [Errno 39] Directory not empty` in `TemporaryDirectory` cleanup (PYPOST-1311).
    - `tests/test_environment_export_ui.py`: 8/8 tests PASSED, then the process exited with -7
      (crash after pass, PYPOST-1315).
    - `tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing`:
      FAILED at 60 s, then the file hit the 120 s worker timeout (PYPOST-1299).
  - [x] Full `make test` run 2: 371 passed, 1 failed, 7 skipped (292 s). The only failure is
    `test_pytest_exit_policy.py` (PYPOST-1299, same signature).
    No new failures, so no base-commit worktree repro was needed. No import-module failures.
  - [x] `make lint` passed (flake8 `pypost/`, Markdown lint, link check). Note: `make lint`
    does not run flake8 on `tests/`. `make typecheck` passed (mypy baseline OK, 181 known
    errors). `make verify-ai-tasks` passed (396 completed tasks, 2 grandfathered legacy gaps).
- [x] **STEP 5: Code Cleanup**
  - Independent cleanup review passed; orchestrator accepted Step 5.
  - Created `40-code-cleanup.md`. Scope: the diff of the two test modules only, with no
    production change.
  - Cleanup-path fix (Step 3 review note) in `test_teardown_pre_start_interruption_applies_nothing`.
    The started thread goes into `started` before the `isinstance(..., _GatedWorker)` assert.
    `finally` releases the gate if gated and always calls `_stop_worker(started)`. No
    assertion was changed.
  - `_HeldReader` docstring: `observed` records exception type names. No unused
    imports, helpers or constants, no debug code, and no line over 100 characters remain.
  - `make lint` flake8 covers only `pypost/` (PYPOST-1303), and `make typecheck` does not
    cover `tests/`. The test files were therefore inspected directly.
  - `make lint` passed, and `make typecheck` passed (baseline OK, 181 known errors).
  - The targeted `make test WORKERS=1 ...` run passed twice: 2/2 files each time, 3.01 s and
    2.81 s. `make verify-ai-tasks` passed (396 completed tasks, 2 grandfathered gaps).
- [x] **STEP 6: Observability**
  - Independent observability re-review passed; orchestrator accepted Step 6.
  - Created `50-observability.md`. Decision: no production logging or metrics change.
    The task is test-only (`git diff -- pypost` is empty), and `10-requirements.md`
    excludes production changes unless a regression proves a defect. None was found.
  - Inventoried the existing events. Worker: `collection_import_parse_worker_cancelled`
    (INFO, `path`), the one handler used by the pre-read, record and post-read
    checkpoints. Presenter: `collection_import_parse_cancelled` (INFO, `from_state`,
    plus metric outcome `rejected`), and the teardown events `_teardown_started`,
    `_worker_interrupting` (WARNING), `_worker_interrupted`, `_worker_interrupt_timeout`
    (WARNING) and `_wait_idle_*`.
  - Tests that assert logs: the pre-start worker test (one worker cancelled record) and the
    explicit-budget teardown test (`worker_interrupted`, one
    `parse_cancelled from_state=parsing`, no `interrupt_timeout`). The other new or changed
    tests are behaviour-only, which the requirements allow.
  - Follow-up candidates for Step 7 (not implemented): the cancellation log has no
    `stage`/`done`/`total` field, so the checkpoint cannot be identified; the metric outcome
    `rejected` (`collection_import_actions.py:581`) is shared with file-picker dismissal
    (`path is None`, `:286-288`); log assertions are uneven across the teardown tests.
  - `make verify-ai-tasks` passed (396 completed tasks; 2 grandfathered legacy gaps).
    `make lint` was not run because no code was touched.
  - Review fix: corrected the `rejected` follow-up wording in `50-observability.md` and above
    (shared with file-picker dismissal, not busy-skip, which logs only and records no metric).
    `make verify-ai-tasks` passed again (396 completed tasks; 2 grandfathered legacy gaps).
- [x] **STEP 7: Technical Debt Analysis**
  - Independent tech-debt review passed and blocker review returned SAFE TO CLOSE;
    follow-ups filed as PYPOST-1328..1331; orchestrator accepted Step 7.
  - Created `60-tech-debt.md`. Scope: the test-only diff (`git diff -- pypost` is empty).
  - BLOCKER check: both changed modules keep `pytestmark = pytest.mark.timeout(30)`, and every
    event wait and worker wait is bounded. There are no blockers.
  - New follow-ups (each `Jira: TBD`): checkpoint `stage`/`done`/`total` on the worker
    cancellation log (Low); a separate `cancelled` metric outcome instead of `rejected` (Low);
    a shared `tests/helpers/` outcome recorder (Low); moving the final-guard test to
    `_stop_worker` and bounded waits (Lowest). Uneven log assertions and the 1000 ms budget are
    accepted with no ticket.
  - Referenced existing tickets instead of re-filing them: PYPOST-1303 (lint `tests/`),
    PYPOST-1320 (`process_until` deadlock), PYPOST-1326 (live logging cost) and PYPOST-1327
    (teardown test seam).
  - Pre-existing failures recorded as NON-BLOCKER: PYPOST-1299, PYPOST-1311 and PYPOST-1315.
  - `make verify-ai-tasks` passed (396 completed tasks; 2 grandfathered legacy gaps).
- [x] **STEP 8: Dev Docs**
  - Independent dev-docs review passed; orchestrator accepted Step 8.
  - Updated `doc/dev/collection_import.md` (existing doc; no new file, no index change).
    New section `### Cancellation test layout (PYPOST-1265)`: path-to-test map; pre-start
    proof via `_GatedWorker` and why (Qt drops `requestInterruption()` before `start()`);
    real JSON/YAML record-level contract; in-flight proof via `_HeldReader` +
    `_release_on_interrupt` (`processed == [1, 2]`, no wall clock); `_OutcomeRecorder`
    exact counts; bounds/cleanup; make command; mutation-red M1-M4; existing log events
    (from `50-observability.md`); follow-ups PYPOST-1328..1331.
  - Refreshed stale text: the PYPOST-1266 coverage paragraph no longer says JSON/YAML and
    lifecycle matrices "remain PYPOST-1265 scope"; the Known follow-ups PYPOST-1265 entry now
    says done and links the new section. The doc had no `_slow_reader` or 300 ms text; the
    new section notes that they were replaced.
  - Claims checked against the two test modules, `collection_import_parse_worker.py`, the
    Makefile and the STEP 3/4 records. All added lines are 100 characters or fewer. Internal
    anchors (`#cancellation-test-layout-pypost-1265`, `#cooperative-cancellation-pypost-1229`,
    `#preparation-checkpoints-pypost-1267`, `#observability`) and the relative link to
    `ai-tasks/PYPOST-1265/60-tech-debt.md` were checked by hand.
  - `make lint` passed (flake8 `pypost/`, Markdown lint OK 16 files, relative link check OK
    18 files). Note: the doc lint and link checks cover User Guide/README files only, not
    `doc/dev/`, so this doc is checked by hand only. `make verify-ai-tasks` passed
    (396 completed tasks; 2 grandfathered legacy gaps).
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1265/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1265/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1265/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1265/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1265/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
