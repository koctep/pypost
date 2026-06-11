# PYPOST-554: Secrets and hidden variables policy for network MCP

## Goals

PyPost users expose HTTP requests as MCP tools for local AI agents. Those requests often
depend on environment variables marked **hidden** to protect credentials during editing and
screen sharing. When an agent connects over network MCP (`list_tools` / `call_tool`), secret
values must not appear in the tool contract the agent receives, while execution must still
resolve hidden variables to real values — matching GUI send behavior.

The business goal is **safety by default**: operators see more than agents; hidden secrets stay
out of agent-visible schemas and diagnostics, without breaking MCP tool execution.

## Programming Language

Python 3.11+ (PyPost project standard).

## User Stories

- As a **PyPost user**, I want hidden environment variables omitted from MCP tool schemas, so
  agents cannot read my credentials from `list_tools`.
- As a **PyPost user**, I want MCP tool execution to still use real hidden variable values, so
  authenticated requests work without duplicating secrets into agent arguments.
- As an **AI agent operator**, I want MCP tool inputs limited to explicit `mcp.request.*`
  parameters, so I only supply values the user intended agents to control.
- As an **operator**, I want MCP execution logs to avoid secret values and hidden key names, so
  diagnostics remain safe during support and screen sharing.

## Definition of Done

- [ ] A documented secrets policy defines agent-visible vs execution-only surfaces for network
  MCP.
- [ ] `list_tools` JSON Schema excludes environment placeholders and hidden keys; only
  `mcp.request.*` (and non-forbidden explicit MCP param metadata) appear.
- [ ] `call_tool` continues to merge real environment values, including hidden keys.
- [ ] `EnvPresenter` supplies active `hidden_keys` to the MCP server alongside env variables.
- [ ] Automated tests cover schema exclusion and execution-time real values.
- [ ] Developer documentation describes the policy and wiring.

## Task Description

### Problem

Network MCP exposes tool metadata to external clients. Without an explicit policy, hidden
environment variables could leak into agent-visible payloads (tool schemas, previews, or
logs), contradicting the product principle that secrets stay hidden from agents.

### Scope

**In scope**

- Policy module and enforcement in MCP `list_tools` schema generation.
- `hidden_keys` supplier wiring from active environment.
- Safe MCP execution logging (counts only).
- Tests and developer documentation.

**Out of scope**

- Masking HTTP response bodies returned to agents (PYPOST-557 / follow-ups).
- UI tool-contract preview (PYPOST-555).
- Changes to GUI hidden-variable display (existing PYPOST-437 behavior).

## Q&A

| Question | Answer |
| --- | --- |
| Should hidden vars block MCP execution? | No — same as GUI; hidden means masked in UI, not blocked at runtime. |
| Can agents ever see hidden key names? | No in `list_tools` schema; names may appear only in user-authored `mcp_description`. |
| Does this change RequestService? | No — policy lives in the MCP adapter layer. |
