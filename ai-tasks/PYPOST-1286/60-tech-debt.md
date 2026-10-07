# PYPOST-1286: Technical Debt Analysis

Scope: the uncommitted diff on `dev` (base `10ba60b7`) in `pypost/core/function_registry.py`,
`pypost/core/template_service.py`, `pypost/ui/widgets/websocket/stream_view.py`,
`tests/test_template_service.py`, `tests/test_websocket_stream_view_repro.py`, and the new
`tests/test_pypost_1286_failing_repro.py` and `tests/test_pypost_1286_observability.py`.

No item below is a **BLOCKER**. All new and changed test modules declare a module-level
`pytestmark = pytest.mark.timeout(30)`, and `tests/conftest.py` enforces timeout markers on every
collected test, so the do-testing timeout rule is met.

## Summary Table

| ID | Priority | Item | Follow-up | Jira |
| --- | --- | --- | --- | --- |
| TD-1 | Medium | `closeEvent` guard misses the tab-removal path | yes | Jira: [PYPOST-1301][] |
| TD-2 | Medium | Template flake root cause unproven (defensive fix) | yes | Jira: [PYPOST-1302][] |
| TD-3 | Medium | `make lint` runs flake8 on `pypost/` only | yes | Jira: [PYPOST-1303][] |
| TD-4 | Low | `FunctionRegistry.reset()` has no callers | yes | Jira: [PYPOST-1300][] |
| TD-5 | Low | Duplicated worker-hold test helpers | yes | Jira: [PYPOST-1304][] |
| TD-6 | Low | Doc drift: "50 ms delay", "conftest reset" | no | not required |
| TD-7 | Low | Stale-worker log test drives the slot directly | no | accepted by design |
| TD-8 | Low | Unbounded 10 ms finalize retry loop | no | accepted by design |
| TD-9 | Low | Nested `QEventLoop` in wait and close | no | accepted by design |
| TD-10 | Low | `sender()`-based worker identity check | no | accepted by design |
| TD-11 | Low | Hardcoded wait budgets | no | accepted by design |
| TD-12 | Low | `hasattr`-only public API repro test | no | covered implicitly |
| TD-13 | Low | `template_service.py` at 264/265 size baseline | no | low risk |
| TD-14 | Low | DoD 7 blocked by pre-existing failures | no | tracked under PYPOST-1298 |

TD-14 is tracked under PYPOST-1298 and PYPOST-1299; their links are under Follow-up Tasks.

## Shortcuts Taken

- **TD-2 (Medium): template strict-conversion fix is defensive, not root-caused.**
  `20-architecture.md` lists plausible causes of the template flake: a mutable
  `_DEFAULT_CATALOG`, leftover registrations, and the compile cache. No red repro showed any of
  them making
  `test_strict_conversion_keeps_literal_fallback_for_unrelated_failed_token` fail. The Step 3
  template repros assert only that the API exists (`MappingProxyType`, `clear_cache`). They do
  not reproduce the flake.
  - `TemplateService._compile_template` is an `lru_cache` closure built per instance in
    `__init__`, and `setUp` creates a new `TemplateService` for every test. The new
    `tearDown` → `clear_cache()` therefore does not change cross-test isolation. It only frees
    memory sooner.
  - Making `_DEFAULT_CATALOG` immutable is a sound hardening step. No test in the repository
    was shown to mutate it.
  - Verification is statistical: 3 full-suite parallel runs passed (`40-code-cleanup.md`). With
    the old failure rate of about 1 in 2, three passes would still happen by chance with
    probability (1/2)^3 ≈ 12.5%. DoD 3 ("0 failures across at least 3 runs") is met as written.
    The evidence does not prove the root cause was removed.
  - Follow-up: soak the target with at least 10 consecutive full-suite `make test` runs. If it
    fails again, capture the actual exception (`IntegerConversionError` or another error) and
    investigate further. Jira: [PYPOST-1302][].
- **TD-6 (Low): documentation drift, not a code shortcut.**
  `20-architecture.md` → "Mandatory — Failing Repro" → Assertion 1 still describes the delay
  as "e.g. 50 ms delay in thread exit". The implemented repro holds the worker with a
  `threading.Event` and contains no sleeps. The roadmap Step 2 sub-item still reads
  "conftest reset", but the decision recorded under Step 4 was to omit the conftest autouse
  fixture. Both artifacts belong to accepted (`[x]`) steps. Under `td-roadmap`, editing them
  would reopen those steps, and the roadmap must not rewrite earlier sub-items. This step
  records the drift and leaves the files unchanged. Recommended fix: Step 8 or the orchestrator
  replaces "50 ms delay" in `20-architecture.md` with "worker held on a `threading.Event`" and
  appends a correction note under roadmap Step 2. Not required as a Jira follow-up.

