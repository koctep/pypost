# PYPOST-412: Remove dead worker ExecutionError handler

## Programming language

Python — per `.cursor/lsr/do-python.md`.

## Goals

After PYPOST-400 and PYPOST-410, `RequestService.execute()` always returns `ExecutionResult`
for handled failures and never raises `ExecutionError` to callers. The dedicated
`except ExecutionError` branch in `RequestWorker.run()` is unreachable dead code that
confuses maintainers and is covered only by a mock-based test that does not reflect
production behavior.

## Problem statement

`RequestWorker` still catches `ExecutionError` from `execute()` and emits the `error`
signal. That path existed when the template render guard could raise before the
`ExecutionResult` contract was fully enforced. With guard removal (PYPOST-410) and
`execute()` catching all transport errors (PYPOST-400), the handler cannot run in
production.

## User stories

- As a **developer maintaining request execution**, I want worker error handling to match
  the `ExecutionResult` contract so I do not maintain unreachable branches.
- As a **user sending requests**, I want unchanged behavior: handled failures still surface
  via the response panel; only truly unexpected worker faults use the error dialog path.

## Functional requirements

- **FR-1:** Remove the `except ExecutionError` handler from `RequestWorker.run()`.
- **FR-2:** Keep the `except Exception` handler for unexpected faults (wrap as
  `ErrorCategory.UNKNOWN`).
- **FR-3:** Handled execution failures continue to flow through `finished` with synthetic
  error responses from `ExecutionResult` (no regression).
- **FR-4:** Tests must reflect production contracts (no mock that forces `execute()` to
  raise `ExecutionError` for handled failures).

## Non-functional requirements

- **NFR-1:** No new logging or metrics; observability unchanged.
- **NFR-2:** Existing worker tests for retry signals, alert injection, and hidden keys pass.

## Out of scope

- Changing `RequestService.execute()` error handling.
- UI changes to `_on_request_error` cancellation heuristics (PYPOST-413).
- Emitting `error` signal for `ExecutionResult.execution_error` (current UX uses `finished`).

## Definition of Done

| # | Criterion |
|---|-----------|
| AC-1 | `except ExecutionError` removed from `RequestWorker.run()` |
| AC-2 | Worker tests document `ExecutionResult` error path via `finished`, not `error` |
| AC-3 | All existing tests pass |
| AC-4 | Developer docs describe worker error signal scope |

## Q&A

- **Q:** Should we add a test that injects template failure to exercise the old branch?  
  **A:** No — the branch is removed. Test the live contract: `execute()` returns
  `ExecutionResult` with `execution_error`; worker emits `finished`.
