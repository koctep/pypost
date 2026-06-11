# PYPOST-138: Code Cleanup

## Changes

| File | Action |
| --- | --- |
| `pypost/core/mcp_server_impl.py` | Removed shared `request_service`; added `_create_request_service` |
| `tests/test_mcp_server_impl.py` | Added `_stub_request_service` helper; updated mocks |
| `tests/test_mcp_server_integration.py` | Stub factory on `_LiveMCPServer` |
| `tests/test_mcp_test_collection_integration.py` | Same factory stub pattern |
| `tests/test_mcp_activity_log.py` | Factory stub for `call_tool` test |
| `tests/test_mcp_server_manager.py` | Removed obsolete `request_service` mocks |

## Lint / format

No new lint issues introduced. Existing module imports unchanged.

## Review

- No dead `request_service` attribute remains on `MCPServerImpl`.
- Test helper centralizes mock seam for future MCP tests.
