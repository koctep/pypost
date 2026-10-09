# PYPOST-1334: Technical Debt Analysis

Scope: the uncommitted change for the GitHub MCP collection (base `36d7782b`):

- new `examples/collections/github_mcp.json` (30 tools),
  `examples/collections/github_mcp_rest_paths.json` and `examples/environments/github.json`
- edited `examples/pypost-library.yaml`, `examples/README.md` and `Makefile`
  (`check-github-mcp-path-freshness`)
- new `tests/test_github_mcp_collection.py` (1665 lines) and
  `tests/helpers/github_mcp_collection_http.py`; edited `tests/test_examples_modernization.py`,
  `tests/test_predefined_library_pypost_1281_repro.py` and `tests/test_gitlab_mcp_collection.py`
  (manifest collection list only)

No production code (`pypost/`) changed. The GitHub tools run on the existing MCP/HTTP pipeline.

**No item below is a BLOCKER.** `tests/test_github_mcp_collection.py` declares
`pytestmark = pytest.mark.timeout(30)`, the loopback e2e test adds `@pytest.mark.timeout(60)`,
and the loopback helper joins its server thread with a bounded timeout. The edited inventory
modules keep their existing module-level markers. The do-testing timeout rule is met.

## Summary Table

| ID | Priority | Item | Follow-up | Jira |
| --- | --- | --- | --- | --- |
| TD-1 | Medium | No-template-marker test scans `json.dumps` of the parsed body, so any nested object ending the body false-positives on `}}`; dispatch body reordered to work around it | yes (new) | [PYPOST-1339][] |
| TD-2 | Low | Third copy of the loopback stub and fixture-contract checkers (Jira, GitLab, GitHub); rule of three now met | yes (new) | [PYPOST-1340][] |
| TD-3 | Low | `X-GitHub-Api-Version: 2022-11-28` pinned; github.com support ends 2028-03-10 (R1) | yes (new) | [PYPOST-1341][] |
| TD-4 | Low | `github_dispatch_workflow` returns `204` with no run id; "dispatch then track run" needs a list-runs lookup | yes (new) | [PYPOST-1341][] |
| TD-5 | Low | MCP params cannot publish `enum` (`event`, `state`, `side`, …) and publish `array` without `items` (`labels`, `assignees`) (R6, R11) | yes (new) | [PYPOST-1342][] |
| TD-6 | Low | `to_json_string` stringifies everything; arrays, object and booleans are hand-written Jinja loops/literals; dispatch inputs are always strings (R4, R5) | yes (new) | [PYPOST-1343][] |
| TD-7 | Low | Merge PR and pending-review submit are out of scope (documented gaps) | yes (new, story) | [PYPOST-1344][] |
| TD-8 | Low | Rendered URLs unsanitized in retry/truncation logs; `retry_exhausted` alert `final_error_message` carries the same text | yes | [PYPOST-1333][], [PYPOST-1122][] |
| TD-9 | Low | Blank `github_owner`/`github_repo` renders `/repos//…` (R2) | yes | [PYPOST-1332][] |
| TD-10 | Medium | `make lint` does not run flake8 on `tests/`; new test modules checked by hand only | yes | [PYPOST-1303][] |
| TD-11 | Low | Pinned inventory lists in four existing tests change with every new example collection (R7) | no | accepted (deliberate) |
| TD-12 | Lowest | MCP metrics labelled by HTTP method only; tool name only in the activity log | no | accepted (PYPOST-1038 decision) |
| TD-13 | Low | API drift caught only offline against a hand-locked catalog; no live smoke | no | accepted (same as Jira/GitLab) |
| TD-14 | Lowest | `examples/README.md` has lines over 100 characters; `examples/` is outside the doc lint | no | accepted (table rows) |
| TD-15 | — | Pre-existing test failures seen in this task's runs | yes | [PYPOST-1337][], [PYPOST-1338][], [PYPOST-1315][], [PYPOST-1299][] |
| TD-16 | Medium | No test proves an empty-body `201`/`202`/`204` write reports MCP success; loopback stub always answers `200` + JSON | yes (new) | [PYPOST-1345][] |
| TD-17 | Medium | `urlencode` leaves `.`/`..` path segments intact and requests resolves them, so `github_owner`/`github_repo`/`workflow_id` = `..` can reach other same-host paths with the same method and token (found by Phase C blocker review) | yes (new) | [PYPOST-1346][] |

## Shortcuts Taken

