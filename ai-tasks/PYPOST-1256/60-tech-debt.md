# PYPOST-1256: Technical Debt Analysis

## Scope and disposition policy

This review compares the final PYPOST-1256 working-tree implementation with
`10-requirements.md`, `20-architecture.md`, `40-code-cleanup.md`,
`50-observability.md`, the lifecycle regression tests, and existing debt-artifact
conventions. The findings below distinguish task-caused follow-up candidates from
accepted design trade-offs and pre-existing full-suite failures. No production or
test change is made by this step. Step 7 was accepted after the independent review.

## Summary

| ID | Area | Severity | Disposition |
| --- | --- | --- | --- |
| TD-1256-01 | Admission fencing | Medium | Task-caused; candidate follow-up, no Jira issue created in this step |
| TD-1256-02 | Teardown-result immutability and diagnostics | Medium | Task-caused; candidate follow-up, no Jira issue created in this step |
| TD-1256-03 | Environment failure state | Medium | Task-caused; candidate follow-up, no Jira issue created in this step |
| TD-1256-04 | Late history-panel delivery coverage | Medium | Task-caused test gap; candidate follow-up, no Jira issue created in this step |
| TD-1256-05 | Telemetry exporter concurrency | Medium | Task-caused; candidate follow-up, no Jira issue created in this step |
| TD-1256-06 | Ledger retention and duplicate shutdown handoff | Low | Task-caused; monitor and consolidate before ticketing |
| TD-1256-07 | Behavioral contract remains dynamically typed | Low | Accepted compatibility trade-off; no follow-up currently required |
| TD-1256-08 | Fixed lifecycle budgets and daemon-retention policy | Low | Accepted bounded-policy trade-off; no follow-up currently required |
| TD-1256-09 | Incomplete teardown has no retry/finalization path | Medium | Task-caused; candidate follow-up, no Jira issue created in this step |
| BASE-1261 | Parser/template/SOLID baseline cluster | Non-blocker | Pre-existing; tracked by PYPOST-1261, no duplicate |
| BASE-1262 | Nested-Make worker timeout cluster | Non-blocker | Pre-existing; tracked by PYPOST-1262, no duplicate |

## Shortcuts Taken

- The contract is implemented as a behavioral, duck-typed `teardown()` API with
  owner-local adapters rather than a shared base class. This follows the approved
  architecture because the owners have incompatible Qt and non-Qt bases, but it
  leaves protocol drift possible (TD-1256-07).
- Cancellation remains cooperative for request workers, while history and
  environment persistence are drained rather than forcibly terminated. This
  preserves transport and storage invariants; a non-cooperative dependency can
  still produce an explicit `incomplete` result and remain retained (TD-1256-08).
- Compatibility seams use `getattr()` fallbacks for injected and legacy owners,
  and the root retains the existing signal signatures. This preserves existing
  tests and callers, but makes unsupported partial doubles detectable only at
  runtime (TD-1256-07).

## Code Quality Issues

### TD-1256-01 — Admission checks are not one atomic public boundary

- **Severity:** Medium.
- **Impact:** A caller arriving concurrently with root teardown can pass a boolean
  admission check and mutate UI or submit work after the teardown snapshot. Normal
  Qt GUI-thread sequencing reduces the practical frequency, but the public contract
  and the lifecycle tests also cover concurrent teardown and cross-thread callbacks.
- **Evidence:** `TabsPresenter._admission_open()` and `add_new_tab()` read
  `_teardown_started` without the teardown lock at
  `pypost/ui/presenters/tabs_presenter.py:210-225`; `close_tab()` does the same at
  `:376-381`. `EnvPresenter` uses unlocked admission reads in
  `pypost/ui/presenters/env_presenter.py:152-165`, `:321-345`, `:365-369`, and
  `:404-423`. Root teardown sets its fence and then drains owners at
  `pypost/ui/main_window_lifecycle.py:66-125`.
