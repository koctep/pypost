# PYPOST-1264: Technical Debt Analysis

Scope analysed: the working-tree diff (`pypost/ui/presenters/collection_import_actions.py`,
`pypost/ui/presenters/collections_presenter.py`,
`tests/test_collection_import_cancellation_repro.py`, `doc/dev/collection_import.md`,
`ai-tasks/PYPOST-376/baseline-metrics.md`), the new module
`pypost/core/collection_import_lifecycle_policy.py` and the new tests
`tests/test_collection_import_lifecycle_policy.py`,
`tests/test_collection_import_teardown_budget_repro.py`,
`tests/test_collection_import_teardown_policy.py` and
`tests/test_collection_import_teardown_latency.py`.

**Timeout markers (do-testing BLOCKER check): no blocker.** Every new or changed test module has
an explicit module-level `pytestmark` timeout: lifecycle policy `timeout(10)`, budget repro
`timeout(30)`, teardown policy `timeout(30)`, latency `[slow, timeout(120)]`, cancellation repro
`timeout(30)`. Internal waits are bounded (`Event.wait(timeout=...)`, `QThread.wait(ms)`,
`process_until(..., timeout_ms=...)`).

## Shortcuts Taken

1. **The real-thread guard turns off the actions logger while it times teardown.**
   `test_teardown_real_threads_stay_within_loose_bound` sets the
   `pypost.ui.presenters.collection_import_actions` logger `disabled = True` for the timed
   `teardown(...)` call and restores it in `finally`. Step 4 found that about 99 % of the elapsed
   time under the parallel runner went to pytest live logging (`log_cli = true`,
   `log_cli_level = "WARNING"` in `pyproject.toml`). One WARNING record took p50 ≈ 5 ms and up to
   413 ms, and teardown emits 5 of them. The workaround is scoped and correct, but it treats a
   symptom. Any test that times code which logs at WARNING or above has the same problem under
   `make test`. CI already avoids it: `.github/workflows/test.yml:146` passes `-o log_cli=false`
   (PYPOST-671). The local `make test` parallel runner does not, so local runs and CI time
   differently. This is **test-infrastructure debt beyond this task**. See follow-up 5.
2. **The cancellation repro budget went from 150 to 1000 ms.**
   `tests/test_collection_import_cancellation_repro.py::_TEARDOWN_WAIT_IDLE_MS` grew because the
   budget now has to cover P0, P1 and the final join (design Risk 1: the extra fixed 100 ms grace
   is gone). 1000 ms is still under the ~2 s reader, so the test still proves an in-flight worker
   is interrupted. The margin is smaller, though. If the reader got faster, or the runner much
   slower, the test could pass without exercising the in-flight path. Broader cancellation
   coverage is already tracked by PYPOST-1265, so no new ticket.
3. **A test patches a private method.**
   `test_default_teardown_requests_interruption_before_wait_and_discards_result` now
   monkeypatches `actions._wait_idle_until` (with `# type: ignore[method-assign]`), because
   teardown stopped calling the public `wait_idle`. The test is now tied to an internal name.
   A public observation seam, such as a phase hook or a logged `interrupted_before_wait` field,
   would remove the coupling. See follow-up 6.
