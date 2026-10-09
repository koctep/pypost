# GitHub MCP Example Collection (PYPOST-1334)

## Overview

PyPost ships a curated GitHub REST API collection that publishes 30 MCP tools
(`github_*`) for github.com and GitHub Enterprise Server (GHES). It covers GitHub Actions
(workflows, runs, jobs, dispatch, re-run, cancel), pull requests (list, get, create,
update, files, commits, review comments, conversation comments, reviews), issues (list,
get, create, update, comments) and the authenticated user and repository lookups.

It is example content only: no production code under `pypost/` was added or changed. The
tools run on the existing generic MCP and HTTP pipeline (`MCPServerImpl` →
`RequestService` → `HTTPClient`). All checks are offline. No test contacts GitHub or needs
a real token.

End-user setup (import order, token permissions, GHES URLs, identifiers, coverage and
gaps) lives in [`examples/README.md`](../../examples/README.md). This page is for
contributors who change the collection or its tests. The design mirrors the
[GitLab MCP Example Collection](gitlab_mcp_collection.md); only the differences are
explained in depth here.

## Architecture

### Files

| File | Role |
| ---- | ---- |
| `examples/collections/github_mcp.json` | Collection `id: github-mcp`, `name: GitHub MCP`, `version: 1.0.0`, embedded `variables[]` and 30 requests. Every request has `expose_as_mcp: true`, an `mcp_description`, explicit `mcp_params`, `body_type: json` and `retry_policy: null`. |
| `examples/environments/github.json` | Companion environment `github-mcp-environment`: `github_api_url`, `github_owner` and `github_repo` (visible, in `mcp_overridable_keys`), `github_token` (the only entry in `hidden_keys`). Placeholders only. |
| `examples/collections/github_mcp_rest_paths.json` | Locked offline catalog: `version`, `description`, `reviewed_on`, `api_version`, `doc_refs[]` and `tools[]` of `{id, tool, capability, method, path}` for all 30 tools. Not importable and not listed in the manifest. |
| `examples/pypost-library.yaml` | Lists `collections/github_mcp.json` (after `gitlab_mcp.json`, before `mcp.json`), the variables `github_api_url`, `github_owner`, `github_repo` and `github_token` (`secret: true`), and the `github_com` preset. The preset never carries the token. |
| `examples/README.md` | User-facing GitHub sections: import order, authentication, github.com vs GHES, default repository and identifiers, coverage vs gaps. |
| `Makefile` | `check-github-mcp-path-freshness` target. |
| `tests/test_github_mcp_collection.py` | All offline contracts (see [Test layout](#test-layout)). |
| `tests/helpers/github_mcp_collection_http.py` | Loopback GitHub stand-in for the wire-level e2e test. |

```text
github.json (env) ----------------------------+
                                              v
github_mcp.json --> MCPServerImpl --> TemplateService --> HTTPClient --> requests
      ^                                (urlencode / to_int / to_json_string / Jinja loops)
      |
github_mcp_rest_paths.json  <-- make check-github-mcp-path-freshness (offline compare)
```

### Request conventions

- Request `id` is the kebab form of the tool name (`github-get-workflow-run` →
  `github_get_workflow_run`). The tool name comes from
  `normalize_mcp_tool_name(request.name)`, so the request `name` "GitHub Get Workflow Run"
  publishes `github_get_workflow_run`.
- Read tools are `GET` with an empty body. Create, dispatch, re-run, cancel and reply tools
  are `POST`. Update tools are `PATCH` (GitHub's update verb, unlike GitLab `PUT`). There
  are no `DELETE` or `PUT` tools.
- Headers are exactly `Accept: application/vnd.github+json`,
  `X-GitHub-Api-Version: 2022-11-28` and `Authorization: Bearer {{ github_token }}`, plus
  `Content-Type: application/json` on `POST` and `PATCH`.
- Repository-scoped URLs start with
  `{{ github_api_url }}/repos/{{ urlencode(github_owner) }}/{{ urlencode(github_repo) }}`.
  Only `github_get_authenticated_user` (`/user`) is not repository-scoped.
- List tools take optional `page` (default `1`) and `per_page` (default `30`, GitHub's
  default) as `integer_or_string`, rendered with `to_int`. The defaults are required,
  because an omitted `to_int` argument would otherwise break the render.
- Argument names equal GitHub field names (including `body`), so there is no argument to
  field mapping (GitLab maps `note_body` to `body`).
- Pull request conversation comments use the issue-comments endpoint
  `/issues/{pull_number}/comments` (a pull request is an issue). The catalog records
  `github_list_pull_request_comments` and `github_list_issue_comments` with the same path
  template shape, told apart by the argument name.

### JSON bodies

Every write sends a JSON body. Field-carrying bodies use the GitLab pattern: each field is
wrapped in a `{% if mcp is defined and mcp.request is defined and mcp.request.X is defined
and mcp.request.X is not none %}` guard with a Jinja `namespace(sep=…)` separator. The body
starts with `{ ` (brace and a space), because `{{%` would be read as the start of a Jinja
expression.

`to_json_string` always emits a JSON **string**, so other JSON types are built in the
template:

| Field type | MCP type | Template | Example fields |
| ---------- | -------- | -------- | -------------- |
| String | `string` | `{{ to_json_string(mcp.request.x) }}` | `title`, `body`, `ref`, `commit_id` |
| Integer | `integer_or_string` | `{{ to_int(mcp.request.x) }}` | `line`, `start_line` |
| Boolean | `boolean` | `{% if mcp.request.x %}true{% else %}false{% endif %}` | `draft`, `enable_debug_logging` |
| String array | `array` | `[{% for x in … %}{% if not loop.first %}, {% endif %}{{ to_json_string(x) }}{% endfor %}]` | `labels`, `assignees` |
| Object | `object` | `{% for k, v in ….items() %}` loop, values stringified | `inputs` (dispatch) |

- An empty array sends `[]`, which clears all labels or assignees on GitHub.
- Dispatch `inputs` values are always sent as JSON strings (booleans become
  `"true"`/`"false"`), which is the documented GitHub form. Nested values would be sent as
  Python `str()` text, so descriptions say "scalar values only, at most 25 keys".
- `github_dispatch_workflow` renders `inputs` before `ref`. Field order does not matter to
  GitHub; the order only avoids a false positive in the template-marker test
  ([PYPOST-1339](https://pypost.atlassian.net/browse/PYPOST-1339)).
- `github_cancel_workflow_run` sends a static `{}`. `github_rerun_workflow_run` with no
  arguments renders `{ }`. Both are sent as `json={}`.

## Design decisions

### Bearer authentication

Every request uses `Authorization: Bearer {{ github_token }}`. GitHub documents Bearer for
personal access tokens and requires it for JWTs, and
`pypost/core/sensitive_text_sanitizer.py` masks the `authorization` header and any
`Bearer <token>` text. The `token <PAT>` scheme also works on GitHub; the README mentions it
as an alternative, but the collection does not use it. A mutation twin rejects
`token {{ github_token }}`.

### Pinned API version

Every request sends `X-GitHub-Api-Version: 2022-11-28`. It is the only version shared by
github.com and every supported GHES release (GHES 3.19 lists only it), it is GitHub's default
when the header is omitted, and github.com supports it until **2028-03-10**.

The value has one source of truth: the catalog field `api_version`. Tests require all 30
header values to equal it. The field choices are forward-compatible with `2026-03-10`:
issues use only `assignees[]` (never singular `assignee`), no tool depends on
`merge_commit_sha`, and dispatch does not send `return_run_details`. The migration is
tracked in [PYPOST-1341](https://pypost.atlassian.net/browse/PYPOST-1341).

### Owner and repository variables

GitHub routes are `/repos/{owner}/{repo}/…`, two path segments. The collection uses two
variables, `github_owner` and `github_repo`, each passed through `urlencode` on its own. A
single `owner/repo` variable would either need string splitting in the template or render
`owner%2Frepo`, which GitHub does not route.

- Both are in `mcp_overridable_keys`, so the 29 repository-scoped tools publish optional
  `github_owner` and `github_repo` string arguments. It is a soft default, not a security
  boundary (the same model as GitLab and
  [Jira MCP Example Project Default](jira_mcp_project_default.md)).
- URLs stay declarative: there is no `{% if %}` fallback. A blank value with no override
  renders `/repos//…` and GitHub answers 404. Mitigation: the non-empty placeholders
  `your-org` / `your-repo` are set in the environment, the `github_com` preset and the
  manifest defaults, and tests enforce that all three match. The runtime fail-closed check
  is [PYPOST-1332](https://pypost.atlassian.net/browse/PYPOST-1332).
- `github_api_url` and `github_token` are never published in a tool schema.

### Review `event` is required

`github_create_pull_request_review` requires `event` (`APPROVE`, `REQUEST_CHANGES` or
`COMMENT`) and renders it unconditionally as the first body field. Without `event` GitHub
creates a PENDING review that no tool in the collection can submit, and a user may hold
only one pending review per pull request (a later create may fail with `422`).

- Presence: `event` is in the published `required` list, so PyPost rejects a call without
  it before any HTTP request.
- Value: PyPost MCP params cannot publish `enum`, so the allowed values are listed in the
  tool and argument descriptions. GitHub rejects any other value with `422`. Schema `enum`
  support is [PYPOST-1342](https://pypost.atlassian.net/browse/PYPOST-1342).

### No merge tool

Merging a pull request is excluded. It is the only irreversible repository write in scope,
it needs **Contents: write** on fine-grained tokens on top of Pull requests: write, and
branch protection and required reviews are better enforced by a human merge. GitLab has no
merge tool either. Users may add `PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge` to
their imported copy. Merge and pending-review submission are a product decision in
[PYPOST-1344](https://pypost.atlassian.net/browse/PYPOST-1344).

## Encoding rules

| Input | Template | Example |
| ----- | -------- | ------- |
| Owner, repository | `{{ urlencode(github_owner) }}` | `my org/x#y` → `my%20org%2Fx%23y` |
| Workflow ID or file name | `{{ urlencode(mcp.request.workflow_id) }}` | `ci.yml` → `ci.yml`; `dir/ci.yml` → `dir%2Fci.yml` |
| PR / issue number, run / job / comment ID | `{{ to_int(mcp.request.run_id) }}` | `7` or `"7"` → `7`; `"7a"`, `"1.5"`, `""` fail before any HTTP send |
| Query value (`branch`, `head`, `labels`, …) | raw `{{ mcp.request.branch }}` in `params` | `feature/x&y=1#z` → `branch=feature%2Fx%26y%3D1%23z` on the wire |
| Body string | `{{ to_json_string(mcp.request.ref) }}` | `feature/x"y` → `"feature/x\"y"` |
| Body integer | `{{ to_int(mcp.request.line) }}` | `"12"` → `12`; `"7a"` fails before send |

- `urlencode` is `urllib.parse.quote(str(v), safe="")`, so a value always stays one path
  segment.
- Never wrap a query value in `urlencode`. `requests` form-encodes `params` once, so
  wrapping would double-encode. Query params that render to `""` are dropped.
- `workflow_id` is a `string`, not `integer_or_string`, because it also accepts file names.
- `labels` is a comma-separated **string** in `github_list_issues` (query) and an
  **array** in `github_create_issue` / `github_update_issue` (body). Descriptions say so.
- Numeric path IDs and body integers use the MCP type `integer_or_string`. Their
  descriptions say "decimal string or integer". A non-decimal value is rejected at the MCP
  boundary (`McpArgumentValidationError`) and, if it reaches the template, by `to_int`
  (`IntegerConversionError`).
- **Limitation:** `urlencode` leaves `.` unencoded and `requests` resolves dot segments, so
  `..` as `github_owner`, `github_repo` or `workflow_id` can reach another path on the same
  host with the same method and token. GitHub does not allow these names, so valid input
  never hits this case. The fail-closed fix is
  [PYPOST-1346](https://pypost.atlassian.net/browse/PYPOST-1346).

## Secrets

- `github_token` is hidden in the environment, `secret: true` in the collection variables
  and the manifest, never overridable and absent from every preset.
- The environment uses the placeholder `your-github-token`; the collection variable and
  manifest defaults are empty. The secret-scan test rejects
  GitHub token-like values (`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_` and `github_pat_`
  prefixes) in the collection, environment, catalog, manifest and `examples/README.md`.

## github.com vs GitHub Enterprise Server

One environment covers both, because the REST paths and headers are identical. Only
`github_api_url` changes: `https://api.github.com` for github.com, or
`https://<host>/api/v3` (the REST base, not the web URL, no trailing slash) for GHES. The
variable is named for the API base on purpose. The pinned API version is the one every
supported GHES release accepts. GHES-specific endpoint differences are not tested; the
catalog `doc_refs` point to the github.com docs.

## Locked path catalog and freshness workflow

`github_mcp_rest_paths.json` locks the exact `method` and `path` of **all 30** tools, like
the GitLab catalog. `path` is the request URL with the `{{ github_api_url }}` prefix
removed. It also holds `api_version`, the header pin.

```bash
make check-github-mcp-path-freshness
```

The target runs two nodes from `tests/test_github_mcp_collection.py`:

- `test_github_mcp_http_contracts_match_locked_catalog` — the catalog equals the test's
  locked spec table (`GITHUB_TOOL_SPECS`), and the collection's request ids, tool names,
  methods and URLs equal the catalog exactly.
- `test_github_mcp_catalog_check_rejects_path_drift` — mutation twin: strips `/replies`
  from a synthetic `github-reply-to-pull-request-review-comment` request and changes the
  `github_update_issue` method to `PUT`, and asserts both drifts are reported.

Both nodes also run in `make test` and `make check`, so the target adds no extra gate.

### Adding or changing a tool

Keep these in one change:

1. The request in `examples/collections/github_mcp.json`: `id` (kebab of the tool name),
   `name`, `method`, `url`, headers, `params`, `body`, `mcp_description` and `mcp_params`
   for every `mcp.request.*` reference. Follow the conventions and encoding rules above.
2. The `tools[]` entry in `github_mcp_rest_paths.json`. Set `reviewed_on` to today and add
   a `doc_refs` page if the endpoint group is new.
3. The `ToolSpec` entry in `GITHUB_TOOL_SPECS` in `tests/test_github_mcp_collection.py`
   (tool, capability, method, path, argument types, query keys, required and optional body
   fields). Add sample values to `_SAMPLE_VALUES` for new argument names.
4. If you add or remove a tool, also update:
   - `GITHUB_TOOL_COUNT` and the collection `description` ("30 MCP tools");
   - `examples/README.md`: the "GitHub coverage vs gaps" list, the "(30 REST tools)"
     inventory count and, if needed, the permission notes in "GitHub authentication";
   - `tests/test_examples_modernization.py` (`len(requests) == 30`).
5. A tool whose verb is not `get`, `list`, `create`, `update`, `rerun`, `cancel`,
   `dispatch` or `reply` also needs `_README_TOOL_PATTERN` widened.
6. Run `make check-github-mcp-path-freshness`, then
   `make test WORKERS=1 PYTEST_ARGS='tests/test_github_mcp_collection.py tests/test_examples_modernization.py'`.

### Maintainer checklist (GitHub docs changed)

1. Open the `doc_refs` URLs and compare each tool's method and path with the current
   GitHub REST docs for `api_version`.
2. If a path changed, update the collection, the catalog and `GITHUB_TOOL_SPECS` as above.
3. If the docs are unchanged, optionally bump `reviewed_on` only.
4. Changing the API version means the catalog `api_version`, all 30 header values,
   `GITHUB_API_VERSION` and the README term `X-GitHub-Api-Version: 2022-11-28` together,
   after checking the breaking-changes page. See PYPOST-1341.

## Test layout

All tests are in `tests/test_github_mcp_collection.py`
(`pytestmark = pytest.mark.timeout(30)`). Missing files are reported by `Path.is_file()`
assertions inside each test, never at import time. The module follows the same nine
groups as the GitLab module.

- **Format and tool publication:** native import of the collection and environment,
  exact published tool set and input schemas (including `boolean`, `array`, `object` and
  `integer_or_string`), override properties on the 29 repository-scoped tools,
  repository-scoped descriptions, and
  `test_github_create_pull_request_review_documents_event_and_pending_gap`.
- **HTTP contracts:** query keys, headers, catalog parity. Bodies are rendered for all
  arguments, required arguments only and every single-optional subset, then parsed with
  `json.loads` and checked for exact keys and native JSON value types
  (`test_github_mcp_body_value_types_are_native_json`).
  `test_github_create_pull_request_review_body_always_carries_event` proves no body without
  `event` can render.
- **Placeholder integrity:** declared vs used `mcp_params`, companion-env coverage,
  argument names that must not shadow `dict` attributes, no surviving `{{`/`{%` after a
  full render.
- **Encoding:** `test_github_template_encoding`, `test_github_body_value_encoding`,
  `test_github_numeric_path_ids_reject_non_decimal`,
  `test_github_body_integers_reject_non_decimal` (MCP boundary and `to_int` layer).
- **Loopback e2e:** `test_github_mcp_loopback_e2e_wire_contract`
  (`@pytest.mark.timeout(60)`, `anyio.fail_after(10)` per call) drives a live MCP server
  through `github_list_workflow_runs_for_workflow` (owner override and encoded workflow file
  name), `github_create_issue` (array body), `github_dispatch_workflow` (object body) and
  `github_cancel_workflow_run` (`{}` body).
  `tests/helpers/github_mcp_collection_http.py` runs a `ThreadingHTTPServer` on
  `127.0.0.1:0` that records method, raw path, raw query, `Authorization`, `Accept`,
  `X-GitHub-Api-Version`, `Content-Type` and the JSON body, and joins its thread within 2 s.
- **Wire-level reserved characters:**
  `test_github_query_reserved_characters_stay_single_key_on_wire` prepares real `requests`
  requests for `branch`, `head` and `labels`.
- **Library and README:** manifest entries, preset and placeholder defaults, README
  sections and tool parity (`test_github_readme_documents_inventory_and_tool_parity`).
- **Mutation twins** (prove each checker can fail):
  `test_github_mcp_catalog_check_rejects_path_drift`,
  `test_github_mcp_auth_convention_rejects_token_scheme_and_missing_version`,
  `test_github_mcp_params_checker_rejects_dangling_and_dead_arguments`,
  `test_github_query_wire_checker_rejects_prejoined_reserved_value`,
  `test_github_fixtures_secret_scan_rejects_ghp_and_github_pat_values`.
- **Makefile contract:** `test_github_makefile_path_freshness_target_declared`.

Adding the collection also changed the pinned manifest collection list in
`tests/test_examples_modernization.py`, `tests/test_predefined_library_pypost_1281_repro.py`
and `tests/test_gitlab_mcp_collection.py`. The next example collection must update them
again.

## Observability

No new logs or metrics. GitHub calls use the existing MCP and HTTP events and the
method-labelled MCP metrics; the tool name appears in the MCP activity log only. The token
travels only in `Authorization`, which the sanitizer masks. Rendered URLs carry owner,
repository, branch and search values, but no secrets. Some generic log events print the
rendered URL without sanitizing it (PYPOST-1122, PYPOST-1333). Details:
`ai-tasks/PYPOST-1334/50-observability.md`.

## Configuration

No environment variables or settings. The offline checks need no credentials. At run time
the user sets `github_api_url`, `github_owner`, `github_repo` and `github_token` in the
imported environment or through the `github_com` preset.

## Troubleshooting

| Symptom | Likely cause | Fix |
| ------- | ------------ | --- |
| `<tool> path drifted: expected …, got …` | Collection URL changed without the catalog | Restore the URL, or update collection, catalog and `GITHUB_TOOL_SPECS` together after a doc review |
| `<tool> method drifted` | Collection method changed without the catalog | As above |
| `github_mcp_rest_paths.json drifted from design` | Catalog changed without the test spec table | Update `GITHUB_TOOL_SPECS` to the reviewed path |
| `<tool> headers drifted` | Header missing or version differs from `api_version` | Restore the three or four exact headers |
| `<tool> [<subset>] body drifted` or `json.loads` error | Broken guard, separator or loop in a body template | Compare with a working body of the same field type |
| README coverage tools differ from catalog | Tool added or renamed without the README list | Update "GitHub coverage vs gaps" |
| GitHub answers 404 with `/repos//` in the URL | Blank `github_owner` or `github_repo` and no override | Set defaults or pass both arguments (see PYPOST-1332) |
| GitHub answers 422 on review create | Invalid `event`, or `REQUEST_CHANGES`/`COMMENT` without `body` | Pass a valid `event` and a `body` |
| GitHub answers 401 or 403 | Missing token, or missing permission or scope | Check `github_token` and the permissions in `examples/README.md` |

## Known limitations and follow-ups

- [PYPOST-1339](https://pypost.atlassian.net/browse/PYPOST-1339) — the template-marker
  test scans re-serialized JSON and false-positives on a body that ends with an object.
- [PYPOST-1340](https://pypost.atlassian.net/browse/PYPOST-1340) — shared loopback stub
  and contract helpers for the Jira, GitLab and GitHub collections.
- [PYPOST-1341](https://pypost.atlassian.net/browse/PYPOST-1341) — migrate to API version
  `2026-03-10` before 2028-03-10; expose dispatch run details (`return_run_details`).
  Today `github_dispatch_workflow` returns no run ID, so the agent must find the run with
  `github_list_workflow_runs_for_workflow`.
- [PYPOST-1342](https://pypost.atlassian.net/browse/PYPOST-1342) — `enum` and array
  `items` in MCP param schemas (`event`, `state`, `side`, `filter`, `state_reason`,
  `labels`, `assignees`).
- [PYPOST-1343](https://pypost.atlassian.net/browse/PYPOST-1343) — type-preserving JSON
  helper to replace hand-written arrays, objects and booleans.
- [PYPOST-1344](https://pypost.atlassian.net/browse/PYPOST-1344) — merge pull request and
  pending-review submit tools (product decision).
- [PYPOST-1345](https://pypost.atlassian.net/browse/PYPOST-1345) — test empty-body
  `201`/`202`/`204` success for re-run, cancel and dispatch.
- [PYPOST-1346](https://pypost.atlassian.net/browse/PYPOST-1346) — reject `.`/`..` as
  rendered path segments.
- [PYPOST-1332](https://pypost.atlassian.net/browse/PYPOST-1332) — fail-closed rendering
  for blank path-segment variables.
- [PYPOST-1333](https://pypost.atlassian.net/browse/PYPOST-1333) — sanitize rendered URLs
  in `sse_stream_detected`, `retryable_error` and `retry_exhausted`.
- [PYPOST-1122](https://pypost.atlassian.net/browse/PYPOST-1122) —
  `response_body_truncated` logs the resolved URL.
- [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303) — `make lint` does not run
  flake8 on `tests/`.

There is no live GitHub test. Catalog accuracy depends on a person re-reviewing
`doc_refs`, the same as for Jira and GitLab. The full analysis is in
`ai-tasks/PYPOST-1334/60-tech-debt.md`.

## See also

- [GitLab MCP Example Collection](gitlab_mcp_collection.md)
- [Examples Collection Library & Legacy Fixtures](examples_library_format.md)
- [Jira MCP critical REST path freshness](jira_mcp_path_freshness.md)
- [MCP Secrets Policy](mcp_secrets_policy.md)
- [Sensitive Data Masking Policy](sensitive_data_masking_policy.md)