- **Mitigation:** Centralize an atomic `try_admit()`/cutoff operation per owner,
  or enforce that every public mutator runs through the same UI-thread state
  boundary. Add race tests for tab creation, environment selection/manager actions,
  and settings callbacks arriving during root teardown.
- **Owner/status:** UI lifecycle maintainers / Open candidate follow-up.
- **Disposition:** Task-caused actionable debt. Do not raise SOLID caps or treat
  this as a baseline issue; no Jira follow-up was created in this step.

### TD-1256-02 — Teardown results expose mutable and incomplete diagnostics

- **Severity:** Medium.
- **Impact:** `TeardownResult` is frozen, but its `dispositions` mapping is a live
  internal dictionary. A result returned from tabs teardown can therefore change
  after return as environment saves finish. The root result also aggregates only
  counts and outcome, so callers cannot inspect accepted environment-update
  dispositions through the composition-root result.
- **Evidence:** `EnvironmentUpdateLedger.dispositions_view()` returns
  `self._dispositions` directly at `pypost/core/lifecycle.py:84-91`; tabs stores that
  view in its result at `pypost/ui/presenters/tabs_presenter_lifecycle.py:148-157`.
  `EnvironmentStorageGateway` constructs its result without a dispositions mapping
  at `pypost/core/qt/environment_storage_gateway.py:239-246`, and
  `main_window_lifecycle.py:133-140` drops child dispositions when aggregating.
- **Mitigation:** Return a locked copy or immutable mapping at the result boundary,
  define whether dispositions are a cutoff snapshot or a retained-owner view, and
  propagate the environment ledger summary through the root diagnostics. Add a test
  that captures a result, completes late persistence, and asserts result identity and
  snapshot semantics.
- **Owner/status:** Lifecycle API maintainers / Open candidate follow-up.
- **Disposition:** Task-caused actionable debt; no Jira issue created in this step.

### TD-1256-03 — Historical environment failure contaminates later teardown status

- **Severity:** Medium.
- **Impact:** One load or save failure can leave the gateway's `_last_failure` set.
  A later successful operation does not clear it, so a future teardown can report
  `failed` even though the active and pending work at that teardown completed. This
  weakens the meaning of the result and can cause the close path to reject a healthy
  retry.
- **Evidence:** `_last_failure` is initialized at
  `pypost/core/qt/environment_storage_gateway.py:57`, set by both failure handlers at
  `:168-198`, and consulted without a per-operation generation at `:230-235`.
  `_on_load_finished()` and `_on_save_finished()` do not reset or scope the value.
- **Mitigation:** Track failure state by operation/generation and clear or resolve it
  when the corresponding accepted queue reaches a later successful terminal state.
  Add a load/save-failure-then-success regression test and assert the resulting
  teardown outcome and close-event behavior.
- **Owner/status:** Environment lifecycle maintainers / Open candidate follow-up.
- **Disposition:** Task-caused actionable debt; no Jira issue created in this step.

### TD-1256-04 — Late history delivery is only partially fenced by tests and code

- **Severity:** Medium.
- **Impact:** The panel's refresh and load-into-editor paths are fenced, but a
  queued selection or filter callback can still enter widget-mutating code after
  teardown. The manager also invokes an arbitrary `on_complete` callback after an
  asynchronous load, relying on each callback consumer to fence itself. A future
  consumer can therefore reintroduce post-close UI mutation.
- **Evidence:** `HistoryPanel._apply_filter()` and
  `_on_selection_changed()` mutate widgets without a teardown check at
  `pypost/ui/widgets/history_panel.py:194-227`. `HistoryManager._run_async_load()`
  calls `on_complete()` unconditionally at `pypost/core/history_manager.py:168-178`.
  Current tests exercise the known panel refresh bridge, but not a queued selection,
  filter event, or an arbitrary callback after manager teardown.
- **Mitigation:** Put the panel generation check at every widget-delivery slot, or
  make the manager callback API generation-aware and centrally fenced. Add bounded
  Qt tests for selection/filter events and callback delivery after both successful
  and incomplete manager teardown.