- **TD-1 (Medium) — dispatch body field order chosen to satisfy a faulty test.**
  `test_github_mcp_full_render_leaves_no_template_markers`
  (`tests/test_github_mcp_collection.py` ~1101-1109) appends
  `json.dumps(kwargs.get("json", kwargs.get("data", "")))` and searches it for `}}`. The payload
  is the **parsed** body, so `json.dumps({"ref": "main", "inputs": {"a": "b"}})` ends in
  `"b"}}` and fails although the rendered template is correct. Step 4 emitted `inputs` before
  `ref` in `github_dispatch_workflow` only to avoid this (roadmap Step 4, Iteration 1). The
  order does not matter to GitHub, but the test now constrains fixture design, and a future
  tool whose last field is an object will hit the same false positive. The check also does not
  scan the raw template output, which is what a surviving marker would show up in. The GitLab
  module has the same latent pattern (`tests/test_gitlab_mcp_collection.py:889`). Fix: scan the
  raw rendered body (the module already has `_render(request.body, …)` used by
  `_render_body_json`) instead of re-serialized JSON; the raw dispatch body is written
  `{ … }` with spaces, so no false `}}`. Then the dispatch field order can return to `ref`
  first. Apply to both GitHub and GitLab modules.
- **TD-6 (Low) — JSON bodies built by hand in Jinja.** `to_json_string` calls `str()` on any
  non-string value (`pypost/core/json_string.py`), so it cannot serialize lists, dicts or
  booleans. The collection writes arrays (`labels`, `assignees`) and the dispatch `inputs`
  object with `{% for %}` loops and booleans as `true`/`false` literals, and every optional
  field repeats the full `mcp is defined and mcp.request is defined …` guard. Dispatch input
  values are always rendered as JSON strings (booleans as `"true"`/`"false"`, nested values as
  Python `str()` text); README says "scalar values only" and GitHub rejects malformed inputs
  upstream. Mitigated by subset rendering, `json.loads` and value-type assertions. A core
  `to_json` (type-preserving) filter, or a "build JSON object from present args" helper, would
  remove most of the template code for GitLab and GitHub. Runtime feature, out of scope.
- **TD-3 (Low) — pinned API version (R1).** `X-GitHub-Api-Version: 2022-11-28` is the only
  version common to github.com and the supported GHES releases. GitHub supports it on
  github.com until **2028-03-10**. The value lives in one place
  (`github_mcp_rest_paths.json` `api_version`, mirrored in 30 headers and enforced by tests),
  and the field choices avoid what `2026-03-10` removes. Follow-up: migrate to `2026-03-10`
  (or later) before the sunset, re-check every tool against that version's breaking changes,
  and decide how to keep GHES users on the older version (for example a variable or a separate
  preset).
- **TD-4 (Low) — dispatch gives no run id.** Under `2022-11-28` `POST
  …/actions/workflows/{workflow_id}/dispatches` answers `204 No Content`. The agent must find
  the run with `github_list_workflow_runs_for_workflow` (branch/event filter, newest first),
  which can pick the wrong run under concurrency. GitHub's `return_run_details` option is a
  documented gap (README "GitHub coverage vs gaps"). Follow-up: expose `return_run_details`
  where the target API supports it, best done together with TD-3.
- **TD-9 (Low) — blank owner/repo (R2).** A blank `github_owner` or `github_repo` renders
  `/repos//…` and GitHub answers `404`. Mitigated by non-empty placeholders in the environment,
  the `github_com` preset and the manifest (test-enforced). The fail-closed runtime check is
  already tracked as [PYPOST-1332][]; GitHub is one more consumer. Do not re-file.
