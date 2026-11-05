# PYPOST-1320: Technical Debt Analysis

Scope analysed: harness-only fix in `tests/helpers/process_until.py`
(`_DeadlineScheduler`, `_arm_posted_quit`, module-scoped daemon),
`tests/test_process_until_watchdog_repro.py`, hang-regression coverage in
`tests/test_env_storage_responsiveness.py`, and prior-step artifacts. Product
`pypost/` unchanged.

**Timeout markers (do-testing BLOCKER check): no blocker.** Watchdog repro,
diagnostics, and env-storage responsiveness modules all declare module
`pytestmark = pytest.mark.timeout(...)`. Internal waits use bounded
`Event.wait` / `process_until(..., timeout_ms=...)` / `QThread.wait(ms)`.

Phase D / tech-debt-jira-sync creates Debt issues; this step only records
candidates. **Jira links left empty** until ticketed.

## Summary Table

| ID | Priority | Item | Follow-up |
| --- | --- | --- | --- |
| TD-1 | Medium | Uncaught `callback()` in `_DeadlineScheduler._run` kills the daemon forever | yes (new) |
| TD-2 | Low | Dev docs still say per-wait `threading.Timer` (Step 8 + sibling docs) | yes (new; Step 8 owns primary) |
| TD-3 | Low | Watchdog repro uses private `threading._active_limbo_lock` | yes (new) |
| TD-4 | Low | No direct unit tests for scheduler arm/cancel/multi-entry/exception path | yes (new) |
| TD-5 | Low | First arm still calls `Thread.start` (bootstrap residual under contention) | yes (new; accepted residual) |
| TD-6 | Lowest | Cancelled heap tombstones until due; growth under cancel churn | no (accepted) |
| TD-7 | Lowest | Optional env-flag scheduler DEBUG (Step 6 deferred) | no (accepted N/A) |

## Shortcuts Taken

1. **Docs wording left for Step 8.** Architecture and Step 6 already defer updating
   `doc/dev/gui_testing.md` / `doc/dev/testing.md` from “daemon `threading.Timer`”
   to the shared deadline scheduler. That is in-workflow, not a skip of the DoD —
   but sibling docs (`environment_storage_async.md`, historical note in
   `collection_import.md`) also still describe `Timer` and must not be forgotten.
   See TD-2.

2. **Quiet warmup before the contended arm.** The repro calls
   `process_until(lambda: True, …)` once so `_DeadlineScheduler` bootstraps outside
   the limbo/logging race. That matches architecture Q&A (bootstrap once under quiet
   conditions). Consumers do not get an explicit public warmup API; first real wait
   in a fresh process still hits `Thread.start`. See TD-5.

3. **Forced limbo hold via private CPython lock.** The repro acquires
   `threading._active_limbo_lock` inside a logging `Handler.emit` to keep the
   DummyThread / `exc_info` critical section stable. Correct for a deterministic
   hang class, but coupled to CPython internals. See TD-3.

4. **No scheduler self-logging.** Step 6 correctly avoided logging on the arm/fire
   path (same lock family as the hang). Optional DEBUG under an env flag remains
   out of scope. See TD-7.

5. **Product `exc_info=True` left unchanged.** Requirements preferred a helper-only
   fix; the worker log path remains a trigger, not a rewrite target. No follow-up
   unless a later hang proves the helper insufficient.

## Code Quality Issues

1. **TD-1 (Medium) — daemon dies on callback exception.**
   `_DeadlineScheduler._run` invokes `callback()` outside the Condition with no
   `try`/`except`. If `post_quit` (or a future arm callback) raises, the `while True`
   loop exits, `_thread` stays non-`None`, and `_ensure_started` never restarts the
   daemon. Later waits enqueue deadlines that never fire; `use_poll_timer=False`
   hang-regression can hang again. Today `QTimer.singleShot(0, loop, loop.quit)` is
   unlikely to raise, but a shared process-lifetime thread should isolate faults.
   Follow-up: wrap fire in try/except (log or swallow), and/or clear `_thread` and
   allow restart on death.

2. **TD-5 (Low) — `_ensure_started` holds the Condition across `Thread.start`.**
   Bootstrap still takes limbo during `start()` while holding `_cv`. Ordering is
   safe with CPython’s `_started`-before-target semantics (no self-deadlock with
   `_run`), but the first arm under QThread `exc_info` contention retains the
   historical hang window. Mitigated by process-lifetime reuse after first success
   and by the repro’s warmup. Residual, not a regression of the hot path.

3. **TD-6 (Lowest) — lazy cancel via heap tombstones.**
   `cancel()` sets `cancelled` / clears `callback` but leaves the entry until it is
   the heap minimum. Fine for typical GUI nested waits; pathological
   arm-and-cancel storms could grow the heap. No action unless profiling shows it.

