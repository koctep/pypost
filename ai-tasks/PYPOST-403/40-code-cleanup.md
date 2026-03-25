# PYPOST-403 Code Cleanup — [HP] Fix failing tests in CI

**Author**: junior_engineer
**Date**: 2026-03-25
**Status**: Complete

---

## Summary

All five failing CI tests are now fixed. One pre-existing test was updated to reflect
the new `HTTPClient` contract. The `core` crash dump has been removed.

---

## Files Changed

| File | Change |
|------|--------|
| `pypost/core/http_client.py` | `__init__`: default-construct `TemplateService()` when arg is `None` |
| `pypost/core/history_manager.py` | `__init__`: add `_save_thread = None`; `_save_async`: store thread ref; add `flush()` method |
| `tests/test_http_client_sse_probe.py` | Import `TemplateService`; inject in `setUp`; replace inline `HTTPClient()` with `self.client` in all 3 test methods |
| `tests/test_history_manager.py` | `_manager_at`: init `_save_thread = None`; add `hm.flush()` to `test_append_single_entry` and `test_get_entries_newest_first` |
| `tests/test_http_client.py` | Updated `test_no_injection_sets_template_service_to_none` → `test_no_injection_creates_default_template_service` to reflect new contract |
| `.gitignore` | Append `core` and `core.*` ELF dump patterns |
| `core` (repo root) | Deleted (86 MB ELF crash dump) |

---

## Cleanup Notes

- No dead code introduced or left behind.
- No trailing whitespace; all files use LF line endings.
- Line length ≤ 100 characters throughout.
- No `time.sleep` introduced in tests; `flush()` provides deterministic synchronization.
- All changes are surgical and additive — no existing passing tests were broken.

---

## Test Results

```
191 passed in 2.38s
```
