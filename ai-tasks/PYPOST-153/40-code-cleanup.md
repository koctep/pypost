# PYPOST-153: Code Cleanup

## Lint / Format

- No new linter issues in changed files.
- Line length within 100 characters.

## Refactoring

- Extracted duplicate bind-error strings from `format_mcp_bind_error` into `server_bind.py`.
- Metrics startup logging aligned with MCP: "starting" vs "listening" split.

## Notes

- `MetricsManager` now subclasses `QObject`; created only after `QApplication` in `main.py`.
