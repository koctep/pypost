# PYPOST-1265: Technical Debt Analysis

Scope: this task changes only tests. It touches
`tests/test_collection_import_cancellation_repro.py` and
`tests/test_collection_import_reader_contract.py`, and `git diff -- pypost` is empty.

**BLOCKER check (do-testing).** There is no blocker:

- Both modules declare `pytestmark = pytest.mark.timeout(30)`.
- Every gate and hold wait is a bounded `Event.wait(timeout=_GATE_S)`, with `_GATE_S = 5.0`.
- Worker joins use `wait(_WORKER_WAIT_MS)`, which is 5000 ms.
- Cleanup runs in `finally`. It sets the release events first, then calls `_stop_worker`.

## Shortcuts Taken

1. **The pre-start branch is reached through a test-only `_GatedWorker` subclass.** The
   subclass overrides `run()` and holds it before the unmodified `super().run()` call. It does
   not fake the predicate (see `20-architecture.md`, cases C and E). Production has no public
   hook to hold `run()`, so the test depends on how `run()` is structured: the
   `isInterruptionRequested()` check must stay the first statement after the `started` log.
   This is accepted by design, and the M1 mutation guards it. There is no follow-up.
2. **The default-budget teardown test still patches the private `_wait_idle_until`.** That
   code was inherited from PYPOST-1264 and is unchanged here. It is already tracked as
   [PYPOST-1327](https://pypost.atlassian.net/browse/PYPOST-1327) (teardown observation seam).
   Do not re-file it.
3. **The record-level YAML contract uses one small fixture with three records.** The
   large-file decode cancellation is already covered by
   `tests/test_collection_import_decode_cancellation.py`, so this is enough. None.

## Code Quality Issues

1. **The unchanged final-guard test duplicates the shared cleanup.** The test is
   `test_final_publication_guard_discards_result_after_last_checkpoint`, and Step 5 flagged
   this in review. It still uses `process_until` for waits that need no Qt event delivery
   (`final_checkpoint_returned`, `worker_finished`). Its inline `finally` block repeats
   `_stop_worker`. It was outside the PYPOST-1265 diff, so it was left as is. Before migrating
   it, note that its middle wait depends on queued presenter slots
   (`not actions.is_busy()`). That wait needs event pumping, so it must stay `process_until`,
   `qt_wait` or `wait_import`. The test logs nothing with `exc_info`, so the
   [PYPOST-1320](https://pypost.atlassian.net/browse/PYPOST-1320) deadlock does not apply to
   it today. → Follow-up 4.
2. **The DirectConnection outcome-recording code is repeated in four modules.** The new
   `_OutcomeRecorder` connects `parse_cancelled`, `parse_completed` and `parse_failed` with
   `Qt.ConnectionType.DirectConnection`. The same code appears in:
   - `test_collection_import_reader_contract.py`: `_run_reader` and the shape test, twice
   - `test_collection_import_progress.py`
   - `test_collection_import_decode_cancellation.py`

   `_GatedWorker` and `_HeldReader` are used only in the repro module, and keeping them local
   is still the right call (Step 2 decision). `_OutcomeRecorder` (plus `_stop_worker`) is the
   part that other cancellation tests would reuse. → Follow-up 3.
3. **Lint and typecheck do not cover `tests/`.** `make lint` runs flake8 only on `pypost/`, and
   `make typecheck` covers only `pypost/core`, `pypost/models` and `pypost/ui`. Both changed
   modules were checked by hand in Step 5. This is already tracked as
   [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303). Do not re-file it.
4. **Observability limits found in Step 6.** Both are production changes outside this task's
   scope:
   - **No checkpoint field on the worker cancellation log.**
     `collection_import_parse_worker_cancelled` logs only `path`. The pre-read, record and
     post-read checkpoints all produce the same line. → Follow-up 1.
   - **Cancellation and file-picker dismissal share one metric outcome.**
     `collection_import_file` records `rejected` both for cancellation
     (`collection_import_actions.py:581`) and when the file picker is dismissed (`:286-288`),
     so metrics cannot tell them apart. → Follow-up 2.

## Missing Tests

1. **Log assertions are uneven across the teardown tests.** Only
   `test_teardown_worker_stops_after_interruption` asserts the presenter
   `collection_import_worker_interrupted` and `collection_import_parse_cancelled` events. Two
   tests check behaviour only:
   - `test_teardown_pre_start_interruption_applies_nothing`
   - `test_default_teardown_requests_interruption_before_wait_and_discards_result`

   The requirements make behaviour the primary proof. The events have one exact contract in
   the explicit-budget test. Adding the same caplog checks to every test would duplicate it
   and add sensitivity to the live-logging setup
   ([PYPOST-1326](https://pypost.atlassian.net/browse/PYPOST-1326)). **Accepted, with no
   ticket.** If follow-up 1 adds a `stage` field, its ticket should add one stage-asserting log
   check per checkpoint.
2. Every other acceptance criterion has covering node ids (roadmap, STEP 4). None.

## Performance Concerns

1. **The explicit 1000 ms teardown budget under oversubscribed `make test`.** This risk was
   noted in Step 2. `test_teardown_worker_stops_after_interruption` keeps
   `_TEARDOWN_WAIT_IDLE_MS = 1000`, which is a real wall-clock budget.

   With the held reader, the budget now covers only the work after the release that follows
   the real `requestInterruption()`: one more checkpoint, the cancellation emit and thread
   exit. That is microseconds of work. It no longer has to outlast a reader that is still
   running, which was the margin from PYPOST-1264 shortcut 2.

   The remaining exposure is scheduler starvation of more than 1 s under parallel load. The
   costly live-logging WARNING path that made similar budgets flaky is tracked as
   [PYPOST-1326](https://pypost.atlassian.net/browse/PYPOST-1326).

   Evidence: five oversubscribed parallel runs (WORKERS=8 on 6 CPUs) and two full `make test`
   runs were all green for this test.

   **Accepted, with no new ticket.** If it ever flakes, treat it as a PYPOST-1326 symptom first.
   Do not widen the budget, because the test exists to prove the explicit budget is honoured.
2. Test runtime improved. The roughly 2 s `_slow_reader` sleep loop and the 300 ms wall-clock
   assert are gone, and the targeted serial run takes about 3 s. None.

## Follow-up Tasks

New follow-ups, filed in Jira via jira-create-issue (estimated). Before filing,
`ai-tasks/` was searched, and no existing key covers any of them.

1. **Add a checkpoint `stage` to the worker cancellation log.** Extend
   `collection_import_parse_worker_cancelled` with `stage=pre_read|record|post_read`, plus
   `done` and `total` for the record stage. A field log can then show where a shutdown stopped
   the parse. Add one log assertion per stage to the existing cancellation tests. This is a
   production change. Priority: **Low**.
   Jira: [PYPOST-1328](https://pypost.atlassian.net/browse/PYPOST-1328)
2. **Separate the cancellation metric outcome from file-picker dismissal.** Record a distinct
   outcome, for example `cancelled`, in `_on_parse_cancelled`
   (`collection_import_actions.py:581`) and keep `rejected` for a dismissed picker (`:286-288`).
   Check that dashboards and consumers of the `collection_import_file` outcome values accept
   the new value. This is a production change. Priority: **Low**.
   Jira: [PYPOST-1329](https://pypost.atlassian.net/browse/PYPOST-1329)
3. **Extract a shared parse-worker outcome recorder into `tests/helpers/`.** Move
   `_OutcomeRecorder`, which records DirectConnection cancelled, completed and failed lists,
   and optionally `_stop_worker`, into a helper such as
   `tests/helpers/collection_import_worker.py`. Switch the repeated inline wiring in
   `test_collection_import_reader_contract.py`, `test_collection_import_progress.py` and
   `test_collection_import_decode_cancellation.py` to the helper. Keep `_GatedWorker` and
   `_HeldReader` local unless a second module needs them. This change touches only tests.
   Priority: **Low**.
   Jira: [PYPOST-1330](https://pypost.atlassian.net/browse/PYPOST-1330)
4. **Modernise the final-guard test.** In
   `test_final_publication_guard_discards_result_after_last_checkpoint`:
   - Replace the inline `finally` cleanup with `_stop_worker`.
   - Replace the `process_until` waits that need no event delivery
     (`final_checkpoint_returned`, `worker_finished`) with bounded `Event.wait` and worker
     `wait(...)`.
   - Keep an event-pumping wait for the presenter idle condition.

   This touches only tests. Coordinate with PYPOST-1320 if that ticket changes `process_until`.
   Priority: **Lowest**.
   Jira: [PYPOST-1331](https://pypost.atlassian.net/browse/PYPOST-1331)

Existing tickets referenced. These are not re-filed:

- [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303): flake8 and lint coverage for
  `tests/`.
- [PYPOST-1320](https://pypost.atlassian.net/browse/PYPOST-1320): `process_until` watchdog
  deadlock. The final-guard test does not trigger it today.
- [PYPOST-1326](https://pypost.atlassian.net/browse/PYPOST-1326): cost of live logging under
  parallel `make test`. This is the main risk for the 1000 ms budget.
- [PYPOST-1327](https://pypost.atlassian.net/browse/PYPOST-1327): teardown observation seam
  (the private `_wait_idle_until` patch).

Pre-existing test failures seen during this task's runs (roadmap STEP 4). These are already
filed; do not file them again:

- `tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing`
  — `NON-BLOCKER — pre-existing` — fails at 60 s, then hits the 120 s worker timeout (seen in
  both full runs). Jira: [PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299).
- `tests/test_env_persistence_e2e.py::test_presenter_load_shows_no_env_when_key_missing_for_encrypted_data`
  — `NON-BLOCKER — pre-existing` — `OSError: [Errno 39] Directory not empty` during
  `TemporaryDirectory` cleanup (full run 1).
  Jira: [PYPOST-1311](https://pypost.atlassian.net/browse/PYPOST-1311).
- `tests/test_environment_export_ui.py` (module) — `NON-BLOCKER — pre-existing` — all 8 tests
  passed, then the process exited with -7 (full run 1).
  Jira: [PYPOST-1315](https://pypost.atlassian.net/browse/PYPOST-1315).
