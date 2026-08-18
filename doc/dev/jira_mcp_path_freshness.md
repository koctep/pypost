# Jira MCP critical REST path freshness (PYPOST-1030)

## Overview

Offline gate that keeps critical REST path markers in
`examples/collections/jira_mcp.json` aligned with a checked-in expected
catalog. No live Jira credentials or network calls.

## Architecture

- **Collection:** `examples/collections/jira_mcp.json` — curated MCP tools.
- **Catalog:** `examples/collections/jira_mcp_critical_rest_paths.json` —
  locked method / path fragments (and optional `mcp_param` / `url_excludes`)
  for the highest-risk drift surfaces.
- **Contract:** `tests/test_example_fixtures.py` —
  `test_jira_mcp_critical_rest_paths_match_locked_catalog`.
- **Makefile:** `make check-jira-mcp-path-freshness`.

```text
Atlassian REST docs  --(periodic human review)-->  critical_rest_paths.json
jira_mcp.json  ---------------------------------->  pytest compare (CI / make)
```

## Locked critical paths

| Capability | Request id | Locked markers |
| ---------- | ---------- | -------------- |
| Enhanced JQL search | `jira-search-issues-jql` | `POST` `/rest/api/3/search/jql` |
| Sprint create | `jira-create-sprint` | `POST` `/rest/agile/1.0/sprint` (no `/sprint/`) |
| Sprint membership | `jira-add-issues-to-sprint` | `POST` `.../sprint/` + `/issue` |
| Parent / epic link | `jira-link-issue-parent` | `PUT` `.../issue/` + `parent_payload` |
| Assignee | `jira-assign-issue` | `PUT` `.../assignee` |

## Usage

```bash
make check-jira-mcp-path-freshness
# equivalent:
make test PYTEST_ARGS='tests/test_example_fixtures.py::test_jira_mcp_critical_rest_paths_match_locked_catalog -q'
```

The fast suite (`make test`) also runs this contract.

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
| Want live smoke | Different gate | See [Optional Live Jira MCP Smoke](jira_mcp_live_smoke.md) |

## See also

- [Example fixtures contract](testing.md#example-fixtures-contract-pypost-1017--pypost-1026--pypost-1047--pypost-1028--pypost-1048)
- [Jira MCP discoverability contracts](testing.md#jira-mcp-discoverability-contracts-pypost-1048)
- [Jira MCP Example Project Default](jira_mcp_project_default.md)
