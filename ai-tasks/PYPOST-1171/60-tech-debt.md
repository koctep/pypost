# PYPOST-1171: Technical Debt Analysis

No AC-breaking debt. Legacy `method: "MCP"` rows remain in collection JSON until
MCP-TM-7 save writes `mcp_clients[]`.

## Follow-up Tasks

1. **NON-BLOCKER — Collections persist (MCP-TM-7)**
   - Save converted legacy items as `mcp_clients[]`; optional removal of legacy
     `requests[]` row on save.
   - Jira: [PYPOST-1172](https://pypost.atlassian.net/browse/PYPOST-1172)

2. **NON-BLOCKER — tabs_presenter factory headroom**
   - Already ticketed extract before further factory growth.
   - Jira: [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184)