- **Owner/status:** History UI maintainers / Open test-and-contract follow-up.
- **Disposition:** Task-caused actionable test/code debt; no Jira issue created in
  this step.

## Missing Tests

The new lifecycle test modules declare explicit module-level timeout markers and
their internal `Event.wait()`, thread joins, and event-loop polling are bounded. No
mandatory timeout-marker blocker was found.

The following coverage remains useful but was not required to reject the accepted
focused gate:

- Concurrent root teardown against tab creation, environment selection, an open
  environment manager, and settings/startup callbacks (TD-1256-01).
- Immutable/snapshot semantics for `TeardownResult.dispositions`, including a
  late environment outcome after the initial result was returned (TD-1256-02).
- Environment failure followed by a successful retry before teardown (TD-1256-03).
- History selection/filter callbacks and arbitrary history-load completion callbacks
  after the panel or manager is fenced (TD-1256-04).
- Concurrent OpenTelemetry metric export while lifecycle gauges are updated, and
  duplicate root drain delivery of a queued environment update.

## Performance Concerns

### TD-1256-05 — OpenTelemetry lifecycle gauges are not synchronized

- **Severity:** Medium.
- **Impact:** The OTel exporter may iterate the per-owner gauge dictionaries while
  teardown code updates them. A concurrent dictionary resize can raise an exporter
  error or lose a sample; this does not affect the no-op metrics path, but it can
  make enabled telemetry unreliable during shutdown.
- **Evidence:** `_observe_lifecycle_active_workers()` and
  `_observe_lifecycle_pending_work()` iterate dictionaries at
  `pypost/core/metrics_otel.py:103-109`, while `track_lifecycle_teardown()` mutates
  those dictionaries at `:484-500` with no shared lock or snapshot.
- **Mitigation:** Protect updates and observations with a small lock, or replace
  each mapping atomically and iterate a snapshot. Add a concurrent exporter/update
  test if the tracker is used from multiple threads.
- **Owner/status:** Observability maintainers / Open candidate follow-up.
- **Disposition:** Task-caused actionable debt; no Jira issue created in this step.

### TD-1256-06 — Lifecycle ledger has unbounded retention and can duplicate a drain

- **Severity:** Low.
- **Impact:** `EnvironmentUpdateLedger` deep-copies and retains every sequence and
  variable payload for the lifetime of a presenter, and the gateway retains terminal
  save sequence IDs. A long-lived session with many script updates grows memory and
  can retain environment/secret values after persistence. During root shutdown, the
  durable drain can also be followed by the queued signal path, causing a coalesced
  duplicate save; terminal claims prevent duplicate visible outcomes but do not
  eliminate I/O overhead.
- **Evidence:** `_records` and `_dispositions` are never compacted at
  `pypost/core/lifecycle.py:42-91`; `_terminal_save_sequences` is retained at
  `pypost/core/qt/environment_storage_gateway.py:51-53`. The root drains accepted
  updates before environment teardown at `pypost/ui/main_window_lifecycle.py:110-125`,
  while normal `env_update_accepted` delivery is separately wired through
  `pypost/ui/main_window_signals.py:56-65`.
- **Mitigation:** Define a retention/compaction point after a terminal root result,
  clear payloads once their terminal disposition is recorded, and make the durable
  drain mark queued signal deliveries as consumed or otherwise avoid re-submitting an
  already accepted sequence. Measure save coalescing before selecting a data-structure
  change.
- **Owner/status:** Environment/lifecycle maintainers / Open low-risk candidate;
  consolidate with TD-1256-02 before ticketing.
- **Disposition:** Task-caused actionable performance debt, but not a current
  blocker; no separate Jira issue created in this step.

### TD-1256-07 — Behavioral teardown contract has no static protocol

- **Severity:** Low.
- **Impact:** New owners or test doubles can omit `begin_teardown()`, timeout
  semantics, or result fields and fail only when composed. Dynamic compatibility
  fallbacks preserve current injected/legacy seams but reduce discoverability and
  static checking.
