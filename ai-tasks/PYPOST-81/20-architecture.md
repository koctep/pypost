# PYPOST-81: Architecture

## Scope

Single-file style fix in `pypost/core/mcp_server_impl.py`. No API, class, or dependency
changes.

## Target layout

```text
# stdlib imports
# blank line
# third-party imports (mcp, starlette)
# blank line
# pypost imports
# blank line
logger = logging.getLogger(__name__)
# blank line
# module functions and MCPServerImpl
```

## Implementation note

The misplaced logger was introduced in PYPOST-45 (`e38b7d0`). A later refactor
(`4f7164ba`, PYPOST-10 area) moved `logger` below all imports while reorganising MCP
imports. PYPOST-81 formally verifies and closes TD-2.

## Tests

No new tests. Existing `tests/test_mcp_server_impl.py` exercises `MCPServerImpl` and
confirms the module imports cleanly.
