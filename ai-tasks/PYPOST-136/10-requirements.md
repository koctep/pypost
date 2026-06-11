# PYPOST-136: Restart MCP server when exposed tools change

## Goals

When a PyPost user adds, removes, renames, or toggles MCP exposure on requests, connected AI
agents must see an up-to-date `list_tools` result without manual server restarts.

## User Stories

- As a **PyPost user** with MCP enabled, I want the MCP server to pick up tool list changes
  automatically when I save a request or edit collections, so agents do not call stale or
  missing tools.
- As a **PyPost user**, I want the MCP Tools count in the top bar to stay accurate after
  collection edits, so I can verify what is exposed.

## Definition of Done

- [ ] Saving a request or changing collections while MCP is running refreshes the server tool
  list (restart when the exposed set changes).
- [ ] No restart when the exposed tool set is unchanged.
- [ ] MCP Tools button count updates on collection changes regardless of server state.
- [ ] Automated tests cover refresh wiring and manager restart behavior.
- [ ] Developer docs describe the tool-refresh flow.

## Task Description

### Problem

`MCPServerManager.update_tools()` existed but was never called from the UI. Agents connected
to a running MCP server could see an outdated tool catalog after the user edited requests.

### Scope

**In scope**

- Detect exposed-tool set changes and restart MCP server when running.
- Wire refresh from request save and collection change signals.
- Logging for tool-set changes.

**Out of scope**

- Push notifications to MCP clients (protocol does not guarantee server-initiated refresh).
- Hot-reloading tools without restart (would require deeper SDK changes).

## Q&A

| Question | Answer |
| --- | --- |
| Restart vs notify? | Restart is pragmatic; MCP clients re-fetch on reconnect/session. |
| When MCP disabled? | Update button count only; no server action. |

## Worklog

role: execution, step: 1, step_name: Requirements, tokens_used: 2800
