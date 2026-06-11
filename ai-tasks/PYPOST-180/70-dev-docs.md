# PYPOST-180: Dev Docs (Step 7)

## Updates

| Document | Change |
| --- | --- |
| [doc/dev/testing.md](../../doc/dev/testing.md) | New "MCP test collection groundwork" subsection |
| [tests/helpers/mcp_test_collection.py](../../tests/helpers/mcp_test_collection.py) | Shared loaders for PYPOST-181 reuse |

## Developer notes

- Groundwork validates `examples/collections/mcp.json` and `config/test/environments.json`.
- Live MCP round-trip with collection tools: follow-up PYPOST-181.
- Doc URL checks remain in `tests/test_mcp_user_docs.py` (PYPOST-552).

## Cross-references

- Parent debt: `ai-tasks/PYPOST-25/40-tech-debt.md`
- Manual setup: `config/test/README.md`
- Protocol integration: `tests/test_mcp_server_integration.py`
