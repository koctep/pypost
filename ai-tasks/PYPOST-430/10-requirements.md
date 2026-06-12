# PYPOST-430: Replace SSE stream URL substring heuristic in HTTPClient

## Goals

HTTP requests that return Server-Sent Events must be handled without blocking the UI or
misclassifying unrelated GET responses. The prior URL substring check (`"/sse" in url`) could
false-positive on arbitrary paths and failed to recognize SSE streams served from other paths.

The business goal is **reliable streaming response handling**: users probing MCP or other SSE
endpoints get correct stream parsing based on what the server actually returns, not URL shape.

## Programming Language

Python 3.11+ (PyPost project standard).

## User Stories

- As a **PyPost user** sending a GET to an SSE endpoint, I want the client to parse the
  event stream when the server responds with `text/event-stream`, regardless of URL path.
- As a **PyPost user** with a URL that happens to contain `/sse` in a non-streaming API path,
  I want normal JSON/text handling so I am not surprised by SSE probe behavior.
- As a **maintainer**, I want detection logic aligned with HTTP semantics (Content-Type) so
  new transport paths do not require URL heuristics.

## Definition of Done

- [x] `HTTPClient` routes GET responses to SSE handling when `Content-Type` is
  `text/event-stream` (media type, case-insensitive, parameters ignored).
- [x] URL substring `"/sse"` is no longer used to classify requests or responses.
- [x] Unit tests cover content-type detection, false-positive guard, and explicit Accept
  header timeout tuning.
- [x] Existing SSE probe integration behavior preserved for saved `/sse` tools that return
  SSE content types.
- [x] Developer documentation updated for the new detection rule.

## Task Description

### Problem

`HTTPClient.send_request()` treated GET requests as SSE when the rendered URL contained `/sse`.
That heuristic predates Streamable HTTP and can misclassify unrelated paths. Response headers
already expose the correct signal.

### Scope

**In scope**

- `pypost/core/http_client.py` detection and pre-request timeout tuning.
- `tests/test_http_client_sse_probe.py`.
- `doc/dev/request_execution.md` (SSE detection note).

**Out of scope**

- MCP Streamable HTTP client transport (`MCPClientService`).
- Removing legacy `/sse` server mounts (PYPOST-551 TD-1).
- Broad HTTPClient content-type refactors (PYPOST-203).

### Functional requirements

1. SSE handling triggers on GET + `Content-Type: text/event-stream` after response headers
   arrive.
2. No URL-path-based SSE classification.
3. When the user sets `Accept: text/event-stream`, apply SSE probe connect/read timeouts
   before dispatch (explicit intent).

### Non-functional requirements

- **Correctness** — no regression for legacy `/sse` probe tools that return SSE bodies.
- **Testability** — unit tests mock responses; no live server required.

### Constraints and assumptions

- Saved MCP test collection SSE probe requests still use `/sse` URLs; servers return SSE
  content types, so behavior remains correct post-change.

## Q&A

| Question | Answer |
| --- | --- |
| Why not auto-set Accept on all GETs? | Would change server negotiation for unrelated APIs. |
| Pre-request timeout without Accept? | Default request timeout applies until SSE content-type is known. |
