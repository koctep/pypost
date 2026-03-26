# PYPOST-419 — Code Cleanup

## Summary

Implementation complete. Three production files modified; one test class added. No cleanup
issues found — the implementation is minimal and follows existing patterns.

---

## Files Changed

| File | Change |
|------|--------|
| `pypost/core/request_service.py` | Added `default_retry_policy` constructor param and two-line fallback in `_execute_http_with_retry` |
| `pypost/core/worker.py` | Added `RetryPolicy` import, `default_retry_policy` constructor param, forwarded to `RequestService` |
| `pypost/ui/presenters/tabs_presenter.py` | Passed `self._settings.default_retry_policy` when constructing `RequestWorker` |
| `tests/test_request_service.py` | Added `TestRequestServiceRetryPolicyResolution` with three branch tests |

---

## Cleanup Checklist

- [x] No dead code introduced
- [x] No unused imports
- [x] Line length ≤ 100 characters (all lines checked)
- [x] Trailing whitespace removed
- [x] Single final newline on all modified files
- [x] All code and comments in English
- [x] No backwards-compatibility hacks required (new param defaults to `None`)
- [x] No structural changes beyond what the architecture specified

---

## Test Results

All 26 tests pass (`tests/test_request_service.py`), including:

- `test_per_request_policy_wins_over_app_default` — AC-2: 2 calls (1 initial + 1 retry)
- `test_app_default_used_when_no_per_request_policy` — AC-1: 3 calls (1 initial + 2 retries)
- `test_hardcoded_fallback_when_both_policies_none` — AC-3: 1 call (max_retries=0)

Existing tests unchanged and all passing.
