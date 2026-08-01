# PYPOST-961: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE (non-blockers only)

Parametrized hook best-effort test covers every member of
`DUMP_BEST_EFFORT_ERRORS` on the lifecycle path. Original assert failure
remains primary. Docs updated. No production changes.

## Shortcuts Taken

- **RuntimeError double coverage:** PYPOST-912 dedicated test kept alongside
  parametrized case — intentional for traceability, not a gap.

## Code Quality Issues

- None blocking.

## Missing Tests

| Scenario | Status |
| --- | --- |
| RuntimeError hook → WARNING (PYPOST-912) | Covered |
| LookupError hook propagates (PYPOST-914) | Covered |
| OSError hook best-effort | Covered (PYPOST-961) |
| TypeError hook best-effort | Covered (PYPOST-961) |
| ValueError hook best-effort | Covered (PYPOST-961) |
| AttributeError hook best-effort | Covered (PYPOST-961) |
| Dump helper TypeError / ValueError dedicated units | Out of scope (PYPOST-915 debt) |

No timeout-marker blockers.

## Performance Concerns

None.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Dump helper TypeError / ValueError units | [PYPOST-915](https://pypost.atlassian.net/browse/PYPOST-915) debt row |
| Shared exception tuple | [PYPOST-960](https://pypost.atlassian.net/browse/PYPOST-960) (done) |

### NON-BLOCKER

None new.
