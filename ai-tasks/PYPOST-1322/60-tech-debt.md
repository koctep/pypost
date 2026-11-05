# PYPOST-1322: Technical Debt Analysis

Scope analysed: test-only characterization of design Risk 3 (nested worker-finish
join during collection-import teardown wait-idle) —
`tests/test_collection_import_teardown_policy.py::test_nested_worker_finish_join_overrun_during_wait_idle`
and prior-step artifacts. No production code changed. Closes PYPOST-1264
follow-up 7 (Missing Tests §2 / Performance §2).

**Timeout markers (do-testing BLOCKER check): no blocker.** The host module
declares `pytestmark = pytest.mark.timeout(30)`, which covers the new test and
siblings. The nesting hook is single-shot; waits are fake-clock + spy
`wait(ms)` only — no unbounded `Event.wait`, wall-clock sleeps, or nested
`QEventLoop.exec()`.

Phase D / tech-debt-jira-sync creates Debt issues for **new** follow-ups below;
this step only records candidates. Do not re-file PYPOST-1264 items already
ticketed elsewhere.

## Summary Table

| ID | Priority | Item | Follow-up |
| --- | --- | --- | --- |
| TD-1 | — | White-box `processEvents` nest + direct `_on_worker_finished` | no (accepted characterization seam) |
| TD-2 | — | Hook forces `IDLE` because finish handler does not clear busy | no (documents production; intentional) |
| TD-3 | Lowest | Overrun uses private `FakeClock._now` | no (local harness polish only) |
| TD-4 | — | Successful nested join (`join_ok=True`) not asserted | no (DoD is stall / warning path) |
| TD-5 | — | APPLYING long GUI-slot Risk 3 facet still untested | no (out of scope; deferred with PYPOST-1265) |
| TD-6 | — | Nested join remains uncapped by remaining deadline | no (accepted Risk 3 product decision) |

## Shortcuts Taken

1. **Characterization via `processEvents` monkeypatch, not a real `QThread.finished`.**
   The first P1 pump advances the fake clock past the caller budget, calls
   `actions._on_worker_finished()` directly, then sets
   `actions._state = CollectionImportState.IDLE`. Matches Step 2 architecture
   (no live threads, deterministic CI). Trade-off: the suite does not prove Qt
   signal delivery into the connected slot — only that when that slot runs
   nested during P1, the join/overrun/warning contract holds. See TD-1.

2. **Manual IDLE after the nested finish.**
   Production `_on_worker_finished` clears `_worker` and may `wait`, but does
   **not** force `CollectionImportState.IDLE` (`is_busy()` is state-based).
   Leaving PARSING would keep pumping until the deadline expires and mix P1
   timeout noise into the Risk 3 asserts. Forcing IDLE keeps the scenario on
   the nested overrun. See TD-2.

3. **No production or policy default changes.**
   Intentional per requirements. The uncapped nested join (Risk 3) remains the
   accepted product behavior; this ticket only locks the bound and warning.
   See TD-6.

4. **Overrun measured from private `clock._now`.**
   Sibling tests only drive the clock via `advance` / `tick_ms` and spy
   `waits`; this test alone reads `_now` for `elapsed_ms` / `overrun_ms`.
   Adequate for a local double; a public `now` (or elapsed helper) would be
   cleaner. See TD-3.

## Code Quality Issues

1. **TD-1 — white-box nesting seam.**
   Calling the private finish handler from the monkeypatch is the smallest
   helper change (architecture preferred this over extending `_SpySignal` with
   `connect`/`emit`). Coupling is acceptable for a characterization of a named
   private slot, but a rename/signature change of `_on_worker_finished` or a
   change to how `_wait_idle_until` invokes `processEvents` would require
   updating this test in lockstep. No separate ticket.

2. **TD-3 — `FakeClock._now` encapsulation leak.**
   Only
   `test_nested_worker_finish_join_overrun_during_wait_idle` reads the private
   attribute. Optional polish: add a read-only `now` property (or
   `elapsed_ms_since(t0)`) on `FakeClock` and use it here. Not worth a Debt
   issue on its own.

3. **No unexplained architecture deviation.**
   Policy-injected `worker_finish_join_ms`, budget `< join`, stalling
   `_SpyWorker`, single-shot nest, spy wait assert, overrun ≤ join, caplog C1
   WARNING `collection_import_worker_finish_wait_timeout` — all match Step 2.
   Module timeout already present; no new production logging/metrics.

4. **Hardcoded test constants.**
   Local `join_ms = 100` / `budget_ms = 50` mirror the architecture example and
   the policy default for `worker_finish_join_ms`. Clear and intentional; not
   debt.

## Missing Tests

1. **This ticket’s DoD path is covered.** Nested finish during P1 with exhausted
   remaining budget, uncapped `wait(worker_finish_join_ms)`, overrun ≤ join,
   stall WARNING. Gap from PYPOST-1264 follow-up 7 is closed.

2. **TD-4 — successful nested join not characterized.**
   `join_ok=False` is required for the stall warning. A green join under the
   same nest would show overrun still ≤ allowance without the WARNING; nice-to-
   have symmetry, not required by DoD. No follow-up.

3. **TD-5 — long GUI slot during APPLYING (other Risk 3 facet).**
   Still untested. Explicitly out of scope here and deferred relative to
   APPLYING rollback / lifecycle matrices (PYPOST-1265). Do not file a new
   Debt issue from this ticket.

4. **Timeout markers.** Present at module scope — no blocker, no gap.

## Performance Concerns

1. **TD-6 — nested finish join still uncapped by remaining teardown deadline.**
   Pathological stall can add up to `worker_finish_join_ms` (default 100 ms)
   past the caller budget. Accepted since PYPOST-1264; normally instant because
   `finished` fires after `run()` returns. This characterization proves the
   bound and the diagnostic WARNING; it does **not** propose capping the join
   (capping risks “QThread destroyed while running”). No new product ticket.

2. **Test harness itself is cheap.** Fake clock + spy waits; no wall-time
   gates; module timeout 30 s is ample.

## Follow-up Tasks

None. Residual items are accepted characterization seams (TD-1, TD-2), local
harness polish not worth filing (TD-3), optional coverage outside DoD (TD-4),
or pre-existing out-of-scope Risk 3 / lifecycle work already owned elsewhere
(TD-5, TD-6). Phase D should create **zero** new Debt issues from this file.
