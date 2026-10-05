# PYPOST-1289: Technical Debt Analysis

## Shortcuts Taken

No temporary implementation or architecture deviation was identified. The presenter owns the
session-end guard, invalidates callbacks and clears the session before best-effort emission.
The workspace injects the configured tracker and closes sessions on all required teardown routes.

The following are intentional contract limits, not deferred implementation:

- The counter represents a connected tab session, not each transport opened for an operation.
- Metrics failures can lose an increment; cleanup proceeds and emits a bounded warning without
  exception contents. Retrying could double-count and is not part of this observability contract.
- Current Refresh and Invoke failures remain nonterminal. The `error` reason is tested at the
  central release boundary; there is no new production terminal-error transition to wire.
- Aggregate counts do not measure individual session durations, as explicitly excluded in scope.

## Code Quality Issues

No new code-quality debt requiring a follow-up was identified. Tracker methods follow the existing
protocol and forwarding conventions. Callers supply fixed reason literals (`user`, `teardown`);
the release boundary also supports `error`. The `str` interface follows the accepted architecture;
future callers must preserve its three-value contract rather than pass external input as labels.
There are no new configurable constants or magic thresholds requiring extraction.

The changed LOC snapshot entries reflect the implementation; their caps were not raised. The
snapshot mismatch found during Step 4 was fixed and its focused checks passed. It is resolved,
not a remaining baseline failure or a reason to open a duplicate ticket.

## Missing Tests

No missing test was identified for the accepted task scope. Presenter regressions cover repeated
release, reconnect, teardown, terminal-error classification, cancelled/failed Connect,
nonterminal errors, stale callbacks, and tracker failure with continued cleanup. Workspace tests
exercise the button, F5, tab close, profile deletion, application teardown, and declined closure.
Backend tests inspect Prometheus samples and OTel attributes, Qt forwarding, and disabled metrics.

Both touched modules have explicit timeout markers: `test_mcp_client_presenter.py` uses 10 seconds
and `test_mcp_client_disconnect_metrics.py` uses 30 seconds. No new unbounded polling, event-loop
wait, or missing-timeout blocker was identified. Deliberate error paths assert captured logs.
Tests simulate session settlement without a live server; this matches the presenter-owned session
contract and does not claim live network integration coverage.

## Performance Concerns

No new performance debt was identified. Release adds a constant-time state check and one counter
increment; metric cardinality is limited to the three caller-owned reasons. Application teardown
uses the existing tab iteration. The change adds no retries, polling, or per-session storage.

## Follow-up Tasks

No new Jira issue is warranted for this implementation. The following existing failures remain
**NON-BLOCKER — pre-existing**, using the baseline classification and existing issue coverage
confirmed by the orchestrator in the roadmap. This step reviewed the existing evidence; it did
not repeat baseline tests or independently create that classification.

The Step 4 reproduction command was `make check`; its output is in
`/tmp/pypost-1289-step4-check.log` (run `2df802db3d7a`). It reported 337 passing, 8 failing and
6 skipped test files, before the task-related LOC snapshot correction. For readable node IDs
below, concatenate each file, optional class, and test name with `::`, without whitespace.

### Malformed-expression classification

**NON-BLOCKER — pre-existing**; Jira:
[PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261).

- File: `tests/test_function_expression_resolver.py`.
  Class: `TestFunctionExpressionResolver`.
  Tests: `test_malformed_nested_expressions`, `test_standalone_malformed_closing_paren`.
- File: `tests/test_template_service.py`.
  Class: `TestTemplateServiceValidationOutcomes`.
  Test: `test_validate_malformed_nested_alignment`.
- File: `tests/test_template_service.py`.
  Class: `TestTemplateServiceObservability`.
  Test: `test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover`.

The assertions expect `invalid_argument` but receive `invalid_arity`; the observability case
also receives the wrong code in `track_template_expression_validation_failure`. Follow-up:
resolve malformed-expression classification and its validation-metric expectations in PYPOST-1261.

### Dialog inventory

**NON-BLOCKER — pre-existing**; Jira:
[PYPOST-1287](https://pypost.atlassian.net/browse/PYPOST-1287).

- File: `tests/test_pypost_1077_verification_artifacts.py`.
  Test: `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`.

The report fails the nine-module/1,790-LOC assertion, the `mcp_servers_dialog.py` 486-LOC
expectation, and inventory consistency. Follow-up: reconcile discovery and recorded aggregates
under the existing issue.

### WebSocket stream export

**NON-BLOCKER — pre-existing**; Jira:
[PYPOST-1286](https://pypost.atlassian.net/browse/PYPOST-1286).

- File: `tests/test_websocket_stream_view_repro.py`.
  Test: `test_stream_view_transcript_export_actions`.

The text-file predicate remains false after 10,000 ms. The log records
`websocket_stream_export_skipped reason=busy format=text` while JSON export completes.
Follow-up: correct export sequencing and verify both outputs in the existing issue.

### Makefile and exit-policy worker timeouts

**NON-BLOCKER — pre-existing**; Jira:
[PYPOST-1262](https://pypost.atlassian.net/browse/PYPOST-1262).

The full-check log reports these failed items at approximately 60 seconds each:

- File: `tests/test_makefile_lifecycle.py`; class: `TestMarkerLifecycle`.
  Test: `test_clean_removes_venv_and_marker`.
- File: `tests/test_makefile_targets.py`; class: `TestExitBehavior`.
  Test: `test_lint_succeeds_from_bare_venv_via_venv_test`.
- File: `tests/test_pytest_exit_policy.py`.
  Test: `test_make_test_fails_closed_when_parallel_runner_is_missing`.

All three file workers then hit the 120-second limit with exit code `-9`. The last active items
were, respectively, `TestMarkerLifecycle::test_venv_is_idempotent`,
`TestTargetExecution::test_venv_test_installs_pytest_and_flake8`, and
`test_pytest_rewrites_exit_code_5_to_0_when_policy_is_warn`. These are interrupted items, not
independently diagnosed assertion failures. The unchanged-tree rerun reproduced all three worker
timeouts; the roadmap records that PYPOST-1262 already includes exit-policy baseline evidence.
Follow-up: resolve Makefile/venv execution timeouts and restore complete worker results there.

## Validation and Handoff

The prior focused tests and typecheck remain applicable because Step 7 changes only task
documentation. No broad suite was repeated and no production or test file was edited. Developer
metrics documentation remains the planned Step 8 work, not a new debt ticket. Step 7 remains
in progress pending independent review and the subsequent blocker review.

Step 7 `make lint verify-ai-tasks` passed: Python lint, Markdown formatting, relative links, and
artifact verification (371 completed tasks; 2 grandfathered legacy gaps).
