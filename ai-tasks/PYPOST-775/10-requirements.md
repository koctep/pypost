# PYPOST-775 — Requirements

> Parent: [PYPOST-690](https://pypost.atlassian.net/browse/PYPOST-690) audit R-P3-003 (D-011)

## Problem

`doc/dev/test_audit.md` links to `testing.md` for how-to guidance but did not link to sibling
Code Audit summaries. Readers could not navigate from the test audit to security, observability,
or maintainability findings without searching filenames.

## Acceptance Criteria

1. `doc/dev/test_audit.md` has a `## Related Audits` section.
2. Section includes links to security, observability, and maintainability audit summaries.
3. Links follow the standardized footer pattern used by other `*_audit.md` siblings.
4. No application code changes.
5. `make check` passes.

## Out of Scope

- Hub table updates in `documentation_audit.md` (PYPOST-767)
- Full seven-sibling footer on other audit files (PYPOST-767)
- New automated doc-link regression tests