- **Hardcoded values (intentional, no debt):** `github_api_url` default
  `https://api.github.com`, placeholders for owner/repo, pagination defaults `page=1`,
  `per_page=30` (GitHub's default), catalog `reviewed_on`, `Accept:
  application/vnd.github+json`, test timeouts 30/60 s. Each is a documented example default or
  a bounded test limit.
- **Deviations from the architecture:** one — the dispatch body field order (TD-1). Otherwise
  the 30 tools, paths, headers, manifest/preset entries, catalog and Make target match
  `20-architecture.md`.

## Code Quality Issues

- **TD-2 (Low) — test helper duplication.** `tests/helpers/github_mcp_collection_http.py` is
  the GitLab stub (`tests/helpers/gitlab_mcp_collection_http.py`) with renamed classes and three
  extra captured headers; both follow `tests/helpers/mcp_collection_http.py` (Jira). The
  fixture-contract checkers (spec table, placeholder integrity, encoding, catalog parity,
  secret scan, Makefile target) are likewise re-implemented per provider, which is why
  `tests/test_github_mcp_collection.py` is 1665 lines. PYPOST-1316 TD-14 accepted this "until a
  third provider collection is added"; this task is that third one. Follow-up: one generic
  loopback stub that captures all headers, plus a shared "MCP example collection contract"
  helper module parametrized by provider constants. Fixing TD-1 there fixes it once.
- **TD-5 (Low) — MCP schema expressiveness (R6, R11).** `build_tool_input_schema`
  (`pypost/core/mcp_tool_contract.py:166`) emits `{"type": spec.type}` only: no `enum`, and
  `array` without `items`. So the required review `event` (`APPROVE` / `REQUEST_CHANGES` /
  `COMMENT`) and the `state`, `side`, `filter`, `state_reason` strings are validated only
  upstream (`422`), and `labels`/`assignees` publish `{"type": "array"}`, which some MCP clients
  reject or validate loosely. Allowed values are listed in descriptions. Follow-up: optional
  `enum` and `items` in `McpToolParam`, published in the schema and enforced at argument
  validation; then tighten the GitHub (and GitLab TD-8) params.
- **TD-11 (Low) — inventory churn (R7).** `test_examples_modernization.py`,
  `test_predefined_library_pypost_1281_repro.py` and now `test_gitlab_mcp_collection.py`
  pin the exact manifest collection list. Each new example edits them. Deliberate, so the change
  is visible in review. A shared helper (TD-2) could own the manifest list in one place.
- **TD-14 (Lowest) — README line length.** GitHub coverage table rows and the "Bundled
  collections" link list exceed 100 characters; `make lint` doc checks cover `doc/user`, not
  `examples/`. Accepted.

## Missing Tests

- **Raw-template marker check (TD-1).** The surviving-marker check runs on re-serialized JSON,
  not on the raw rendered body. Covered indirectly by `json.loads` of every body subset, but
  the test as written is both over-strict (false positives) and indirect.
- **No live GitHub test (TD-13).** All checks are offline: fixture contract, loopback wire
  capture, catalog lock (`make check-github-mcp-path-freshness`). Catalog accuracy against the
  real API depends on a person re-reviewing `doc_refs` and `reviewed_on`. Out of scope by
  requirements; same as Jira and GitLab. Accepted.
- **Lint coverage of tests (TD-10).** `make lint` runs `flake8 pypost/` only (Makefile `lint`
  target), so the new test modules were checked by hand in Step 5. Already tracked:
  [PYPOST-1303][]. Do not re-file.
- **Enum values / array item types (TD-5).** Not tested locally because the runtime cannot
  enforce them.
- **TD-16 (Medium) — no-body success is not tested.** `10-requirements.md` (~257-259) requires
  dispatch, cancel and re-run to report success without a response body, and
  `20-architecture.md` (~283) names the statuses (`201` re-run, `202` cancel, `204`/`200`
  dispatch). The loopback stub always answers `200` with a JSON body
  (`tests/helpers/github_mcp_collection_http.py` ~91-96), and no test drives a `204` or other
  empty-body success through an MCP tool call. Code reading shows the runtime already treats it
  as success, so AC2 is not at risk today, but nothing guards it:
  - `read_streamed_body` (`pypost/core/http_response_body_reader.py:24-25, :42`) skips empty chunks
    and returns `""`; `send_request` builds `ResponseData(status_code=204, body="")`
    (`pypost/core/http_client.py:345-380`) with no JSON parsing of the response.
  - `RequestService` returns any status outside `retryable_status_codes` unchanged
    (`pypost/core/request_service.py:172-173`).
  - `_tool_result_has_error` (`pypost/core/mcp_server_impl.py:62-66`) is true only for an
    `execution_error` or status `0`, so `format_structured_tool_result` emits
    `{"status": 204, "error": false, "body": ""}` and the call is recorded as `success`
    (`pypost/core/mcp_server_impl.py:207-208, :224; payload :81-85`).

  Follow-up: let the stub answer per tool (`201` re-run, `202` cancel, `204` dispatch) with an
  empty body, and assert the MCP tool result has `error: false`, the expected `status` and
  `body: ""`.

Otherwise none. All 30 tools are covered for import, published tool set and exact schemas,
headers, bodies (full, minimal, single-optional subsets, value types), encoding, numeric-ID
rejection, wire capture, catalog and README parity, manifest/preset, secret scan and the
Makefile target; the no-body success path is the TD-16 gap above.

## Performance Concerns

- Large responses (`github_list_pull_request_files`, `github_list_workflow_runs`,
  `github_list_pull_requests`, `github_list_issues`; the collection has no repository-contents
  tool) are bounded by the generic response-size cap ([PYPOST-753][], done) and logged via `response_body_truncated`.
  Pagination is explicit (`page`/`per_page`), no auto-pagination.
- **TD-12 (Lowest) — metric granularity.** MCP metrics are labelled by HTTP method, so the 30
  tools collapse into `GET`/`POST`/`PATCH`; the tool name is only in the activity log. Follows
  the PYPOST-1038 decision against high-cardinality labels. Accepted.
- The `request_retry_exhaustions_total{endpoint}` label (`request_service.py:343`) uses
  `RequestData.url`, the **template** URL, so it carries no rendered values and has bounded
  cardinality (one per request). No debt.

Otherwise none.

## Follow-up Tasks

New follow-ups (Jira to be created by the orchestrator):

1. **TD-1 — Scan raw rendered bodies for surviving template markers** (Medium)
   Jira: [PYPOST-1339](https://pypost.atlassian.net/browse/PYPOST-1339)
   In `tests/test_github_mcp_collection.py::test_github_mcp_full_render_leaves_no_template_markers`
   and `tests/test_gitlab_mcp_collection.py` (same check, ~line 889), check the raw rendered
   body text instead of `json.dumps` of the parsed payload. Then restore `ref` before `inputs`
   in the `github_dispatch_workflow` body (optional) and add a twin proving a nested-object
   final field no longer false-positives.
2. **TD-2 — Extract shared MCP example-collection test helpers** (Low)
   Jira: [PYPOST-1340](https://pypost.atlassian.net/browse/PYPOST-1340)
   Merge `tests/helpers/{mcp,gitlab_mcp,github_mcp}_collection_http.py` into one loopback stub
   capturing all headers, and move the provider-agnostic fixture-contract checkers into a shared
   helper parametrized by provider constants. Rule of three met (Jira, GitLab, GitHub).
3. **TD-3 + TD-4 — Migrate GitHub collection to API version 2026-03-10 before the 2028-03-10
   sunset; expose dispatch run details** (Low)
   Jira: [PYPOST-1341](https://pypost.atlassian.net/browse/PYPOST-1341)
   Re-verify all 30 tools against the newer version's breaking changes, decide GHES
   compatibility (variable or preset), update catalog `api_version`, headers, tests and README,
   and add `return_run_details` to `github_dispatch_workflow` so dispatch can return the run id.
4. **TD-5 — Support `enum` and array `items` in MCP param schemas** (Low)
   Jira: [PYPOST-1342](https://pypost.atlassian.net/browse/PYPOST-1342)
   Extend `McpToolParam` / `build_tool_input_schema` (`pypost/core/mcp_tool_contract.py`) with
   optional `enum` and `items`, enforce them at argument validation, then use them for GitHub
   `event`/`state`/`side`/`filter`/`state_reason` and `labels`/`assignees`, and GitLab
   `state_event`/`membership`/`recursive`.
5. **TD-6 — Type-preserving JSON serialization helper for body templates** (Low)
   Jira: [PYPOST-1343](https://pypost.atlassian.net/browse/PYPOST-1343)
   Add a template function (for example `to_json`) that serializes lists, dicts, booleans and
   numbers with their JSON types, so bodies stop hand-building arrays/objects with loops and
   dispatch inputs can carry booleans/numbers. Simplify the GitHub and GitLab bodies after.
6. **TD-7 — GitHub collection: merge pull request and pending-review submit tools** (Low,
   story)
   Jira: [PYPOST-1344](https://pypost.atlassian.net/browse/PYPOST-1344)
   Product decision first: `PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge` (irreversible,
   needs Contents write) and `POST …/reviews/{review_id}/events` (submit a pending review, which
   would also allow `event` to become optional). Both are documented gaps in
   `examples/README.md` ("GitHub coverage vs gaps").
7. **TD-16 — Test empty-body success for GitHub dispatch, cancel and re-run** (Medium)
   Jira: [PYPOST-1345](https://pypost.atlassian.net/browse/PYPOST-1345)
   Make `tests/helpers/github_mcp_collection_http.py` answer per tool (`201`
   `github_rerun_workflow_run`, `202` `github_cancel_workflow_run`, `204`
   `github_dispatch_workflow`) with an empty body, and assert in
   `tests/test_github_mcp_collection.py` that each MCP tool result is success (`error: false`,
   expected `status`, `body: ""`). Covers the `10-requirements.md` no-body success rule.

8. **TD-17 — Reject `.` / `..` as rendered path segments** (Medium)
   Jira: [PYPOST-1346](https://pypost.atlassian.net/browse/PYPOST-1346)
   `urlencode` (`quote(..., safe="")`) leaves dot segments unchanged and requests/urllib3
   resolves them (`https://api.github.com/repos/../user` → `/user`, confirmed in the project
   venv). An MCP caller can set `github_owner`, `github_repo` or `workflow_id` to `..` and reach
   other paths on the same host with the tool's method and token. Not a blocker (AC3.3 lists
   `/`, space, `#`, `?`, `%`, `+`; token scope is the real boundary; GitLab has the same
   pattern; README notes the limitation). Fix in runtime or template: fail closed on `.`/`..`
   segments, possibly together with [PYPOST-1332][] (blank segments); add offline tests for
   GitHub and GitLab.

