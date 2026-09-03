# PYPOST-1252: Technical Debt Analysis

## Scope Reviewed

PYPOST-1252 is an artifact-only correction. The accepted scope is to synchronize the
source-authoritative dialog inventory with its executable contract and human-readable report:

- `settings_dialog.py` is recorded as 263 LOC instead of the stale 260 LOC.
- The nine-dialog aggregate is recorded as 1,790 LOC instead of the stale 1,787 LOC.
- `mcp_servers_dialog.py` remains 486 LOC and is outside the correction.

No production dialog code, runtime behavior, MCP behavior, or audit methodology changed.

## Shortcuts Taken

No production shortcut or implementation crutch was taken. The change updates only the directly
affected hardcoded expectation and audit-report records, preserving the existing discovery,
inventory, aggregate, and stale-claim checks.

The accepted tradeoff is that the audit contract still contains hardcoded frozen counts. A future
source line-count change can make the report and expectation stale until the inventory is
regenerated and the records are synchronized. The contract test exposes that drift; replacing
the frozen records with automatic regeneration is outside this Jira scope.

## Code Quality Issues

No new code-quality issue was introduced:

- No production Python code changed.
- No new abstraction, dependency, duplication, or error-handling path was added.
- The test and report edits are limited to the corrected `settings_dialog.py` count and aggregate.
- No architecture deviation was found; the existing source-discovery-to-contract pattern remains
  intact.

## Missing Tests

No task-specific test coverage is missing. The existing focused contract test verifies discovery,
inventory membership, aggregate coherence, the preserved MCP count, report wording, and stale
claims after the correction.

The focused test module declares `pytestmark = pytest.mark.timeout(10)`. No missing explicit test
timeout or unbounded wait was introduced by this task.

## Performance Concerns

None. The change does not execute in the application, does not alter dialog startup or rendering,
and does not change the inventory algorithm. The contract test continues to perform a small,
offline source/report comparison.

## Observability

No runtime logs, metrics, alerts, or monitoring integrations were added. The existing contract
failure remains the appropriate diagnostic when the source inventory and frozen records diverge.

## Full-Suite Failure Triage

The focused contract passed after the correction. The full `make check` run reported four failing
test files and six exact failing nodes. Each is a `NON-BLOCKER — pre-existing` failure from an
existing Jira issue and is unrelated to this artifact-only correction.

- `NON-BLOCKER — pre-existing`: `tests/test_function_expression_resolver.py::`
  `TestFunctionExpressionResolver::test_malformed_nested_expressions` — expected
  `invalid_argument`, got `invalid_arity`. Existing Jira: PYPOST-1261.
- `NON-BLOCKER — pre-existing`: `tests/test_function_expression_resolver.py::`
  `TestFunctionExpressionResolver::test_standalone_malformed_closing_paren` — expected
  `invalid_argument`, got `invalid_arity`. Existing Jira: PYPOST-1261.
- `NON-BLOCKER — pre-existing`: `tests/test_environment_list_widget.py::<module>` — parallel
  worker exited with SIGSEGV (`-11`); node attribution is unavailable. Existing Jira: PYPOST-1261.
- `NON-BLOCKER — pre-existing`: `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::`
  `test_markdown_snapshot_matches_current_metrics` — the frozen metrics snapshot differs from
  current measurements. Existing Jira: PYPOST-1261 (PYPOST-1111 is historical context for the
  earlier audit-baseline work).
- `NON-BLOCKER — pre-existing`: `tests/test_template_service.py::`
  `TestTemplateServiceValidationOutcomes::test_validate_malformed_nested_alignment` — expected
  `invalid_argument`, got `invalid_arity`. Existing Jira: PYPOST-1261.
- `NON-BLOCKER — pre-existing`: `tests/test_template_service.py::`
  `TestTemplateServiceObservability::test_render_malformed_nested_validation_failure_tracks_`
  `validation_metrics_on_hover` — expected metric code `invalid_argument`, got `invalid_arity`.
  Existing Jira: PYPOST-1261.

The corrected `tests/test_pypost_1077_verification_artifacts.py::`
`test_dialog_audit_report_has_full_discovery_and_coherent_aggregates` node passed and is not a
full-suite blocker. No unrelated failure was fixed, and no follow-up issue was created because
the remaining failures are already ticketed.

## Follow-up Tasks

No new follow-up task is required for PYPOST-1252. The hardcoded-count tradeoff is accepted for
this narrowly scoped record synchronization. The pre-existing parser, Qt worker, template, and
SOLID snapshot failures are tracked by PYPOST-1261 as listed above; PYPOST-1111 is retained only
as historical context.

## Validation Results

- `make test PYTEST_ARGS='tests/test_pypost_1077_verification_artifacts.py'` — passed; 1 file,
  4 tests.
- `make check` — lint and documentation checks passed; test summary was 322 passed, 4 failed,
  5 skipped. The nonzero result is caused only by the six pre-existing nodes listed above.
- `make verify-ai-tasks` — passed; AI-task artifact integrity is valid.

Step 7 remains in progress pending acceptance.
