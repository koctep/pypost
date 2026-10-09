# Roadmap: PYPOST-1264

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Independent requirements review passed (DoD 3 caller-budget criterion ruled in scope);
    orchestrator accepted Step 1.
  - Created `10-requirements.md` from the assigned issue and PYPOST-1229 debt item 4.
  - Reviewed current collection import wait/teardown behavior, its presenter delegation, and the
    main-window per-owner budget allocation; noted the inherited 5000 ms and 100 ms literals.
  - Documented one named lifecycle policy, caller-budget adherence, preserved outcomes, and a
    measured, recorded configurability decision as the required outcome (no option mandated).
  - `make verify-ai-tasks` passed: 395 completed tasks; 2 grandfathered legacy gaps.
  - Acceptance remains with the autonomous orchestrator after independent review.
- [x] **STEP 2: High-Level Architecture Design**
  - Independent architecture review passed after two fix rounds; orchestrator accepted Step 2.
  - Created `20-architecture.md`: Qt-free `pypost/core/collection_import_lifecycle_policy.py`
    (frozen `CollectionImportLifecyclePolicy`: 5000 budget, 100 final join, 100 worker-finish
    join, 10 idle poll, 50 ms tolerance; `ImportTeardownDeadline` with injectable clock).
  - Teardown phases share one monotonic deadline (final join = min(100, remaining); library
    join = remaining). DoD 3 asserted deterministically (sum of waits ≤ budget, exhausted →
    `wait(0)` + unclean); `timeout_ms + 50 ms` wall time is a documented contract value, not
    a CI timing gate.
  - Test seam: keyword-only `clock` on `CollectionImportActions`, passed to every
    `ImportTeardownDeadline.start`; `wait_idle` loop uses `deadline.expired`.
  - Presenter/actions defaults become `None` resolved from the policy; logs, cooperative
    interruption, disconnect-before-reap order, and idempotency preserved.
  - Latency measurement (`pytest.mark.slow`, N=20, run via `make test-slow
    PYTEST_ARGS="tests/test_collection_import_teardown_latency.py -m slow -s"`, one worker,
    load recorded); p95 thresholds are recorded decision inputs, only `clean`/`n == 20`
    asserted; decision recorded in `doc/dev/collection_import.md`.
  - Step 3 repro designed: `tests/test_collection_import_teardown_budget_repro.py`
    (`pytest.mark.timeout(30)`). Test A (behavioural red by assertion): no new keywords, spy
    `wait(ms)` really sleeps `ms` (budgets ≤ 300 ms); asserts sum of requested waits ≤ B,
    P2 ≤ 100, B=0 → only `wait(0)` + unclean. Red today (400 > 300, 150 > 50, `wait(100)` at
    B=0), green after the fix (real elapsed shrinks remaining); load-safe (no wall-time upper
    bound). Rejected: non-sleeping load-proof asserts (pass on current code except B=0).
  - Test B is the seam / exact-arithmetic fake-clock test; its `TypeError` red (missing
    `clock=`) is accepted because test A carries the behavioural red; the Step 3 reviewer
    must confirm test A fails on assertions, not errors. Plus one loose real-thread guard
    (B=300 → < 600 ms vs ≈700 today; B=0 → unclean, < 100 ms).
  - Nested `_on_worker_finished` join kept uncapped (normally instantaneous after
    `finished`; capping risks reaping a still-exiting thread), recorded under Risk 3.
  - Risk noted: `CollectionsPresenter` is not a main-window teardown owner (follow-up debt).
  - Review-gap fix: `make verify-ai-tasks` passed (395 completed tasks; 2 grandfathered
    legacy gaps).
  - Review-gap fix #2 (test A real-sleep spies): `make verify-ai-tasks` passed (395 completed
    tasks; 2 grandfathered legacy gaps).
