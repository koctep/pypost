# Jira MCP critical REST path freshness (PYPOST-1030 / PYPOST-1056)

## Overview

Offline gate that keeps critical REST path markers in
`examples/collections/jira_mcp.json` aligned with a checked-in expected
catalog (`examples/collections/jira_mcp_critical_rest_paths.json`). No live Jira credentials or network calls.

PYPOST-1056 adds an offline mutation reject contract (`test_jira_mcp_critical_rest_paths_rejects_url_drift`) to guarantee that any path drift raises an actionable `AssertionError` diagnostic pinpointing the affected request id, locked fragment, and observed URL.

## Architecture

- **Collection:** `examples/collections/jira_mcp.json` — curated MCP tools.
- **Catalog:** `examples/collections/jira_mcp_critical_rest_paths.json` —
  locked method / path fragments (and optional `mcp_param` / `url_excludes`)
  for the highest-risk drift surfaces.
- **Positive contract:** `tests/test_example_fixtures.py` —
  `test_jira_mcp_critical_rest_paths_match_locked_catalog` (verifies aligned collection matches catalog).
- **Mutation reject contract:** `tests/test_example_fixtures.py` —
  `test_jira_mcp_critical_rest_paths_rejects_url_drift` (verifies drift rejection and diagnostic completeness).
- **Comparator:** `tests/test_example_fixtures.py` —
  `assert_jira_mcp_critical_rest_paths_match_catalog(collection, catalog)`.
- **Makefile:** `make check-jira-mcp-path-freshness` (runs both positive and reject contracts).

```text
Atlassian REST docs  --(periodic human review)-->  critical_rest_paths.json
jira_mcp.json  ---------------------------------->  pytest compare (CI / make)
                                                             │
                                   ┌─────────────────────────┴─────────────────────────┐
                                   ▼                                                   ▼
                         Positive Contract                                   Mutation Reject Contract
                         (collection == catalog)                             (URL drift raises diagnostic)
```

## Locked critical paths

| Capability | Request id | Locked markers |
| ---------- | ---------- | -------------- |
| Enhanced JQL search | `jira-search-issues-jql` | `POST` `/rest/api/3/search/jql` |
| Sprint create | `jira-create-sprint` | `POST` `/rest/agile/1.0/sprint` (no `/sprint/`) |
| Sprint membership | `jira-add-issues-to-sprint` | `POST` `.../sprint/` + `/issue` |
| Parent / epic link | `jira-link-issue-parent` | `PUT` `.../issue/` + `parent_payload` |
| Assignee | `jira-assign-issue` | `PUT` `.../assignee` |

## Mutation diagnostic contract (PYPOST-1056)

To protect diagnostic quality against regressions, `test_jira_mcp_critical_rest_paths_rejects_url_drift` simulates a path fragment mismatch by cloning the `jira-search-issues-jql` request in memory and mutating `/rest/api/3/search/jql` to `/rest/api/3/search`.

The comparator `assert_jira_mcp_critical_rest_paths_match_catalog` raises `AssertionError`, and the test asserts that the diagnostic message explicitly contains:
1. **Request ID:** `jira-search-issues-jql` — identifies which MCP tool drifted.
2. **Locked Fragment:** `'/rest/api/3/search/jql'` — specifies the expected path fragment.
3. **Observed URL:** `{{jira_base_url}}/rest/api/3/search` — reveals the actual mismatched URL found in the collection.

### Diagnostic message example

```text
jira-search-issues-jql URL missing locked fragment '/rest/api/3/search/jql': {{jira_base_url}}/rest/api/3/search
```

This contract operates entirely in-memory using `Collection.model_copy(deep=True)` and checked-in JSON fixtures, ensuring deterministic execution with zero network, tenant data, or credential dependencies.

## Usage

```bash
make check-jira-mcp-path-freshness
# equivalent:
make test PYTEST_ARGS='tests/test_example_fixtures.py::test_jira_mcp_critical_rest_paths_match_locked_catalog tests/test_example_fixtures.py::test_jira_mcp_critical_rest_paths_rejects_url_drift -q'
```

The fast suite (`make test`) also runs both contracts.

## Maintainer checklist (periodic doc refresh)

1. Open the `doc_refs` URLs in
   `examples/collections/jira_mcp_critical_rest_paths.json` (Issue Search,
   Sprint, Issues / assignee / parent).
2. Confirm each locked method + path still matches current Atlassian Cloud
   REST docs (especially that search remains `/search/jql`, not legacy
   `/search`).
3. If Atlassian changed a path: update **both** `jira_mcp.json` and the
   catalog entry in the same change; set `reviewed_on` to today.
4. If docs are unchanged: optionally bump `reviewed_on` only.
5. Run `make check-jira-mcp-path-freshness` (must stay green; still no live
   credentials).

## Configuration

None. Offline compare only; no environment variables.

## Troubleshooting

| Symptom | Likely cause | Fix |
| ------- | ------------ | --- |
| Missing catalog file | Catalog not committed | Add `jira_mcp_critical_rest_paths.json` |
| URL missing locked fragment | Collection drift | Restore path in `jira_mcp.json` or intentionally update catalog after doc review |
| Missing required catalog ids | Catalog incomplete | Ensure all five critical ids are listed |
| Drift diagnostic test fails | Comparator message format regressed | Ensure `assert_jira_mcp_critical_rest_paths_match_catalog` includes request ID, locked fragment, and observed URL |
| Want live smoke | Different gate | See [Optional Live Jira MCP Smoke](jira_mcp_live_smoke.md) |

## See also

- [Example fixtures contract](testing.md#example-fixtures-contract-pypost-1017--pypost-1026--pypost-1047--pypost-1028--pypost-1048--pypost-1056)
- [Jira MCP critical REST path catalog and mutation diagnostics](testing.md#jira-mcp-critical-rest-path-catalog-and-mutation-diagnostics-pypost-1030--pypost-1056)
- [Jira MCP discoverability contracts](testing.md#jira-mcp-discoverability-contracts-pypost-1048)
- [Jira MCP Example Project Default](jira_mcp_project_default.md)
