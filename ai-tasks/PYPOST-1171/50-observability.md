# PYPOST-1171: Observability

- `legacy_mcp_request_migrated` INFO log on convert-on-open (`mcp_client_migration`).
- `legacy_mcp_body_not_json` DEBUG when body is non-JSON (falls through to list_tools).
- No new metrics — outbound MCP metrics remain on `McpClientPresenter` paths.