## Code Quality Issues

- **TD-1 (Medium): the close guard does not protect the real disposal path.**
  `WebSocketStreamView` is a child widget inside `WebSocketTab` (in a splitter). Qt sends
  `closeEvent` only to a widget that is explicitly `close()`d or to a top-level window. Closing
  a WebSocket tab goes through `presenter._tabs.removeTab(index)`
  (`pypost/ui/presenters/tabs_presenter_ws_close.py:80` and the generic close paths), which never
  calls `close()` on the stream view. Nothing in production calls `cleanup()` either.
  - Result: the new "refuse close while export is owned" contract (DoD 5, architecture "Widget
    Teardown Safety") is exercised only by tests that call `closeEvent` directly.
  - `QTabWidget.removeTab` does not delete the page, and nothing calls `deleteLater` on it. The
    removed tab and its view stay alive, hidden and leaked until exit, still holding
    `_export_worker`. A running export therefore finishes and finalizes normally after the tab
    is removed.
  - The real risk is app exit while an export is still running. The worker is a parentless
    `QThread` (`pypost/core/qt/websocket_stream_export_worker.py:39`, `super().__init__()`),
    held only by `view._export_worker`. Destroying it at shutdown while it runs can abort with
    "QThread: Destroyed while thread is still running". The leaked hidden tab is a secondary
    memory cost.
  - A refused close also gives the user no feedback, only a WARNING log, and no deferred close
    is scheduled after the export finishes.
  - Follow-up: hook export teardown into the WebSocket tab close/dispose path and app exit.
    Options are to ask or wait in the tab-close presenter or on app quit, or to reparent the
    worker and join it on `destroyed`. Add a test that removes a tab during an export.
    Jira: [PYPOST-1301][].
  - Priority stays Medium and the follow-up is unchanged. The corrected facts narrow the
    trigger from tab removal to app exit during an export, but the guard still does not cover
    any production disposal path, and a crash at exit can lose the export file.
- **TD-4 (Low): `FunctionRegistry.reset()` is dead code.**
  The method is at `pypost/core/function_registry.py` around line 75. Nothing in `pypost/` or
  `tests/` calls it. The Step 4 review added it as a test-isolation seam, but per-instance
  registries made it unnecessary. It also repeats the `{"to_int"}` literal from `__init__`, so
  the two could drift apart. Follow-up: either delete it, or have `__init__` call `reset()` and
  add a unit test. Jira: [PYPOST-1300][].
- **TD-5 (Low): duplicated test scaffolding and private-state coupling.**
  - `_PendingJoinWorker` is defined twice, once in `test_pypost_1286_failing_repro.py` and once
    in `test_pypost_1286_observability.py`.
  - The `entered`/`release` `blocked_run` monkeypatch pattern is copied three times.
  - The bounded `QEventLoop` spin is written inline twice.
  - The tests read or write `_export_worker`, `_export_btn` and `_finalize_export_worker`
    directly, so they depend on private implementation details.
  - Follow-up: move these into a `tests/helpers/` worker-hold fixture, and prefer the public
    `is_export_busy()` and `export_finished` where possible. Jira: [PYPOST-1304][].
- **TD-8 (Low): finalize retry is unbounded.**
  `_finalize_export_worker` re-arms `QTimer.singleShot(_FINALIZE_RETRY_MS, self, ...)` until
  `wait(0)` succeeds, with no cap. For a real `QThread`, `wait(0)` succeeds shortly after
  `finished`. The retry is tied to the view's lifetime through the context object and is
  logged once. Accepted by design. A retry cap with a WARNING would only help if a native join
  ever hangs.
- **TD-9 (Low): nested event loop.**
  `wait_for_export` runs a local `QEventLoop`. Because `closeEvent` calls it through `cleanup()`,
  a close can dispatch arbitrary queued events for up to 100 ms. The wait is bounded and the
  helper is mostly used by tests. Accepted by design. Revisit together with TD-1.
- **TD-10 (Low): `sender()` identity check.**
  `_on_export_worker_finished` uses `self.sender()`. Qt discourages this pattern, and it returns
  `None` for direct calls or lambda connections. It is correct for the current direct
  `worker.finished` connection. Accepted by design.
- **TD-11 (Low): hardcoded values.**
  `_WORKER_FINISH_WAIT_MS = 100` and `_FINALIZE_RETRY_MS = 10` are named module constants. The
  `wait_for_export(timeout_ms=5000)` default is a bare literal. None of these are configurable,
  and none need to be for a desktop UI. Accepted by design.
  - Comment drift: the comment above `_WORKER_FINISH_WAIT_MS`
    (`pypost/ui/widgets/websocket/stream_view.py:86`) still says "Short join after
    QThread.finished", but the constant is now the close-wait budget used by `cleanup()` and
    `closeEvent`. Fix the comment in the next change that touches the file. Not a Jira
    follow-up.
- **TD-13 (Low): file-size headroom.**
  The regenerated `ai-tasks/PYPOST-376/baseline-metrics.md` records `template_service.py` at
  264 lines against a 265 ceiling. The next addition to the file will hit the size gate. Low
  risk.

## Missing Tests

- **TD-1**: no test covers export teardown through the real WebSocket tab removal or widget
  destruction path. This is part of the TD-1 follow-up.
- **TD-7 (Low): the stale-worker test does not use a real stale worker.**
  `test_stale_worker_finished_signal_logs_debug_and_keeps_ownership` calls
  `_on_export_worker_finished()` directly, so `sender()` is `None`. No old
  `WebSocketStreamExportWorker` delivers a late `finished`. The view holds ownership until
  finalization, so a new worker cannot start before the old one is released. A genuinely stale
  `finished` cannot reach this slot in normal operation, which makes the branch a defensive
  guard. The test covers the log contract only. Accepted by design.
- **TD-12 (Low)**: `test_websocket_stream_view_public_signals_and_wait_helper` checks only
  `hasattr`/`callable`. The behavior tests in the same file cover the signals and
  `wait_for_export` implicitly. `export_completed` and `export_failed` relaying on the view
  have no direct `QSignalSpy`-style assertion. Covered implicitly.
- **TD-2**: no deterministic red repro exists for the template flake (see Shortcuts Taken).

## Performance Concerns

- Busy ownership now lasts through queued `finished` handling plus at least one `wait(0)`
  check, possibly with extra 10 ms retries. The export button therefore re-enables slightly
  later than before. This cannot be noticed by a user.
- `MappingProxyType` and the `clear_cache()` seam add no runtime cost.
- None of the changes add measurable CPU or memory overhead.

## Acceptance Criteria Honesty Check

- DoD 1–3: met for both target tests in 3 consecutive full-suite runs, with the caveat in TD-2.
- DoD 4: met for the WebSocket test. For the template test it is met by construction, since
  services are per test, but the original cause was never identified (TD-2).
- DoD 5: met inside the view. Not met on the production tab-removal path (TD-1).
- DoD 6: met. No assertions were removed; the target test now asserts `wait_for_export()`
  in addition to the file checks.
- DoD 7 (TD-14): `make lint` and `make typecheck` pass (181 baseline mypy errors). `make check`
  exits non-zero only because of pre-existing failures PYPOST-1298 and PYPOST-1299, so its
  `verify-ai-tasks` stage never ran inside `make check`. Run on its own in Step 7,
  `make verify-ai-tasks` passes (386 completed tasks, 2 grandfathered legacy gaps).
- DoD 8: met. Changed lines are 100 characters or fewer.

## Follow-up Tasks

### New Debt (filed during PYPOST-1286)

1. **TD-1 (Medium)**: guard `WebSocketStreamView` export teardown on WebSocket tab removal and
   widget destruction, and add a regression test. Jira: [PYPOST-1301][].
2. **TD-2 (Medium)**: soak-verify
   `tests/test_template_service.py::TestTemplateServiceRenderString::`
   `test_strict_conversion_keeps_literal_fallback_for_unrelated_failed_token` over at least 10
   full-suite parallel runs. Root-cause it if it fails again. Jira: [PYPOST-1302][].
3. **TD-3 (Medium)**: extend `make lint` (`Makefile` line 214, `flake8 --jobs=1 pypost/`) to
   cover `tests/`, or add a `lint-tests` target. Step 5 found an unused
   `process_until` import in `tests/test_websocket_stream_view_repro.py` that lint did not
   report. Fix or baseline the existing test-tree findings first. Jira: [PYPOST-1303][].
4. **TD-4 (Low)**: delete `FunctionRegistry.reset()`, or route `__init__` through it and test
   it. Jira: [PYPOST-1300][].
5. **TD-5 (Low)**: extract shared worker-hold helpers for the stream view tests into
   `tests/helpers/`. Jira: [PYPOST-1304][].

### Pre-existing Failures (already filed — do not re-file)

1. [PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299) — `NON-BLOCKER — pre-existing`
   - `tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing`
   - The `test_make_test_cov_...` variant in the same file.
   - Failed in 3 of 3 task-tree runs and at base `10ba60b7` (60 s pytest-timeout).
2. [PYPOST-1298](https://pypost.atlassian.net/browse/PYPOST-1298) — `NON-BLOCKER — pre-existing`
   - `tests/test_makefile_recipes.py`, `tests/test_makefile_markers.py`,
     `tests/test_makefile_install_stamp_contract.py`,
     `tests/test_makefile_stamp_otel_idempotency.py`,
     `tests/test_makefile_stamp_test_idempotency.py`, `tests/test_makefile_target_filtering.py`.
   - Setup timeouts on the shared base venv `fcntl.flock`
     (`tests/makefile_test_helpers.py:376`). Flaky in 1 of 3 task-tree runs;
     `test_makefile_target_filtering.py` also timed out at base.

### Base-only Flaky Failures (seen at base, not on task tree)

The base `10ba60b7` run (`make test`, 365 files: 354 passed / 5 failed / 6 skipped, wall clock
781 s) failed three files. None of them failed in the 3 task-tree runs. Each one has a tight
wall-clock budget that parallel load can exceed, and the task diff does not touch them. Under
the triage rules they are **flaky pre-existing** failures. Item 1 is already tracked by
PYPOST-1263. Items 2 and 3 were filed during PYPOST-1286 as PYPOST-1305 and PYPOST-1306 with
priority Low.

1. [PYPOST-1263](https://pypost.atlassian.net/browse/PYPOST-1263) — `NON-BLOCKER — pre-existing`
   (flaky: failed in the base run, passed in 3 of 3 task-tree runs; already filed, do not
   re-file):
   `tests/test_collection_import_profile.py::test_plan_collection_import_large_dataset_performance`
   - `AssertionError: plan_collection_import took 105.12ms, exceeding 100ms budget`.
   - Suspected cause: a hard 100 ms performance budget asserted under parallel CPU contention.
2. `NON-BLOCKER — pre-existing` (flaky: failed in the base run, passed in 3 of 3
   task-tree runs), Jira: [PYPOST-1305][]:
   `tests/test_env_presenter.py::TestEnvPresenter::`
   `test_async_load_wait_exits_near_deadline_when_never_complete`
   - A subprocess running `process_until(lambda: False, timeout_ms=300)` exceeded its 2.0 s
     `subprocess.TimeoutExpired` budget:
     `AssertionError: async-load wait hung past wall-clock deadline`.
   - Suspected cause: interpreter and PySide6 startup cost under load counts against the 2 s
     limit.
3. `NON-BLOCKER — pre-existing` (flaky: failed in the base run, passed in 3 of 3
   task-tree runs), Jira: [PYPOST-1306][]:
   `tests/test_run_parallel_tests.py::test_worker_timeout_terminates_grandchild_process_group`
   - `AssertionError: Grandchild PID file was not created; stdout= stderr=worker timeout after
     1.0s`.
   - Suspected cause: the 1.0 s worker timeout expired before the child spawned the grandchild
     under load.

Evidence: `base-run.log` in the session scratchpad. Excerpts are at log lines 1148, 1238–1243 and
1410. The repro command was `make test` in a temporary worktree of base `10ba60b7`, which has
since been removed.

## Decision

**SAFE TO PROCEED** to Step 8. There are no BLOCKER items. TD-1 and TD-2 are the substantive
gaps against the spirit of DoD 4–5 and need follow-up issues. The flaky target tests themselves
pass deterministically in every observed run.

[PYPOST-1300]: https://pypost.atlassian.net/browse/PYPOST-1300
[PYPOST-1301]: https://pypost.atlassian.net/browse/PYPOST-1301
[PYPOST-1302]: https://pypost.atlassian.net/browse/PYPOST-1302
[PYPOST-1303]: https://pypost.atlassian.net/browse/PYPOST-1303
[PYPOST-1304]: https://pypost.atlassian.net/browse/PYPOST-1304
[PYPOST-1305]: https://pypost.atlassian.net/browse/PYPOST-1305
[PYPOST-1306]: https://pypost.atlassian.net/browse/PYPOST-1306
