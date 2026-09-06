# PYPOST-1279: Technical Debt Analysis

## Shortcuts Taken

No correctness or safety shortcut was accepted. The implementation deliberately retains the
existing file-import planner and persistence boundary, and reuses the existing library operation
metric rather than introducing a second telemetry system.

## Code Quality Issues

- `CollectionImportActions` now coordinates two source flows and linked refresh in one presenter
  action object. This preserves the existing lifecycle seams, but a future extraction could make
  source-specific state transitions easier to test independently.
- `LibraryCollectionImportService` accepts the existing manager through a deliberately loose
  boundary so it remains Qt-free and injectable. A future typed protocol would improve static
  guarantees once the library manager API settles.
- Linked refresh is synchronous from the presenter entry point. Source parsing is small and local
  today; a future large-library use case should move refresh through the existing worker boundary.

## Missing Tests

- The regression suite covers the service, presenter dispatch, cancellation, source safety, and
  multi-record Link refresh. Full interactive dialog rendering for every unavailable-library and
  mixed-error visual state remains a candidate for a future GUI-focused test.
- No task-specific timeout-marker gap was found; the new regression module has an explicit 30-second
  timeout marker.

## Performance Concerns

- Listing parses each manifest-declared file to produce display rows, and resolving parses selected
  files again to protect against stale selections. This favors correctness and source immutability;
  a cache could reduce repeated work for very large libraries after profiling.
- Copy/Link materialization deep-copies collection content. This is bounded by the selected
  collection size and is appropriate for isolation, but large bundles may warrant progress UI.

## Follow-up Tasks

No new follow-up Jira issue is required for this task. The items above are bounded, documented
trade-offs without a demonstrated production failure; ticketing should follow profiling or a
concrete UX requirement.

The following are `NON-BLOCKER — pre-existing` baseline findings and remain outside PYPOST-1279:

- `NON-BLOCKER — pre-existing` — [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261):
  malformed nested-expression diagnostic alignment nodes in
  `tests/test_function_expression_resolver.py` and `tests/test_template_service.py`.
- `NON-BLOCKER — pre-existing` — [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261):
  Qt file-level SIGSEGV risk in `tests/test_environment_list_widget.py::<module>` and
  `tests/test_env_dialog.py::<module>` (the latter has passed isolated reruns).
- `NON-BLOCKER — pre-existing` — [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261):
  frozen solid-audit metrics snapshot mismatch.
- `NON-BLOCKER — pre-existing` — [PYPOST-1262](https://pypost.atlassian.net/browse/PYPOST-1262):
  two load-sensitive nested-Make timeout nodes.
- `NON-BLOCKER — pre-existing` — [PYPOST-1077](https://pypost.atlassian.net/browse/PYPOST-1077):
  verification-artifact inventory mismatch.

## Validation Results

- Focused `make test` for the collection import, UI, and metrics files: 6 files passed.
- `make lint`: passed.
- `make typecheck`: passed the repository baseline gate; 180 known baseline errors remain.
- `make verify-ai-tasks`: passed before and during the final artifact validation.
- Complete `make check`: 334 files passed, 4 failed, and 6 skipped. The four failing files are
  pre-existing baseline findings: `tests/test_function_expression_resolver.py` (two malformed
  nested-expression alignment nodes), `tests/test_pypost_1077_verification_artifacts.py` (dialog
  inventory mismatch), `tests/test_solid_audit_baseline.py` (module-cap and metrics-snapshot
  mismatch), and `tests/test_template_service.py` (two malformed nested-expression alignment and
  observability nodes). No PYPOST-1279 test failed.

Exact pre-existing failing nodes from that run:

- `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_malformed_nested_expressions`
- `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_standalone_malformed_closing_paren`
- `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_audit_module_inventory_within_caps`
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
- `tests/test_template_service.py::TestTemplateServiceValidationOutcomes::test_validate_malformed_nested_alignment`
- `tests/test_template_service.py::TestTemplateServiceObservability::test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover`
