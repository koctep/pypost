# PYPOST-1034: Developer Documentation

## Scope

PYPOST-1034 adds regression coverage, not a new MCP feature or Jira tool. The
developer documentation records the existing request-template contract that the
tests protect: an MCP tool argument is available at `mcp.request.<argument>` and
is rendered in the request query or JSON body before outbound HTTP transport.

## Documentation Updates

| File | Update |
| --- | --- |
| `doc/dev/mcp_integration.md` | Added the Jira query/body template examples, the fixture-backed loopback testing boundary, expected wire assertions, and the exact focused test command. |
| `doc/dev/testing.md` | Clarified that most MCP integration tests mock execution while the PYPOST-1034 pair uses the real template/request/HTTP path and a local HTTP boundary. |
| `doc/dev/README.md` | Added a discoverable MCP index entry for this regression coverage. |

The user-facing Jira/MCP documentation is unchanged: the public tool and
argument contracts already existed, and this task adds automated proof only.

## Validation

- [x] The documented Jira tool names and argument names match
  `examples/collections/jira_mcp.json` and the integration test node ids.
- [x] The focused command runs the query and JSON-body MCP regressions through
  the standard `make test` target.
- [x] The documentation describes loopback-only coverage and does not imply a
  live Jira dependency, credentials, or Jira-project mutation.
- [x] `git diff --check` reports no whitespace errors.
- [x] Independent documentation review passed: fixture contract, test node ids,
  focused command, index anchor, and test-only scope were all verified.

## Approval Basis

The sprint runner's autonomous workflow authorizes this step to continue
without a separate user gate. The user's standing instruction requires a
subagent for review; an independent documentation reviewer returned PASS with
no findings before the roadmap step was completed.

## Worklog

```text
role: execution
step: 8
step_name: Dev Docs
actions: documented the MCP query/body substitution contract, fixture-backed
         integration boundary, and focused validation command; updated docs index
time_spent: 10m
tokens_used: 3000

role: independent_docs_reviewer
step: 8
step_name: Dev Docs Review
verdict: PASS — no findings
actions: verified fixture templates and arguments, test node ids and command,
         index anchor, scope, assertions, and diff whitespace
time_spent: 7m
tokens_used: 1700
```
