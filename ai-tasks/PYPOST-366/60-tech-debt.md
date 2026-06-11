# PYPOST-366: Technical Debt Analysis

## Shortcuts Taken

None. Verification-only task; dead code was removed in PYPOST-554.

## Code Quality Issues

None introduced. PYPOST-38 dead Jinja2 branch item is **resolved**.

## Missing Tests

Coverage is adequate:

- `tests/test_mcp_secrets_policy.py::test_extract_mcp_request_variables_from_request_fields`
- `tests/test_mcp_secrets_policy.py::test_extract_environment_variable_names_excludes_mcp_namespace`

No new tests required — behavior unchanged.

## Performance Concerns

None. Removing dead AST parsing slightly reduces wasted work (already done in PYPOST-554).

## Follow-up Tasks

None from this task. Related items from PYPOST-38 remain as separate issues:

| Item | Jira |
| --- | --- |
| No unit tests for MCPServerImpl or MCP routing | [PYPOST-367](https://pypost.atlassian.net/browse/PYPOST-367) |
| No integration tests for MCP tool invocation | [PYPOST-368](https://pypost.atlassian.net/browse/PYPOST-368) |
| do-testing.md vs automated pytest | [PYPOST-369](https://pypost.atlassian.net/browse/PYPOST-369) |

## Blocker Review

**SAFE TO CLOSE** — no blockers.
