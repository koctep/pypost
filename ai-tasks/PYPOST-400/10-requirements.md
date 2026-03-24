# PYPOST-400: Stabilize Post Publishing API Error Handling

## Overview

**Ticket:** PYPOST-400
**Type:** Debt
**Priority:** High
**Labels:** high-priority, sprint-mar24
**Status:** To Do

**Summary:** Audit and stabilize API error handling for post publishing flow. Ensure consistent
status codes and actionable error messages.

---

## Context

PyPost is a desktop HTTP client application. The "post publishing flow" refers to the full
lifecycle of executing an HTTP POST request: URL/header/body template rendering, script
execution, HTTP dispatch, response capture, history recording, and UI feedback.

Currently, error handling is inconsistent across the execution layers. Exceptions bubble up
differently, error messages are not always actionable, and there is no uniform contract between
the service layer and the UI for communicating failure modes.

---

## Problem Statement

### Identified Issues

1. **Inconsistent exception propagation** — `HTTPClient` re-raises raw exceptions; `RequestService`
   silently swallows history-recording errors; `RequestWorker` converts all exceptions to plain
   strings before emitting signals.

2. **Non-actionable error messages** — The UI displays `"Request failed: {raw_exception_str}"`.
   Raw Python exception strings (e.g. `ConnectionError('...')`) are not human-friendly.

3. **Missing error categorization** — Network errors, timeout errors, configuration errors, and
   script execution errors are all surfaced through the same generic path with no distinction.

4. **Inconsistent status code usage in the MCP layer** — `MCPClientService` uses HTTP status
   codes (200, 500, 504) inside an in-process JSON response dict, which conflates transport-level
   and application-level semantics.

5. **Silent failures** — History recording failures are silently logged but never surfaced to
   the user or metrics. Script errors are returned in `ExecutionResult.script_error` but there
   is no guarantee the UI checks this field.

6. **No structured error type** — There is no shared error model or enum. Each layer invents its
   own error representation (string, dict, tuple, exception).

---

## Requirements

### REQ-1: Define a Structured Error Model

A shared error model must be introduced to represent failures in the post-execution flow.

- **REQ-1.1** Create an `ExecutionError` dataclass (or similar) with at minimum:
  - `category: ErrorCategory` — enum value (see REQ-1.2)
  - `message: str` — human-readable, actionable description
  - `detail: str | None` — optional technical detail for logs/debug view
- **REQ-1.2** Define an `ErrorCategory` enum with at minimum:
  - `NETWORK` — connection failures, DNS errors, refused connections
  - `TIMEOUT` — request exceeded configured timeout
  - `TEMPLATE` — Jinja2 template rendering errors
  - `SCRIPT` — post-request script execution errors
  - `HISTORY` — history recording errors (non-fatal)
  - `UNKNOWN` — uncategorized exceptions

### REQ-2: Consistent Exception Handling in HTTPClient

- **REQ-2.1** `HTTPClient.execute()` must catch all exceptions and raise a typed
  `ExecutionError` instead of re-raising raw exceptions.
- **REQ-2.2** `requests.ConnectionError` and similar network failures must map to
  `ErrorCategory.NETWORK`.
- **REQ-2.3** `requests.Timeout` must map to `ErrorCategory.TIMEOUT`.
- **REQ-2.4** All other `requests.RequestException` subclasses must map to `ErrorCategory.UNKNOWN`
  with the original exception message preserved in `detail`.

### REQ-3: Consistent Error Propagation in RequestService

- **REQ-3.1** `RequestService.execute()` must catch `ExecutionError` from `HTTPClient` and
  populate `ExecutionResult` with the error rather than letting it propagate unchecked.
- **REQ-3.2** Template rendering errors must be caught, categorized as `ErrorCategory.TEMPLATE`,
  and returned in `ExecutionResult` before any HTTP dispatch is attempted.
- **REQ-3.3** Script execution errors must populate `ExecutionResult.script_error` using the
  `ExecutionError` model (or an equivalent field already present).
- **REQ-3.4** History recording errors must remain non-fatal but must be tracked via
  `MetricsManager` (increment a dedicated counter) rather than only logged.

### REQ-4: Actionable Error Messages in RequestWorker / UI

- **REQ-4.1** `RequestWorker` must emit structured error information through its `error` signal.
  The signal payload must carry enough information for the UI to display a categorized, actionable
  message.
- **REQ-4.2** The UI presenter (`tabs_presenter.py`) must map each `ErrorCategory` to a
  user-friendly message template. Examples:
  - `NETWORK` → "Could not connect to {url}. Check that the server is running and reachable."
  - `TIMEOUT` → "Request to {url} timed out. Try increasing the timeout or check server load."
  - `TEMPLATE` → "Template rendering failed: {detail}. Check variable names and syntax."
  - `SCRIPT` → "Post-script execution failed: {detail}. Review the script for errors."
  - `UNKNOWN` → "An unexpected error occurred: {detail}."
- **REQ-4.3** The raw exception string must NOT be shown directly to the user. It may appear
  in debug/detail view only.

### REQ-5: MCP Layer Status Code Consistency

- **REQ-5.1** `MCPClientService` must not use HTTP status codes in its internal response dicts.
  Internal communication must use the `ExecutionError` model or a dedicated result type.
- **REQ-5.2** The MCP HTTP server endpoints (`/messages`, `/sse`) may continue to use HTTP
  status codes for their actual HTTP responses to clients. This requirement applies only to
  internal Python method return values.

### REQ-6: Metrics Coverage

- **REQ-6.1** Each `ErrorCategory` must have a corresponding Prometheus counter in
  `MetricsManager`, e.g. `request_errors_total{category="network"}`.
- **REQ-6.2** Existing `responses_received_total` metric must be preserved unchanged.
- **REQ-6.3** History recording failures must increment a `history_record_errors_total` counter.

### REQ-7: No Regression

- **REQ-7.1** All existing tests must continue to pass.
- **REQ-7.2** All existing public interfaces of `RequestService`, `HTTPClient`, and
  `RequestWorker` must remain callable with the same arguments (return types may evolve).
- **REQ-7.3** The `ExecutionResult` model must remain backward-compatible (new fields are
  additive, existing fields must not be removed).

---

## Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-1 | `ExecutionError` and `ErrorCategory` exist in a shared module importable by all layers. |
| AC-2 | `HTTPClient` raises `ExecutionError` (not raw `requests` exceptions) for all failure modes. |
| AC-3 | `RequestService.execute()` never raises; it always returns an `ExecutionResult`. |
| AC-4 | `RequestWorker.error` signal carries enough data for the UI to show a categorized message. |
| AC-5 | UI shows actionable, category-specific messages — no raw Python exception strings. |
| AC-6 | Each error category has a Prometheus metric counter that increments on error. |
| AC-7 | History recording failures increment `history_record_errors_total`. |
| AC-8 | All existing tests pass with no modifications to test inputs. |

---

## Out of Scope

- Changes to the HTTP request model (`RequestData`, `ResponseData`) beyond additive fields.
- UI redesign beyond error message copy.
- Adding new request execution features.
- Retry logic or automatic error recovery.
