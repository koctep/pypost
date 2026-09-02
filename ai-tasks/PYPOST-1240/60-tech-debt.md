# PYPOST-1240: Technical Debt Analysis

## Scope and Evidence

Reviewed all current PYPOST-1240 artifacts:

- `00-roadmap.md`
- `10-requirements.md`
- `20-architecture.md`
- `40-code-cleanup.md`
- `50-observability.md`

Also reviewed the complete working-tree diff and the existing ownership repro tests. The
implementation diff is test-only: it retains two target assertion-message edits in
`tests/test_display_role_scan_ownership.py` and adds two source-inspection AST repros in
`tests/test_display_role_scan_ownership_repro.py`. No PYPOST-1240 synthetic mutant or
production module, runtime behavior, or application-facing API was added or changed.

The task's earlier validation record reports the focused PYPOST-1240 test as passing and
`make check` as failing only on the pre-existing baseline set described below.

## Shortcuts Taken

No production shortcut was taken. The scope is correctly limited to improving quality-gate
diagnostics.

The new regression tests inspect the ownership test's own source through the existing
`_parse_file`/AST pattern. They do not monkeypatch the parser, add a mutant, or execute a Qt
implementation; no test-harness coupling debt is introduced.

## Implementation-Specific Debt

No new implementation-specific debt was found. The two target messages remain localized in the
main ownership test, and the two new repros inspect those messages directly without changing
ownership logic or introducing a new harness.

## Missing Tests and Test/Maintenance Risks

### Targeted diagnostic repros (No debt)

The two new tests in `tests/test_display_role_scan_ownership_repro.py` use `_parse_file` and AST
inspection to locate the main ownership test's `find_tree_index_by_display_text` and
`_select_item_view` assertion messages. Each requires the symbol, correct owner module,
actionable remedy, and one-line message, so each fails before its corresponding message edit.
The existing five repro tests remain intact. No aggregate-coverage harness or new mutant is
required for this two-message fail-fast contract.

### Timeout and bounded-wait conclusion (No debt)

The module-level `pytestmark = pytest.mark.timeout(10)` in both ownership test modules covers all
tests, including the two new source-inspection repros. The new tests contain no event-loop or
blocking wait. The mandatory explicit timeout requirement is satisfied; no timeout blocker is
introduced.

### Runtime test coverage conclusion (No new debt)

No runtime behavior changed. The existing runtime coverage for tree lookup and UI selection
therefore remains the relevant coverage, and no Qt integration test is owed by this diagnostic-
only change.

## Performance Concerns

No new performance debt was found. The added tests parse the small ownership-test source file,
and the production lookup and selection paths are unchanged. No optimization or profiling
follow-up is suggested.

## Documentation Drift

### TD-4 — developer testing guidance describes the old guard surface (Resolved in Step 8)

Before Step 8, `doc/dev/testing.md` and `doc/dev/ui_actions.md` described the older five-test
repro set without the current diagnostic message contract. Step 8 synchronized both sections
with the two source-inspection repro names and focused Make command, and documents the
owner/remedy one-line contract. The documentation drift is resolved.

## Observability Debt

### No production observability debt

The changed surface is an existing `AssertionError` rendered by pytest in local and CI quality-
gate output. There is no new runtime failure path, request flow, metric, log event, trace, or
operational state to instrument. The source-inspection repros preserve the owner/remedy text as
a diagnostic-only contract, and the Step 6 conclusion that no production logging, metrics,
tracing, or telemetry is needed remains correct.

## Known Repository Baseline Failures

The earlier full-gate record reports `make check` with 319 files passed, 6 failed files, and 5
skipped. It had 8 failing nodes total: `tests/test_function_expression_resolver.py` and
`tests/test_template_service.py` each contributed two nodes, while the other four failed files
each contributed one. The PYPOST-1240 diff cannot cause these failures because it changes only
ownership-test source and does not touch the affected production, parser, audit, GUI, or
baseline files. They are `NON-BLOCKER — pre-existing` findings, not PYPOST-1240 implementation
debt.

### Existing cluster tracked by PYPOST-1261

The following six of the eight failing nodes, spanning four failed files, are already recorded
by [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261). The function-expression and
template-service files each contribute two nodes; the environment-list-widget and solid-audit
files each contribute one:

- `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_malformed_nested_expressions`
  — expected `invalid_argument`, received `invalid_arity`.
- `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_standalone_malformed_closing_paren`
  — expected `invalid_argument`, received `invalid_arity`.
- `tests/test_environment_list_widget.py::<module>` — parallel worker exited `-11` (SIGSEGV);
  node attribution was unavailable.
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
  — baseline snapshot expectation drift.
- `tests/test_template_service.py::TestTemplateServiceValidationOutcomes::test_validate_malformed_nested_alignment`
  — expected `invalid_argument`, received `invalid_arity`.
- `tests/test_template_service.py::TestTemplateServiceObservability::test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover`
  — expected the `invalid_argument` metric code, received `invalid_arity`.

Priority/impact: pre-existing, non-blocking for this task, but Medium repository-gate impact
because these failures reduce confidence in the full `make check` result. Suggested follow-up:
resolve or re-triage the existing PYPOST-1261 cluster; do not fix it in PYPOST-1240.

### Additional baseline failures in the Step 5 report

The Step 5 report also names the remaining two of the eight failing nodes, one in each of two
additional failed files not present in PYPOST-1261's six-node description:

- `tests/test_mypy_baseline.py::TestMypyBaseline::test_baseline_scope_includes_core_models_and_ui`
  — `error_count` was 189 while the serialized error list contained 185 entries.
- `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
  — dialog-audit inventory/LOC expectations are stale.

Both are pre-existing relative to PYPOST-1240. Jira search found existing related tracking:
[PYPOST-1241](https://pypost.atlassian.net/browse/PYPOST-1241) covers an earlier mypy-baseline
gate failure, and [PYPOST-1252](https://pypost.atlassian.net/browse/PYPOST-1252) covers the
dialog-audit expectation drift (with
[PYPOST-1259](https://pypost.atlassian.net/browse/PYPOST-1259) covering the broader
structural-parser follow-up).
No duplicate Jira issue was created. Suggested follow-up: confirm the current failure details
against those existing tickets and reopen or update an existing ticket if still applicable,
rather than creating a duplicate.

## Jira Actions

Read-only Jira checks were performed for PYPOST-1240, PYPOST-1261, and related baseline-failure
search results. No Jira issue was created, updated, commented on, or duplicated. The only new
items identified here are low-priority local maintenance/documentation follow-ups; the known
baseline failures already have existing Jira coverage.

## Conclusion

The PYPOST-1240 implementation is low risk and satisfies its diagnostic-only scope. The two
source-inspection repros cover the exact message contract without aggregate-coverage debt or
new test-harness coupling, and the documentation drift is resolved in Step 8. There is no
production behavior, performance, timeout, or observability debt. The known full-suite failures
are explicitly classified as `NON-BLOCKER — pre-existing` and are kept separate from the
PYPOST-1240 findings.
