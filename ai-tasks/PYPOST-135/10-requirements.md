# PYPOST-135: MCP tools accept agent arguments

## Goals

Close the PYPOST-16 technical-debt item **No Arguments Support**: MCP tools must accept
runtime arguments from AI agents so requests can be parameterized dynamically (for example,
passing a resource ID in the URL or body) instead of executing only with static configuration
and environment variables.

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
- [x] Full test suite passes.

## Task Description

**Origin:** `ai-tasks/PYPOST-16/40-tech-debt.md` — tools executed exactly as configured with
no dynamic agent input.

**Scope for this ticket:** Verify whether the feature is already implemented (via
`{{ mcp.request.* }}` placeholders, `McpToolParam`, and related MCP tasks). Complete any
gaps or close with evidence if already done.

### In Scope

- Requirements verification against current codebase
- Regression test run
- Traceability to implementing tasks (PYPOST-550, PYPOST-553, PYPOST-554)

### Out of Scope

- New placeholder syntax
- Restart-on-tool-update notification (PYPOST-136)
- Structured tool call response format (PYPOST-557)

## Q&A

| Question | Answer |
| --- | --- |
| Is PYPOST-140 still needed? | No — PYPOST-140 ("Implement argument parsing for tools") is superseded by the shipped pipeline; close or mark duplicate when triaging. |
| What if a placeholder has no metadata? | Defaults to `type: string`, `required: true` (PYPOST-553). |
| Can agents pass args not in templates? | Yes — explicit `mcp_params` entries appear in schema even without template placeholders. |