Existing tickets referenced (do not re-file):

- [PYPOST-1333][] — rendered URLs unsanitized in `sse_stream_detected`, `retryable_error`,
  `retry_exhausted` (TD-8). Note for its scope: `_emit_exhaustion_alert`
  (`pypost/core/request_service.py:344-352`) puts the same `error.message` (rendered URL for
  timeouts/connection failures) into `AlertPayload.final_error_message`; the `endpoint` field
  and the metric label use the template URL and are fine. Suggest adding the alert message to
  PYPOST-1333 rather than a new issue.
- [PYPOST-1122][] — `response_body_truncated` logs the resolved URL (TD-8 sibling).
- [PYPOST-1332][] — fail closed on a blank rendered path segment (TD-9).
- [PYPOST-1303][] — `make lint` does not flake8 `tests/` (TD-10).
- [PYPOST-753][] — response body size cap (done; context only).

Pre-existing test failures seen in this task's runs (Step 4 full `make test`, Step 5 notes):

1. `NON-BLOCKER — pre-existing` — [PYPOST-1337][]
   `tests/test_mypy_baseline_live.py::test_mypy_baseline_live_gate_passes`
   (also why `make typecheck` is not part of this task's gate)
2. `NON-BLOCKER — pre-existing` (flaky) — [PYPOST-1338][]
   `tests/test_collection_import_profile.py::test_plan_collection_import_large_dataset_performance`
   (fails under full parallel `make test`; observed: failed 1 of 2 full parallel runs (Step 3
   run failed, Step 4 run passed); passed 2/2 isolated runs)
3. `NON-BLOCKER — pre-existing` (environment-dependent) — [PYPOST-1315][]
   `tests/test_collection_export_ui.py` (worker crash, exit -11, after tests pass)
4. `NON-BLOCKER — pre-existing` — [PYPOST-1299][]
   `tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing`

### Possible Future Enhancements (not debt; no ticket proposed)

Out of scope by requirements, listed for product planning only: other destructive or admin
operations (deletes, branch protection, releases, repository contents writes), GraphQL API,
GitHub App / OAuth flows, job log and artifact download, and an opt-in live smoke target
(analog of `make test-jira-mcp-live`) for API drift (TD-13).

## Validation

- `make verify-ai-tasks` — exit 0, "ai-tasks artifacts baseline OK (398 completed tasks; 2
  grandfathered legacy gaps)"
