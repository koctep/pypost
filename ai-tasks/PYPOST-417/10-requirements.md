# PYPOST-417 — Requirements: RequestWorker One-Shot Lifecycle

> Analyst: 2026-06-11
> Jira: PYPOST-417
> Parent: PYPOST-401 (TD-3)
> Type: Debt
> Priority: Low

---

## Goals

`RequestWorker` uses a cooperative stop flag (`threading.Event`) that is set by `stop()` and
never cleared. The UI already creates a fresh worker per send, but the permanent stop
semantics are undocumented. A future maintainer could silently break behaviour by reusing a
stopped worker (requests would cancel immediately).

This task makes the one-shot lifecycle explicit and verifiable so the constraint is discoverable
without reading implementation details.

---

## User Stories

- As a **maintainer**, I want `RequestWorker` lifecycle documented so I know not to reuse an
  instance after cancellation.
- As a **reviewer**, I want a test that locks in the permanent stop flag so regressions are caught.

---

## Definition of Done

| # | Criterion |
|---|-----------|
| AC-1 | `RequestWorker` class or `stop()` docstring states the instance is not reusable after `stop()`. |
| AC-2 | Developer docs describe one worker per send and no restart after stop. |
| AC-3 | A test proves the stop flag remains set on a second `run()` after `stop()`. |
| AC-4 | All existing tests pass. |

---

## Task Description

Follow-up from PYPOST-401 TD-3. `threading.Event` is cleared only in `__init__` and set only
by `stop()`. Reusing a stopped worker would appear to "work" (thread starts) but every poll of
`stop_flag` returns true, cancelling the request silently.

**Approach:** Document the one-shot contract; enforce behaviour with a focused unit test. No
change to presenter wiring (already allocates new workers).

---

## Q&A

| Question | Answer |
|----------|--------|
| Should we reset `_stop_event` in `run()`? | No — PYPOST-401 explicitly removed that reset to fix races. |
| Should we block `start()` on stopped workers? | Out of scope; documentation + test suffice for this debt item. |
