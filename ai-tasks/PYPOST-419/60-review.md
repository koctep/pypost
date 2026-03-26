# PYPOST-419 — Tech Debt Review

**Reviewer**: Team Lead
**Date**: 2026-03-26
**Scope**: `request_service.py`, `worker.py`, `tabs_presenter.py`,
`tests/test_request_service.py`

---

## Summary

PYPOST-419 resolves RISK-2 carry-forward from Sprint 134: `AppSettings.default_retry_policy`
was persisted and editable via the Settings dialog but never applied at runtime. The fix
threads the value through the existing DI chain (`TabsPresenter` → `RequestWorker` →
`RequestService`) using a minimal two-line insert at the single policy-resolution point inside
`_execute_http_with_retry`.

---

## Resolved Tech Debt

| Item | Status |
|------|--------|
| RISK-2 (Sprint 134) — `default_retry_policy` inert end-to-end | **Closed** |
| Policy resolution gap — per-request fell straight through to hardcoded defaults | **Closed** |
| DI chain incomplete for retry configuration | **Closed** |

---

## Code Quality Assessment

### Strengths

1. **Minimal scope** — four files touched; zero files added. The two-line insert in
   `_execute_http_with_retry` resolves the bug at the only point where `request.retry_policy`
   is read, requiring no refactoring of the surrounding logic.

2. **Consistent DI pattern** — `default_retry_policy: RetryPolicy | None = None` follows
   the same keyword-argument-with-`None`-default convention used for `alert_manager`,
   `template_service`, and `history_manager` in both `RequestService` and `RequestWorker`.

3. **Backward compatibility** — all existing callers continue to work unchanged; the new
   parameter defaults to `None`, which preserves the prior hardcoded-fallback behaviour
   (AC-3, AC-4, AC-5 verified).

4. **Snapshot semantics** — `default_retry_policy` is extracted from `AppSettings` at
   `RequestWorker` construction time (i.e. when Send is clicked). This is intentional:
   a settings change while a request is in-flight does not alter that request's policy,
   consistent with how `alert_manager` and `template_service` are handled.

5. **Test coverage** — three explicit branch tests cover every resolution tier
   (AC-1 / AC-2 / AC-3); all 26 pre-existing tests pass unmodified.

6. **Observability** — three targeted debug-log statements cover the full DI chain:
   injection at `RequestService.__init__`, forwarding at `RequestWorker.__init__`, and
   per-request source annotation at `_execute_http_with_retry`. No new metrics required.

### Observations (No Blocking Issues)

1. **`apply_settings` does not propagate `default_retry_policy` to in-flight workers** —
   This is by design; in-flight workers already hold the policy they were constructed with.
   No action required. Future work: document this in user-facing settings help text if
   confusion is reported.

2. **`_policy_source` computed unconditionally on every request** — The ternary is O(1)
   and DEBUG-only; no performance concern. If logging overhead becomes measurable, a
   `logger.isEnabledFor(logging.DEBUG)` guard could be added, but this is premature at
   current load.

3. **No integration test for the full DI chain from `TabsPresenter` to policy application**
   — Unit tests validate `RequestService` in isolation (correct) and the wiring is covered
   by code review + observability logs. An integration test of `TabsPresenter.send_request`
   end-to-end would add confidence but is out of scope for this issue given the Qt event-loop
   complexity. Tracked as potential tech debt for a future sprint.

---

## New Tech Debt Introduced

**None.** The implementation is minimal, follows established patterns, and introduces no
abstractions that will need future maintenance.

---

## Acceptance Criteria Verification

| AC | Criterion | Result |
|----|-----------|--------|
| AC-1 | `retry_policy=None` + `default_retry_policy=RetryPolicy(max_retries=3)` → 3 retries | **PASS** (`test_app_default_used_when_no_per_request_policy`: 3 calls) |
| AC-2 | Explicit `retry_policy=RetryPolicy(max_retries=1)` overrides app default | **PASS** (`test_per_request_policy_wins_over_app_default`: 2 calls) |
| AC-3 | Both `None` → `max_retries=0`, exactly 1 call | **PASS** (`test_hardcoded_fallback_when_both_policies_none`: 1 call) |
| AC-4 | Existing tests pass without modification | **PASS** (26/26 tests green) |
| AC-5 | Old `settings.json` without `default_retry_policy` loads cleanly | **PASS** (Pydantic `Optional` default; no migration) |

---

## Risk Assessment

| Risk | Finding |
|------|---------|
| Regression in existing retry paths | None — `max_retries=0` default preserved |
| Constructor signature conflict with PYPOST-418 `alert_manager` | None — new param added after `alert_manager`; all call sites use keyword args |
| Retry counts logged inaccurately | None — `max_retries` derived from the already-resolved effective policy |
| Silent failure if `AppSettings.default_retry_policy` is `None` | None — falls through to hardcoded defaults, unchanged from prior behaviour |

---

## Verdict

**Approved.** No blocking issues. PYPOST-419 fully resolves RISK-2. Implementation is
clean, minimal, and consistent with the codebase's DI conventions. Ready for developer
documentation and final commit.
