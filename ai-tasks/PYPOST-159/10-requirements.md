# PYPOST-159: Document Mount + direct ASGI efficiency for SSE

## Goals

Close technical debt from PYPOST-21 by documenting why legacy MCP HTTP+SSE routing uses Starlette
`Mount` and direct ASGI callables, and that this design is at least as efficient as
`request_response` wrappers on `Route`.

## User Stories

- As a **maintainer**, I want clear developer documentation on MCP SSE routing efficiency, so
  future refactors do not assume `Mount` is a performance shortcut to remove.
- As a **reviewer**, I want the performance rationale recorded next to the routing code, so
  PYPOST-21 follow-ups can be closed without re-investigating Starlette internals.

## Definition of Done

- `doc/dev/mcp_integration.md` explains outer `Mount`, inner direct ASGI on `Route`, and the
  intentional `request_response` wrapper on GET `/` (`handle_sse_get`).
- Module-level docstring in `mcp_legacy_sse.py` references the same rationale.
- PYPOST-21 performance concern item is addressed (documented, not a code change).
- Existing MCP tests pass.

## Task Description

Follow-up from `ai-tasks/PYPOST-21/40-tech-debt.md`: performance was listed as a concern for
Mount + direct ASGI. Investigation shows no issue — the pattern is efficient. This task records
that conclusion for maintainers.

## Q&A

- **Q:** Does this require refactoring SSE to pure ASGI on GET?
  - **A:** No — `handle_sse_get` needs a `Response` after stream teardown; one thin wrapper is
    acceptable for long-lived connections.
- **Q:** Are new tests required?
  - **A:** PYPOST-161 already asserts direct ASGI registration; this task is documentation.
