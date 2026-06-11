# PYPOST-555: UI preview of MCP tool contract

## Goals

Operators configure MCP tools in PyPost but cannot see what local AI agents receive from
`list_tools`. Without a preview, mismatches between authored metadata, template placeholders,
and hidden-variable policy are discovered only when an agent mis-invokes a tool or leaks
secrets into the contract.

## Programming Language

Python 3.11+ (PyPost project standard).

## User Stories

- As a **PyPost operator**, I want to preview the agent-visible tool name and description
  while editing a request, so I can confirm agents see the intended contract without
  connecting an MCP client.
- As a **PyPost operator**, I want to preview the `inputSchema` JSON agents receive, so I
  can verify parameter types, descriptions, and required fields match my templates and
  `mcp_params` annotations.
- As a **PyPost operator**, I want to see which environment or hidden variables are excluded
  from the agent contract, so I understand the secrets policy before enabling MCP on an
  environment.

## Definition of Done

- [x] Request editor MCP tab shows read-only preview of `list_tools` metadata for the
  current request when **MCP Tool** is enabled.
- [x] Preview includes normalized tool name, description, and formatted `inputSchema`.
- [x] Preview lists variables excluded by hidden-key / env-only policy with clear labels.
- [x] Preview updates when request fields, MCP metadata, or active environment hidden keys
  change.
- [x] Preview logic reuses the same schema pipeline as `MCPServerImpl` (no drift).
- [x] Unit tests cover preview content and policy exclusions.
- [x] Developer documentation updated.

## Task Description

### Problem

PYPOST-553 added MCP metadata authoring and PYPOST-554 added secrets policy for
`list_tools`, but the UI still only shows editable fields. Operators must use an external
MCP client to discover the effective tool contract.

### Scope

**In scope**

- Read-only agent contract preview in the request editor MCP tab.
- Shared preview builder aligned with `MCPServerImpl.list_tools`.
- Hidden-variable policy summary in the preview.
- Tests and developer docs.

**Out of scope**

- Global MCP tools overview across collections (PYPOST-556).
- Structured `call_tool` response preview (PYPOST-557).
- Auto-populating `mcp_params` from template scan (deferred in PYPOST-553).

### Non-functional requirements

- Preview must not expose hidden variable **values** — names and policy reasons only.
- No network calls; preview is computed locally from request + active hidden keys.
- Keep UI change minimal — one panel on the existing MCP tab.

## Q&A

| Question | Answer |
| --- | --- |
| What if MCP Tool is unchecked? | Preview shows a short message that the request is not exposed. |
| What if no environment is selected? | Hidden-key exclusions use an empty set; env-only exclusions still apply from templates. |
| Does preview match a running server? | Yes — same functions as `MCPServerImpl._generate_schema` and `_tool_description`. |
