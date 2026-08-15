# CI-safe Jira MCP Collection E2E (PYPOST-1053)

## Overview

`make test-mcp-collection-e2e` verifies a representative, read-only Jira MCP
collection workflow without Jira credentials, tenant data, or external network
access. It executes four requests from the committed
`examples/collections/jira_mcp.json` collection:

1. `jira_get_current_user`
2. `jira_search_issues_jql`
3. `jira_get_issue`, using the key returned by the search
4. `jira_list_boards`

The module is part of the normal fast suite because it has no `slow` marker.
Use this pack for routine local development and pull-request CI. It complements,
but does not replace, the protected live check documented in
[Optional Live Jira MCP Smoke](jira_mcp_live_smoke.md).

## Architecture

`tests/test_mcp_collection_e2e.py` loads only the four committed requests and
calls them through a live Streamable HTTP MCP server. The server uses the real
`RequestService`, `HTTPClient`, and `requests` socket path. Test variables point
the collection at `tests/helpers/mcp_collection_http.py`, which starts a
`ThreadingHTTPServer` on `127.0.0.1` and an ephemeral port.

The loopback fixture accepts only the expected methods, paths, query values,
and bounded search payload. It returns deterministic Jira-shaped JSON, records
only safe canonical request metadata for assertions, and suppresses default
HTTP-server logging. It neither records headers nor retains rejected payloads.
Its context manager always shuts down the server and joins its daemon thread
with a bounded wait.

```text
Committed Jira collection -> MCP server -> RequestService -> HTTPClient
    -> requests socket -> 127.0.0.1 loopback Jira stand-in
```

This is deliberately different from agent UI e2e HTTP stubs, which patch
`send_request` and therefore do not exercise outbound socket dispatch.

## Usage

Run the focused pack from the repository root:

```bash
make test-mcp-collection-e2e
```

Run it through the default CI-safe suite with:

```bash
make test
```

The focused target selects `tests/test_mcp_collection_e2e.py` directly. The
module has `pytest.mark.timeout(30)` and needs no custom pytest marker, command
arguments, environment variables, or Jira account.

## Configuration and safety boundary

The test provides all collection variables in process with fixed offline
values. `jira_base_url` is the loopback URL, `jira_credentials` is a dummy
value, and `jira_project_key` is `OFFLINE`. The base URL and credentials are
hidden from MCP diagnostics. Do not change this test to read real `JIRA_*`
environment values or to bind a non-loopback address.

The stand-in supports exactly four read-only routes. It is not a Jira emulator,
does not validate real authentication or authorization, and must not acquire
write-route coverage. For an explicitly authorized service integration check,
use `make test-jira-mcp-live` as documented in
[Optional Live Jira MCP Smoke](jira_mcp_live_smoke.md); that target is separate
from routine CI and requires protected environment configuration.

## Troubleshooting

- **Focused target fails before a tool call:** Run `make install` to ensure the
  development and OpenTelemetry extras are installed, then rerun the target.
- **Route, query, or body assertion fails:** Restore the corresponding committed
  request id, template, or fixed tool input. Keep the four calls and their
  search-to-issue-key handoff intact.
- **An unexpected loopback request is rejected:** The fixture intentionally
  accepts only its four canonical read routes. Extend its catalog only with
  approved collection-e2e scope and matching assertions.
- **A live Jira expectation fails in this pack:** This pack does not contact
  Jira. Use the protected `make test-jira-mcp-live` path only when authorized.
- **Loopback server shutdown fails:** Treat it as a test-fixture lifecycle
  defect. Preserve the context-manager cleanup and bounded thread join rather
  than adding an unbounded wait.
