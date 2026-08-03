# PYPOST-1039: Developer Documentation

## Scope

PYPOST-1039 adds developer guidance for the optional protected live Jira MCP
smoke. It documents the existing test, Make target, and dispatch-only workflow;
it does not add a user-facing Jira setup path or reveal protected configuration.

## Documentation updates

| File | Update |
| --- | --- |
| `doc/dev/jira_mcp_live_smoke.md` | New maintainer reference covering the opt-in gate, HTTPS-only configuration contract, read-only operation allowlist, protected dispatch, secrecy, outcomes, and offline verification boundary. |
| `doc/dev/mcp_integration.md` | Added a concise Jira MCP live-smoke integration section linking to the focused reference. |
| `doc/dev/testing.md` | Documents the dedicated target, default-safe skip, enabled-invalid failure, and separation from normal test/PR paths. |
| `doc/dev/README.md` | Adds discoverability for the PYPOST-1039 reference from the MCP index. |

## Validation

- [x] Names the explicit opt-in and protected configuration labels without
  giving values or inline secret-assignment commands.
- [x] Documents the HTTPS-only base URL contract and rejects URL credentials.
- [x] Distinguishes an absent opt-in intentional skip from a failed enabled
  configuration.
- [x] Limits live calls to current-user lookup, bounded JQL search, returned
  issue retrieval, and board listing; documents excluded write actions.
- [x] Identifies `workflow_dispatch` on `master` and GitHub Environment
  `jira-live-smoke` as the only protected CI route; normal push/PR jobs stay
  offline and secret-free.
- [x] States value-free reporting and the ban on secrets/Jira-derived data in
  source, docs, logs, command lines, test output, worklogs, artifacts, and job
  summaries.
- [x] Independent final documentation review completed. The apparent duplicate
  current-user dispatch is false: the enabled smoke dispatches current-user
  once, validates that result locally, then dispatches search, issue retrieval,
  and board listing. The documented four-call contract is accurate.

## Approval basis

The sprint runner's autonomous workflow authorizes Step 8 to proceed without a
separate user gate. The user's standing instruction requires an independent
subagent review before the step is marked complete.

## Worklog

```text
role: execution
step: 8
step_name: Dev Docs
actions: documented the protected opt-in live-smoke contract, dispatch-only CI,
         read-only allowlist, skip/failure outcomes, secrecy rules, and offline
         verification boundaries; added MCP index and task artifact
time_spent: 12m
tokens_used: 4000

role: independent_docs_reviewer
step: 8
step_name: Dev Docs Review
verdict: PASS — the four-call documentation contract exactly matches the
         enabled smoke implementation
actions: verified one current-user dispatch plus local result validation,
         followed by bounded JQL search, returned-issue retrieval, and board
         listing; rechecked gate and outcome semantics, HTTPS/no-URL-
         credentials rule, read-only allowlist, protected dispatch, secrecy,
         index link, and focused-command safety
time_spent: 8m
tokens_used: 1800
```
