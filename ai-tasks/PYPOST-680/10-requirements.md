# PYPOST-680: Agents must parse JSON TextContent in MCP tool responses

## Goals

PYPOST-557 introduced a structured JSON envelope for every successful PyPost MCP `call_tool`
response (`status`, `error`, `body`, optional `logs`). Developer docs describe the schema, but
operators and AI agents still lack user-facing guidance that the MCP `TextContent.text` field
is JSON — not the raw upstream HTTP body. Agents that treat tool output as plain text misread
outcomes and cannot distinguish PyPost execution failures from upstream HTTP errors.

The business goal is **documented, parseable tool results for agents**: anyone connecting an
MCP client to PyPost knows to `json.loads` the envelope before reading `status`, `error`,
`body`, and `logs`.

## Programming Language

Python 3.11+ (PyPost project standard). Primary deliverables are documentation, checklist
updates, and automated doc consistency tests; no MCP server code changes.

## User Stories

- As a **Cursor operator**, I want user-facing MCP docs to explain the JSON envelope, so my
  agent instructions tell it to parse `TextContent` before using `body`.
- As an **AI agent author**, I want a clear envelope schema and parsing example, so I can
  reliably read HTTP status and execution errors from PyPost tools.
- As a **contributor**, I want automated tests that user-facing docs mention envelope parsing,
  so guidance does not drift after PYPOST-557.

## Definition of Done

- [x] User-facing `doc/mcp_integration.md` documents JSON envelope parsing for `call_tool`
  responses (`status`, `error`, `body`, optional `logs`).
- [x] Developer `doc/dev/mcp_integration.md` includes explicit `json.loads` agent guidance.
- [x] Cursor verification checklist and `config/test/README.md` updated for envelope parsing.
- [x] Automated tests verify envelope guidance in user docs (`tests/test_mcp_user_docs.py`).
- [x] Existing integration tests continue to pass (already parse JSON envelope).

## Task Description

### Problem

Follow-up from PYPOST-557 tech debt: envelope schema lives in dev docs only. Agents expecting
raw HTTP body text break when PyPost returns JSON. Operators configuring Cursor lack setup
guidance on parsing tool results.

### Scope

**In scope**

- Update `doc/mcp_integration.md` (user-facing agent/operator guidance).
- Update `doc/dev/mcp_integration.md` (`json.loads` parsing section).
- Update Cursor checklist and test README.
- Automated doc consistency tests.

**Out of scope**

- Changing `MCPServerImpl` envelope format (PYPOST-557).
- UI preview of structured results (PYPOST-664).
- Response-body secret redaction (PYPOST-703 / existing sanitizer).

### Functional requirements

1. User docs explain that `call_tool` returns JSON in `TextContent.text`.
2. Docs list envelope keys: `status`, `error`, `body`, optional `logs`, optional error fields.
3. Docs include a parsing example using `json.loads`.
4. Docs note breaking change for agents that expected raw upstream body.
5. Checklist verifies agent can parse envelope fields after `call_tool`.

### Non-functional requirements

- **Accuracy** — matches PYPOST-557 server behavior and integration tests.
- **Maintainability** — pytest guards key phrases in user docs.
- **Clarity** — operators can copy parsing guidance into agent system prompts.

### Constraints and assumptions

- MCP SDK returns tool results as `TextContent`; JSON is serialized to the `text` field.
- Protocol errors (unknown tool, internal exception) are not JSON envelopes — unchanged.
- Automated envelope round-trip already covered by `test_mcp_server_integration.py`.

## Q&A

| Question | Answer |
| --- | --- |
| Is this a code change? | No — documentation and tests only. |
| Where was schema documented before? | `doc/dev/mcp_integration.md` (PYPOST-557 Step 7). |
| Do Cursor agents auto-parse JSON? | Not guaranteed — operators should document parsing in prompts. |
