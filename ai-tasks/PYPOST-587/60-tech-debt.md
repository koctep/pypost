# PYPOST-587: Technical Debt Analysis

## Resolution

Follow-up from PYPOST-136. When `expose_as_mcp` is toggled off mid-session, a signature change
triggers server restart. Connected MCP agents may retain cached tool names until they reconnect
and re-list tools. This is acceptable for a local development MCP server; clients are expected
to handle reconnect after restart.

## Blocker Review

**Verdict: SAFE TO CLOSE** — acceptable trade-off; no code changes required.

## Follow-up Tasks

None.
