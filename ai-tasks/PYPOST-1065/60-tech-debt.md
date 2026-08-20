# PYPOST-1065: Technical Debt Analysis

## Shortcuts Taken

No shortcuts or temporary production solutions were introduced. The task adds four direct,
hermetic contract tests to the existing `tests/test_mypy_baseline.py` seam and makes no production
code changes.

The tests call the private `_format_new_report()` and `_format_fixed_report()` helpers directly.
This is intentional rather than a workaround: those pure helpers are the existing formatting
boundary, the surrounding `main()` function only coordinates filesystem, subprocess, argument,
and stream I/O, and the approved architecture explicitly selected direct helper verification.

## Code Quality Issues

No task-created code quality issue was found.

- The four explicit tests keep the partial-new, whole-key-new, partial-fixed, and whole-key-fixed
  business rules independently readable. Parametrizing them would save little code while making
  failures less diagnostic.
- Exact `list[str]` assertions deliberately couple the tests to the complete user-visible report
  contract, including headings, indentation, wording, occurrence counts, and line ordering.
- The repeated synthetic path, error code, and message are stable test fixtures, not production
  hardcoded configuration. Extracting them would add indirection without reducing maintenance.
- No production abstraction, dependency, or public API was added, and no architecture deviation
  occurred.

## Missing Tests

No required scenario remains uncovered. The task adds coverage for:

- a partially new error, including the accurate `N new of M total` qualifier;
- an entirely new key, including omission of the partial qualifier;
- ascending numeric line ordering from deliberately scrambled current input;
- a partially fixed error, including the accurate `N of M baselined` qualifier; and
- an entirely fixed key, including omission of the partial qualifier.

CLI-level formatting integration is intentionally outside this task's scope. `main()` passes the
pure helpers' returned lines to stderr without transforming them, so an additional subprocess or
filesystem-based test would duplicate the formatter assertions while adding environmental setup.

### Timeout audit

All four added tests are in `tests/test_mypy_baseline.py`, which declares the module-level marker
`pytestmark = pytest.mark.timeout(30)`. Therefore every changed test has an explicit timeout and
there is no timeout-marker blocker.

## Performance Concerns

None. The added tests use small in-memory record lists, invoke pure formatting helpers directly,
and perform no filesystem, network, subprocess, or GUI work. Production runtime and memory use are
unchanged.

## Architecture Deviations

None. The implementation follows the approved functional-core / imperative-shell architecture:
tests exercise the pure formatters directly and leave parsing, comparison, persistence, mypy
invocation, and CLI policy untouched.

## Hardcoded Values

No production hardcoded values were introduced. Synthetic file paths, line numbers, counts, error
codes, messages, and exact expected strings are purposeful examples defining the report contract.
The 30-second timeout is the repository's existing test-module policy and was not added or changed
by this task.

## Follow-up Tasks

No follow-up is required for PYPOST-1065 itself.

### NON-BLOCKER — pre-existing

The repository-wide validation failures reported during Step 5 are unrelated to this task's sole
code change in `tests/test_mypy_baseline.py` and are already tracked:

- `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
  and
  `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
  — audit-report and snapshot drift tracked by
  [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111).
- `tests/test_suite_qapp_alignment.py::test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication`
  — local `qapp` fixture policy drift tracked by
  [PYPOST-1110](https://pypost.atlassian.net/browse/PYPOST-1110).
- `make typecheck` reports mypy-baseline drift in existing production modules outside the task
  diff. The eight Qt overload errors and stale baseline entry are tracked by
  [PYPOST-1086](https://pypost.atlassian.net/browse/PYPOST-1086), which is the open sprint issue
  for making `make typecheck` exit 0; they are not a formatter-test defect. PYPOST-1111 tracks
  only the two audit-report and snapshot pytest failures listed above.

These findings are recorded for validation transparency only. They do not block PYPOST-1065 and
must not be treated as debt introduced by this task.
