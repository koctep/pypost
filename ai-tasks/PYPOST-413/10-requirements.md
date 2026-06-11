# PYPOST-413: Type-safe request cancellation detection

## Programming language

Python — per `.cursor/lsr/do-python.md`.

## Goals

User-initiated request cancellation must be recognized reliably without substring heuristics
on exception text. False positives (e.g. a network error whose detail mentions "cancelled")
must not suppress error dialogs.

## Problem statement

`_on_request_error` treats `ExecutionError` as cancellation when `"cancelled"` or `"aborted"`
appears in `error.detail`. That string match is fragile and can misclassify real failures.

## User stories

- As a **user stopping a long request**, I want no error dialog when I cancel.
- As a **user hitting a real failure**, I want an actionable error even if the underlying
  message contains words like "cancelled".

## Functional requirements

- **FR-1:** Add `ErrorCategory.CANCELLED` for user-initiated stop.
- **FR-2:** Stop-flag paths in `RequestService` emit `ErrorCategory.CANCELLED`.
- **FR-3:** `_on_request_error` detects cancellation via `error.category == CANCELLED`
  for `ExecutionError` payloads (no detail substring checks).
- **FR-4:** Legacy `str` error payloads keep existing cancellation substring handling.
- **FR-5:** `RequestWorker` routes `ExecutionResult` with `CANCELLED` to the `error` signal
  so the UI handler runs without showing a synthetic error response.

## Non-functional requirements

- **NFR-1:** Cancellation must not increment `request_errors_total`.
- **NFR-2:** Existing tests updated; new tests cover category-based detection.

## Out of scope

- Changing HTTP streaming partial-body behavior on stop.
- MCP cancellation semantics.
- Pre-existing unrelated test failures (PYPOST-414).

## Definition of Done

| # | Criterion |
|---|-----------|
| AC-1 | `ErrorCategory.CANCELLED` exists |
| AC-2 | Stop-flag raises use `CANCELLED`, not `NETWORK` |
| AC-3 | `_on_request_error` uses category check for `ExecutionError` |
| AC-4 | Cancellation excluded from `request_errors_total` |
| AC-5 | Tests pass for presenter, worker, and retry cancellation |
