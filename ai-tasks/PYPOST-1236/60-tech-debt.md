# PYPOST-1236: Technical Debt Analysis

## Scope and conclusion

The implementation is limited to AST-based regression coverage in the two ownership test
modules. No production code, public API, runtime behavior, logging, metrics, or dependency
configuration changed. No Step 7 blockers were identified.

## Blockers

- None identified.
- Both in-scope pytest modules declare an explicit 10-second module timeout. The tests do not
  use unbounded waits, retries, external services, or GUI event loops.

## Shortcuts Taken

- NON-BLOCKER — Synthetic source mutants are assembled as small in-memory Python strings. This is an
  intentional, bounded test seam rather than a production shortcut; it keeps the ownership
  checks independent from Qt runtime setup.
- NON-BLOCKER — The existing aggregate ownership test was retained while its checks were extracted into
  private assertion helpers. This minimizes behavioral change but leaves the helper names as a
  structural test interface.

None of these shortcuts blocks PYPOST-1236 acceptance.

## Code Quality Issues

- NON-BLOCKER — The AST checks are coupled to the current function names, import path, `__all__` manifest, and
  `ItemDataRole.DisplayRole` source shape. A future production refactor that preserves behavior
  but changes these structures will require coordinated test updates.
- NON-BLOCKER — The independent repro imports the ownership test module and monkeypatches its private `_parse`
  seam. This is appropriate for the current architectural test, but the private seam is not a
  stable project API.
- NON-BLOCKER — The four diagnostic constants include condition-specific source wording. If the production
  implementation or naming convention changes, the diagnostics and mutant fixtures must be
  updated together.

None of these code-quality issues blocks PYPOST-1236 acceptance.

## Missing Tests

- NON-BLOCKER — No task-specific scenario is missing for AC-1, AC-2, or AC-4: each has an independent mutant,
  expected diagnostic, and compliant control case.
- NON-BLOCKER — The suite does not execute real lookup behavior or Qt model instances. That is intentional for
  this task because the contract under test is static ownership, and runtime lookup coverage is
  outside scope.
- NON-BLOCKER — No timeout-marker gap was found in the changed test modules.

None of these missing-test items blocks PYPOST-1236 acceptance.

## Performance Concerns

- NON-BLOCKER — None material. The tests parse small source strings in memory and avoid GUI startup, network
  access, and production-module execution.
- NON-BLOCKER — The AST traversal helpers walk each small function/module repeatedly. This is negligible for the
  fast suite; caching or consolidating traversals would be an optimization only if the ownership
  matrix grows substantially.

None of these performance concerns blocks PYPOST-1236 acceptance.

## Pre-existing Test Failures

- NON-BLOCKER — pre-existing: Jira [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261)
  tracks the failures below. They are outside PYPOST-1236's test-only diff and were not caused by
  this implementation. Repro command: `make test`. Base commit:
  `b09b86ada34b992fa9844b29ab4ccd7742f52941`.

  Exact node IDs / process-level failure and captured last output:
  - `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_malformed_nested_expressions`
    ```text
    E       AssertionError: assert 'invalid_arity' == 'invalid_argument'
    E         - invalid_argument
    E         + invalid_arity
    =========================== short test summary info ============================
    FAILED tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_malformed_nested_expressions
    ```
  - `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_standalone_malformed_closing_paren`
    ```text
    E       AssertionError: assert 'invalid_arity' == 'invalid_argument'
    E         - invalid_argument
    E         + invalid_arity
    =========================== short test summary info ============================
    FAILED tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_standalone_malformed_closing_paren
    ```
  - `tests/test_environment_list_widget.py::<module>` — parallel worker SIGSEGV exit `-11`, so
    node attribution was unavailable.
    ```text
    test_file_failed file=tests/test_environment_list_widget.py exit_code=-11
    =========================== short test summary info ============================
    FAILED tests/test_environment_list_widget.py::<module> - worker exited with exit code -11
    ```
  - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
    ```text
    E       AssertionError: assert 241 == 260
    E         - 260
    E         + 241
    =========================== short test summary info ============================
    FAILED tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics
    ```
  - `tests/test_template_service.py::TestTemplateServiceValidationOutcomes::test_validate_malformed_nested_alignment`
    ```text
    E       AssertionError: assert 'invalid_arity' == 'invalid_argument'
    E         - invalid_argument
    E         + invalid_arity
    =========================== short test summary info ============================
    FAILED tests/test_template_service.py::TestTemplateServiceValidationOutcomes::test_validate_malformed_nested_alignment
    ```
  - `tests/test_template_service.py::TestTemplateServiceObservability::test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover`
    ```text
    E       AssertionError: assert 'invalid_arity' == 'invalid_argument'
    E         - invalid_argument
    E         + invalid_arity
    =========================== short test summary info ============================
    FAILED tests/test_template_service.py::TestTemplateServiceObservability::test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover
    ```

  Evidence: resolver/template cases expected `invalid_argument` but returned `invalid_arity`;
  environment widget exited with SIGSEGV; solid-audit snapshot expected `260` but measured `241`.
  Suspected causes are parser error-classification drift, Qt teardown/process interaction, and a
  stale audit snapshot respectively; root causes remain uninvestigated.

## Follow-up Tasks

1. NON-BLOCKER — pre-existing: investigate and resolve the failure cluster tracked by
   [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261) before relying on a fully green
   repository quality gate.
2. NON-BLOCKER — consider introducing a small shared AST-test utility if additional ownership
   contracts need the same source-mutant and diagnostic pattern; avoid broadening this task's
   scope unless the matrix grows.
3. NON-BLOCKER — update the ownership fixtures and diagnostics together if future refactoring
   changes the inspected function names or source-level ownership representation.

None of these follow-up tasks blocks PYPOST-1236 acceptance; they are separate future work.

## Validation

- `make lint` — passed.
- `make test PYTEST_ARGS='tests/test_display_role_scan_ownership.py
  tests/test_display_role_scan_ownership_independent_repro.py'` — passed.
- `make verify-ai-tasks` — passed.
- No production or test files were changed during Step 7.
