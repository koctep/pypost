# PYPOST-1316: Technical Debt Analysis

Scope: the uncommitted change for the GitLab MCP collection (base `811fde38`):

- new `examples/collections/gitlab_mcp.json`, `examples/environments/gitlab.json` and
  `examples/collections/gitlab_mcp_rest_paths.json`
- edited `examples/pypost-library.yaml`, `examples/README.md` and `Makefile`
  (`check-gitlab-mcp-path-freshness`)
- new `tests/test_gitlab_mcp_collection.py` and `tests/helpers/gitlab_mcp_collection_http.py`;
  edited `tests/test_examples_modernization.py` and
  `tests/test_predefined_library_pypost_1281_repro.py`

No production code (`pypost/`) changed. The GitLab tools run on the existing MCP/HTTP pipeline.

**No item below is a BLOCKER.** All four touched test modules declare
`pytestmark = pytest.mark.timeout(30)`. The loopback e2e test adds `@pytest.mark.timeout(60)`
and uses `anyio.fail_after(10)` per MCP call. The loopback helper joins its thread with a 2 s
bound. The do-testing timeout rule is met.

## Summary Table

| ID | Priority | Item | Follow-up | Jira |
| --- | --- | --- | --- | --- |
| TD-1 | Low | Rendered URL logged unsanitized in `sse_stream_detected`, `retryable_error`, `retry_exhausted` (generic, pre-existing) | yes (new) | TBD |
| TD-2 | Low | Blank `gitlab_project` gives `/projects//…` or list projects; no fail-closed empty path segment (R2) | yes (new) | TBD |
| TD-3 | Low | `response_body_truncated` logs the rendered URL (generic, pre-existing) | yes | [PYPOST-1122][] |
| TD-4 | Low | Bearer header chosen over GitLab's `PRIVATE-TOKEN` (R1) | no | accepted (documented) |
| TD-5 | Low | Render fallback sends the raw template on non-strict render failure (R3, generic) | no | accepted (pre-existing core behaviour) |
| TD-6 | Low | Verbose, guard-per-field body templates and the `{ ` whitespace workaround (R4) | no | accepted (test-enforced) |
| TD-7 | Low | GitLab API drift is caught only offline against a hand-locked catalog (R5) | no | accepted (same as Jira) |
| TD-8 | Low | String booleans and enums are not schema-validated (R6) | no | accepted (documented) |
| TD-9 | Low | Pinned inventory lists in existing tests change with each new example collection (R7) | no | accepted (deliberate) |
| TD-10 | Low | Large or binary raw file responses (R8) | no | accepted; size cap is [PYPOST-753][] |
| TD-11 | Low | `.` / `..` as a whole file path, branch or SHA is not encoded | no | accepted (documented limitation) |
| TD-12 | Lowest | MCP metrics labelled by method only; tool name only in activity log | no | accepted (PYPOST-1038 decision) |
| TD-13 | Low | README parity regex covers only `get`/`list`/`create`/`update` verbs | no | accepted (fix with the next new verb) |
| TD-14 | Low | Loopback stub and catalog checks partly duplicate the Jira test helpers; 1311-line test module | no | accepted (two instances only) |
| TD-15 | Medium | `make lint` does not run flake8 on `tests/` (existing) | yes | [PYPOST-1303][] |
| TD-16 | — | Pre-existing test failures seen in this task's runs | yes | [PYPOST-1299][], [PYPOST-1320][] |

## Shortcuts Taken

