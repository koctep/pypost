# GitLab MCP Example Collection (PYPOST-1316)

## Overview

PyPost ships a curated GitLab REST API v4 collection that publishes 25 MCP tools
(`gitlab_*`) for GitLab.com and self-managed GitLab. It is example content only: no
production code under `pypost/` was added or changed. The tools run on the existing
generic MCP and HTTP pipeline (`MCPServerImpl` → `RequestService` → `HTTPClient`).

All checks are offline. No test contacts GitLab or needs a real token.

End-user setup (import order, scopes, self-managed URLs, coverage and gaps) lives in
[`examples/README.md`](../../examples/README.md). This page is for contributors who change
the collection or its tests.

## Architecture

### Files

| File | Role |
| ---- | ---- |
| `examples/collections/gitlab_mcp.json` | Collection `id: gitlab-mcp`, `name: GitLab MCP`, `version: 1.0.0`, embedded `variables[]` and 25 requests. Every request has `expose_as_mcp: true`, an `mcp_description`, explicit `mcp_params`, `body_type: json` and `retry_policy: null`. |
| `examples/environments/gitlab.json` | Companion environment `gitlab-mcp-environment`: `gitlab_base_url`, `gitlab_project` (visible, in `mcp_overridable_keys`), `gitlab_token` (the only entry in `hidden_keys`). Placeholders only. |
| `examples/collections/gitlab_mcp_rest_paths.json` | Locked offline catalog: `version`, `description`, `reviewed_on`, `doc_refs[]` and `tools[]` of `{id, tool, capability, method, path}` for all 25 tools. Not importable and not listed in the manifest. |
| `examples/pypost-library.yaml` | Lists `collections/gitlab_mcp.json` (after `jira_mcp.json`), the variables `gitlab_base_url`, `gitlab_project`, `gitlab_token` (`secret: true`) and the `gitlab_com` preset. The preset never carries the token. |
| `examples/README.md` | User-facing GitLab sections: import order, authentication, GitLab.com vs self-managed, default project and identifiers, coverage vs gaps. |
| `Makefile` | `check-gitlab-mcp-path-freshness` target. |
| `tests/test_gitlab_mcp_collection.py` | All offline contracts (see [Test layout](#test-layout)). |
| `tests/helpers/gitlab_mcp_collection_http.py` | Loopback GitLab stand-in for the wire-level e2e test. |

```text
gitlab.json (env) ----------------------------+
                                              v
gitlab_mcp.json --> MCPServerImpl --> TemplateService --> HTTPClient --> requests
      ^                                (urlencode / to_int / to_json_string)
      |
gitlab_mcp_rest_paths.json  <-- make check-gitlab-mcp-path-freshness (offline compare)
```

### Request conventions

- Request `id` is the kebab form of the tool name (`gitlab-get-file` →
  `gitlab_get_file`). The tool name comes from `normalize_mcp_tool_name(request.name)`,
  so the request `name` "GitLab Get File" publishes `gitlab_get_file`.
- Read tools are `GET` with an empty body. Create tools are `POST`, update tools are
  `PUT`. There are no `DELETE` tools.
- Headers are exactly `Accept: application/json` and
  `Authorization: Bearer {{ gitlab_token }}`, plus `Content-Type: application/json` on
  `POST` and `PUT`.
- Project-scoped URLs start with
  `{{ gitlab_base_url }}/api/v4/projects/{{ urlencode(gitlab_project) }}`.
- List tools take optional `page` (default `1`) and `per_page` (default `20`) as
  `integer_or_string`, rendered with `to_int`. The `mcp_params` defaults are required,
  because an omitted `to_int` argument would otherwise break the render.
- JSON bodies use typed arguments, not a free-form payload string. Each field is wrapped
  in a `{% if mcp is defined and mcp.request is defined and mcp.request.X is defined and
  mcp.request.X is not none %}` guard with a Jinja `namespace` separator, and its value
  goes through `to_json_string`. Note-creation tools map the argument `note_body` to the
  GitLab field `body`.
- Body templates start with `{ ` (brace and a space) before the first `{% if %}`.
  Without the space, `{{%` would be read as the start of a Jinja expression.

## Encoding rules

| Input | Template | Example |
| ----- | -------- | ------- |
| Project path or ID | `{{ urlencode(gitlab_project) }}` | `group/subgroup/my-project` → `group%2Fsubgroup%2Fmy-project` |
| File path, branch, SHA (path segment) | `{{ urlencode(mcp.request.file_path) }}` | `docs/a b#c?d%e+f.md` → `docs%2Fa%20b%23c%3Fd%25e%2Bf.md` |
| IID, pipeline ID, job ID | `{{ to_int(mcp.request.issue_iid) }}` | `7` or `"7"` → `7`; `"7a"` fails before any HTTP send |
| Query value (`ref`, `search`, `path`, …) | raw `{{ mcp.request.ref }}` in `params` | `feature/x&y=1#z` → `ref=feature%2Fx%26y%3D1%23z` on the wire |

- `urlencode` is `urllib.parse.quote(str(v), safe="")`, so a value always stays one path
  segment. `requests` keeps the existing `%2F` escapes.
- Never wrap a query value in `urlencode`. `requests` form-encodes `params` once, so
  wrapping would double-encode. Query params that render to `""` are dropped, which makes
  optional string filters disappear when omitted.
- Numeric path IDs use the MCP type `integer_or_string`. Their descriptions say
  "decimal string or integer". `to_int` raises `IntegerConversionError` for anything
  else, and `HTTPClient` reports it before sending.
- **Limitation:** `urlencode` leaves `.` unencoded. A `file_path`, `branch` or `sha` that
  is exactly `.` or `..` becomes a dot segment that HTTP stacks may normalise away. Git
  does not allow these names, so valid input never reaches this case. Values such as
  `a.md` or `../x` (rendered `..%2Fx`) are not affected. Fixing it would need a core
  `urlencode` change.

## Authentication and secrets

- Every request uses `Authorization: Bearer {{ gitlab_token }}`. GitLab also accepts
  `PRIVATE-TOKEN`, but Bearer was chosen because `pypost/core/sensitive_text_sanitizer.py`
  masks the `authorization` header and any `Bearer <token>` text by name. It does not
  treat `PRIVATE-TOKEN` as sensitive, so that header would rely only on hidden-value
  masking. The README documents `PRIVATE-TOKEN` as a manual alternative (risk R1).
- `gitlab_token` is hidden in the environment, `secret: true` in the collection variables
  and the manifest, and never overridable. It never appears in a published MCP schema;
  neither does `gitlab_base_url`.
- Committed files use the placeholder `your-gitlab-access-token`. The secret-scan test
  rejects any GitLab token-like value (`glpat-…` and the other `gl…-` prefixes) in the
  collection, environment, catalog, manifest and `examples/README.md`.

## Default project behaviour

- `gitlab_project` is an environment variable in `mcp_overridable_keys`, so every
  project-scoped tool publishes an optional `gitlab_project` string argument. It is a soft
  default, not a security boundary (the same model as `jira_project_key`, see
  [Jira MCP Example Project Default](jira_mcp_project_default.md)).
- URLs stay declarative: there is no `{% if %}` fallback. A blank value with no override
  renders `/projects//…` (GitLab answers 404). For `gitlab_get_project` it renders
  `/api/v4/projects/`, which GitLab may treat as "list projects" (risk R2).
- Mitigation: the non-empty placeholder `your-group/your-project` is set in the
  environment, in the `gitlab_com` preset and as the manifest default, and tests enforce
  that all three match. Each project-scoped `mcp_description` tells the agent to pass
  `gitlab_project` when no default is configured.
- A runtime fail-closed check for blank path segments is tracked in
  [PYPOST-1332](https://pypost.atlassian.net/browse/PYPOST-1332).

## Locked path catalog and freshness workflow

`gitlab_mcp_rest_paths.json` is the single offline source of truth for the tool set.
Unlike the Jira catalog (five critical markers, see
[Jira MCP critical REST path freshness](jira_mcp_path_freshness.md)), it locks the exact
`method` and `path` of **all 25** tools. `path` is the request URL with the
`{{ gitlab_base_url }}` prefix removed.

```bash
make check-gitlab-mcp-path-freshness
```

The target runs two nodes from `tests/test_gitlab_mcp_collection.py`:

- `test_gitlab_mcp_http_contracts_match_locked_catalog` — the catalog equals the test's
  locked spec table, and the collection's request ids, tool names, methods and URLs equal
  the catalog exactly.
- `test_gitlab_mcp_catalog_check_rejects_path_drift` — mutation twin: strips `/raw` from a
  synthetic `gitlab-get-file` request and asserts the diagnostic names `gitlab_get_file`
  and the observed URL.

Both nodes also run in `make test` and `make check`, so the target adds no extra gate.

### Maintainer checklist (GitLab paths changed)

1. Open the `doc_refs` URLs in `gitlab_mcp_rest_paths.json` and compare each tool's
   method and path with current GitLab REST v4 docs.
2. If a path changed, update in one change:
   - the request `url` (and `method`) in `examples/collections/gitlab_mcp.json`;
   - the matching `tools[]` entry in `gitlab_mcp_rest_paths.json`, and set `reviewed_on`
     to today;
   - the `ToolSpec` entry in `GITLAB_TOOL_SPECS` in `tests/test_gitlab_mcp_collection.py`
     (the catalog is compared to this table too).
3. If you add or remove a tool, also update the README coverage table, the
   "(25 REST tools)" inventory count, the collection `description`, `GITLAB_TOOL_COUNT`
   and the inventory tests in `tests/test_examples_modernization.py`. A tool with a verb
   other than `get`/`list`/`create`/`update` also needs the README parity regex widened.
4. If the docs are unchanged, optionally bump `reviewed_on` only.
5. Run `make check-gitlab-mcp-path-freshness`, then
   `make test WORKERS=1 PYTEST_ARGS='tests/test_gitlab_mcp_collection.py tests/test_examples_modernization.py'`.

## Test layout

All tests are in `tests/test_gitlab_mcp_collection.py`
(`pytestmark = pytest.mark.timeout(30)`). Missing files are reported by `Path.is_file()`
assertions inside each test, never at import time.

- **Offline contract tests:** native import of the collection and environment, exact
  published tool set and input schemas, query keys, headers, body fields, Bearer auth,
  declared vs used `mcp_params`, companion-env coverage, argument names that must not
  shadow `dict` attributes, no surviving `{{`/`{%` after a full render, encoding
  (`test_gitlab_template_encoding`), numeric-ID rejection, project-scoped descriptions,
  manifest entries and README parity
  (`test_gitlab_readme_documents_inventory_and_tool_parity`).
- **Loopback e2e:** `test_gitlab_mcp_loopback_e2e_wire_contract`
  (`@pytest.mark.timeout(60)`, `anyio.fail_after(10)` per call) drives a live MCP server
  through `gitlab_get_current_user`, `gitlab_get_file`, `gitlab_list_projects` and
  `gitlab_create_issue_note`. `tests/helpers/gitlab_mcp_collection_http.py` runs a
  `ThreadingHTTPServer` on `127.0.0.1:0` that records method, raw path, raw query,
  `Authorization` and the JSON body (read up to 64 KiB), and joins its thread within 2 s.
- **Wire-level reserved characters:**
  `test_gitlab_query_reserved_characters_stay_single_key_on_wire` prepares real
  `requests` requests and asserts that `ref="feature/x&y=1#z"` and `search="a b&c"` stay
  one key each, with no fragment.
- **Mutation twins** (prove each checker can fail):
  `test_gitlab_mcp_catalog_check_rejects_path_drift`,
  `test_gitlab_mcp_auth_convention_rejects_private_token_header`,
  `test_gitlab_mcp_params_checker_rejects_dangling_and_dead_arguments`,
  `test_gitlab_query_wire_checker_rejects_prejoined_reserved_value`,
  `test_gitlab_fixtures_secret_scan_rejects_glpat_like_value`.
- **Makefile contract:** `test_gitlab_makefile_path_freshness_target_declared`.

## Observability

No new logs or metrics: GitLab calls use the existing MCP and HTTP events and the
method-labelled MCP metrics. The tool name appears in the MCP activity log only.

- The token travels only in `Authorization`. The sanitizer masks that header and
  `Bearer` values, and hidden-key value redaction covers MCP tool output.
- Rendered URLs carry project paths, file paths and search terms, but no secrets.
  Some generic log events print the rendered URL without sanitizing it:
  `response_body_truncated` ([PYPOST-1122](https://pypost.atlassian.net/browse/PYPOST-1122)),
  `sse_stream_detected`, `retryable_error` and `retry_exhausted`
  ([PYPOST-1333](https://pypost.atlassian.net/browse/PYPOST-1333)).
- `gitlab_get_file` returns raw file content as decoded text. Large responses are cut by
  the generic `max_response_bytes` cap and logged as `response_body_truncated`.

## Configuration

No environment variables or settings. The offline checks need no credentials. At run
time the user sets `gitlab_base_url`, `gitlab_project` and `gitlab_token` in the
imported environment or through the `gitlab_com` preset.

## Troubleshooting

| Symptom | Likely cause | Fix |
| ------- | ------------ | --- |
| `<tool> path drifted: expected …, got …` | Collection URL changed without the catalog | Restore the URL, or update collection, catalog and `GITLAB_TOOL_SPECS` together after a doc review |
| `gitlab_mcp_rest_paths.json drifted from design` | Catalog changed without the test spec table | Update `GITLAB_TOOL_SPECS` to the reviewed path |
| README coverage tools differ from catalog | Tool added or renamed without the README table | Update the "GitLab coverage vs gaps" table |
| GitLab answers 404 with `/projects//` in the URL | Blank `gitlab_project` and no override | Set a default or pass `gitlab_project` (see PYPOST-1332) |
| "Could not render integer template expression" | Non-decimal IID, pipeline or job ID | Pass a native integer or a decimal string |
| GitLab answers 401 | Missing or wrong token, or a proxy strips `Authorization` | Check `gitlab_token`; use `PRIVATE-TOKEN` in your imported copy if needed |

## Follow-ups

- [PYPOST-1332](https://pypost.atlassian.net/browse/PYPOST-1332) — fail-closed rendering
  for blank path-segment variables.
- [PYPOST-1333](https://pypost.atlassian.net/browse/PYPOST-1333) — sanitize rendered URLs
  in `sse_stream_detected`, `retryable_error` and `retry_exhausted`.
- [PYPOST-1122](https://pypost.atlassian.net/browse/PYPOST-1122) — `response_body_truncated`
  logs the resolved URL.
- [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303) — `make lint` does not run
  flake8 on `tests/`.

## See also

- [Examples Collection Library & Legacy Fixtures](examples_library_format.md)
- [Jira MCP critical REST path freshness](jira_mcp_path_freshness.md)
- [CI-safe Jira MCP collection e2e](jira_mcp_collection_e2e.md)
- [MCP Secrets Policy](mcp_secrets_policy.md)
- [Sensitive Data Masking Policy](sensitive_data_masking_policy.md)