- [x] **STEP 3: Failing Repro Test**
  - Independent repro re-review passed after one test-harness fix; orchestrator accepted Step 3.
  - Red test: `tests/test_collection_import_teardown_budget_repro.py`
    (`pytestmark = pytest.mark.timeout(30)`, `qapp`); no production change (`pypost/` untouched).
  - Command: `make test WORKERS=1
    PYTEST_ARGS='tests/test_collection_import_teardown_budget_repro.py'` → 8 failed.
  - Test A (behavioural red, by assertion; real-sleep spies, today's constructor):
    `::test_teardown_requested_waits_fit_caller_budget[300]` → `400 <= 300` (P2 `[100]`, P3
    `[300]`); `[50]` → `150 <= 50` (`[100]`, `[50]`); `[0]` → `100 <= 0` (`[100]`, `[0]`).
  - Test B (seam / exact arithmetic, fake clock):
    `::test_teardown_wait_arithmetic_with_fake_clock[300-100-200]`, `[50-50-0]`, `[0-0-0]` →
    `TypeError: ... unexpected keyword argument 'clock'` (accepted per design; test A carries
    the behavioural red).
  - Loose real-thread guard: `::test_teardown_real_threads_stay_within_loose_bound[300]` →
    `took 737 ms >= loose bound 600 ms`; `[0]` → `took 126 ms >= loose bound 100 ms`
    (`clean is False` held in both). Real workers' `deleteLater` deferred until released and
    joined (`wait(2000)`) in `finally`.
  - Review harness fix (test file only): the guard now sets `reader_entered` /
    `library_entered` events as the first action in the stuck reader and the stuck library
    op, and asserts both `wait(timeout=_RELEASE_TIMEOUT_S)` before the timer starts. Without
    this, P0 `requestInterruption()` could beat the parse worker's `run()`, skip the reader
    and P2, so red was non-deterministic. Each worker goes into `threads` and gets its
    deferred `deleteLater` right after it starts, so `finally` also joins a partial setup.
  - Rerun after the harness fix (3 runs, same command): 8 failed every time with the same
    reasons: Test A `400<=300`, `150<=50`, `100<=0`; Test B `TypeError ... 'clock'` x3;
    guard `[300]` took 824 / 802 / 769 ms >= 600 ms; `[0]` took 141 / 122 / 131 ms >= 100 ms
    (`clean is False` held). No hangs, no errors, no Qt thread warnings.
  - Slow latency module not created (assigned to Step 4 by the design).
  - `20-architecture.md` wording fix: "Green after Step 4" now states real-clock P2 is
    typically 49 at `B=50`; exact `50/0` holds only in test B, test A asserts `<=` only.
- [x] **STEP 4: Development**
  - Independent implementation review passed; orchestrator accepted Step 4. Pre-existing
    full-suite failures filed: PYPOST-1299, PYPOST-1311, PYPOST-1315, PYPOST-1320.
  - [x] Iteration 1 (red → green): added Qt-free
    `pypost/core/collection_import_lifecycle_policy.py` (frozen
    `CollectionImportLifecyclePolicy` 5000/100/100/10/50 with validation and
    `resolve_budget_ms`; `ImportTeardownDeadline` with injectable clock, truncating
    `remaining_ms()` computed from whole microseconds so float noise such as
    `1000.1 - 1000.0` cannot drop a fake-clock 200 to 199). Wired
    `CollectionImportActions` (keyword-only `lifecycle_policy` / `clock`; `wait_idle` /
    `teardown` default `None`; one shared deadline: P1 `_wait_idle_until(deadline)`, P2
    `min(final_join_ms, remaining)`, P3 `remaining`; idle poll `bounded(idle_poll_ms)`;
    `_WORKER_FINISH_WAIT_MS` replaced by `worker_finish_join_ms`, still uncapped).
    `CollectionsPresenter` defaults `None`, logs the resolved budget from the actions'
    policy. `make test WORKERS=1 PYTEST_ARGS='tests/test_collection_import_teardown_budget_repro.py'`
    → 8 passed (guard `[300]` teardown 311 ms, `[0]` 14 ms).
  - [x] Existing-test seam fix: `tests/test_collection_import_cancellation_repro.py::
    test_default_teardown_requests_interruption_before_wait_and_discards_result`
    monkeypatched public `wait_idle`, which teardown no longer calls (design: P1 shares the
    teardown deadline via `_wait_idle_until`). Now observes `_wait_idle_until` and asserts
    `(deadline.budget_ms, interrupted) == (5000, True)`; intent unchanged.
  - [x] Iteration 2 (design test strategy): `tests/test_collection_import_lifecycle_policy.py`
    (Qt-free: defaults, `resolve_budget_ms`, frozen, `ValueError`, deadline arithmetic and
    truncation) and `tests/test_collection_import_teardown_policy.py` (fake clock + spies:
    injected policy drives default waits 30/170; deadline passing in P1 → P2/P3 `wait(0)`,
    unclean, `_wait_idle_timeout`; no-app poll `[10, 10, 5]`; idle teardown clean and
    idempotent; presenter `None` logs resolved 5000 without waiting).
  - [x] Iteration 3 (DoD 5 measurement): `tests/test_collection_import_teardown_latency.py`
    (`pytest.mark.slow`, `timeout(120)`, N=20, structural asserts only). Command
    `make test-slow PYTEST_ARGS="tests/test_collection_import_teardown_latency.py -m slow -s"`
    (1 worker; Linux 6.8 aarch64, 6 CPUs, Python 3.13.5, PySide6/Qt 6.11.1, offscreen; load
    0.10/0.30/0.19 → 0.08/0.29/0.19): idle p95 0.06 ms (max 0.19); file cancel p95 2.43
    (max 2.45); library 200 ms p95 208.71 (max 211.59); all 60 clean; reference blocked
    library, budget 100 → p95 111.05, max 111.17, 0/20 clean. Decision rule holds → **limits
    stay fixed policy values**, no user setting. Data and decision added to
    `doc/dev/collection_import.md` § "Teardown lifecycle policy (PYPOST-1264)" (Step 8 owns
    the final wording); the stale "bounded 100 ms join" sentence there was corrected.
  - [x] Iteration 4 (suite fallout): `tests/test_collection_import_cancellation_repro.py`
    `_TEARDOWN_WAIT_IDLE_MS` 150 → 1000. Before this, `test_teardown_worker_stops_after_interruption`
    failed 2 of 5 parallel runs: the budget now covers P0 and the final join (design Risk 1:
    the old fixed 100 ms grace is gone). Still well under the 2 s reader, so the in-flight
    intent holds. Regenerated `ai-tasks/PYPOST-376/baseline-metrics.md` with
    `make baseline-metrics` (`collections_presenter.py` 520 → 527 LOC, cap 535). Replaced
    the latency module's `print` calls (T201, caught by `test_lint_pytestmark_e402`) with
    `sys.stdout.write`.
  - Validation 1: `make test WORKERS=1 PYTEST_ARGS='tests/test_collection_import_teardown_budget_repro.py'`
    → 8/8 passed (repro sha256 unchanged); guard `[300]` 311 ms, `[0]` 14 ms.
  - Validation 2 (**open issue: guard not load-safe**): 5 runs of `make test
    PYTEST_ARGS='tests/test_collection_import_teardown_budget_repro.py tests/test_collection_import*.py'`
    (default WORKERS=8). Guard teardown times from log timestamps: `[300]` 893.8 / 852.5 /
    458.4 / 740.4 / 800.5 ms (max 893.8, bound 600); `[0]` 31.2 / 789.0 / 21.3 / 272.8 /
    264.0 ms (max 789.0, bound 100). It failed in 4 of 5 runs, and in 5 of 5 more runs
    after iteration 4. Root cause, from in-suite instrumentation: about 99 % of the time is
    spent in logging handlers. Under the parallel runner, pytest live logging
    (`log_cli_level = "WARNING"` in `pyproject.toml`) takes p50 ≈ 5 ms and up to 413 ms per
    WARNING record, even with no threads alive. Teardown emits 5 WARNING records that the
    design says to keep. Qt calls without logging take ≤ 0.3 ms. With `-o log_cli=false`
    (diagnostic only, 3 runs) the guard measures `[300]` 299–378 ms and `[0]` 0.2–0.8 ms.
    Fixing this needs a change to the reviewed test (or to log levels or the runner config),
    which is outside Step 4's mandate, so it is reported to the orchestrator.
  - Validation 3: all `tests/test_collection_import*.py`, `tests/test_collections_import_ui*.py`
    and `tests/test_collections_presenter.py` pass except the load-sensitive guard above.
  - Validation 4: full `make test` (2 runs) → 369/379 passed. Failures:
    `tests/test_pytest_exit_policy.py` timed out at 120 s (pre-existing: also times out at
    base c3f8e183 in a worktree with its own venv; its fresh-venv `make install` exceeds
    60 s here). `tests/test_environment_export_ui.py` exits -11/-7 after all 8 tests pass
    (pre-existing flaky crash: base failed 2 of 3 runs alone). The guard failed in 1 of 2
    full runs (`[0]` 115 ms).
  - Validation 5: `make lint` OK; `make typecheck` → mypy baseline OK (181 known errors).
  - [x] Fix loop (guard load-safety, test harness only): in
    `tests/test_collection_import_teardown_budget_repro.py::test_teardown_real_threads_stay_within_loose_bound`
    the timed `actions.teardown(...)` call now runs with the
    `pypost.ui.presenters.collection_import_actions` logger `disabled` and restored in
    `try/finally` (only that window; no process-global change), with a comment on why. The
    600/100 ms bounds are unchanged. Teardown still emits its log records; tests that check
    log content are not affected. Results (timings from a scratch `-p` timer plugin that
    wraps `teardown`): `make test WORKERS=1 PYTEST_ARGS='tests/test_collection_import_teardown_budget_repro.py'`
    → 8 passed (`[300]` 303 ms, `[0]` 0.5 ms). 5 parallel runs (WORKERS=8) of the
    repro + `tests/test_collection_import*.py` → guard passed 5/5, `[300]` max 482.6 ms
    (351–483), `[0]` max 4.0 ms. Base c3f8e183 worktree with only this file copied →
    8 failed: Test A by assertion (`400 <= 300`, `150 <= 50`, `100 <= 0`), guard by
    elapsed (`[300]` 718 ms ≥ 600, `[0]` 106 ms ≥ 100). Full `make test` → 370/379 passed,
    7 skipped, 2 failed: `test_pytest_exit_policy.py` timed out (known, PYPOST-1299), and
    `tests/test_collection_import_teardown_repro.py` timed out at 120 s in
    `test_unexpected_reader_exception_requires_teardown_and_reaps_worker`. That file
    passes 3/3 alone and passed in all 6 collection-import parallel runs, so it is
    intermittent and still needs triage.
  - [x] Triage of the intermittent hang in
    `tests/test_collection_import_teardown_repro.py::test_unexpected_reader_exception_requires_teardown_and_reaps_worker`
    → **pre-existing flaky, not caused by this task; no code change**. With
    `-o faulthandler_timeout=50` added to `PYTEST_ARGS`, the hang reproduced in 1 of 7 targeted
    parallel runs (`make test PYTEST_ARGS='tests/test_collection_import_teardown_repro.py
    tests/test_collection_import*.py tests/test_collections*.py ...'`). All dumps show the
    same stack, at test line 106, before any teardown code runs: the main thread is stuck in
    `threading.Thread.start()` (`self._started.wait()`) when it starts the watchdog
    `threading.Timer` in `tests/helpers/process_until.py:136`. The `QThread` parse worker is
    stalled in `logger.error(..., exc_info=True)` at `collection_import_parse_worker.py:93`
    (`current_thread()` / traceback formatting), and the timer thread is stalled in
    `Timer.run`. None of the three threads makes progress. pytest-timeout (signal method,
    30 s) never fires because the main thread never returns to bytecode, so the runner kills
    the file at 120 s. The parse worker, `process_until` and the test are unchanged by this
    task. The new lifecycle code is not on the stack, and none of its waits run before the
    hang. Stress check, a scratch file copied ×6 that repeats the scenario 150× per process
    (`make test WORKERS=6 WORKER_TIMEOUT=300`). The scratch files were removed afterwards.
    Results: current tree 2/12 processes hung; base c3f8e183 worktree 1/18 processes hung,
    with an identical stack. Base targeted runs: 0/15 hangs; 1 run failed on the known
    `test_teardown_worker_stops_after_interruption` flake. Base full `make test` ×2: run 2
    hung in `tests/test_collections_import_ui.py::test_zero_candidates_treated_as_invalid_file`
    with the same deadlock: main thread in `Thread.start` from `process_until:136` (through
    `collection_import_wait.wait_import`), parse worker in `run`. Full `make test` on the
    current tree ×3: no hang. The other failures are known or unrelated:
    `test_pytest_exit_policy.py` timeout (PYPOST-1299), `test_environment_export_ui.py` crash,
    and `test_env_persistence_e2e.py` `OSError: Directory not empty` in tmp cleanup (once).
    Same symptom class as PYPOST-1148 (signal timeout cannot interrupt a futex wait). This is
    reported to the orchestrator for a Jira issue.
- [x] **STEP 5: Code Cleanup**
  - Independent cleanup review passed; orchestrator accepted Step 5.
  - Created `40-code-cleanup.md`. Cleanup scope: the Step 4 diff and the new untracked
    files. No behaviour change; the reviewed repro test was not modified.
  - Review item 2: `collection_import_actions.py` now uses the policy module's `Clock` alias
    for `clock` / `self._clock`. `Callable` is still used elsewhere, so its import stays.
  - Review item 1: the `test_teardown_worker_stops_after_interruption` assertion messages now
    say "the final join" in place of "wait(100)". Only the messages changed.
  - Manual check of the test files (`make lint` flake8 covers `pypost/` only): no lines over
    100 characters, no unused imports, no debug or commented-out code, timeout markers present.
  - `make lint` OK; `make typecheck` mypy baseline OK (181 known); targeted
    `make test WORKERS=1 PYTEST_ARGS='...'` → 5/5 files passed.
  - `make verify-ai-tasks` passed: 395 completed tasks; 2 grandfathered legacy gaps.
- [x] **STEP 6: Observability**
  - Independent observability review passed; orchestrator accepted Step 6.
  - Created `50-observability.md`: listed the existing teardown events and found two gaps.
    P2/P3 join timeouts did not show how much of the shared deadline they got, and no line
    gave the total teardown duration.
  - Appended scalar fields only. Event names and levels are unchanged:
    `collection_import_worker_interrupt_timeout wait_ms= elapsed_ms=`,
    `collection_library_import_worker_timeout wait_ms= elapsed_ms=`,
    `collection_import_teardown_completed clean= elapsed_ms= timeout_ms=`. `remaining_ms` was
    not added because it can be derived from the other fields.
  - Added caplog tests to `tests/test_collection_import_teardown_policy.py` (fake clock, exact
    messages, WARNING level, `wait_ms=0` when the budget is used up). The reviewed repro test
    was not changed.
  - Targeted `make test WORKERS=1`: 6/7 files passed. `test_collection_import_teardown_repro.py`
    hit the known pre-existing deadlock (Step 4 triage), which happens before teardown runs.
    Three reruns of that file alone: 3/3 passed. `make lint` OK; `make typecheck` baseline OK
    (181 known).
  - Step 8 should update the log field lists in `doc/dev/collection_import.md`.
  - `make verify-ai-tasks` passed: 395 completed tasks; 2 grandfathered legacy gaps.
- [x] **STEP 7: Technical Debt Analysis**
  - Independent tech-debt re-review passed and blocker review returned SAFE TO CLOSE;
    orchestrator accepted Step 7.
  - Created `60-tech-debt.md` covering the diff, the new policy module and the new tests.
  - Timeout-marker check: every new or changed test module has an explicit module-level
    `pytestmark` timeout, so there is no do-testing BLOCKER.
  - Main debt items: `CollectionsPresenter` is not a main-window teardown owner (Risk 5).
    Main-window 5000 literals remain outside any policy. Four other `_WORKER_FINISH_WAIT_MS =
    100` constants remain. The library worker cannot be interrupted (Risk 4). The nested
    worker-finish join is uncapped (Risk 3, accepted). The guard disables a logger because of
    `make test` live-logging cost (CI already uses `-o log_cli=false`, PYPOST-671). The
    cancellation repro budget went from 150 to 1000 ms. One test patches private
    `_wait_idle_until`.
  - New follow-ups (Jira: TBD, not filed): 1 High (collections shutdown owner), 1 Medium
    (interruptible library worker), 1 Medium (`make test` live logging), 3 Low (other 100 ms
    constants, app shutdown policy, teardown API/test seam), 1 Lowest (nested-join test).
  - Pre-existing NON-BLOCKERs recorded: PYPOST-1299, PYPOST-1315, PYPOST-1311, PYPOST-1320.
  - Code, tests and docs were not changed in this step.
  - `make verify-ai-tasks` passed: 395 completed tasks; 2 grandfathered legacy gaps.
  - Review fix (documentation accuracy): corrected the `teardown` docstring in
    `collection_import_actions.py` and the budget paragraph in `doc/dev/collection_import.md`.
    The guarantee now covers only deadline-bounded phase waits; the uncapped nested
    worker-finish join (Risk 3) and long GUI slots are named as overruns, and
    `budget_tolerance_ms` (50 ms) is stated as a contract value. Docstring text only, no
    behaviour change. Updated `60-tech-debt.md` Code Quality item 4 and follow-up 6.
- [x] **STEP 8: Dev Docs**
  - Independent dev-docs review passed; orchestrator accepted Step 8.
  - Updating `doc/dev/collection_import.md` in place (no new doc, so no index change).
  - § "Teardown lifecycle policy (PYPOST-1264)" expanded: policy module API (policy,
    default instance, `ImportTeardownDeadline`, `Clock`), field table and default rationale,
    P0–P4 shared-deadline phases with the two documented exceptions (nested worker-finish
    join, long GUI slots) and the 50 ms tolerance, keyword-only `lifecycle_policy` / `clock`
    and presenter delegation, preserved behaviour, test layout (deterministic fake-clock/spy
    tests, loose real-thread guard and why it disables the actions logger, slow latency
    module with `make test-slow PYTEST_ARGS="tests/test_collection_import_teardown_latency.py
    -m slow -s"`), configurability decision with evidence and re-run note, scope limits
    linking PYPOST-1321/1323/1325/1327.
  - Stale content fixed: `wait(100)` / "(100ms)" / "fixed 100 ms" / `_WORKER_FINISH_WAIT_MS`
    wording now says `min(final_join_ms, remaining)` or `worker_finish_join_ms`; API
    signatures now `timeout_ms: int | None = None`; teardown step list now includes the library
    join and the shared deadline; Configuration section rewritten (fixed policy values, no
    setting); added the policy module to the Architecture component list.
  - Observability: `collection_import_worker_interrupt_timeout wait_ms= elapsed_ms=`,
    `collection_library_import_worker_timeout wait_ms= elapsed_ms=` (newly listed),
    `collection_import_teardown_completed clean= elapsed_ms= timeout_ms=`; a `wait_ms=0`
    reading guide and two log examples (one exact from the fake-clock caplog test).
  - Troubleshooting: updated finish-wait, wait-idle and interrupt-timeout entries; added
    library-worker timeout and "Teardown takes longer than its budget" (overrun diagnosis,
    live-logging check via `-o log_cli=false`, PYPOST-1321 app-shutdown gap).
  - Known follow-ups: PYPOST-1264 marked done; PYPOST-1321..1327 listed with priority;
    pre-existing PYPOST-1299/1311/1315/1320 added to the baseline-failure section.
  - Verified: every internal anchor resolves (scripted check; ambiguous `#troubleshooting`
    replaced by plain text); no added line exceeds 100 characters; names, defaults, log
    formats and commands checked against the code, tests and Makefile.
  - `make lint` OK (flake8 `pypost/`; Markdown lint 16 files; link check 18 files). Note: the
    doc lint and link checker cover only `doc/user/`, `doc/README.md` and root/examples
    READMEs, not `doc/dev/`, so this doc was checked manually as above.
  - `make verify-ai-tasks` OK: 395 completed tasks; 2 grandfathered legacy gaps.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1264/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1264/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1264/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1264/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1264/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
