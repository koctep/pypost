# PYPOST-63: Duplicate template rendering in request_service

## Programming language

Python — per `.cursor/lsr/do-python.md`.

## Goals

Eliminate duplicate Jinja2 template rendering on the HTTP/MCP request path when recording
history, without changing outbound request behavior or hidden-value masking semantics.

## Problem statement

After PYPOST-410, URL templates render once in `HTTPClient.send_request()`. History recording
still calls `SensitiveDataMaskingPolicy.build_history_safe_fields()`, which re-renders URL,
headers, and body for every successful request — duplicating work on the common path (no hidden
keys).

## User stories

- As a **user sending requests with templates**, I want the same resolved URL/headers/body in
  history as were sent on the wire, without paying for a second render when nothing is hidden.
- As a **developer**, I want transport-layer resolved fields reused by history so the execution
  path is easier to reason about.

## Functional requirements

- **FR-1:** `HTTPClient.send_request()` returns resolved URL, headers, and body alongside
  `ResponseData`.
- **FR-2:** `RequestService.execute()` passes resolved fields to history when available.
- **FR-3:** When `hidden_keys` is non-empty, history still masks via template re-render with
  placeholder variables (unchanged behavior).
- **FR-4:** MCP requests return resolved fields from `_execute_mcp()` for history reuse.

## Non-functional requirements

- **NFR-1:** No new metrics or log lines; `TemplateService` observability unchanged.
- **NFR-2:** Existing tests pass; new tests document the reuse contract.

## Out of scope

- Caching template renders across requests.
- Changing `TemplateService.render_string` fallback semantics.
- Params in history (not stored today).

## Definition of Done

| # | Criterion |
|---|-----------|
| AC-1 | HTTP transport returns resolved request fields |
| AC-2 | History reuses resolved fields when no hidden keys |
| AC-3 | Hidden-key masking behavior unchanged |
| AC-4 | All affected tests pass |
