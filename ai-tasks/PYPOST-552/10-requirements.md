# PYPOST-552: E2E verify MCP tools with Cursor (list_tools + call_tool)

## Goals

After PYPOST-551 migrated PyPost's MCP server to Streamable HTTP, users and operators need
confidence that **local AI agents (Cursor)** can still connect, discover tools, and invoke
them — and that setup instructions match the new transport. Outdated SSE-only documentation
blocks adoption and causes failed connections even when the server and tools are correctly
configured.

The business goal is **verified, documented MCP agent connectivity**: anyone following
PyPost's user-facing setup can connect Cursor (or equivalent) using the current transport,
list exposed tools, and successfully call at least one tool.

## Programming Language

Python 3.11+ (PyPost project standard). Primary deliverables are documentation, test config
examples, and automated doc/consistency tests; no new MCP server implementation.

## User Stories

- As a **PyPost user**, I want MCP setup docs to show the correct Streamable HTTP URL, so I
  can connect Cursor without guessing deprecated SSE paths.
- As a **Cursor operator**, I want a clear checklist to verify `list_tools` and `call_tool`
  against my local PyPost instance, so I know the integration works before relying on it.
- As a **contributor**, I want automated tests that user-facing docs and test collections
  reference `/mcp`, so SSE URL drift is caught in CI.
- As a **PyPost user** using the MCP test collection, I want the in-app **List Tools**
  request to use Streamable HTTP, so in-app verification matches Cursor behavior.

## Definition of Done

- [x] User-facing `doc/mcp_integration.md` describes Streamable HTTP at `/mcp` (not SSE as
  primary) including Cursor configuration steps.
- [x] `config/test/README.md` and `examples/collections/mcp.json` updated for `/mcp` where
  appropriate (List Tools / agent connection).
- [x] Manual **Cursor verification checklist** documented under `ai-tasks/PYPOST-552/`.
- [x] Automated tests verify doc/collection URL consistency (`tests/test_mcp_user_docs.py`).
- [x] Existing integration tests (`tests/test_mcp_server_integration.py`) continue to pass
  (automated `list_tools` + `call_tool` over Streamable HTTP).
- [ ] Manual Cursor sign-off recorded on checklist (operator task — not automatable in CI).

## Task Description

### Problem

PYPOST-551 moved the MCP network transport to Streamable HTTP. User-facing docs and test
collection examples still pointed agents at `/sse`. Users configuring Cursor with SSE type
and `/sse` URL fail to connect despite a working server. Acceptance requires end-to-end
verification that a local agent can list and call tools, plus updated setup guidance.

### Scope

**In scope**

- Update `doc/mcp_integration.md` (user-facing MCP setup).
- Update `config/test/README.md` and `examples/collections/mcp.json` (List Tools URL).
- Cursor manual verification checklist.
- Automated doc/consistency tests.
- Developer doc touch-ups where user-facing gaps are referenced.

**Out of scope**

- MCP server transport implementation (PYPOST-551).
- Environment variable injection (PYPOST-550).
- Rewriting legacy SSE probe GET requests (still valid for HTTPClient SSE-probe mode).
- Live Cursor automation in CI.

### Functional requirements

1. Primary connection URL in user docs: `http://127.0.0.1:1080/mcp` (configurable host/port
   noted).
2. Cursor section: Streamable HTTP type, not SSE-only.
3. Checklist covers connect → list_tools → call_tool with triage table.
4. Test collection **List Tools** request uses `/mcp`.

### Non-functional requirements

- **Accuracy** — docs match PYPOST-551 server behavior.
- **Maintainability** — automated tests guard primary URLs in user docs and test config.
- **Clarity** — legacy `/sse/` documented as optional transition path, not primary.

### Constraints and assumptions

- Automated protocol E2E already covered by `test_mcp_server_integration.py`.
- Manual Cursor verification requires a human operator with PyPost + Cursor running locally.
- SSE probe tools in test collection intentionally keep `/sse` URLs (HTTPClient heuristic).

## Q&A

| Question | Answer |
| --- | --- |
| Why not automate Cursor in CI? | Cursor is a desktop agent; CI validates protocol via SDK integration tests. |
| Keep SSE probe URLs in collection? | Yes — they test legacy SSE stream readability, separate from agent transport. |
| Is PYPOST-578 still needed? | Overlaps this task; user doc update is done here. |

## Worklog

role: execution, step: 1, step_name: Requirements, tokens_used: 4200
