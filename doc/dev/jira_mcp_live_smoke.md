# Optional Live Jira MCP Smoke (PYPOST-1039)

## Purpose

`make test-jira-mcp-live` is a **maintainer-only, opt-in** check of the
shipped Jira MCP example against an authorized Jira site. It complements the
offline fixture and loopback tests; routine development and pull-request
validation do not need Jira access.

The smoke is deliberately small and read-only. In one enabled run it calls,
in order:

1. current-user lookup;
2. JQL issue search, limited to one returned issue key;
3. retrieval of that in-memory issue; and
4. board listing.

It does not register or call any write operation. Create, update, delete,
transition, assign, comment, and worklog operations are excluded. It is safe
to rerun with an authorized read-only account.

## Local opt-in and outcomes

Run the dedicated target only when you are an authorized maintainer and the
protected process environment has been configured by an approved secret
management path:

```bash
make test-jira-mcp-live
```

The protected configuration names are:

| Name | Requirement |
| --- | --- |
| `PYPOST_LIVE_JIRA_SMOKE` | Explicit operator opt-in; it must be exactly `1`. |
| `JIRA_BASE_URL` | A non-placeholder, valid HTTPS Jira base URL. It must not contain credentials. |
| `JIRA_CREDENTIALS` | Protected Jira credentials. |
| `JIRA_PROJECT_KEY` | Protected project scope used for the bounded search. |

Do not place protected values in shell commands, command-line arguments,
repository files, or documentation. Provide them only through the protected
process environment.

The gate intentionally has two different outcomes:

| State | Result |
| --- | --- |
| `PYPOST_LIVE_JIRA_SMOKE` is unset or has a value other than `1` | Successful pytest skip: the live smoke is intentionally not enabled. Other Jira configuration is not read. |
| Opt-in is `1`, but a required value is missing, placeholder, malformed, non-HTTPS, or includes URL credentials | Failed enabled run with a generic configuration failure; it is never reported as a skip. |
| Opt-in and configuration are valid | The four read-only operations run sequentially and the test passes or fails. |

An enabled failure is a signal to investigate protected configuration or the
live integration. Do not reproduce its values in issue comments, worklogs, or
logs.

## Protected CI dispatch

The only CI route is the manual `workflow_dispatch` job on `master`:
`jira-mcp-live-smoke`. It uses GitHub Environment `jira-live-smoke` and passes
the required configuration only as protected environment variables.

Normal `push` and `pull_request` jobs neither invoke `test-jira-mcp-live` nor
receive Jira configuration. The protected job must not be repurposed for
untrusted pull-request code or `pull_request_target` execution.

Its job summary is deliberately value-free and may report only one of:
`passed`, `failed`, or `intentionally skipped`. It does not copy pytest output
or Jira data into the summary.

## Secrecy and test boundaries

Never commit, log, paste into docs, put on a command line, or include in test
output, worklogs, artifacts, or job summaries any credential, authorization
value, account identity, Jira URL, project/issue/board data, request payload,
or response body. The test keeps the search result only in memory long enough
to retrieve that issue.

During the protected call window, test logging is suppressed and failures use
fixed operation labels instead of upstream exception text. This reduces the
risk of accidental disclosure; it does not authorize printing sensitive data
elsewhere.

## Verification boundaries

The standard test suite remains offline. It contains deterministic coverage for
the opt-in gate, HTTPS validation, the four-tool read-only allowlist, current
user dispatch against a local stub, and the Makefile/workflow isolation
contract. Run the focused offline coverage with:

```bash
PYTEST_ARGS='tests/test_jira_mcp_live_smoke.py tests/test_example_fixtures.py -m "not live_jira"' make test
```

This focused command deliberately excludes the `live_jira`-marked operation.
Use the dedicated target only for the authorized live check above.

See also [MCP Integration](mcp_integration.md),
[MCP Secrets Policy](mcp_secrets_policy.md), and
[Testing via MCP and Prometheus](testing.md).