4. **No unexplained architecture deviation.** Dual-deadline contract, posted
   `QTimer.singleShot(0, loop, loop.quit)`, public `process_until` API, and
   hang-regression mode match Step 2. Product unchanged by design.

## Missing Tests

1. **TD-4 (Low) — no direct `_DeadlineScheduler` unit coverage.**
   Behavior is proven only through:
   - `test_process_until_exits_near_deadline_under_qthread_exc_info` (limbo race)
   - hang-regression / diagnostics modules (posted quit + timeout text)
   There is no focused test that arms multiple overlapping deadlines, cancels one,
   asserts fire order, or kills the callback and checks the daemon stays usable
   (pairs with TD-1). A small non-Qt unit module (or private helper tests) would
   lock the scheduler contract without spinning `QEventLoop`.

2. **Otherwise covered for this task:** green watchdog repro; posted-quit without
   poll timer; wall-clock deadline; timeout_detail / gateway diagnostics; stress
   evidence recorded in Step 4 roadmap notes. Timeout markers present (no blocker).

3. **TD-3 (Low) — repro portability.**
   If a future CPython renames or removes `_active_limbo_lock`, the forced critical
   section breaks. Prefer a documented private-API note in the module docstring
   and/or a skip/xfail with a clear reason if the attribute is missing — or a
   public-API-only amplification if one can be found that still races reliably.

## Performance Concerns

1. **One long-lived daemon** (`process-until-deadline`) per process. Negligible idle
   cost; sleeps on `Condition.wait` until the next deadline. No follow-up.

2. **Cancelled tombstones (TD-6).** Only a concern under extreme cancel rates; GUI
   suites do not exhibit that pattern.

3. **No new product path cost.** Helper-only; poll timer interval remains 10 ms
   (pre-existing).

## Follow-up Tasks

Specific tasks for Phase D / tech-debt Jira sync (do **not** create issues in Step 7):

1. **TD-1 — Harden `_DeadlineScheduler` against callback failures** (Medium)  
   Isolate `callback()` so an exception cannot permanently stop the daemon; allow
   restart or keep the loop alive. Add a regression that raises from a scheduled
   callback and still arms a later deadline.  
   Jira: [PYPOST-1487](https://pypost.atlassian.net/browse/PYPOST-1487)

2. **TD-2 — Align remaining Timer wording in developer docs** (Low)  
   Step 8 must update `doc/dev/gui_testing.md` and `doc/dev/testing.md` (planned).
   Also refresh `doc/dev/environment_storage_async.md` (dual-deadline still says
   daemon `threading.Timer`) and the PYPOST-1320 historical hang note in
   `doc/dev/collection_import.md` so maintainers do not reintroduce per-wait
   `Timer.start`. Prefer folding sibling docs into Step 8; file Debt only if Step 8
   leaves them stale.  
   Jira: [PYPOST-1488](https://pypost.atlassian.net/browse/PYPOST-1488)

3. **TD-3 — Reduce private limbo-lock coupling in the watchdog repro** (Low)  
   Document the CPython dependency; guard missing `_active_limbo_lock`; or find a
   public-API contention setup that still forces the DummyThread / logging window.  
   Jira: [PYPOST-1489](https://pypost.atlassian.net/browse/PYPOST-1489)

4. **TD-4 — Unit-test `_DeadlineScheduler` arm / cancel / multi-entry** (Low)  
   Cover overlapping deadlines, cancel-before-fire, and (with TD-1) post-exception
   recovery without requiring a full Qt limbo repro.  
   Jira: [PYPOST-1490](https://pypost.atlassian.net/browse/PYPOST-1490)

5. **TD-5 — Optional: document or pre-warm bootstrap for first contended wait** (Low)  
   Residual first-`Thread.start` window. Options: note in Step 8 docs that the
   first `process_until` in a worker process starts the daemon; or a quiet
   session-scoped harness warmup. Not required for DoD (hot path is fixed).  
   Jira: [PYPOST-1491](https://pypost.atlassian.net/browse/PYPOST-1491)

**Accepted / no new ticket:**

- **TD-6** — cancelled heap tombstones (acceptable for harness load).
- **TD-7** — env-flag scheduler DEBUG (Step 6 N/A; logging on this path is harmful).
- Product `exc_info=True` retention (requirements / architecture).

### Pre-existing suite failures

None newly discovered in this Step 7 analysis (artifact-and-source review only;
focused green evidence already recorded in Steps 4–5). The hang class this ticket
fixes was previously filed as PYPOST-1320 itself (see PYPOST-1264 debt notes) and
is the subject of this task, not a separate Debt follow-up.

## User documentation

N/A for this step — no user-facing product change. Step 8 owns `doc/dev/` wording
for the shared deadline scheduler (see TD-2).

## Decision

**SAFE TO PROCEED** to Step 8. No BLOCKER debt. Medium item TD-1 is a hardening
follow-up, not a gate on documenting the shipped scheduler.
