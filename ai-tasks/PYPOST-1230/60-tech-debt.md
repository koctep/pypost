# PYPOST-1230: Technical Debt Analysis

## Scope and conclusion

This review covers the test-only extraction of `_wait_import()` from
`tests/test_collections_import_ui.py` into
`tests/helpers/collection_import_wait.py`, the migrated collection-import UI call sites, and the
focused contract tests in `tests/test_collection_import_wait_repro.py`.

The change introduces no production behavior or runtime dependency. The extraction is a net
maintainability improvement: the outcome-plus-idle predicate and bounded event-loop wait now have
one shared implementation, and the helper's timeout path has focused coverage. No blocker was
found. The follow-ups below are deliberately limited to risks that are useful to address later.

## Shortcuts Taken

- The helper accepts a presenter and reads the existing private
  `presenter._import_actions.is_busy()` surface. This preserves the original test behavior with a
  small diff, but couples shared test support to presenter internals.
- The existing 5-second default was retained as `_IMPORT_WAIT_MS` rather than introducing a new
  timeout configuration layer. This is an intentional test-only trade-off, not a production
  timeout guarantee.
- Migration was limited to the equivalent waits in `tests/test_collections_import_ui.py`.
  Cancellation, teardown, progress, and responsiveness tests have different lifecycle predicates
  and were not mechanically folded into this helper.

## Code Quality Issues

- **NEW — private presenter coupling (Low):** `wait_import()`'s `_ImportPresenter` protocol
  requires `_import_actions`, a private presenter attribute. A presenter refactor can break a
  shared test helper even when the import completion contract is unchanged. A stable test seam,
  explicit idle callback, or a public presenter lifecycle interface would remove this coupling.
- The helper keeps the existing `timeout_ms` integer API and delegates deadline enforcement to
  `process_until()`. That keeps ownership clear, but callers can still choose inconsistent timeout
  values. The current defaults are acceptable for this test-only helper and do not warrant an
  immediate ticket.

## Missing Tests

The focused tests cover the important new contract: an outcome becoming visible before the
presenter is idle does not release the wait, and an unmet condition fails within a bounded timeout
with diagnostic state. All migrated call sites retain their existing scenario assertions, and the
new test module declares an explicit timeout marker.

Remaining coverage opportunities are non-blocking:

- The shared helper's `presenter=None` compatibility path is exercised indirectly by the preserved
  API shape but has no dedicated focused test.
- There is no focused test that exercises a failure while collecting timeout diagnostics. The
  underlying `process_until()` contract already protects the timeout assertion from diagnostic
  callback failures.

These gaps are low-risk because they concern test-support diagnostics and compatibility paths, not
application behavior.

## Performance Concerns

No production performance concern was introduced. During a test wait, the helper evaluates the
caller predicate and `is_busy()` on the existing 10 ms `process_until()` polling cadence. The
5-second default is bounded and matches the former local helper. A suite-wide timeout budget or
polling optimization would be premature until broader helper reuse demonstrates a measurable cost.

## Architectural Deviations

The implementation follows the Step 2 design: collection-import test scenarios own outcome
predicates, `wait_import()` composes outcome and idle state, and `process_until()` owns Qt event
processing and the wall-clock deadline. No production module imports test support, and no public
presenter API was added. The only deviation from an ideal abstraction is the deliberate use of the
existing private `_import_actions` path noted above.

## Follow-up Tasks

### Actionable new follow-ups

1. **NEW — Low — decouple `wait_import()` from `_import_actions`**

   Introduce a stable test seam, such as an explicit `is_idle` callback or a public lifecycle
   observation method, and update the helper protocol and callers. Preserve the combined
   outcome-plus-idle contract while allowing presenter internals to change independently.
   This is not ticketed in this step; create a Jira Debt issue only if the seam is scheduled for
   broader presenter refactoring.

2. **NEW — Low — audit adjacent collection-import async waits**

   Review `tests/test_collection_import_async_gaps.py`,
   `tests/test_collection_import_progress.py`,
   `tests/test_collection_import_responsiveness.py`, and
   `tests/test_collection_import_teardown_repro.py`. Migrate only waits with the same
   outcome-plus-idle semantics to `wait_import()`; retain specialized worker, cancellation, and
   teardown waits. This avoids duplicate helper logic without conflating different contracts.
   No Jira issue is created in this step.

### Existing baseline issues — do not duplicate

These failures are outside PYPOST-1230 and already have Jira tracking. They are non-blockers for
this test-helper extraction; no new issues were created.

- **NON-BLOCKER — pre-existing — `PYPOST-1261`**
  - `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_malformed_nested_expressions`
  - `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_standalone_malformed_closing_paren`
  - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
  - `tests/test_template_service.py::TestTemplateServiceValidationOutcomes::test_validate_malformed_nested_alignment`
  - `tests/test_template_service.py::TestTemplateServiceObservability::test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover`
  - The existing issue also records the unrelated Qt environment-widget worker SIGSEGV, for which
    individual node attribution is unavailable.
  - Reproduction command recorded by the existing issue: `make test`.

- **NON-BLOCKER — pre-existing — `PYPOST-1262`**
  - `tests/test_makefile_lifecycle.py::TestVenvExtraStampIdempotency::test_venv_test_installs_when_stamp_stale`
  - `tests/test_makefile_targets.py::TestTargetExecution::test_test_succeeds_from_bare_venv_via_venv_test`
  - The existing issue records file-level worker timeouts and unavailable attribution for the
    remaining tests in those files.
  - Reproduction command recorded by the existing issue: `make test`.

## Validation

- `make verify-ai-tasks` is required for the task-artifact integrity check.
- `make lint` is required for Markdown and repository static checks.
- Focused helper tests and the broader collection-import tests passed during Steps 4–6.
- The full suite's five unrelated parser/audit/template failures remain covered by `PYPOST-1261`;
  the separate worker-timeout cluster remains covered by `PYPOST-1262`.
