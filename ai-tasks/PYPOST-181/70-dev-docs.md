# PYPOST-181: Dev Docs (Step 7)

## Updates

| Document | Change |
| --- | --- |
| [doc/dev/testing.md](../../doc/dev/testing.md) | New "MCP test collection integration" subsection |
| [tests/helpers/mcp_test_collection.py](../../tests/helpers/mcp_test_collection.py) | Added `mcp_exposed_requests()` |

## Developer notes

- Groundwork tests (`test_mcp_test_collection.py`) validate committed JSON without a server.
- Integration tests (`test_mcp_test_collection_integration.py`) start ephemeral uvicorn with
  collection-derived tools and round-trip via MCP SDK.
- Upstream HTTP is mocked; protocol and tool registration are live.

## Cross-references

- Parent debt: `ai-tasks/PYPOST-25/40-tech-debt.md`
- Groundwork: `ai-tasks/PYPOST-180/`
- Protocol harness: `tests/test_mcp_server_integration.py`
- Manual setup: `config/test/README.md`