- **TD-2 (Low) — blank project mitigated by placeholders, not by runtime checks (R2).** Every
  project-scoped URL is `.../projects/{{ urlencode(gitlab_project) }}/...`. A blank
  `gitlab_project` renders `/projects//issues` (GitLab answers 404). For `gitlab_get_project` it
  renders `/api/v4/projects/`, which GitLab may treat as "list projects", so the agent gets a
  wrong but harmless read-only answer. The design accepts this. The non-empty placeholder
  `your-group/your-project` is set in the environment, the `gitlab_com` preset and the manifest
  default (all test-enforced). The tool descriptions and README tell the user to set it or pass
  the override. PyPost has no "required variable" or "empty path segment" fail-closed check for
  request rendering. Adding one is a core runtime feature and out of scope (requirements, "New
  PyPost runtime features"). Follow-up 1 below.
- **TD-4 (Low) — `Authorization: Bearer` instead of `PRIVATE-TOKEN` (R1).** GitLab documents
  both. Bearer was chosen because the sanitizer already masks `authorization` headers and Bearer
  tokens. Some proxies strip `Authorization`, and DPoP accounts need an extra header (out of
  scope). The README (`examples/README.md`, authentication section) documents the
  `PRIVATE-TOKEN` alternative. Switching is one header per request plus a test constant. No
  follow-up.
- **TD-8 (Low) — string booleans and enums (R6).** `membership`, `recursive` and `state_event`
  are plain `string` MCP params. The descriptions list the allowed values. A bad value gets an
  upstream 400 and is not rejected locally. The MCP param model has no enum support, so this
  is accepted. No follow-up.
- **TD-11 (Low) — dot segments.** `urlencode` is `quote(..., safe="")`, which leaves `.`
  unencoded. A `file_path`, `branch` or `sha` that is exactly `.` or `..` becomes a dot segment
  that HTTP stacks may normalise away. Git does not allow `.`/`..` as a branch name, a SHA is hex,
  and `.`/`..` is never a file, so in practice the input is never valid. Values such as `a.md`
  or `../x` (rendered `..%2Fx`) are not affected. Documented in `20-architecture.md` and the
  README. Fixing it needs a core `urlencode` change. No follow-up.
- **Hardcoded values (intentional, no debt):** `gitlab_base_url` default `https://gitlab.com`,
  placeholder project `your-group/your-project`, pagination defaults `page=1` and `per_page=20`,
  catalog `reviewed_on` `2026-10-09`, helper `_MAX_BODY_BYTES = 64 KiB` and the 2 s thread join,
  test timeouts 30/60 s and the 10 s per-call `fail_after`. Each one is a documented example
  default or a bounded test limit.
- **Deviations from the architecture:** none. The 25 tools, paths, encodings, auth header,
  manifest and preset entries, catalog and Make target all match `20-architecture.md`. The only
  fixes made during review (manifest default, wire-layer AC3.3 proof, Makefile target test,
  narrowed README regex) were folded back into the design before Step 4.

## Code Quality Issues

- **TD-6 (Low) — body templates (R4).** Each optional JSON field repeats the full guard
  `{% if mcp is defined and mcp.request is defined and mcp.request.X is defined and
  mcp.request.X is not none %}` and uses a `namespace` separator. The opening brace has to be
  written `{ ` (brace and a space) before the first `{% if %}`. Without the space, `{{%` would
  be read as the start of a Jinja expression. This is brittle when edited by hand. It is
  mitigated by tests that render the all-args, minimal and each-single-optional subsets and
  `json.loads` each one, and by the "no surviving `{{`/`{%`" assertions. A cleaner fix would be
  a core "build JSON object from present args" helper. That is a runtime feature and out of
  scope. Accepted, no follow-up.
- **TD-13 (Low) — README parity regex.** `test_gitlab_readme_documents_inventory_and_tool_parity`
  extracts tool names with `\bgitlab_(?:get|list|create|update)_[a-z_]+`. It was narrowed on
  purpose so that `gitlab_mcp`, `gitlab_project` and `gitlab_token` prose does not match. It
  covers all 25 current tools (9 get, 10 list, 4 create, 2 update). A future tool with another
  verb (`search`, `retry`, `merge`, …) would be missed by the README parity check. The locked
  25-tool spec table in the same module must change anyway when a tool is added, so whoever
  adds the tool also widens the regex. Accepted, no separate follow-up.
- **TD-14 (Low) — test helper duplication and module size.**
  `tests/helpers/gitlab_mcp_collection_http.py` follows the same loopback-stub pattern as
  `tests/helpers/mcp_collection_http.py` (Jira). The catalog-drift checks repeat the shape of the
  Jira path-freshness test. `tests/test_gitlab_mcp_collection.py` has 1311 lines. With only two
  provider collections, extracting a shared "MCP example collection contract" helper would be
  premature (rule of three). Accepted. Revisit when a third provider collection is added.
- **TD-9 (Low) — inventory churn (R7).** `tests/test_examples_modernization.py` and
  `tests/test_predefined_library_pypost_1281_repro.py` pin the exact collection list and counts.
  Each new example collection has to edit them. This is deliberate, because the change shows up
  in review. Accepted.

## Missing Tests

- **No live GitLab test.** All checks are offline: fixture contract, wire capture on a loopback
  stub, and catalog lock. A live opt-in smoke (like `make test-jira-mcp-live`) is explicitly out
  of scope (requirements, "Out of scope"). See "Possible Future Enhancements".
- **API drift (TD-7, R5).** `make check-gitlab-mcp-path-freshness` only proves that the
  collection matches the locked catalog. Whether the catalog still matches GitLab REST v4 depends
  on a person re-reviewing `doc_refs` and bumping `reviewed_on`. Nothing flags a stale
  `reviewed_on` date. The Jira catalog works the same way, so this is accepted.
- **Blank `gitlab_project` at runtime (TD-2).** Not tested as fail-closed, because the behaviour
  does not exist. Only the placeholder defaults are tested.
- **`PRIVATE-TOKEN` alternative.** Documentation only. The test enforces Bearer and rejects
  `PRIVATE-TOKEN` (mutation twin), as designed.
- **Dot segments (TD-11).** Not tested. This is a documented, unsupported input.
- **Lint coverage of tests.** `make lint` runs flake8 on `pypost/` only, so the new test modules
  were checked by hand in Step 5. Already tracked: [PYPOST-1303][] (TD-15). Do not re-file.

Otherwise none. All 25 tools are covered for import, published tool set, params, headers,
bodies, encoding, numeric-ID rejection, reserved query characters on the wire, catalog parity,
manifest, README parity, secret scan and the Makefile target.

## Performance Concerns

- **TD-10 (Low) — large raw file responses (R8).** `gitlab_get_file` returns raw file bytes as
  text, and large blobs count against GitLab rate limits. The generic response-size cap and
  `response_body_truncated` handling exist ([PYPOST-753][]). Binary content arrives as decoded
  text. The README says only that the tool "returns the raw file content" and does not warn
  about binary or very large files, which is a small documentation gap that Step 8 can close.
  No artifact or job-log download tools are included. Accepted.
- **TD-12 (Lowest) — metric granularity.** `record_mcp_call_outcome` metrics are labelled by
  MCP method only. The GitLab tool name appears only in the activity log. This follows the
  PYPOST-1038 decision not to add per-tool or other high-cardinality labels. Accepted, no
  follow-up.

Otherwise none. Rendering is per call. Pagination is explicit (`page`/`per_page`) with no
auto-pagination.

## Follow-up Tasks

New follow-ups, filed in Jira via jira-create-issue (estimated):

1. **TD-2 — Fail-closed rendering for blank path-segment variables** (Low)
   Jira: [PYPOST-1332](https://pypost.atlassian.net/browse/PYPOST-1332)
   Add an opt-in runtime guard (for example a manifest/environment `required: true` honoured at
   request render, or a check that rejects an empty rendered path segment such as `//`). A blank
   value like `gitlab_project` would then fail before dispatch with a clear MCP error, instead of
   hitting `/projects//…` or the list-projects endpoint. Generic: it also helps `jira_project_key`.
   Runtime feature, so it is out of scope for PYPOST-1316.
2. **TD-1 — Sanitize rendered URLs in the remaining HTTP/retry log events** (Low)
   Jira: [PYPOST-1333](https://pypost.atlassian.net/browse/PYPOST-1333)
   `http_client` `sse_stream_detected` (`url=%s`) and `request_service` `retryable_error` /
   `retry_exhausted` log the rendered URL without sanitizing it. The retry events do so through
   `exc.message` (`Request to {url} timed out.` / `Could not connect to {url}.`). Route these
   through the same bounded origin sanitizer used by the transport ERROR paths. Not a GitLab
   secret leak (the token is only in `Authorization`), but URLs can carry query secrets for
   other collections. Pre-existing and generic. Can be merged into [PYPOST-1122][] when it is
   ticketed, since that issue covers the sibling `response_body_truncated` event.

Existing tickets referenced (do not re-file):

- [PYPOST-1122][] — `response_body_truncated` logs the resolved URL (TD-3).
- [PYPOST-1303][] — `make lint` does not flake8 `tests/` (TD-15).
- [PYPOST-753][] — response body size cap (context for TD-10).

Pre-existing test failures seen in this task's runs (Step 4 full `make test`):

1. `NON-BLOCKER — pre-existing` — [PYPOST-1299][]
   `tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing`
2. `NON-BLOCKER — pre-existing` (flaky) — [PYPOST-1320][]
   `tests/test_collection_import_teardown_repro.py::test_unexpected_reader_exception_requires_teardown_and_reaps_worker`
   (worker timeout 120 s inside `process_until`; failed 2/3 alone on this tree and 1/3 at base
   `811fde38`)

Related, no action for this task: PYPOST-1326 (live logging) and PYPOST-1328 (cancellation log
stage) cover unrelated subsystems. None of the items above duplicate them.

### Possible Future Enhancements (not debt; no ticket proposed)

These are the GitLab capabilities that the requirements explicitly put out of scope. They are
listed for product planning only and are not debt of this change:

- Destructive or privileged operations: deletes, MR approvals, merge/rebase, pipeline
  trigger/retry/cancel, repository file writes or commits, releases, wikis, admin APIs.
- Job log or artifact download (would need streaming or size handling, see TD-10).
- GitLab GraphQL API and OAuth flows, including DPoP.
- An opt-in live smoke target (analog of `make test-jira-mcp-live`) to detect API drift (TD-7).

## Validation

- `make verify-ai-tasks` — exit 0, "ai-tasks artifacts baseline OK (397 completed tasks; 2
  grandfathered legacy gaps)"

[PYPOST-753]: https://pypost.atlassian.net/browse/PYPOST-753
[PYPOST-1122]: https://pypost.atlassian.net/browse/PYPOST-1122
[PYPOST-1299]: https://pypost.atlassian.net/browse/PYPOST-1299
[PYPOST-1303]: https://pypost.atlassian.net/browse/PYPOST-1303
[PYPOST-1320]: https://pypost.atlassian.net/browse/PYPOST-1320
