# PYPOST-701: MCP inbound history asymmetry

## Goals

Close architecture audit finding **R-P3-003** (S-HIST-004) from PYPOST-684 by formally
accepting that inbound MCP tool invocations do not record request history, and documenting
this asymmetry relative to GUI sends.

**Business intent:** Give developers and operators a clear, authoritative statement that the
difference is intentional — not a bug — so future work does not chase false parity. Revisit
only if agents require audit-trail parity with GUI executions.

## User Stories

- As a **developer**, I want dev docs to state whether inbound MCP records history, so I do
  not assume GUI and MCP paths behave identically.
- As a **reviewer**, I want the architecture audit recommendation marked resolved with a
  pointer to the product-choice documentation.

## Definition of Done

- `doc/dev/mcp_integration.md` documents inbound MCP history omission as an accepted product
  choice (with rationale and revisit criteria).
- `doc/dev/request_execution.md` clarifies which entry points record history and which do
  not.
- `doc/dev/architecture_audit.md` marks R-P3-003 as **Done** (PYPOST-701).
- No application code or behavior changes.
- `make check` passes.

## Out of Scope

- Wiring `history_manager` into `MCPServerImpl._create_request_service()`.
- Changes to MCP activity log (session-scoped inbound telemetry remains separate from
  persistent request history).

## Source

- Jira [PYPOST-701](https://pypost.atlassian.net/browse/PYPOST-701)
- Audit R-P3-003 / S-HIST-004 in `ai-tasks/PYPOST-684/30-audit-report.md`

## Q&A

| Question | Answer |
| --- | --- |
| Is this a bug? | No — accepted product choice; GUI uses `HistoryManager`, inbound MCP omits it by design. |
| What audit trail exists for MCP? | Session MCP activity log (`McpActivityDialog`); not persistent request history. |
