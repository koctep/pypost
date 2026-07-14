# PYPOST-680: Dev Docs (Step 7)

## Updates

| Document | Change |
| --- | --- |
| [doc/mcp_integration.md](../../doc/mcp_integration.md) | User-facing — JSON envelope + `json.loads` (Step 3) |
| [doc/dev/mcp_integration.md](../../doc/dev/mcp_integration.md) | Agent parsing subsection (PYPOST-680) |
| [cursor-verification-checklist.md](../PYPOST-552/cursor-verification-checklist.md) | Envelope field checks after `call_tool` |
| [config/test/README.md](../../config/test/README.md) | Cursor envelope parsing note |

## Developer notes

- Envelope schema and error semantics: `doc/dev/mcp_integration.md` (PYPOST-557).
- Automated envelope round-trip: `tests/test_mcp_server_integration.py`.
- Doc consistency: `tests/test_mcp_user_docs.py` (PYPOST-680).

## Cross-references

- Closes PYPOST-557 tech-debt item "Agents must parse JSON TextContent".
- Parent epic context: PYPOST-557 structured MCP tool results.
