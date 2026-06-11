# PYPOST-411: MCPClientService heuristic error classification is fragile

## Goals

PYPOST-400 introduced structured `ExecutionError` categories for MCP transport failures.
The initial implementation classified errors by inspecting exception type names and message
substrings, which is brittle — a library version bump could rename types and silently
misclassify errors. This task replaces heuristics with explicit exception handling so
error categories remain stable and predictable.

## Programming Language

Python (pypost application codebase).

## User Stories

- As a maintainer, I want MCP connection and timeout failures classified by concrete
  exception types so library upgrades do not silently change error categories.
- As a developer debugging MCP requests, I want `ErrorCategory.NETWORK` and
  `ErrorCategory.TIMEOUT` to map to the same httpx exception families used by the MCP
  SSE client under the hood.

## Definition of Done

- `MCPClientService.run()` uses explicit `except` clauses for httpx transport exceptions
  (mirroring `HTTPClient` pattern with `requests`).
- No string or `__name__` heuristics remain for error classification.
- `asyncio.TimeoutError` from the outer `wait_for` still maps to `ErrorCategory.TIMEOUT`.
- Unit tests cover httpx `ConnectError`, `ReadTimeout`, and generic failures.
- Developer documentation reflects the typed exception mapping.

## Task Description

Follow-up to PYPOST-400 tech debt item TD-3. Scope is limited to
`pypost/core/mcp_client_service.py` and its unit tests. No changes to `RequestService`,
metrics labels, or UI messaging.

### Out of scope

- Template render guard / double-render (PYPOST-410).
- Worker `ExecutionError` handler test coverage (PYPOST-412).
- Cancellation category (PYPOST-413).

## Q&A

- **Why httpx?** The MCP SSE client (`mcp.client.sse`) uses httpx for transport; connection
  and timeout failures surface as httpx exception types.
- **What about non-httpx errors?** ValueError from invalid operations and other unexpected
  exceptions fall through to `ErrorCategory.UNKNOWN`.
