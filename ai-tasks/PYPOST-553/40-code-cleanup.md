# PYPOST-553: Code Cleanup (Step 4)

## Lint / format

- No new linter issues in touched modules (`models.py`, `mcp_server_impl.py`,
  `request_editor.py`, `request_sync.py`).
- Line length within 100 characters.

## Structure

- Schema helpers extracted as module-level functions in `mcp_server_impl.py` for direct
  unit testing without spinning up `MCPServerImpl`.
- `McpParamsTable` colocated with `RequestWidget` following existing `KeyValueTable` pattern.

## Tests

- Extended `tests/test_mcp_server_impl.py` (existing `pytestmark` timeout retained).

## Verdict

Ready for review — no cleanup blockers.
