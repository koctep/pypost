# PYPOST-141: MCP call logging and inspection in UI

## Goals

Operators debugging agent integrations need visibility into inbound MCP traffic (`list_tools`,
`call_tool`) without reading application logs or attaching an external MCP inspector.

## User Stories

- As a **PyPost user**, I want to see recent MCP server operations in the UI, so I can confirm
  my agent is calling the expected tools.
- As a **PyPost user**, I want call outcomes (success/error, HTTP status, duration) visible
  without exposing secret argument values, so I can troubleshoot safely.

## Definition of Done

- [x] Top bar offers **MCP Activity** dialog listing recent `list_tools` and `call_tool` events.
- [x] Activity is recorded automatically while the MCP server handles requests.
- [x] Logged fields exclude argument values and environment secrets (counts and outcomes only).
- [x] Button shows session activity count; dialog live-refreshes while open.
- [x] Automated tests cover activity log, server recording, and presenter wiring.
- [x] Developer docs updated.

## Scope

**In scope:** In-memory ring buffer, UI dialog, wiring via `MCPServerManager` / `EnvPresenter`.

**Out of scope:** Persistence across restarts, full request/response body inspection, metrics
dashboard changes.

## Q&A

| Question | Answer |
| --- | --- |
| Where in UI? | Top bar next to MCP Tools (EnvPresenter). |
| Requires MCP ON? | Entries appear only when the server receives MCP calls. |
| Parent epic? | PYPOST-16 follow-up debt item. |

## Worklog

role: execution, step: 1, step_name: Requirements, tokens_used: 3200
