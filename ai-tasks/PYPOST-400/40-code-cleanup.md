# PYPOST-400: Code Cleanup Report

## Summary

Implementation of structured error handling across the post publishing flow is complete.
All code changes follow the architecture in `20-architecture.md`. No significant cleanup
issues found; minor notes below.

---

## Files Changed

### New File: `pypost/models/errors.py`
- Clean, minimal module — `ErrorCategory` enum and `ExecutionError` dataclass.
- No issues.

### `pypost/core/metrics.py`
- Added `request_errors` and `history_record_errors` counters to `_init_metrics()`.
- Added `track_request_error()` and `track_history_record_error()` methods.
- Import of `ErrorCategory` placed at module level after stdlib/third-party imports.
- No issues.

### `pypost/core/http_client.py`
- Replaced bare `except Exception: raise` with three ordered `except` clauses:
  `requests.Timeout` → `requests.ConnectionError` → `requests.RequestException`.
- `requests.Timeout` caught first (it is a subclass of `ConnectionError` in some builds).
- No issues.

### `pypost/core/mcp_client_service.py`
- `asyncio.TimeoutError` branch raises `ExecutionError(TIMEOUT)`.
- General `Exception` branch classifies by error type/message and raises `ExecutionError`.
- Dead `elapsed` variable removed (no longer needed in error paths).
- No issues.

### `pypost/core/request_service.py`
- `ExecutionResult` dataclass gains `execution_error: Optional[ExecutionError] = None`
  with `field(default=None)` — backward-compatible.
- Template render guard at top of `execute()` is conditional on `self._template_service`
  being set, preserving compatibility with callers that omit `template_service`.
- `_error_response()` is a module-level private function (not a method) — consistent with
  keeping `ExecutionResult` data-only.
- History failure now calls `self._metrics.track_history_record_error()` when metrics
  are available.
- No issues.

### `pypost/core/worker.py`
- `error = Signal(object)` replaces `Signal(str)` — carries `ExecutionError` or `str`.
- Two `except` clauses: specific `ExecutionError` and catch-all `Exception` wrapping.
- No issues.

### `pypost/ui/presenters/tabs_presenter.py`
- `_ERROR_MESSAGES` is a module-level constant dict — testable in isolation.
- `_on_request_error()` handles both `str` (legacy/cancellation) and `ExecutionError`.
- No issues.

---

## Test Files Changed/Added

| File | Change |
|------|--------|
| `tests/test_http_client.py` | Updated `test_connection_error_propagates` → expects `ExecutionError`; added 3 new tests |
| `tests/test_mcp_client_service.py` | Updated `test_connection_error_returns_500` → expects `ExecutionError`; added 2 new tests |
| `tests/test_request_service.py` | Added `history_failure_tracked_via_metrics` and `TestRequestServiceErrorHandling` class (7 tests) |
| `tests/test_worker.py` | New file — 3 tests for worker error signal behavior |
| `tests/test_tabs_presenter.py` | Added `TestOnRequestError` class (6 tests) |
| `tests/conftest.py` | New file — sets `QT_QPA_PLATFORM=offscreen` before Qt imports |

---

## Pre-existing Failures (Not Introduced by This PR)

The following test failures existed before this change and are unrelated:

| Test | Root Cause |
|------|-----------|
| `test_http_client_sse_probe.py` (3 tests) | `HTTPClient()` without `template_service` — pre-existing DI gap |
| `test_history_manager.py` (flaky) | `OSError: Directory not empty` on tmpdir cleanup — OS-level race |

---

## No Action Required

- Line lengths are within the 100-character limit.
- No trailing whitespace introduced.
- All new code is English, UTF-8, LF line endings.
- No dead code, no commented-out blocks, no unused imports.
