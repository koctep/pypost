# PYPOST-953: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: runtime unit test on `MCPServerImpl.list_tools()` in canonical
`tests/test_mcp_server_impl.py` fails if agent UI tool names or any `ui_*`
prefixed tools appear in the product catalog. No production changes required.

## Shortcuts Taken

- **Guard test green on first run** — production already excluded UI tools; Step 4
  had no impl fix (expected for hardening-only debt).
- **Sibling overlap with PYPOST-952** — `test_agent_ui_actions_mcp.py` retains
  similar assert; not deduplicated in this Lowest ticket.
- **Prefix heuristic `ui_*`** — broad guard; acceptable because product MCP should
  never use that prefix for HTTP request tools.

## Code Quality Issues

- None introduced. Single test method + import from sidecar constants module.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Product catalog ∩ `AGENT_UI_MCP_TOOL_NAMES` = ∅ | Covered (`test_mcp_server_impl.py`) |
| Any `ui_*` name on product catalog | Covered |
| Live HTTP list_tools integration | Out of scope — unit guard sufficient |
| Deduped single shared assert helper | Optional — not required for close |

**No timeout-marker blockers.**

## Performance Concerns

None. One `list_tools()` call with a single registered tool.

## Follow-up Tasks

### Blockers

None.

### Non-blockers

1. **Deduplicate catalog exclusion assert with PYPOST-952 test module**
   - Priority: Lowest
   - Extract tiny shared helper or keep one test only if duplication becomes noisy
   - Files: `tests/test_mcp_server_impl.py`, `tests/test_agent_ui_actions_mcp.py`
   - Jira: [PYPOST-994](https://pypost.atlassian.net/browse/PYPOST-994)

## Deviations from Architecture

None.

## Blocker Verdict

**SAFE TO CLOSE** — acceptance satisfied; optional dedup is non-blocking.
