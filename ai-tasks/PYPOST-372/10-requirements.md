# PYPOST-372: Close Dead Jinja2 Branch Follow-Up (Duplicate of PYPOST-366)

## Goals

Close the PYPOST-38 tech-debt follow-up that asked to simplify `_extract_mcp_variables` by
removing its dead Jinja2 AST branch. Confirm the work is already complete and record closure
without redundant code changes.

## User Stories

- As a **maintainer**, I want duplicate follow-up issues closed with clear verification notes so
  the backlog does not suggest unfinished work.
- As a **reviewer**, I want evidence that MCP request-variable extraction uses regex only and
  that `_extract_mcp_variables` no longer exists in `MCPServerImpl`.

## Definition of Done

- Verified: dead Jinja2 AST branch removed from MCP request-variable extraction (PYPOST-554).
- Verified: `_extract_mcp_variables` absent from `mcp_server_impl.py`.
- Verified: `McpSecretsPolicy.extract_mcp_request_variables` uses regex only.
- `ai-tasks/PYPOST-372/` artifacts document verification-only closure.
- PYPOST-38 tech-debt entry updated to reflect resolution.
- No redundant source or dev-doc edits (PYPOST-366 already synced `doc/dev/mcp_integration.md`).

## Task Description

**Origin:** PYPOST-38 tech-debt follow-up — same item as
[PYPOST-366](https://pypost.atlassian.net/browse/PYPOST-366). The dead Jinja2 loop in
`_extract_mcp_variables` was removed when logic moved to `McpSecretsPolicy` in PYPOST-554;
PYPOST-366 confirmed closure and updated dev docs. This issue tracks the duplicate PYPOST-38
link only.

**Scope:** Verification and documentation. No behavioral or code changes.

## Q&A

| Question | Answer |
| --- | --- |
| Is this duplicate of PYPOST-366? | Yes — same PYPOST-38 item; both link from `60-tech-debt.md`. |
| Any code to remove? | No — already done in PYPOST-554. |
| Update `doc/dev/`? | No — PYPOST-366 already updated `mcp_integration.md`. |
