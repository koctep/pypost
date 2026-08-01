# PYPOST-915: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE (non-blockers only)

Dedicated dump-helper units lock `OSError` (write path) and `AttributeError`
(capture path) as best-effort with WARNING + `None`. Test-only change; no
production edits. No Jira follow-ups in this run (user directive).

## Shortcuts Taken

- **Outer catch path only for AttributeError.** Inner `is_ui_ready` probe
  also catches `AttributeError` but has no dedicated unit — same tuple,
  different sub-path.
- **OSError via `_write_json` patch.** Exercises write I/O without patching
  global `Path.mkdir`.

## Code Quality Issues

- None material. Tests follow sibling caplog patterns in the same module.

## Missing Tests

| Scenario | Status |
| --- | --- |
| RuntimeError best-effort | Covered (PYPOST-876) |
| OSError best-effort on write | Covered (this ticket) |
| AttributeError best-effort on capture | Covered (this ticket) |
| TypeError / ValueError best-effort | Implicit via tuple; no dedicated unit |
| Hook per-type best-effort | [PYPOST-961](https://pypost.atlassian.net/browse/PYPOST-961) |
| Shared exception tuple module | [PYPOST-960](https://pypost.atlassian.net/browse/PYPOST-960) |

No timeout-marker blockers.

## Performance Concerns

Two additional pure mocked units. Negligible cost.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Dump tuple narrowing | [PYPOST-876](https://pypost.atlassian.net/browse/PYPOST-876) |
| Hook caplog proof | [PYPOST-912](https://pypost.atlassian.net/browse/PYPOST-912) |
| Hook per-type units | [PYPOST-961](https://pypost.atlassian.net/browse/PYPOST-961) |
| Shared tuple module | [PYPOST-960](https://pypost.atlassian.net/browse/PYPOST-960) |

### NON-BLOCKER

#### Dedicated TypeError / ValueError dump best-effort units

- **Priority:** Lowest
- **Jira:** [PYPOST-962](https://pypost.atlassian.net/browse/PYPOST-962)
- **Description:** Mirror PYPOST-915 pattern for remaining tuple members
  not yet covered by dedicated mocked units.
- **Files:** `tests/test_agent_e2e_failure_artifacts.py`

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to AC |
| Missing tests with timeout markers | **None** — module `timeout(60)` |
| Deviations from architecture | None — test-only as planned |
| Hardcoded values | Event prefix intentional |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR4 and DoD satisfied.
