# PYPOST-553: Tool metadata authoring — description and parameter annotations

## Goals

AI agents need a clear tool contract (name, description, typed parameters with required vs
optional) to invoke PyPost MCP tools correctly. Today `list_tools` uses the request display
name as the only description and exposes every `{{ mcp.request.* }}` placeholder as a required
string — which misleads agents and operators.

## Programming Language

Python 3.11+ (PyPost project standard).

## User Stories

- As a **PyPost user**, I want to write a dedicated MCP tool description separate from the
  request name, so agents understand what the tool does without renaming my request.
- As a **PyPost user**, I want to annotate each MCP parameter with type, description, and
  whether it is required, so agents pass correct arguments.
- As an **AI agent operator**, I want `list_tools` to return rich JSON Schema metadata, so
  clients can render helpful tool pickers and validate arguments.

## Definition of Done

- [x] `RequestData` stores `mcp_description` and per-parameter `mcp_params` metadata.
- [x] `MCPServerImpl.list_tools` uses `mcp_description` (fallback: request name).
- [x] `inputSchema` reflects param type, description, and required vs optional.
- [x] Template-discovered `{{ mcp.request.* }}` placeholders merge with explicit metadata.
- [x] Request editor exposes minimal MCP tab for description and parameter rows.
- [x] New fields participate in tab isolation / persisted-field comparison.
- [x] Unit tests cover description fallback and schema metadata.
- [x] Developer docs updated in `doc/dev/mcp_integration.md`.

## Task Description

### Problem

MCP tool registration reuses the HTTP request name as the agent-visible description and treats
all discovered placeholders as required strings. That does not match the PYPOST-549 vision of
a clear tool contract.

### Scope

**In scope**

- Model fields and persistence via existing collection JSON.
- Schema generation and `list_tools` description in `MCPServerImpl`.
- Minimal request-editor UI (MCP tab).
- Tests and developer documentation.

**Out of scope**

- Operator preview panel (PYPOST-555).
- Structured tool call results (PYPOST-557).
- Secrets masking policy for agent-visible metadata (PYPOST-554).

### Non-functional requirements

- Backward compatible: requests without new fields behave as before (name as description,
  string/required defaults for discovered params).
- Keep `RequestData` lean — metadata is small structured data only.

## Q&A

| Question | Answer |
| --- | --- |
| What if `mcp_description` is empty? | Fall back to `RequestData.name`. |
| What if a placeholder has no `mcp_params` entry? | Default: `type=string`, `required=True`. |
| Can users define params not in templates? | Yes — explicit `mcp_params` entries are included in schema. |
