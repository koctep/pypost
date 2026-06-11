# PYPOST-158: Legacy SSE close and 405 test coverage

## Goals

Close technical debt from PYPOST-21 by adding automated regression tests for legacy MCP HTTP+SSE
transport behavior that was previously verified manually or assumed covered by integration tests.

## User Stories

- As a **maintainer**, I want automated tests that legacy SSE GET streams return a proper HTTP
  response after the connection closes, so SDK disconnect handling does not regress to
  `TypeError` on shutdown.
- As a **maintainer**, I want automated tests that wrong HTTP methods on legacy `/sse` and
  `/messages` paths return 405 via Starlette routing, so method guards stay declarative.
- As an **operator**, I expect legacy MCP HTTP behavior to remain unchanged; tests document and
  lock current semantics only.

## Definition of Done

- `tests/test_mcp_legacy_sse.py` covers SSE stream closure (empty 200 `Response` after
  transport teardown) without requiring a live long-running SSE handshake in CI.
- Tests assert 405 for non-GET on the SSE stream path and non-POST on `/messages` (inner app
  and mounted `/sse` prefix).
- Existing MCP legacy SSE and routing tests pass.
- Developer testing docs list the new coverage.

## Task Description

Follow-up from `ai-tasks/PYPOST-21/40-tech-debt.md`: no automated tests existed for correct SSE
shutdown and 405 on non-POST `/messages`. PYPOST-155/157 refactored routing; this task adds the
missing test layer.

## Q&A

- **Q:** Does this change MCP client behavior?
  - **A:** No — tests only; production code unchanged unless a regression is found.