4. **The configurability decision rests on one machine.** The DoD 6 decision ("limits stay
   fixed policy values") comes from a single `make test-slow` run on one Linux 6.8 aarch64 host
   with 6 CPUs and a low load. The latency module asserts structure only. Nothing re-runs it
   automatically, so the evidence can go stale. This is accepted by design (Risk 2: no timing
   gate in CI), and the procedure is documented in `doc/dev/collection_import.md`. No ticket.

## Code Quality Issues

1. **`CollectionsPresenter` is not a main-window teardown owner** (design Risk 5, found in
   Step 2, out of scope by requirements). `pypost/ui/main_window_lifecycle.py:67-76` only builds
   the owner list from `tabs`, `history_panel`, `history_manager` and `env`. Application shutdown
   therefore never calls `CollectionsPresenter.teardown`, and the budgeted import teardown added
   here only protects callers that invoke it directly (panel teardown, tests). On app close
   during an import, the parse or library worker is not interrupted or joined under any budget.
   This is the most significant remaining gap. See follow-up 1.
2. **The main-window budget still lives outside any policy.** `main_window_lifecycle.py:55`
   (`budget_ms = 5000 if timeout_ms is None ...`) and `:166` (`window.teardown(timeout_ms=5000)`)
   are unnamed literals. They match `CollectionImportLifecyclePolicy.teardown_budget_ms` only by
   coincidence. The application-wide budget and its per-owner allocation were out of scope.
   Fix this together with follow-up 1 so that the collections owner gets its share from a named
   application shutdown policy. See follow-up 4.
3. **The same 100 ms literal remains in other components** (left out of scope by requirements):
   `_WORKER_FINISH_WAIT_MS = 100` in `pypost/core/qt/environment_storage_gateway.py:25`,
   `pypost/core/qt/collection_storage_gateway.py:14`,
   `pypost/ui/widgets/settings/encryption_migration_section.py:31` and
   `pypost/ui/widgets/websocket/stream_view.py:87`. Each is a named module constant with a
   PYPOST-829 H3 rationale. They are not unnamed duplicates, but the "change it in one place"
   goal of this task only holds for collection import. See follow-up 2.
4. **The teardown docstring said more than the code guarantees (fixed in this ticket).**
   `CollectionImportActions.teardown` used to say "the sum of all waits never exceeds it". The
   Step 7 fix loop corrected the docstring and `doc/dev/collection_import.md`: they now limit
   the guarantee to the deadline-bounded phase waits, name the uncapped nested
   `_on_worker_finished` join (Risk 3) and long queued GUI slots as overruns, and state
   `budget_tolerance_ms` (50 ms) as a contract value. No debt remains for this item.
5. **No runtime code reads `budget_tolerance_ms`.** It is validated in `__post_init__` and
   documented as a contract value, but no code or CI test uses it. That is deliberate (it is not
   a timing gate), but a policy field nothing reads can drift from the documentation unnoticed.
   It is low risk. Note it in follow-up 6.
6. **`collections_presenter.py` is close to its size cap.** It grew from 520 to 527 LOC against
   a cap of 535 (`ai-tasks/PYPOST-376/baseline-metrics.md`). The next change to this presenter
   will probably have to extract code first. No ticket yet; it is tracked by the existing
   baseline-metrics gate.
7. **The presenter resolves the budget twice.** `CollectionsPresenter.teardown` calls
   `resolve_budget_ms(timeout_ms)` for its log line and then passes the raw `timeout_ms` to the
   actions, which resolve it again. The function is pure, so the result is the same. This is a
   cosmetic issue with no action needed.

## Missing Tests

1. **App shutdown with an import in flight.** No test exists, and none can until follow-up 1
   connects collections to main-window teardown.
2. **The nested worker-finish join inside teardown P1** (Risk 3). No test shows that
   `_on_worker_finished` running inside P1's `processEvents()` adds no more than
   `worker_finish_join_ms` to teardown, or that the
   `collection_import_worker_finish_wait_timeout` warning fires when native exit stalls. This
   was an accepted design decision. A fake-clock or spy test would pin it down. See follow-up 7.
3. **A long GUI slot during teardown** (Risk 3, APPLYING state). Teardown is not exercised
   while a long queued slot runs. This is out of scope because APPLYING is not rolled back, and
   lifecycle matrices belong to PYPOST-1265.
4. **Real JSON/YAML input, pre-start interruption and user-close matrices.** These are
   already tracked by PYPOST-1265. No new ticket.
5. Otherwise covered: policy defaults, validation and immutability; deadline arithmetic and
   truncation; the shared-budget sum ≤ B (real-sleep spies and fake clock); `B = 0` probes with
   only `wait(0)`; no-app poll slicing; idempotent idle teardown; presenter `None` resolution; the
   new log fields (caplog).

## Performance Concerns

1. **The library worker cannot be interrupted** (design Risk 4). A stuck
   `LibraryOperationWorker` always uses the rest of the caller budget (up to 5000 ms by default)
   and teardown returns unclean. The thread is then abandoned while still running. Behaviour is
   unchanged by this task, but this is the worst-case shutdown delay for collection import. See
   follow-up 3.
2. **The nested worker-finish join is uncapped** (design Risk 3). It can add up to 100 ms beyond
   the deadline when the slot runs inside P1 and native thread exit stalls. Normally the join is
   instant, because `finished` is emitted after `run()` returns. This is accepted within the
   documented 50 ms tolerance in the normal case. Only the pathological case goes over, and the
   existing warning makes it visible. Capping it would risk "QThread destroyed while running".
   There is no ticket beyond the test in follow-up 7.
3. **P1 busy-pumps.** `_wait_idle_until` calls `processEvents()` in a tight loop when a
   `QApplication` exists, so it uses one GUI-thread core for up to the whole budget. This
   behaviour is unchanged (the old `QElapsedTimer` loop did the same), and only the no-app path
   uses `idle_poll_ms`. It is acceptable for a shutdown path. No ticket.
4. **Live logging makes timing slow and inconsistent under `make test`** (see Shortcut 1). It
   affects test wall time and the reliability of timing assertions, not production.

## Follow-up Tasks

New follow-ups, filed in Jira via jira-create-issue (estimated). Before writing each one,
`ai-tasks/` was searched for an existing ticket.

1. **Register collection import teardown with main-window shutdown.** Add
   `CollectionsPresenter` (or its import actions) to the owner list in
   `pypost/ui/main_window_lifecycle.py:67-76`, with its share of the shutdown budget. Add a
   regression test for app close during file and library import. Priority: **High**.
   Jira: [PYPOST-1321](https://pypost.atlassian.net/browse/PYPOST-1321).
   (No existing ticket found; this is PYPOST-1264 design Risk 5.)
2. **Consolidate the remaining `_WORKER_FINISH_WAIT_MS = 100` constants** in
   `environment_storage_gateway.py`, `collection_storage_gateway.py`,
   `encryption_migration_section.py` and `stream_view.py` behind named lifecycle policies (one
   shared or one per component), as done for collection import. Priority: **Low**.
   Jira: [PYPOST-1323](https://pypost.atlassian.net/browse/PYPOST-1323).
   (Earlier mentions in PYPOST-829, PYPOST-881, PYPOST-1076, PYPOST-1228 and PYPOST-1286 debt
   notes are accepted-by-design remarks, not tickets.)
3. **Make `LibraryOperationWorker` interruptible.** Support cooperative cancellation for
   connected-library import and refresh, so teardown can stop it within the final join instead
   of using the whole remaining budget and abandoning a running thread. Priority: **Medium**.
   Jira: [PYPOST-1324](https://pypost.atlassian.net/browse/PYPOST-1324).
   (No existing ticket; design Risk 4.)
4. **Name the application shutdown budget.** Replace the 5000 literals at
   `main_window_lifecycle.py:55` and `:166` with a named application lifecycle policy. Decide
   the per-owner allocation, including the collections owner from follow-up 1. This can be done
   in the same ticket as follow-up 1. Priority: **Low**.
   Jira: [PYPOST-1325](https://pypost.atlassian.net/browse/PYPOST-1325).
5. **Make `make test` live logging cheap or switch it off for parallel runs.** Under
   `scripts/run_parallel_tests.py`, `log_cli` WARNING output costs up to hundreds of ms per
   record. That makes any timing assertion depend on how much the code logs, and it differs from
   CI, which already passes `-o log_cli=false`. Options: pass `-o log_cli=false` (or a higher
   level) from the parallel runner, keep the `--log-file` capture, and record the decision.
   Once this is fixed, remove the logger-disable workaround in
   `tests/test_collection_import_teardown_budget_repro.py`. Priority: **Medium**.
   Jira: [PYPOST-1326](https://pypost.atlassian.net/browse/PYPOST-1326).
   (Related: PYPOST-671 only covered the CI `test.yml` override and is already applied there.
   It does not cover local `make test`.)
6. **Polish the teardown API and test seam.** Add a public observation seam for teardown phases,
   so `test_default_teardown_requests_interruption_before_wait_and_discards_result` stops
   patching private `_wait_idle_until`. Either use `budget_tolerance_ms` somewhere checkable
   (for example the slow latency module) or keep it documentation-only. (The `teardown`
   docstring was already fixed in this ticket: it names the Risk 3 exceptions and calls
   `budget_tolerance_ms` a contract value, not a runtime check.) Priority: **Low**.
   Jira: [PYPOST-1327](https://pypost.atlassian.net/browse/PYPOST-1327).
7. **Test the nested worker-finish join during teardown** (Risk 3). Add a spy or fake-clock
   test where `_on_worker_finished` runs inside P1 and its join exceeds the remaining budget.
   Assert that the overrun is bounded by `worker_finish_join_ms` and that the warning is
   emitted. Priority: **Lowest**.
   Jira: [PYPOST-1322](https://pypost.atlassian.net/browse/PYPOST-1322).

Pre-existing test failures seen during this run. These are already filed; do not file again.

- `tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing`
  — `NON-BLOCKER — pre-existing` — times out at 120 s (also at base c3f8e183). Jira: PYPOST-1299.
- `tests/test_environment_export_ui.py` (module process exits -11/-7 after all tests pass) —
  `NON-BLOCKER — pre-existing` — segfault after pass, flaky at base. Jira: PYPOST-1315.
- `tests/test_env_persistence_e2e.py::test_presenter_load_shows_no_env_when_key_missing_for_encrypted_data`
  — `NON-BLOCKER — pre-existing` — tmp cleanup `OSError: Directory not empty`. Jira: PYPOST-1311.
- `tests/test_collection_import_teardown_repro.py::test_unexpected_reader_exception_requires_teardown_and_reaps_worker`
  and `tests/test_collections_import_ui.py::test_zero_candidates_treated_as_invalid_file` —
  `NON-BLOCKER — pre-existing` — `process_until` watchdog `threading.Timer` start deadlock
  (reproduced at base c3f8e183). Jira: PYPOST-1320.
