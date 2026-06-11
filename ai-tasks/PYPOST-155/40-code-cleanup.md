# PYPOST-155: Code Cleanup

## Changes

- Removed dead `_send_response` helper from `MessagesEndpoint` in both MCP and metrics servers.
- Removed duplicate GET method guard inside `SSEEndpoint` (handled by `Route(..., methods=["GET"])`).
- No new imports; `Route` was already imported in both modules.

## Lint

- Targeted MCP tests pass; no new flake8 issues in edited files.
