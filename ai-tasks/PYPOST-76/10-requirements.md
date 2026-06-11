# PYPOST-76: Remove Dead Jinja2 AST Branch in MCP Variable Extraction

## Goals

Close tech-debt item TD-4 from PYPOST-44: the MCP tool schema pipeline must not contain
misleading dead code that parses Jinja2 AST without contributing to variable discovery.
Developers reading the extraction logic should see a single, clear mechanism for discovering
`{{ mcp.request.* }}` placeholders.

## User Stories

- As a **maintainer**, I want MCP request-variable extraction to use one obvious code path so
  I am not misled by a no-op Jinja2 loop when debugging tool schemas.
- As an **MCP integrator**, I want `list_tools` input schemas to remain unchanged — only
  internal clarity improves.

## Definition of Done

- No dead Jinja2 AST parsing loop remains in MCP request-variable extraction.
- `{{ mcp.request.VAR }}` placeholders are discovered via the active regex-based path only.
- Existing MCP secrets-policy and server tests pass.
- Developer docs reflect the current function names and pipeline.

## Task Description

**Origin:** PYPOST-44 TD-4 — `_extract_mcp_variables` in `MCPServerImpl` contained a
try/except block that parsed Jinja2 AST but only executed `pass` in the loop body; regex below
performed the real work.

**Scope:** Remove or relocate dead code; keep agent-visible tool contracts and execution
behavior unchanged.

## Q&A

| Question | Answer |
| --- | --- |
| Which module owns extraction now? | `McpSecretsPolicy.extract_mcp_request_variables` in `mcp_secrets_policy.py` (PYPOST-554). |
| Is Jinja2 still used anywhere for MCP vars? | Yes, separately in `extract_environment_variable_names` for env-only placeholders — that path is live and must remain. |
