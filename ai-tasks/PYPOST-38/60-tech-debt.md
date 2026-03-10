# PYPOST-38: Technical Debt Analysis

## Code Review Summary

**Reviewed:** `mcp_server_impl.py`, `do-testing.md`, `doc/dev/testing.md`

### mcp_server_impl.py

- **Routing:** SSE and messages correctly nested under `Mount("/sse")`. Client POSTs to
  `/sse/messages`. Fix applied in STEP 3.
- **Lint:** E501 compliance done in STEP 4. `flake8 pypost/core/mcp_server_impl.py` passes.
- **Dead code:** `_extract_mcp_variables` has a try/except block (lines 126–141) that parses
  Jinja2 AST but does nothing with `meta_vars` (pass). The regex fallback does the work.
  Low priority — could simplify by removing the unused Jinja2 branch.

### Documentation Sync

- **do-testing.md vs doc/dev/testing.md:** Content aligned. Both reference metrics and MCP URLs.

## Shortcuts Taken

None. Routing fix and E501 cleanup completed.

## Code Quality Issues

- `_extract_mcp_variables`: Unused Jinja2 AST branch (see above).

## Missing Tests

- No unit tests for `MCPServerImpl` or MCP routing.
- No integration tests that start the MCP server and verify tool invocation.
- `do-testing.md` describes manual/AI-driven verification, not automated pytest.

## Performance Concerns

None identified.

## Follow-up Tasks

- Consider adding automated integration tests for MCP tools and metrics (out of scope).
- If `do-testing.md` rules are extended, ensure `doc/dev/testing.md` stays in sync.
- Optionally simplify `_extract_mcp_variables` by removing the dead Jinja2 branch.
