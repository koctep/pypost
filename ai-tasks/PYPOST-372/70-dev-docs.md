# PYPOST-372: Dev Docs

## Updated Files

None. `doc/dev/mcp_integration.md` was already updated in PYPOST-366 to describe:

- Regex-only `McpSecretsPolicy.extract_mcp_request_variables` for `{{ mcp.request.* }}`
- Separate Jinja2 AST path in `extract_environment_variable_names` for env placeholders

## Verification

Dev docs remain accurate relative to `pypost/core/mcp_secrets_policy.py`. No further edits
required for this duplicate follow-up closure.

## Key Documentation Points (unchanged)

- MCP request variables: regex in `extract_mcp_request_variables`.
- Environment variables: Jinja2 AST in `extract_environment_variable_names`.
- `MCPServerImpl` delegates schema generation to policy + contract helpers.
