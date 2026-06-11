# PYPOST-366: Dev Docs

## Updated Files

| File | Change |
| --- | --- |
| `doc/dev/mcp_integration.md` | Schema generation overview now states regex-only discovery via `McpSecretsPolicy.extract_mcp_request_variables` instead of "regex + optional TemplateService parse". |

## Key Documentation Points

- **MCP request variables** (`{{ mcp.request.VAR }}`) are discovered by regex in
  `McpSecretsPolicy.extract_mcp_request_variables` — not Jinja2 AST.
- **Environment variables** (top-level `{{ base_url }}` etc.) use Jinja2 AST in
  `McpSecretsPolicy.extract_environment_variable_names` for exclusion from agent schema.
- `MCPServerImpl` delegates schema generation to policy + `mcp_tool_contract` helpers.

## Verification

Docs align with `pypost/core/mcp_secrets_policy.py` and `pypost/core/mcp_tool_contract.py`.
