# PYPOST-556: MCP tools overview and reliable server status in UI

## Goals

PyPost operators need confidence that the local MCP server is actually serving their exposed
requests before connecting an AI agent. Today the top bar can show "MCP: ON" before the server
listens, and there is no single place to see which requests are exposed as tools.

## User Stories

- As a **PyPost user**, I want one overview of all MCP-exposed requests across collections,
  so I know what my agent can call without opening each request.
- As a **PyPost user**, I want "MCP: ON" only when the server is listening on the configured
  host and port, so the status matches reality.
- As a **PyPost user**, I want a clear message when the MCP port is busy or unavailable,
  so I can fix the conflict instead of guessing from logs.

## Definition of Done

- [ ] Top bar offers a single MCP tools overview (name, collection, method, description).
- [ ] "MCP: ON" appears only after the server binds and listens; "MCP: OFF" when stopped.
- [ ] Bind failures (e.g. port in use) show an operator-visible error and keep status OFF.
- [ ] Automated tests cover startup signaling and overview data collection.
- [ ] Developer docs updated for status lifecycle and overview UI.

## Task Description

### Problem

Operators enabling MCP on an environment see a green "MCP: ON" label as soon as a background
thread starts, even if uvicorn fails to bind (port busy). There is no consolidated list of
exposed tools in the UI.

### Scope

**In scope**

- Top-bar MCP tools overview dialog.
- Accurate MCP ON/OFF status tied to actual listen readiness.
- User-visible error on startup failure (port busy, bind error).

**Out of scope**

- Per-request tool contract preview editor (PYPOST-555).
- Structured tool call results (PYPOST-557).
- Auto-retry or alternate port selection.

## Q&A

| Question | Answer |
| --- | --- |
| Where does overview live? | Top bar next to MCP status (EnvPresenter). |
| Does overview require MCP ON? | No — lists configured exposed requests regardless of server state. |
| Relation to PYPOST-154? | Port-busy UX delivered here; PYPOST-154 may cover broader error handling. |

## Worklog

role: execution, step: 1, step_name: Requirements, tokens_used: 4200
