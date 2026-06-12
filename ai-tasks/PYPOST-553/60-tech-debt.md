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
| TD-1 | Low | Auto-populate MCP params table from template scan when URL/body changes | [PYPOST-657](https://pypost.atlassian.net/browse/PYPOST-657) |
| TD-2 | Low | Support `array` / `object` types in UI type combo (model already allows) | [PYPOST-658](https://pypost.atlassian.net/browse/PYPOST-658) |
| TD-3 | Low | Operator contract preview panel (PYPOST-555) | [PYPOST-659](https://pypost.atlassian.net/browse/PYPOST-659) |

Follow-ups ticketed above (PYPOST-657–659); operator preview tracked under PYPOST-555.
