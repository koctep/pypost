# PYPOST-1278: Technical Debt Analysis

## Shortcuts Taken

No task-specific shortcuts were accepted that weaken safety or correctness. The Library
Manager keeps compatibility seams for the older `GitLibraryService` callers while the
connection-based manager is adopted; this is intentional migration scaffolding rather than
a new behavior defect.

## Code Quality Issues

No new blocking code-quality issue was identified. The presenter still contains both the
manager-service and legacy-service branches required for compatibility, which increases
maintenance cost until legacy callers are migrated.

The manager now cleans up a cloned directory when manifest validation or durable registration
fails. Failure snapshots use the injected presenter/manager clock, so neither behavior remains
an unresolved task debt.

## Missing Tests

The focused PYPOST-1278 tests cover the new row model, status handling, connection lifecycle,
safe deletion, both clone-failure cleanup paths, async operation admission, observability, and
path redaction. The final full-repository gate was also run; its pre-existing failures are listed
below for provenance and remain outside this task's scope.

All changed Python test modules have explicit timeout markers. No timeout-marker blocker was
found.

## Performance Concerns

No unbounded task-specific performance issue was identified. Library status and Git work run in
bounded worker operations; list projection and filtering remain in-memory. The existing
recursive last-modified scan may become noticeable for very large local libraries and should
be profiled if that usage becomes common.

Two medium-priority optimization candidates remain documented for future profiling: each Git
status refresh performs a five-second remote health probe, and initial loading schedules a
refresh for every discovered connection. These are bounded and correct today, but a large
library set or slow remote could make refresh latency noticeable.

Failure-status timestamps now receive the injected clock, removing the earlier determinism
concern.

## Follow-up Tasks

No new follow-up Jira issue is required for PYPOST-1278. The compatibility branches,
large-library timestamp scan, five-second remote probe, and refresh-all-on-load behavior are
documented trade-offs with no observed task-specific failure; profile before filing further
work so any ticket is evidence-based.

The following are `NON-BLOCKER — pre-existing` baseline findings and must not be duplicated or
fixed as part of PYPOST-1278:

- `NON-BLOCKER — pre-existing` — [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261):
  `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_malformed_nested_expressions`
  (malformed nested-expression diagnostic alignment).
- `NON-BLOCKER — pre-existing` — [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261):
  `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_standalone_malformed_closing_paren`
  (malformed nested-expression diagnostic alignment).
- `NON-BLOCKER — pre-existing` — [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261):
  `tests/test_template_service.py::TestTemplateServiceValidationOutcomes::test_validate_malformed_nested_alignment`.
- `NON-BLOCKER — pre-existing` — [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261):
  `tests/test_template_service.py::TestTemplateServiceObservability::test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover`.
- `NON-BLOCKER — pre-existing` — [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261):
  `tests/test_environment_list_widget.py::<module>` (worker exit `-11` / Qt SIGSEGV).
- `NON-BLOCKER — pre-existing` — [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261):
  `tests/test_env_dialog.py::<module>` (one full-suite worker exit `-11` / Qt SIGSEGV;
  isolated rerun passed, so node attribution remains unavailable).
- `NON-BLOCKER — pre-existing` — [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261):
  `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
  (frozen audit snapshot differs from current metrics).
- `NON-BLOCKER — pre-existing` — [PYPOST-1262](https://pypost.atlassian.net/browse/PYPOST-1262):
  `tests/test_makefile_lifecycle.py::TestVenvExtraStampIdempotency::test_venv_test_installs_when_stamp_stale`
  (load-sensitive nested-Make timeout).
- `NON-BLOCKER — pre-existing` — [PYPOST-1262](https://pypost.atlassian.net/browse/PYPOST-1262):
  `tests/test_makefile_targets.py::TestTargetExecution::test_test_succeeds_from_bare_venv_via_venv_test`
  (load-sensitive nested-Make timeout).
- `NON-BLOCKER — pre-existing` — [PYPOST-1077](https://pypost.atlassian.net/browse/PYPOST-1077):
  `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
  (dialog discovery inventory does not match the frozen nine-module, 1,790-LOC baseline).

## Validation Results

- `make test PYTEST_ARGS='tests/test_ui_library_manager_pypost_1278_repro.py
  tests/test_ui_library_manager.py tests/test_ui_library_manager_repro.py -q'`: 3 files
  passed, 0 failed, 0 skipped.
- `make test PYTEST_ARGS='tests/test_metrics_otel.py tests/test_metrics_server_endpoint.py
  tests/test_lifecycle_observability.py -q'`: 3 files passed, 0 failed, 0 skipped.
- `make lint`: passed.
- `make typecheck`: passed the repository baseline gate; 180 known baseline errors remain.
- `make check`: the repository test run completed with 332 passed, 5 failed, and 6 skipped.
  The five failed files represent the two parser-alignment nodes, two template-alignment nodes,
  and the audit-snapshot node tracked by PYPOST-1261, the flaky `tests/test_env_dialog.py` module
  exit tracked by PYPOST-1261, and the PYPOST-1077 verification-artifact node; the isolated
  `tests/test_env_dialog.py` rerun passed. The separate `make lint` and `make verify-ai-tasks`
  gates passed.
