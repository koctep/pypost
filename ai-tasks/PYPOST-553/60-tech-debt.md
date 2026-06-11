# PYPOST-553: Technical Debt (Step 6)

**Verdict:** SAFE TO CLOSE

## Acceptance check

| Criterion | Status |
| --- | --- |
| Separate tool description | Met — `mcp_description` + fallback |
| Parameter type/description/required | Met — `McpToolParam` + schema builder |
| Backward compatible | Met — defaults match prior behavior |
| UI authoring | Met — MCP tab (minimal) |
| Tests | Met — `test_mcp_server_impl.py` |
| Dev docs | Met — `doc/dev/mcp_integration.md` |

## Follow-ups (non-blockers)

| ID | Priority | Item |
| --- | --- | --- |
| TD-1 | Low | Auto-populate MCP params table from template scan when URL/body changes |
| TD-2 | Low | Support `array` / `object` types in UI type combo (model already allows) |
| TD-3 | Low | Operator contract preview panel (PYPOST-555) |

No Jira issues created — items tracked in PYPOST-555 epic child or future polish.
