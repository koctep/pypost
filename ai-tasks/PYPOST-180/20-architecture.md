# Architecture: PYPOST-180 — MCP test collection test groundwork

## Research

| Area | Finding |
| --- | --- |
| Test collection | `examples/collections/mcp.json` — three requests, two MCP-exposed SSE probes |
| Test environment | `config/test/environments.json` — single "MCP Test" entry with `enable_mcp: true` |
| Setup docs | `config/test/README.md` — copy instructions for local manual testing |
| Doc URL tests | `tests/test_mcp_user_docs.py` (PYPOST-552) — asserts `/mcp` in docs and List Tools URL |
| Live MCP tests | `tests/test_mcp_server_integration.py` (PYPOST-368/551) — synthetic tools, not collection |
| Tool naming | `collect_mcp_tool_overview` + `normalize_mcp_tool_name` in `mcp_tools_overview.py` |

## Implementation Plan

1. **Helper module** (`tests/helpers/mcp_test_collection.py`)
   - Repo-root-relative paths to collection and environment files.
   - Frozen constants for expected ids, names, and MCP tool names.
   - `load_mcp_test_collection()` and `load_mcp_test_environments()` using Pydantic models.

2. **Validation tests** (`tests/test_mcp_test_collection.py`)
   - File existence.
   - Model parse success.
   - MCP tool overview matches expected exposed tools.
   - List Tools request: `method=MCP`, `expose_as_mcp=false`, Streamable HTTP URL.
   - SSE probe URLs and exposure flags.
   - Agent contract previews for exposed requests.
   - Environment `enable_mcp` flag.

3. **Documentation** (`doc/dev/testing.md`)
   - New subsection with scope table and focused pytest command.

## Architecture

```
examples/collections/mcp.json ──┐
config/test/environments.json ──┼──► tests/helpers/mcp_test_collection.py
                                │         │
                                │         ▼
                                └──► tests/test_mcp_test_collection.py
                                           │
                                           ▼
                                 collect_mcp_tool_overview / contract preview
```

PYPOST-181 will import the same helper to start a live server with collection-derived tools.
