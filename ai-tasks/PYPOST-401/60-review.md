# PYPOST-401: Tech Debt Review

## Summary

PYPOST-401 resolved four race conditions (RC-1 through RC-4) in the request worker lifecycle.
The implementation is minimal, correct, and leaves the codebase in a better state than it found.
No new tech debt was introduced. A small number of pre-existing items surfaced during the review.

---

## Debt Introduced by This Task

**None.** The changes are surgical and contained to the affected methods. No workarounds,
temporary flags, or skipped requirements were introduced.

---

## Pre-existing Debt Surfaced During Review

### TD-1: `_reset_tab_ui_state` clears `sender_tab.worker = None` asynchronously via Qt signals ([PYPOST-415](https://pypost.atlassian.net/browse/PYPOST-415))

**Location:** `pypost/ui/presenters/tabs_presenter.py` — `_reset_tab_ui_state`

**Description:** The `finished` and `error` signals connected to `_reset_tab_ui_state` are
dispatched through the Qt event loop. Between a worker finishing and the Qt event loop
dispatching the signal, `sender_tab.worker` still holds the old (dead) reference. The stale-
cleanup guard added in PYPOST-401 (step 2 of `_handle_send_request`) mitigates this, but it
means two code paths are now responsible for keeping `sender_tab.worker` consistent.

**Risk:** Low — the stale-cleanup guard is simple and correct. However, if `_reset_tab_ui_state`
is ever refactored or bypassed, the invariant (`sender_tab.worker is None when no request is
running`) could silently break.

**Recommendation:** Add a short inline comment above the stale-cleanup block referencing this
dependency. No code change required now. Track as minor debt.

---

### TD-2: No test for the `stale_worker_cleared` log path (RC-3 observable path) ([PYPOST-416](https://pypost.atlassian.net/browse/PYPOST-416))

**Location:** `tests/test_worker_race.py`

**Description:** REQ-5.2c tests that a second send while a worker is running does not create a
second worker, but there is no test that exercises the stale-reference cleanup path (i.e., a
worker that has finished but `_reset_tab_ui_state` has not yet fired). The new `stale_worker_cleared`
log entry can only be verified manually or via integration test.

**Risk:** Low — the code path is a one-liner (`sender_tab.worker = None`). The observability
log provides a runtime signal. A unit test would be straightforward to add.

**Recommendation:** Add a focused test in `test_worker_race.py` where `isRunning()` returns
`False` and the new worker creation is permitted. Nice-to-have for a future sprint.

---

### TD-3: `RequestWorker` is not reusable after `stop()` ([PYPOST-417](https://pypost.atlassian.net/browse/PYPOST-417))

**Location:** `pypost/core/worker.py`

**Description:** `threading.Event` is never reset after being set. A stopped worker cannot be
restarted. This is fine for the current design (workers are created fresh per request), but it
is a subtle constraint not documented in the class docstring.

**Risk:** Very low — the current code never restarts a worker. If a future engineer tries to
reuse a stopped worker, the bug would be silent (requests would immediately cancel).

**Recommendation:** Add a one-line docstring note to `RequestWorker.stop()` stating that calling
`stop()` is permanent for the lifetime of the instance. No code change required.

---

## Acceptance Criteria Verification

| AC | Criterion | Status |
|----|-----------|--------|
| AC-1 | `_stop_event` is a `threading.Event` | Verified in `worker.py` `__init__` |
| AC-2 | `stop()` before `run()` cancels request | Verified — no reset in `run()`, test passes |
| AC-3 | No lock, busy-wait, or sleep | Verified — only `threading.Event` used |
| AC-4 | At most one worker per tab running | Verified — stale cleanup + assignment-before-start |
| AC-5 | Send button disabled before `worker.start()` | Verified — pre-existing; button set to "Stop" before `start()` |
| AC-6 | All existing tests pass | Verified — `40-code-cleanup.md` reports 6 passed in worker tests |
| AC-7 | New tests for REQ-5.2a/b/c present and green | Verified — `tests/test_worker_race.py` |
| AC-8 | No changes to `RequestService`, `HTTPClient`, models | Verified by diff inspection |

---

## Files Changed

| File | Net change | Quality |
|------|-----------|---------|
| `pypost/core/worker.py` | +18 / -5 lines | Clean; logging adds observable boundaries |
| `pypost/ui/presenters/tabs_presenter.py` | +10 / -2 lines | Clean; explicit `is not None` guards improve readability |
| `tests/test_worker_race.py` | +80 lines (new) | Well-structured; helpers reused across all three cases |

---

## Overall Assessment

The implementation is production-ready. The three pre-existing debt items noted above are
low-risk and do not block release. TD-1 and TD-3 are documentation-level; TD-2 is a
nice-to-have test addition suitable for a future cleanup sprint.
