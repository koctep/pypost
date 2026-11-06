# PYPOST-1345: Technical Debt Analysis

Parent debt: [PYPOST-1334](https://pypost.atlassian.net/browse/PYPOST-1334) TD-16.
Scope closed by this task: path-aware empty-body stub replies (`/rerun`→201,
`/cancel`→202, `/dispatches`→204) plus MCP success assertions in
`tests/test_github_mcp_collection.py`. No production `pypost/` changes.

## Shortcuts Taken

- **Suffix-only stub matching.** Empty-body replies key off `path.endswith("/rerun"|
  "/cancel"|"/dispatches")` rather than full Actions REST path shapes. Good enough for
  the offline GitHub collection suite (paths are under
  `/repos/{owner}/{repo}/actions/...`), but a future stub consumer that ends an unrelated
  path with those tokens would get empty-body statuses unintentionally.
- **Re-run omitted from wire-capture loopback.** Architecture allowed either extending
  `_LOOPBACK_CALLS` or a dedicated guard. Step 4 kept
  `test_github_mcp_loopback_e2e_wire_contract`’s captured method/path/body tuples
  unchanged and covered `github_rerun_workflow_run` only via
  `test_github_mcp_empty_body_write_success`. Cancel/dispatch empty-body success is
  therefore exercised twice (loopback e2e + dedicated test); re-run wire capture is not.
- **`expect_empty_body=expected_status != 200` in loopback.** The shared helper accepts an
  explicit flag, but `_run_loopback_calls` derives empty-body expectation from
  “status is not 200”. Correct for today’s `_LOOPBACK_CALLS` (200+JSON vs 202/204 empty),
  fragile if a future loopback call expects a non-200 *with* a body (e.g. dispatch
  `return_run_details` → 200+JSON is still 200 today; a hypothetical 201+JSON would be
  mis-flagged).
- **Status map duplicated.** `_EMPTY_BODY_SUCCESS_BY_SUFFIX` in the stub helper and
  `_EMPTY_BODY_WRITE_CASES` / `_LOOPBACK_CALLS` expected statuses in the test module are
  hand-kept in sync. Acceptable for three fixed GitHub docs values; drift would only
  show up as a red suite, not a compile-time check.
- **No injectable stub reply policy.** Reply map is hard-coded in the helper (architecture
  allowed hard-coded vs injectable). Keeps the fixture small; blocks tests that need a
  dual mode (e.g. force 200+JSON on `/dispatches` without a second stub).
- **Shared stub extraction deferred.** Intentionally not folded into
  [PYPOST-1340](https://pypost.atlassian.net/browse/PYPOST-1340); local GitHub helper only.

## Code Quality Issues

- **Fixture boilerplate duplicated.** `test_github_mcp_empty_body_write_success` rebuilds
  the same `live_mcp_server` + variable/hidden/overridable suppliers block as the
  loopback e2e test. A small shared setup helper would shrink noise if more MCP+stub
  cases land.
- **Unused capture in the dedicated guard.** The empty-body test opens
  `stub_github_mcp_collection_http` as `stub` only for `base_url`; it does not assert
  captured method/path (re-run wire shape is therefore unchecked). Harmless, but the
  binding invites a follow-up assertion or a rename to `_`.
- **Heuristic empty-body flag** (see Shortcuts) should eventually be an explicit third
  column or named flag on `_LOOPBACK_CALLS` if that table grows beyond JSON-200 vs
  empty non-200.
- **Timeouts are present (not a blocker).** Module `pytestmark = pytest.mark.timeout(30)`;
  empty-body and loopback e2e tests override with `@pytest.mark.timeout(60)`; per-call
  `anyio.fail_after(_LOOPBACK_CALL_TIMEOUT_SECONDS)` remains. Meets do-testing mandatory
  timeout markers.

## Missing Tests

- **No negative / misclassification stub case.** Nothing asserts that a *wrong* stub reply
  (e.g. 200+JSON on `/cancel`) fails the empty-body guard — only the happy path is locked.
  Acceptable: the dedicated test would fail if the stub map or helper regresses to
  always-200; an explicit “assert would fail on old stub” is not required for DoD.
- **No re-run row in wire-capture e2e.** Path, query, and body for
  `POST …/actions/runs/{id}/rerun` are not in
  `test_github_mcp_loopback_e2e_wire_contract`’s expected capture lists. Request-body
  shape for re-run is covered elsewhere
  (`test_github_cancel_and_rerun_send_json_object_bodies`); only the empty-body *response*
  path is new here.
- **Dispatch `return_run_details` / 200+JSON.** Explicitly out of scope (PYPOST-1341 /
  TD-3+4). Collection still pins default empty-body 204.
- **Production classifier unit tests.** Out of scope by requirements; runtime empty-body
  success already implemented. This debt only adds the offline MCP regression gate.
- **Ambiguous suffix collisions.** No test that a non-Actions path ending in `/cancel`
  (etc.) would be mishandled — low risk given stub consumers and URL construction.

Covered by this task (DoD): parametrized MCP calls for re-run 201, cancel 202, and
dispatch 204 with `isError is False`, envelope `error is False`, expected status, and
`body == ""`, through `live_mcp_server` + the path-aware stub.

## Performance Concerns

- **Per-parameter MCP server spin-up.** Each of the three empty-body cases starts a fresh
  stub + `live_mcp_server` (same pattern as other loopback tests). Cost is bounded by the
  60s pytest timeout and 10s per-call `fail_after`; no suite-level concern for three cases.
- **No production hot path change.** Stub and test-only; no latency/metrics impact on
  shipping MCP servers.

## Follow-up Tasks

Low-priority cleanup from this implementation (do **not** block PYPOST-1345 close-out;
Jira filing deferred — orchestrator / tech-debt sync owns ticket creation):

1. Optionally add `github_rerun_workflow_run` to `_LOOPBACK_CALLS` (and extend wire-capture
   expectations) so all three empty-body writes share one e2e table.
2. Replace `expect_empty_body=expected_status != 200` with an explicit per-call flag if
   `_LOOPBACK_CALLS` gains non-empty non-200 replies.
3. Consider a single source of truth for suffix→status if more empty-body GitHub writes
   are added, or when merging into the shared stub work ([PYPOST-1340][]).

### Suite triage (NON-BLOCKER — pre-existing / flaky)

Recorded during Step 4 full-suite runs. Not caused by PYPOST-1345 (scoped
`test_github_mcp_collection` empty-body + loopback e2e green). Do not re-file clusters
that already have keys.

| Test ids | Verdict | Jira |
| --- | --- | --- |
| `tests/test_bundled_examples_packaging.py::test_explicit_packages_cover_application_tree_and_examples`; `tests/test_makefile_install_seed_contract.py::test_committed_seed_covers_independent_source_inventory` | NON-BLOCKER — pre-existing (already filed; same cluster as prior sprints) | [PYPOST-1474](https://pypost.atlassian.net/browse/PYPOST-1474) |
| `tests/test_pypost_1077_verification_votes.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`; `tests/test_pypost_1287_failing_repro.py::test_live_report_inventory_loc_matches_discovery` | NON-BLOCKER — pre-existing | [PYPOST-1475](https://pypost.atlassian.net/browse/PYPOST-1475) |
| `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift` | NON-BLOCKER — pre-existing / env drift | [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397) |
| `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics` | NON-BLOCKER — pre-existing | [PYPOST-1492](https://pypost.atlassian.net/browse/PYPOST-1492) |
| `tests/test_mcp_stdio_harness.py::test_harness_stderr_collection` | NON-BLOCKER — flaky (already filed) | [PYPOST-1493](https://pypost.atlassian.net/browse/PYPOST-1493) |
| `tests/test_mcp_process_isolation_repro.py::test_process_mode_variable_isolation_under_concurrent_load` | NON-BLOCKER — flaky (failed in parallel `make test`; passed solo re-run at base `6931e4dd`) | [PYPOST-1508](https://pypost.atlassian.net/browse/PYPOST-1508) |

[PYPOST-1340]: https://pypost.atlassian.net/browse/PYPOST-1340
