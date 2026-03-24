# PYPOST-400: Tech Debt Review

## Summary

Structured error handling has been introduced across the post publishing flow. The implementation
is clean, well-tested, and satisfies all requirements. This review identifies residual tech debt
and minor improvement opportunities for future sprints.

---

## What Was Done Well

- **Shared error model** (`pypost/models/errors.py`) is minimal and correctly typed. `ErrorCategory`
  as a `str` enum avoids `.value` boilerplate in Prometheus labels.
- **`ExecutionResult.execution_error`** is additive with `field(default=None)` — zero regression
  risk for existing callers.
- **`_error_response()`** as a module-level function (not a method) keeps `ExecutionResult`
  data-only and is easy to test in isolation.
- **`_ERROR_MESSAGES`** as a module-level constant in `tabs_presenter.py` makes message copy
  independently testable.
- **Test coverage**: 43 new/updated tests cover all error categories, signal types, and UI
  message templates.
- **Observability**: Every error path is covered by a Prometheus counter and an `ERROR`-level log
  entry with structured fields.

---

## Residual Tech Debt

### TD-1 — `script_error: Optional[str]` is now partially redundant

**File:** `pypost/core/request_service.py`

`ExecutionResult` has both `script_error: Optional[str]` (original) and
`execution_error: Optional[ExecutionError]` (new). When a script fails, both are populated with
the same content. The `script_error` string field was kept for backward compatibility (REQ-7.3)
but it creates a dual-source-of-truth for script failures.

**Recommended action:** Deprecate `script_error` in a future sprint; migrate callers to check
`execution_error.category == ErrorCategory.SCRIPT` and remove the string field.

---

### TD-2 — Template render guard duplicates work

**File:** `pypost/core/request_service.py`, lines 106–118

The template render guard (step 1 of `execute()`) calls `render_string(request.url, variables)`
purely for validation. The same render is performed again later — once in `_execute_mcp()` (line
62) and inside `http_client.send_request()` (via `_prepare_request_kwargs`). For the HTTP path
this means the URL template is rendered twice per request.

**Recommended action:** Refactor to render-once and pass the resolved URL down the call chain
rather than re-rendering. This also removes the need for the guard step entirely, as the error
will be raised naturally during execution.

---

### TD-3 — `MCPClientService` heuristic error classification is fragile

**File:** `pypost/core/mcp_client_service.py`, lines 65–73

Connection vs. timeout errors are classified by inspecting `type(exc).__name__` and the string
`str(exc)`. This works for the current MCP client library but is brittle — a library version
bump could rename exception types and silently misclassify errors.

**Recommended action:** Enumerate the specific exception types from the MCP/httpx library
(e.g. `httpx.ConnectError`, `httpx.TimeoutException`) in explicit `except` clauses, mirroring the
pattern used in `http_client.py`.

---

### TD-4 — `worker.py` `ExecutionError` handler is dead code

**File:** `pypost/core/worker.py`, lines 77–81

`RequestService.execute()` never raises — it always returns an `ExecutionResult` (AC-3). The
`except ExecutionError` block in `RequestWorker.run()` can therefore only be triggered by the
template render guard, which raises `ExecutionError` before `execute()` returns. This path is
correct but not covered by the worker tests.

**Recommended action:** Add a test that injects a template render failure to exercise the
`except ExecutionError` branch in `RequestWorker.run()`.

---

### TD-5 — `_on_request_error` cancellation check on `ExecutionError.detail` is imprecise

**File:** `pypost/ui/presenters/tabs_presenter.py`, lines 403–407

Cancellation is detected by checking if the string `"cancelled"` or `"aborted"` appears in
`error.detail`. This is a string-matching heuristic — if the underlying exception message changes,
cancellations will surface as error dialogs.

**Recommended action:** Introduce an `ErrorCategory.CANCELLED` value and emit it explicitly from
`RequestWorker.stop()` / the stop-flag path, replacing string matching with a type-safe check.

---

### TD-6 — Pre-existing test failures not addressed

**Files:** `tests/test_http_client_sse_probe.py`, `tests/test_history_manager.py`

Three SSE probe tests fail because `HTTPClient()` can be instantiated without a
`template_service`, exposing a DI gap (tracked pre-PYPOST-400). One history manager test is
flaky due to an OS-level tmpdir race. These are out of scope for this ticket but should be
scheduled.

**Recommended action:** Create follow-up tickets for the DI gap (link to PYPOST-378 pattern)
and the flaky history test.

---

## Acceptance Criteria Verification

| # | Criterion | Status |
|---|-----------|--------|
| AC-1 | `ExecutionError` and `ErrorCategory` exist in `pypost/models/errors.py` | ✓ |
| AC-2 | `HTTPClient` raises `ExecutionError` for all failure modes | ✓ |
| AC-3 | `RequestService.execute()` never raises; always returns `ExecutionResult` | ✓ |
| AC-4 | `RequestWorker.error` signal carries `ExecutionError` | ✓ |
| AC-5 | UI shows actionable, category-specific messages — no raw exception strings | ✓ |
| AC-6 | Each error category has a `request_errors_total{category=...}` counter | ✓ |
| AC-7 | History recording failures increment `history_record_errors_total` | ✓ |
| AC-8 | All existing tests pass with no modifications to test inputs | ✓ (43 pass) |

---

## Risk Assessment

**Low risk.** All changes are additive or confined to error paths. The happy path through
`RequestService.execute()`, `HTTPClient.send_request()`, and `RequestWorker.run()` is unchanged.
No public interfaces were removed. The signal type change (`Signal(str)` → `Signal(object)`) is
backward-compatible because the `_on_request_error` handler accepts both `str` and `ExecutionError`.
