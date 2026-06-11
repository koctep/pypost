# PYPOST-410: Template render guard duplicates work

## Programming language

Python — per `.cursor/lsr/do-python.md`.

## Goals

Eliminate redundant template rendering on the request execution path so each HTTP request
renders URL templates once, improving efficiency without changing successful request
behavior or existing error-handling contracts from PYPOST-400.

## Problem statement

`RequestService.execute()` performs an upfront URL template render for validation, then
`HTTPClient.send_request()` renders the same URL again (twice in the HTTP client for SSE
detection and kwargs preparation). MCP execution also re-renders after the guard. This
duplicates Jinja2 work on every send.

## User stories

- As a **user sending HTTP requests**, I want requests to complete with the same outcomes as
  today while avoiding unnecessary duplicate template work.
- As a **developer maintaining request execution**, I want a single render point per field
  on the hot path so behavior is easier to reason about.

## Functional requirements

- **FR-1:** Remove the dedicated template render guard from `RequestService.execute()`.
- **FR-2:** HTTP URL templates must be rendered exactly once per `send_request` call.
- **FR-3:** MCP URL/body rendering behavior unchanged (one render per field in `_execute_mcp`).
- **FR-4:** `RequestService.execute()` continues to return `ExecutionResult` for execution
  failures caught in its try/except (no regression to PYPOST-400 AC-3 for handled errors).

## Non-functional requirements

- **NFR-1:** No new metrics or log volume; observability paths in `TemplateService` unchanged.
- **NFR-2:** Existing tests pass; add tests proving guard removal and single HTTP URL render.

## Out of scope

- Changing `TemplateService.render_string` fallback semantics (PYPOST-460+).
- Worker `ExecutionError` handler test coverage ([PYPOST-412](https://pypost.atlassian.net/browse/PYPOST-412)).
- Deprecating `script_error` dual field ([PYPOST-409](https://pypost.atlassian.net/browse/PYPOST-409)).

## Definition of Done

| # | Criterion |
|---|-----------|
| AC-1 | Template render guard removed from `RequestService.execute()` |
| AC-2 | HTTP URL rendered once per request in `HTTPClient` |
| AC-3 | All existing `test_request_service` and `test_http_client` tests pass |
| AC-4 | New tests document single-render contract |

## Q&A

- **Q:** Should template failures still raise from `execute()`?  
  **A:** No — guard removal aligns with PYPOST-400: execution errors return `ExecutionResult`.
  `TemplateService` already falls back on render errors; strict template failure handling is
  out of scope.
