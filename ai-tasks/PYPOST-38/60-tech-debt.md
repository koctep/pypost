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

- `_extract_mcp_variables`: unused Jinja2 AST branch (see above).
  — [PYPOST-366](https://pypost.atlassian.net/browse/PYPOST-366)

## Missing Tests

- No unit tests for `MCPServerImpl` or MCP routing.
  — [PYPOST-367](https://pypost.atlassian.net/browse/PYPOST-367)
- No integration tests that start the MCP server and verify tool invocation.
  — [PYPOST-368](https://pypost.atlassian.net/browse/PYPOST-368)
- `do-testing.md` describes manual/AI-driven verification, not automated pytest.
  — [PYPOST-369](https://pypost.atlassian.net/browse/PYPOST-369)

## Performance Concerns

None identified.

## Follow-up Tasks

- Consider adding automated integration tests for MCP tools and metrics (out of scope).
  — [PYPOST-370](https://pypost.atlassian.net/browse/PYPOST-370)
- If `do-testing.md` rules are extended, ensure `doc/dev/testing.md` stays in sync.
  — [PYPOST-371](https://pypost.atlassian.net/browse/PYPOST-371)
- Optionally simplify `_extract_mcp_variables` by removing the dead Jinja2 branch.
  — [PYPOST-372](https://pypost.atlassian.net/browse/PYPOST-372)
