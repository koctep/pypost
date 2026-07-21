# PYPOST-877: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

DoD met: env-presenter async-load encryption refresh check and its hang-exit
proof use shared `tests.helpers.process_until.process_until` (wall-clock +
posted quit). Timer-only nested `QEventLoop` wait is gone. Product
`EnvPresenter` / encryption / gateway runtime unchanged. Items below are
non-blocking follow-ups or work already owned elsewhere.

## Shortcuts Taken

- **Wire-only; no helper API change.** Reused existing `process_until` defaults
  (`timeout_ms=5_000` on the business wait; no `timeout_detail`). Matches
  architecture option “wire only” and sibling gateway waits.
- **Kept module-local `QApplication` via `setUpClass`.** Aligning
  `tests/test_env_presenter.py` onto shared `qapp` /
  `usefixtures("qapp")` was explicitly out of scope (was once attributed to
  PYPOST-830; suite-wide remainder is [PYPOST-886](https://pypost.atlassian.net/browse/PYPOST-886)).
- **Omitted richer timeout diagnostics on the presenter wait.** Default
  neutral `AssertionError` text is enough for list-refresh waits; busy/pending
  / worker snapshots remain the gateway path ([PYPOST-828](https://pypost.atlassian.net/browse/PYPOST-828),
  done).
- **Call-site hang proof kept as a subprocess.** Architecture allowed a thin
  module-local proof after green so a hang cannot wedge the parent pytest
  process. The child exercises `process_until(lambda: False, timeout_ms=300)`
  (not a full `EnvPresenter` load), overlapping responsiveness helper proofs
  by design for isolation — see Follow-up Tasks.
- **Dev-doc consumer list not updated in this step.** Listing
  `test_env_presenter.py` under `doc/dev/gui_testing.md` is Step 8 for this
  task, not a separate Debt ticket.

No other shortcuts. Implementation matched architecture (shared helper at the
call site; business assertions preserved).

## Code Quality Issues

- **Hang-exit proof duplicates helper coverage.**
  `test_async_load_wait_exits_near_deadline_when_never_complete` re-proves
  wall-clock deadline exit already covered by
  `tests/test_env_storage_responsiveness.py` (and diagnostics module), via an
  embedded `-c` child script. Valuable as parent-process isolation; optional
  later slim/delete once docs list the env-presenter consumer (TD-1).
- **Embedded child script string.** The hang proof inlines a multi-line
  `python -c` payload with `%` path formatting. Readable enough for one proof;
  extracting a tiny helper module would be polish only (fold into TD-1 if
  kept).
- **Architecture vs implementation:** no meaningful deviation — shared
  `process_until`, 5 s business wait, hang-exit near 300 ms, unused
  `QEventLoop` / `QTimer` imports removed.

No naming, structure, or copy-drift issues in the wire-up. No remaining
timer-only nested `exec()` in `tests/` outside the shared helper itself.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Async load + encryption refreshes env list | Covered (wired business check) |
| Wait ends near wall-clock deadline (never-true) | Covered (subprocess hang-exit proof) |
| Posted quit without poll timer | Covered (responsiveness; not re-proven here) |
| Explicit timeout markers | Covered (`pytestmark = timeout(60)`; hang proof `@timeout(15)`) |
| `timeout_detail` on presenter wait | Not added (N/A — not a gateway wait) |
| Shared `qapp` / `usefixtures` for this module | Out of scope (PYPOST-886) |
| Dedicated `tests/helpers/test_process_until.py` | Not required — hang regressions already cover the helper |

**No timeout-marker blockers** (`.cursor/lsr/do-testing.md`).

## Performance Concerns

None introduced. Business wait budget matches sibling gateways (5 s). Hang-exit
proof stays ~300 ms by design inside a 2 s subprocess outer timeout. Focused
suite (Step 5): **45/45** `tests/test_env_presenter.py` passed.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Richer `process_until` timeout diagnostics | [PYPOST-828](https://pypost.atlassian.net/browse/PYPOST-828) (done) |
| Production worker finish teardown (H3) | [PYPOST-829](https://pypost.atlassian.net/browse/PYPOST-829) (done) |
| Gateway shared-`qapp` alignment | [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) (done) |
| Suite-wide migrate remaining `setUpClass` / local `qapp` (includes presenters) | [PYPOST-886](https://pypost.atlassian.net/browse/PYPOST-886) |
| This story (env-presenter hang-resistant wait) | [PYPOST-877](https://pypost.atlassian.net/browse/PYPOST-877) |

### NON-BLOCKER — optional hygiene (no new Jira unless sync wants it)

| ID | Priority | Task | Notes |
| -- | -------- | ---- | ----- |
| TD-1 | Lowest | Slim or drop call-site hang subprocess proof if docs + business check suffice | Overlaps responsiveness wall-clock proof; keep while useful as parent-isolation canary, or delete after Step 8 documents the consumer |

### Planned this ticket (not separate Debt)

- Step 8: add `tests/test_env_presenter.py` to the shared-helper consumer list
  in `doc/dev/gui_testing.md` (and cross-links if needed).

## User documentation

N/A — harness-only change; no `doc/user/` updates. Developer docs are Step 8.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to DoD |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None — wire-only shared helper |
| Hardcoded values | `timeout_ms=5_000` / `300` intentional parity with siblings |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — PYPOST-827 Medium follow-up closed: env-presenter
async-load nested wait is hang-resistant via the shared definition; suite no
longer depends on timer-only quit for that check. Remaining gaps are optional
hygiene or already-ticketed suite-wide `qapp` migration.

## Worklog

```
tokens_used: 45000
role: execution
step: 7
step_name: Review
```
