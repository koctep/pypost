# PYPOST-138: MCP thread safety for HTTP execution

## Goals

PyPost exposes saved HTTP requests as MCP tools. The MCP server runs on a background thread
with its own asyncio loop while the GUI runs on the Qt main thread. Concurrent MCP tool
calls and overlapping GUI sends must not corrupt shared HTTP state or produce undefined
behavior.

The business goal is **reliable MCP execution**: agents and users can invoke tools safely
even when multiple calls happen at once or while the user sends requests from the app.

## Programming Language

Python 3.10+ (PyPost project standard).

## User Stories

- As a **PyPost user**, I want MCP tool calls to remain stable when several agents or tabs
  invoke tools concurrently, so my integration does not fail unpredictably.
- As an **AI agent operator**, I want each MCP tool invocation to behave independently, so
  one slow or failing call does not break others.
- As a **PyPost maintainer**, I want MCP execution to follow the same one-shot request
  pattern as the GUI worker path, so lifecycle rules stay consistent.

## Definition of Done

- [x] MCP `call_tool` execution does not share a single `HTTPClient` / `requests.Session`
  across concurrent or sequential invocations from the MCP server threadpool.
- [x] Each MCP tool call uses an isolated execution stack suitable for background-thread
  use (no reliance on a long-lived shared session on `MCPServerImpl`).
- [x] Automated tests verify fresh `RequestService` / session per MCP execution.
- [x] Existing MCP integration tests continue to pass.

## Task Description

### Problem

`MCPServerImpl` previously held one `RequestService` (and thus one `HTTPClient` with one
`requests.Session`) for the lifetime of the server. MCP handlers offload synchronous work
to Starlette's threadpool; `requests.Session` is not documented as thread-safe. Concurrent
MCP calls could race on the same session.

### Scope

- MCP inbound path (`MCPServerImpl._execute_request_sync` / `call_tool`).
- Out of scope: making `HTTPClient` globally thread-safe; GUI worker already creates a new
  `RequestService` per send.

## Q&A

- **Q:** Instantiate per request or add locks to `HTTPClient`?
  **A:** Per-call `RequestService` — matches `RequestWorker`, minimal surface, no lock
  contention on hot path.