- **Evidence:** The result type is defined in `pypost/core/lifecycle.py:22-39`,
  while root coordination discovers owner methods with `getattr()` at
  `pypost/ui/main_window_lifecycle.py:56-125`. Metrics compatibility similarly
  relies on optional `getattr()` calls in `pypost/core/lifecycle.py:99-125`.
- **Mitigation:** Add a small `Protocol` for the behavioral owner contract and
  runtime contract tests for each owner and supported legacy double. Keep the
  existing duck-typed adapter at external compatibility boundaries.
- **Owner/status:** UI architecture maintainers / Accepted compatibility trade-off;
  no immediate follow-up required.
- **Disposition:** Accepted scope trade-off from the approved architecture, not a
  blocker and not proposed as a new Jira item.

### TD-1256-08 — Fixed lifecycle budgets and retained daemon workers are policy values

- **Severity:** Low.
- **Impact:** The default 5-second budget, the 100 ms post-finish QThread wait, and
  the 1 ms request-worker polling sleep are fixed values. They bound normal close
  behavior, but may be too short for slow storage or too long for a highly
  interactive UI. A timed-out daemon worker also requires retained owner lifetime
  and operational follow-up.
- **Evidence:** The defaults are declared at
  `pypost/core/history_manager.py:26-27`,
  `pypost/core/qt/environment_storage_gateway.py:23-25`, and
  `pypost/ui/main_window_lifecycle.py:53-66`; request polling is bounded by
  `pypost/ui/presenters/tabs_presenter_lifecycle.py:212-221`.
  `shutdown_for_exit()` also performs the existing state-manager flush before the
  root teardown at `pypost/ui/main_window_lifecycle.py:157-171`.
- **Mitigation:** Keep the finite defaults, collect duration/outcome metrics, and
  tune only from production/test evidence. If application shutdown must include
  state-manager and MCP cleanup in the same total budget, handle that as a separate
  lifecycle task rather than silently widening PYPOST-1256.
- **Owner/status:** Application lifecycle maintainers / Accepted bounded-policy
  trade-off; monitor, no immediate Jira follow-up.
- **Disposition:** Accepted risk within the approved design. The existing
  pre-teardown state-manager flush and MCP stop are outside this task's presenter
  scope and are not refiled here.

### TD-1256-09 — Incomplete teardown cannot be retried or finalized

- **Severity:** Medium.
- **Impact:** When a bounded wait returns `incomplete`, the owner retains its worker
  or persistence coordinator, but later calls return the cached incomplete result.
  A worker that settles shortly after the deadline has no public finalization path;
  a close event can therefore remain rejected even after the original work is safe.
- **Evidence:** `MainWindow.teardown()` returns the cached result on every later call
  at `pypost/ui/main_window_lifecycle.py:60-63` and stores incomplete aggregates at
  `:133-140`. `close_event()` accepts only `success` at `:175-180`. The request-tab
  helper has the same permanent per-tab result cache at
  `pypost/ui/presenters/tabs_presenter_lifecycle.py:41-43` and `:71-81`.
- **Mitigation:** Define an explicit post-timeout lifecycle state and finalizer, or
  permit a bounded retry after retained work settles while preserving the original
  cutoff and diagnostics. Add a test that releases a gated worker after an initial
  timeout and verifies the next close attempt's behavior.
- **Owner/status:** Application and request lifecycle maintainers / Open candidate
  follow-up.
- **Disposition:** Task-caused actionable lifecycle debt; no Jira issue created in
  this step.

## Pre-existing Test Failures

### BASE-1261 — NON-BLOCKER — pre-existing

- **Severity:** Non-blocker.
- **Impact:** The full quality gate is not fully green for parser/template
  expectation drift and the protected SOLID metrics snapshot. These failures are
  unrelated to PYPOST-1256 lifecycle behavior.
