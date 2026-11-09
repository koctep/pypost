# PYPOST-1541: Stabilize flaky MCP integration port bind

## Goals

CI and local developers must trust `make test` under parallel workers. The MCP
integration check that Jira MCP JSON-body placeholders reach the wire rendered
must not fail intermittently with “address already in use” when the same module
passes alone. Stabilizing this flake restores confidence in the Test Gate Recovery
sprint quality signal and reduces noise that masks real regressions.

## User Stories

- As a **CI engineer**, I want parallel `make test` runs to pass the Jira MCP
  JSON-body substitution integration test reliably, so that green builds mean the
  product behavior is sound rather than “lucky with ports.”
- As a **developer**, I want the same test to pass both in isolation and in the
  full parallel suite, so I do not waste time re-running flaky failures.
- As a **maintainer of related MCP process tests**, I want this class of ephemeral
  port race addressed in the shared test helpers so sibling flakes
  (PYPOST-1546, PYPOST-1508, PYPOST-1552) can reuse the same approach.

## Definition of Done

- `tests/test_mcp_server_integration.py::TestMCPServerIntegration::test_call_tool_substitutes_jira_mcp_json_body`
  does not fail with address-in-use under parallel `make test` for this race class.
- A deterministic automated repro proves the allocate-then-release gap and passes
  after the fix (Step 3 → Step 4).
- Shared test port helpers prefer holding a bound socket (or retrying bind) rather
  than releasing a probed port before the server listens.
- No new unbounded waits; pytest timeouts remain explicit.
- Developer testing docs mention the preferred allocation pattern.

## Task Description

**Problem:** Under parallel `make test`,
`test_call_tool_substitutes_jira_mcp_json_body` intermittently fails when uvicorn
cannot bind an ephemeral loopback port (`EADDRINUSE` / errno 98). The same test
passes when the module runs alone. Evidence from PYPOST-1388 Step 4 and base
commit `4dc78f4346f3caf5bdf7e85244f51af6cf43cf1a` attributes this to an ephemeral
TCP port allocate-then-release race among workers.

**In scope:** Stabilize the live MCP test harness / shared port allocation used by
this integration test so bind succeeds reliably under parallel load.

**Out of scope:** Fixing every related ticket’s distinct node id in this change
(they remain follow-ups of the same class); changing production MCP listen
semantics for end users; disabling parallel test workers.

**Programming language:** Python.

## Q&A

- **Q:** Why treat this as business-facing debt rather than “just a test flake”?
  **A:** Flaky parallel failures block sprint gates and hide real product bugs;
  the Jira MCP body-substitution path is a shipped integration contract.
- **Q:** Why prefer a shared helper over a one-off sleep in one test?
  **A:** The same allocate-then-release class appears in PYPOST-1546 / 1508 / 1552;
  one held-bind / retry helper reduces repeated fixes.
