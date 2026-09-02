# PYPOST-1239: Technical Debt Analysis

PYPOST-1239 is a test/documentation contract. The implementation changes only
`tests/test_display_role_scan_ownership.py` and adds its focused discoverability
tests; no production code, public behavior, logging, metrics, dependencies, or
runtime architecture changed. **No new in-scope technical debt exists, and no
Step 7 blocker was identified.**

## Shortcuts Taken

- The independently written Step 3 source-contract test remains alongside the
  structured validator rather than being consolidated. This duplicates a small
  amount of source-shape logic, but it is an intentional defense-in-depth
  boundary: the original red repro must remain independent of the validator it
  later validates. No follow-up is required.
- The three assertion groups retain explicit target-specific comments and the
  `find_child` pair retains its two-helper layout. This is deliberate load-bearing
  repetition required by the accepted requirements, not an implementation
  shortcut to be removed.
- No production instrumentation was added because the observability artifact
  correctly identifies this as an offline test/documentation contract with no
  production runtime path.

## Code Quality Issues

- No unresolved lint, formatting, dead-code, or unrelated-refactoring issue was
  found in the in-scope implementation.
- The validator is private test infrastructure coupled to the current helper
  names, assertion shapes, target labels, and source regions. That coupling is
  intentional for a source-structure fitness function and matches the accepted
  architecture; it is a maintenance consideration, not new actionable debt.
- The validator and focused tests use separate private seams. This keeps the
  red repro independent, but means changes to the ownership suite may require
  coordinated updates in both test modules. No separate Jira issue is warranted
  for the current bounded contract.

### Hardcoded values

The fixed target table, marker labels, diagnostic codes, rationale keywords, and
`_LOCAL_PROXIMITY = 12` are hardcoded by design. They encode the static
PYPOST-1239 contract; deriving them from the source under test would permit the
guard to validate its own weakened expectations. These values are therefore not
technical debt.

## Missing Tests

- All acceptance-critical cases are covered: compliant real source; missing,
  detached, wrong-target, missing-intentionality, and incomplete-rationale
  mutations; deterministic aggregation/order; and protection against marker text
  in single- and multiline string literals.
- Both changed test modules declare `pytest.mark.timeout(10)`, so there is no
  explicit-timeout blocker under `do-testing` and no unbounded wait.
- The defensive `MISSING_ASSERTION_PAIR` and `INVALID_SOURCE` validator branches
  do not have dedicated focused tests. They are outside the required mutation
  contract, have stable fallback behavior, and are a low-value coverage
  opportunity rather than a blocker or new in-scope debt. Add cases only if the
  validator's defensive-input scope is expanded.

## Performance Concerns

No material performance concern was identified. The validator parses a small
in-memory Python source string and performs bounded AST/token scans; the focused
test run is well within the fast quality-gate boundary. It does not initialize
Qt, use a display server, access the network, retry, sleep, or write files.
Repeated parsing across focused mutation cases is linear and appropriate for a
test-side contract. No optimization follow-up is justified.

## Architectural Deviations

No material deviation from `20-architecture.md` was found. Source text and AST
locations are kept together, the three targets use a fixed table, diagnostics are
stable and target-ordered, and the validator accepts source text without
executing the inspected module. The developer-guide update is intentionally a
Step 8 deliverable, not missing Step 7 work. The observability artifact's N/A
conclusion remains correct.

## Follow-up Tasks

No new in-scope follow-up task should be created from this analysis. The minor
defensive-branch coverage opportunity above can be addressed if the validator's
scope grows; it does not justify a Jira issue now.

### NON-BLOCKER — pre-existing full-suite failures

The recorded full `make test` result from the preceding task's baseline audit
(base commit `b09b86ada34b992fa9844b29ab4ccd7742f52941`) contains six unrelated
failures. They are outside PYPOST-1239, do not touch its implementation or test
files, and are all tracked by Jira
[PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261). They are listed
for provenance only; **do not fix them or create issues here**.

- **NON-BLOCKER — pre-existing** —
  `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_malformed_nested_expressions`;
  expected `invalid_argument`, received `invalid_arity`.
- **NON-BLOCKER — pre-existing** —
  `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_standalone_malformed_closing_paren`;
  expected `invalid_argument`, received `invalid_arity`.
- **NON-BLOCKER — pre-existing** —
  `tests/test_environment_list_widget.py::<module>`; parallel worker exited
  with SIGSEGV, exit code `-11`, so more specific node attribution was
  unavailable.
- **NON-BLOCKER — pre-existing** —
  `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`;
  snapshot expected `260`, measured `241`.
- **NON-BLOCKER — pre-existing** —
  `tests/test_template_service.py::TestTemplateServiceValidationOutcomes::test_validate_malformed_nested_alignment`;
  expected `invalid_argument`, received `invalid_arity`.
- **NON-BLOCKER — pre-existing** —
  `tests/test_template_service.py::TestTemplateServiceObservability::test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover`;
  expected `invalid_argument`, received `invalid_arity`.

## Validation

- `make lint` — PASS; flake8, Markdown lint (16 files), and relative-link
  checks (18 files) passed.
- `make verify-ai-tasks` — PASS; 340 completed tasks verified with 2
  grandfathered legacy gaps.
- Focused `make test PYTEST_ARGS='tests/test_display_role_scan_ownership.py
  tests/test_display_role_scan_ownership_discoverability.py -q'` — PASS; 2
  files passed, 0 failed, 0 skipped, in 1.75 seconds wall-clock time.
- The focused test run for
  `tests/test_display_role_scan_ownership.py` and
  `tests/test_display_role_scan_ownership_discoverability.py` completed with
  both files passing.
- The prior cleanup artifact records that `make analyze` is unavailable because
  the repository has no `analyze` target; it was not run as part of this Step 7
  validation.