- `make lint` — exit 0 (flake8 `pypost/`, Markdown lint, relative link check)

[PYPOST-753]: https://pypost.atlassian.net/browse/PYPOST-753
[PYPOST-1122]: https://pypost.atlassian.net/browse/PYPOST-1122
[PYPOST-1299]: https://pypost.atlassian.net/browse/PYPOST-1299
[PYPOST-1303]: https://pypost.atlassian.net/browse/PYPOST-1303
[PYPOST-1315]: https://pypost.atlassian.net/browse/PYPOST-1315
[PYPOST-1332]: https://pypost.atlassian.net/browse/PYPOST-1332
[PYPOST-1333]: https://pypost.atlassian.net/browse/PYPOST-1333
[PYPOST-1337]: https://pypost.atlassian.net/browse/PYPOST-1337
[PYPOST-1338]: https://pypost.atlassian.net/browse/PYPOST-1338
[PYPOST-1339]: https://pypost.atlassian.net/browse/PYPOST-1339
[PYPOST-1340]: https://pypost.atlassian.net/browse/PYPOST-1340
[PYPOST-1341]: https://pypost.atlassian.net/browse/PYPOST-1341
[PYPOST-1342]: https://pypost.atlassian.net/browse/PYPOST-1342
[PYPOST-1343]: https://pypost.atlassian.net/browse/PYPOST-1343
[PYPOST-1344]: https://pypost.atlassian.net/browse/PYPOST-1344
[PYPOST-1345]: https://pypost.atlassian.net/browse/PYPOST-1345
[PYPOST-1346]: https://pypost.atlassian.net/browse/PYPOST-1346