- **Evidence:** The PYPOST-1256 full-gate reports record 332 passed, 6 skipped, and
  3 failed files. The exact nodes are:
  - `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_malformed_nested_expressions`
  - `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_standalone_malformed_closing_paren`
  - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
  - `tests/test_template_service.py::TestTemplateServiceValidationOutcomes::test_validate_malformed_nested_alignment`
  - `tests/test_template_service.py::TestTemplateServiceObservability::test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover`
  The resolver/template nodes expect `invalid_argument` but receive `invalid_arity`;
  the SOLID node compares the current metrics with the protected frozen snapshot.
  These failures were reproduced and documented before the PYPOST-1256 changes and
  are recorded in Jira [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261),
  currently To Do.
- **Mitigation:** Resolve or re-triage the existing Jira cluster. Do not modify
  `ai-tasks/PYPOST-376/baseline-metrics.md` as part of PYPOST-1256.
- **Owner/status:** Existing PYPOST-1261 owner / Open pre-existing baseline debt.
- **Disposition:** NON-BLOCKER — pre-existing — tracked by PYPOST-1261. No duplicate
  Jira issue or PYPOST-1256 fix is warranted.

### BASE-1262 — NON-BLOCKER — pre-existing

- **Severity:** Non-blocker.
- **Impact:** Under full parallel load, nested Make tests can consume the worker
  timeout and obscure the result of unrelated tasks. The issue is not a lifecycle
  implementation failure and did not fail the final PYPOST-1256 focused gate.
- **Evidence:** Existing baseline triage records these file-level timeout nodes:
  - `tests/test_makefile_lifecycle.py::TestVenvExtraStampIdempotency::test_venv_test_installs_when_stamp_stale`
  - `tests/test_makefile_targets.py::TestTargetExecution::test_test_succeeds_from_bare_venv_via_venv_test`
  The PYPOST-1256 validation reports `make typecheck` passing against the known
  180-error baseline and the full run's failures limited to the BASE-1261 nodes;
  the nested-Make issue is already tracked in Jira
  [PYPOST-1262](https://pypost.atlassian.net/browse/PYPOST-1262), currently To Do.
- **Mitigation:** Continue the existing PYPOST-1262 investigation and tune worker
  budgets only in that test-infrastructure scope.
- **Owner/status:** Test-infrastructure maintainers / Open pre-existing baseline
  debt.
- **Disposition:** NON-BLOCKER — pre-existing — tracked by PYPOST-1262. No duplicate
  Jira issue was created.

The repository's known 180-error mypy baseline is also pre-existing; `make typecheck`
passes its baseline gate for this task. It is recorded as context, not a new
PYPOST-1256 debt item.

## Follow-up Tasks

No Jira issue or worklog is created by this Step 7 artifact. If the task-caused
items are ticketed later, consolidate them into the smallest lifecycle follow-ups:

1. Make public admission and teardown-result diagnostics atomic and immutable
   (TD-1256-01 and TD-1256-02).
2. Scope environment failures to operation generations and prevent duplicate
   shutdown handoff (TD-1256-03 and TD-1256-06).
3. Complete late-history callback fencing and add the missing bounded Qt tests
   (TD-1256-04).
4. Synchronize OTel lifecycle gauge observations and add concurrent exporter
   coverage (TD-1256-05).
5. Define retry/finalization semantics after an incomplete teardown (TD-1256-09).

TD-1256-07 and TD-1256-08 are accepted trade-offs and do not warrant new Jira
issues unless the supported owner set or shutdown policy changes.

## Validation

- `make lint` — PASS (flake8, Markdown lint, and relative-link checks).
- `make verify-ai-tasks` — PASS (`358 completed tasks; 2 grandfathered legacy gaps`).
- `make test WORKERS=1 WORKER_TIMEOUT=60 PYTEST_ARGS='tests/test_presenter_teardown_contract_repro.py tests/test_lifecycle_observability.py'` — PASS (2 focused files, 0 failures).
- The accepted Step 6 full-gate evidence records 332 passed, 6 skipped, and only
  the pre-existing BASE-1261 failures described above; Step 7 did not rerun the
  full gate because it changes no production or test code.
- No root coverage/test artifacts were created by Step 7.
- No production, test, AGENTS.md, sprint registry, or protected baseline file was
  modified by Step 7.
