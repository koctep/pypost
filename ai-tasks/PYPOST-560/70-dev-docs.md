# PYPOST-560: Dev Docs

## Updated

- `doc/dev/testing.md` — documented the regression test `test_mcp_client_service_list_tools_over_live_streamable_http` under the MCP server integration test section.
- `pypost/core/mcp_client_service.py` — updated docstrings to clarify anyio-based execution and clean teardown using `ClientSession` as an async context manager.

## Unchanged

- `doc/dev/mcp_integration.md` — already describes SSE endpoints and setup; the underlying fix is transparent to users.
