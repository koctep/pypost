# PYPOST-140: Implement argument parsing for tools

## Goals

Close the PYPOST-16 technical-debt item **Implement argument parsing for tools**: MCP
`call_tool` must accept agent-supplied arguments and substitute them into request templates at
execution time.

## Programming Language

Python 3.11+ (PyPost project standard).

## User Stories

- As an **AI agent operator**, I want MCP tools to declare typed input parameters, so clients
  can validate arguments before calling a tool.
- As an **AI agent operator**, I want to pass values at `call_tool` time that substitute into
  request templates, so the same tool can target different resources per invocation.
- As a **PyPost user**, I want to annotate MCP parameters (type, description, required) in
  the request editor, so agents receive a clear tool contract.

## Definition of Done

- [x] `list_tools` exposes JSON Schema for agent-supplied parameters derived from request
  templates and/or explicit metadata.
- [x] `call_tool` merges agent arguments into the Jinja2 context under `mcp.request.*`.
- [x] Placeholders such as `{{ mcp.request.id }}` resolve at execution time from agent input.
- [x] Environment variables and MCP arguments occupy separate namespaces (GUI parity).
- [x] Automated tests cover schema generation, argument merge, and end-to-end execution.
- [x] Developer documentation describes the argument pipeline.

## Task Description

**Origin:** `ai-tasks/PYPOST-16/40-tech-debt.md` — follow-up debt item from initial MCP
integration (tools executed without dynamic agent input).

**Scope for this ticket:** Verify the shipped pipeline satisfies acceptance criteria; close
with traceability. Implementation was delivered in PYPOST-550 and PYPOST-553.

### In Scope

- Requirements verification against current codebase
- MCP unit test run for argument parsing paths
- ai-tasks documentation and Jira closure

### Out of Scope

- New placeholder syntax
- Restart-on-tool-update notification (PYPOST-136)
- Structured tool call response format (PYPOST-557)

## Q&A

| Question | Answer |
| --- | --- |
| Was new code required? | No — pipeline shipped in PYPOST-550/553; this ticket closes the original debt item. |
| What if a placeholder has no metadata? | Defaults to `type: string`, `required: true` (PYPOST-553). |
| Can agents pass args not in templates? | Yes — explicit `mcp_params` entries appear in schema even without template placeholders. |
