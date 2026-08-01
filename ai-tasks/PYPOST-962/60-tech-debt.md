# PYPOST-962: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE (non-blockers only)

Dedicated dump-helper units lock `TypeError` and `ValueError` on the capture
path as best-effort with WARNING + `None`. Test-only change; no production
edits.

## Shortcuts Taken

- **Capture path only for both types.** Inner `is_ui_ready` probe also catches
  these types but has no dedicated unit — same tuple, different sub-path.
- **ValueError on capture, not write.** OSError write-path unit exists from
  PYPOST-915; capture path matches AttributeError / RuntimeError pattern.

## Code Quality Issues

- None material. Tests follow sibling caplog patterns in the same module.

## Missing Tests

| Scenario | Status |
| --- | --- |
| RuntimeError best-effort | Covered (PYPOST-876) |
| OSError best-effort on write | Covered (PYPOST-915) |
| AttributeError best-effort on capture | Covered (PYPOST-915) |
| TypeError best-effort on capture | Covered (this ticket) |
| ValueError best-effort on capture | Covered (this ticket) |
| Hook per-type best-effort | Covered (PYPOST-961) |
| Shared exception tuple module | Covered (PYPOST-960) |

All `DUMP_BEST_EFFORT_ERRORS` members now have dedicated dump-helper or hook
units. No timeout-marker blockers.

## Performance Concerns

Two additional pure mocked units. Negligible cost.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Dump tuple narrowing | [PYPOST-876](https://pypost.atlassian.net/browse/PYPOST-876) |
| OSError / AttributeError dump units | [PYPOST-915](https://pypost.atlassian.net/browse/PYPOST-915) |
| Hook per-type units | [PYPOST-961](https://pypost.atlassian.net/browse/PYPOST-961) |
| Shared tuple module | [PYPOST-960](https://pypost.atlassian.net/browse/PYPOST-960) |

No new follow-ups required.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to AC |
| Missing tests with timeout markers | **None** — module `timeout(60)` |
| Deviations from architecture | None — test-only as planned |
| Hardcoded values | Event prefix intentional |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR4 and DoD satisfied.
