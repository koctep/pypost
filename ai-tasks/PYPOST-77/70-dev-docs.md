# PYPOST-77: Dev Docs

## Updated Files

| File | Change |
| --- | --- |
| `doc/dev/mcp_secrets_policy.md` | Added `extract_mcp_request_variables` API section documenting module-level regex pattern. |

## Key Documentation Points

- **`import re`** and **`_MCP_REQUEST_VAR_PATTERN`** live at module top in
  `mcp_secrets_policy.py` — not inside method bodies.
- **`extract_mcp_request_variables`** scans url, body, headers, and params for
  `{{ mcp.request.VAR }}` placeholders using the compiled pattern.
- **`MCPServerImpl`** delegates to `McpSecretsPolicy`; no local regex imports.

## Verification

Docs align with `pypost/core/mcp_secrets_policy.py`.
