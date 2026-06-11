# Architecture: PYPOST-181 — MCP test collection live integration

## Research

| Area | Finding |
| --- | --- |
| Collection loader | `tests/helpers/mcp_test_collection.py` (PYPOST-180) |
| Live MCP harness | `tests/test_mcp_server_integration.py` — uvicorn + MCP SDK client |
| Exposed tools | `sse_probe_metrics`, `sse_probe_main` from `examples/collections/mcp.json` |
| Non-exposed | **List Tools** — `method=MCP`, `expose_as_mcp=false` |
| Execution | `MCPServerImpl.register_tools` + mocked `RequestService.execute` |

## Implementation Plan

1. **Helper extension** (`tests/helpers/mcp_test_collection.py`)
   - `mcp_exposed_requests()` — filter `expose_as_mcp` requests from loaded collection.

2. **Integration tests** (`tests/test_mcp_test_collection_integration.py`)
   - Ephemeral-port `_LiveMCPServer` (same pattern as PYPOST-368).
   - `test_list_tools_over_live_streamable_http` — collection tools discoverable.
   - `test_call_tool_for_each_exposed_collection_request` — JSON envelope per tool.
   - `test_call_tool_executes_matching_collection_request` — correct `RequestData` forwarded.
   - `pytestmark = pytest.mark.timeout(120)` per integration tier.

3. **Documentation** (`doc/dev/testing.md`)
   - New subsection with scope table and focused pytest command.

## Architecture

```
examples/collections/mcp.json
        │
        ▼
tests/helpers/mcp_test_collection.py ──► mcp_exposed_requests()
        │
        ▼
tests/test_mcp_test_collection_integration.py
        │
        ├──► MCPServerImpl.register_tools(collection requests)
        ├──► uvicorn (ephemeral port)
        └──► MCP SDK ClientSession (list_tools / call_tool)
                    │
                    ▼
              RequestService.execute (mocked)
```
