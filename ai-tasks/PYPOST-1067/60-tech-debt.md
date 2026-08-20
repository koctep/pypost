# PYPOST-1067: Technical Debt Analysis

## Summary

The accepted PYPOST-1067 implementation introduces no blocker and no unticketed follow-up. The
production change is the approved minimal design, and the tests cover the configuration coupling,
escaping, overlap ordering, slash boundary, current paths, and downstream baseline behavior.

## Shortcuts Taken

None.

- The implementation derives the parser alternation directly from `MYPY_PATHS`; it does not add
  a second configuration source, temporary compatibility branch, fallback, or stub.
- Import-time compilation, source-level configuration, and the non-empty path tuple are approved
  architecture constraints rather than shortcuts.
- The hermetic test's AST-assisted source rewrite intentionally models a fresh CLI import after a
  maintainer changes configuration. It avoids mutating production module state at runtime.

## Code Quality Issues

No in-scope code-quality debt was identified.

- `_MYPY_PATH_RE` is private, derived once, and used directly by `_ERROR_RE`.
- Escaping and deterministic longest-first ordering are explicit and readable.
- Invocation order, named captures, parser results, baseline identity, and report formatting are
  unchanged.
- The test helper's `dict[str, Any]` return type is appropriately limited to the dynamic namespace
  returned by `runpy.run_path()`.
- There are no unused imports, debug branches, duplicated production logic, or dead code in the
  accepted diff.

## Missing Tests

None identified.

- A configured path extension is recognized without a second parser-scope edit.
- A prefix lookalike remains excluded by the slash boundary.
- Regular-expression metacharacters in configured paths are treated literally.
- Overlapping prefixes are ordered with the more specific path first.
- Existing parser, baseline comparison, reporting, update, and serialization coverage remains
  green in the 22-test mypy-baseline module.
- `tests/test_mypy_baseline.py` declares `pytestmark = pytest.mark.timeout(30)`, so there is no
  missing-timeout blocker.

## Performance Concerns

None.

Sorting the small static tuple is `O(n log n)` and escaping/joining is linear in the total path
length. Both happen once at import and are negligible compared with starting and running mypy.
The compiled regex continues to be reused for every output line.

## Architecture Deviations

None. The implementation follows the approved architecture:

- `MYPY_PATHS` is the single source of truth.
- Prefixes are escaped independently and sorted by `(-len(path), path)`.
- The slash boundary, anchors, and named captures are preserved.
- No configuration validation, parser abstraction, dependency, logging, or metrics surface was
  added outside the approved scope.

## Accepted Existing Behavior

Direct changed-file flake8 reports seven pre-existing `T201` findings in
`scripts/check_mypy_baseline.py`. These are the established user-facing CLI output contract for
baseline updates, missing or malformed baselines, new and resolved errors, aggregate counts, and
successful completion. They are not debug prints, and PYPOST-1067 must preserve reporting.

**Classification:** accepted intentional behavior, not PYPOST-1067 debt. No follow-up is warranted
without a separate requirement to replace the CLI output mechanism.

## Follow-up Tasks

### Pre-existing Full-Suite Failures

The three failures reproduced unchanged at base commit `3f97f904`. They are non-blockers and are
already ticketed.

- `tests/test_suite_qapp_alignment.py`
  - Test: `test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication`
  - Classification: NON-BLOCKER — pre-existing.
  - Jira: [PYPOST-1110](https://pypost.atlassian.net/browse/PYPOST-1110), To Do.
- `tests/test_pypost_1077_verification_artifacts.py`
  - Test: `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
  - Classification: NON-BLOCKER — pre-existing.
  - Jira: [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111), To Do.
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline`
  - Test: `test_markdown_snapshot_matches_current_metrics`
  - Classification: NON-BLOCKER — pre-existing.
  - Jira: [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111), To Do.

### Pre-existing Typecheck Drift

`make typecheck` reports unrelated Qt signal overload errors and stale resolved baseline entries.
Step 5 reproduced the drift at base commit `3f97f904`, so it is not caused by PYPOST-1067.

**Classification:** NON-BLOCKER — pre-existing. It is owned by
[PYPOST-1086](https://pypost.atlassian.net/browse/PYPOST-1086), which read-only Jira verification
found in To Do status in active sprint 1303 (`CI Guardrails & Type Safety`). No duplicate ticket is
needed.

## Blocker and Ticketing Assessment

- **Blocker:** none.
- **In-scope technical debt:** none.
- **Unticketed follow-up remaining:** none.
- **New Jira issues created in Step 7:** none, as required.

Read-only Jira verification on 2026-08-20 confirmed the three linked issues and their statuses.
The implementation is ready to proceed to developer documentation after Step 7 review.
