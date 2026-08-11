# PYPOST-1012: Technical Debt Analysis

## Shortcuts Taken

None. The feature retains the established core / Qt-dialog / presenter-action split,
reuses the native collection import shape, and preserves the injected per-collection
serializer seam used by the existing single-export flow.

## Code Quality Issues

None blocking or requiring follow-up. The pure list payload helper is covered independently,
while the UI action deliberately applies its injected serializer once per collection so test
and caller dependency injection remains consistent with single export.

## Missing Tests

No required coverage is missing:

- Core tests cover ordered JSON-list fidelity through the real import reader, empty-library
  output, non-mutation, result formatting, and write failures.
- UI tests cover the identifiable button, selection independence, success counts, empty
  backup, cancellation before serialization, write failure, and completion logging.
- Both changed pytest modules declare an explicit module-level
  `pytest.mark.timeout(60)` marker; there is no timeout-marker blocker.

The focused export suite passed (26 tests). The full fast-suite run remains explicitly
unconfirmed in `40-code-cleanup.md`; this is verification evidence to complete before a
release, not a missing feature test or acceptance-criteria gap.

## Performance Concerns

No material concern at the established collection-export scale. Bulk export intentionally
serializes and writes one in-memory JSON list on the GUI path, matching the existing
single-export interaction. Extremely large libraries could cause a brief synchronous UI
pause, but no performance regression or measured need justifies a worker/streaming redesign
in this scoped feature.

## Deviations from Initial Architecture

None material. The UI path maps the injected serializer over the captured collection list
rather than calling the default core helper directly; this is the architecture's documented
dependency-injection requirement, not a behavioral deviation. User documentation was added
to `doc/user/collections.md`; no Step 8 developer documentation was performed here.

## Follow-up Tasks

None. No genuine unticketed non-blocker follow-up requires Jira creation; therefore no
priority or Jira link is applicable.

## Blocker Review

| Check | Result |
| --- | --- |
| Acceptance-criteria implementation | Covered by focused core and UI tests |
| Required explicit pytest timeout markers | None missing |
| User-facing backup/restore guidance | Added to `doc/user/collections.md` |
| Product or data-safety blocker | None found |
| Unticketed technical-debt follow-up | None |

**SAFE TO CLOSE**
