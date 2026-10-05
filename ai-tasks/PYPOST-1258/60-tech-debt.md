# PYPOST-1258: Technical Debt Analysis

## Shortcuts Taken

- **In-process `main(argv)` execution vs subprocess invocation**:
  The unit test suite invokes `_baseline_metrics.main(argv)` and `_dialogs_inventory.main(argv)`
  directly in-process rather than launching child processes via `subprocess.run`. This was a
  deliberate shortcut to ensure high test execution speed (~2.0s total test runtime) and clean
  stream interception using pytest's `capsys` fixture. The trade-off is that true OS-level process
  isolation (e.g., shell quoting, environment variable inheritance, fresh interpreter state) is
  not exercised per test case.
- **Monkeypatching cap and inventory evaluation functions**:
  Testing failure and violation paths (`--check` returning code 1 with stderr diagnostics) relies
  on monkeypatching `check_caps`, `AUDIT_REPORT`, or `check_audit_report_covers`. This avoids
  mutating codebase files or generating synthetic filesystem defects on disk, but bypasses raw
  AST analysis and disk file traversal during simulated violation checks.

## Code Quality Issues

- **Dynamic script module loading via `importlib`**:
  `scripts/audit_baseline_metrics.py` and `scripts/audit_dialogs_inventory.py` reside in `scripts/`
  outside the installable `pypost` package hierarchy. As a result, tests in
  `tests/test_audit_scripts_cli.py` use `importlib.util.spec_from_file_location` to load scripts as
  modules dynamically. Exposing audit tools via structured console script entry points or a package
  utility namespace would eliminate manual importlib loading boilerplate.
- **Module-level global constants in scripts**:
  `scripts/audit_dialogs_inventory.py` references `REPO_ROOT` and `AUDIT_REPORT` as module-level
  globals. Testing missing-report branches required monkeypatching module globals rather than
  passing custom paths via CLI options or function arguments.
- **Zero task-caused production defects**:
  No production code in `pypost/` was modified; all changes are strictly isolated to dedicated unit
  test suites adhering to repository code quality and linting standards.

## Missing Tests

- **Subprocess-level CLI integration tests**:
  End-to-end process execution via `python scripts/audit_*.py` in isolated subshells is omitted.
  All CLI entry points, argument parsers, error branches, and exit codes are covered in-process.
- **Cross-platform path quoting tests**:
  Tests rely on `pathlib.Path` abstractions and do not explicitly test esoteric Windows shell
  quoting or mixed-delimiter paths.
- **Concurrency stress tests**:
  Simultaneous parallel invocation of scripts against identical filesystem targets is not tested,
  though the scripts are read-only except when writing specified export files.
- All functional requirements (FR-1 through FR-4), exit codes (0, 1, 2), and timeout markers
  (`@pytest.mark.timeout(30)`) are fully implemented and passing.

## Performance Concerns

- **Fast execution verified**:
  The entire dedicated test suite executes in ~2.06s wall-clock duration across 16 unit tests in
  `tests/test_audit_scripts_cli.py` and 3 contract verification tests in
  `tests/test_pypost_1258_failing_repro.py`.
- **Minimal resource consumption**:
  Tests execute in-process with minimal CPU and memory overhead, using lightweight `tmp_path`
  directories that are cleaned up automatically by pytest.
- No performance regressions or slow test bottlenecks were introduced.

## Follow-up Tasks

- Optional future refactoring: migrate audit scripts from standalone `scripts/` into a formal
  package namespace (e.g., `pypost.tools.audit`) with console script entry points.
- Pre-existing repository test failures and grandfathered gaps (outside PYPOST-1258 scope):
  1. **NON-BLOCKER — pre-existing — PYPOST-1249 / PYPOST-1261:**
     - Test: `tests/test_function_expression_resolver.py`
     - Node: `TestFunctionExpressionResolver::test_malformed_nested_expressions`
     - Node: `TestFunctionExpressionResolver::test_standalone_malformed_closing_paren`
     - Test: `tests/test_template_service.py`
     - Node: `TestTemplateServiceValidationOutcomes::test_validate_malformed_nested_alignment`
     - Node: `TestTemplateServiceObservability::test_render_malformed_nested_validation_failure`
       `_tracks_validation_metrics_on_hover`
     - Failure: Expression validator produces `invalid_arity` instead of `invalid_argument`.
  2. **NON-BLOCKER — pre-existing — Worker Exit:**
     - Test: `tests/test_environment_list_widget.py::<module>`
     - Failure: Parallel worker exited `-11` (SIGSEGV) after tests completed.
  3. **NON-BLOCKER — pre-existing — PYPOST-1241:**
     - Test: `tests/test_mypy_baseline.py`
     - Node: `TestMypyBaseline::test_baseline_scope_includes_core_models_and_ui`
     - Failure: Mypy baseline counter mismatch (189 declared vs 185 serialized entries).
  4. **NON-BLOCKER — pre-existing — PYPOST-1111 / PYPOST-1252:**
     - Test: `tests/test_pypost_1077_verification_artifacts.py`
     - Node: `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
     - Failure: Inventory does not match frozen nine-module/1,787-LOC expectation.
  5. **NON-BLOCKER — pre-existing — PYPOST-1111:**
     - Test: `tests/test_solid_audit_baseline.py`
     - Node: `TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
     - Failure: Frozen Markdown metrics snapshot differs from current repository metrics.
  6. **NON-BLOCKER — pre-existing — Grandfathered legacy gaps:**
     - 2 grandfathered legacy gaps verified in `make verify-ai-tasks`.

Zero unresolved BLOCKERS exist for PYPOST-1258. SAFE TO CLOSE.
