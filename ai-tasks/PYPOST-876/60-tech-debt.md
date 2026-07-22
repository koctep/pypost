# PYPOST-876: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE (non-blockers only)

Dump helper catches a documented best-effort tuple instead of blind
`Exception`. Red→green locks propagation for unexpected kinds. Docs
updated. Items below are non-blocking follow-ups — record here only
(no Jira in this run).

## Shortcuts Taken

- **AttributeError included in the catch tuple** without a dedicated
  unit that forces AttributeError on `ui_snapshot` / `is_ui_ready` —
  covered by catalogue rationale + RuntimeError best-effort test.
- **Lifecycle dump-hook wrapper** still uses broad `except Exception`
  (`# noqa: BLE001`) so a hook bug cannot mask the original test
  failure — intentionally left for a later follow-up.

## Code Quality Issues

- None blocking. `_DUMP_BEST_EFFORT_ERRORS` is module-private; if other
  modules need the same set, export a public alias later.

## Missing Tests

| Scenario | Status |
| --- | --- |
| RuntimeError best-effort WARNING + None | Covered |
| LookupError propagates | Covered (PYPOST-876) |
| AttributeError best-effort on ui_ready | Not dedicated |
| OSError / TypeError / ValueError best-effort | Implicit via tuple; no dedicated unit |
| Lifecycle hook BLE001 narrowing | Out of scope |

No timeout-marker blockers.

## Performance Concerns

None. Catch tuple does not change success-path cost.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Parent failure artifacts | [PYPOST-860](https://pypost.atlassian.net/browse/PYPOST-860) |
| Direct-session auto-dump | [PYPOST-875](https://pypost.atlassian.net/browse/PYPOST-875) |
| CI upload of failure artifacts | [PYPOST-874](https://pypost.atlassian.net/browse/PYPOST-874) |

### NON-BLOCKER

#### Narrow lifecycle dump-hook exception types

- **Priority:** Lowest
- **Description:** Replace broad `except Exception` around
  `_failure_dump_hook` in `AgentAppSession.__exit__` with a documented
  tuple (aligned with `_DUMP_BEST_EFFORT_ERRORS` or hook-specific
  kinds) once hook failure modes are catalogued. Keep “never mask the
  original test failure” semantics.
- **Files:** `pypost/agent/lifecycle.py`,
  `tests/test_agent_e2e_failure_artifacts.py` (or lifecycle unit),
  `doc/dev/agent_e2e_failure_artifacts.md`
- **Jira:** [PYPOST-914](https://pypost.atlassian.net/browse/PYPOST-914)

#### Dedicated best-effort units for OSError / AttributeError

- **Priority:** Lowest
- **Description:** Add mocked units that force `OSError` on write and
  `AttributeError` on `is_ui_ready` / `ui_snapshot` to lock each member
  of `_DUMP_BEST_EFFORT_ERRORS`.
- **Files:** `tests/test_agent_e2e_failure_artifacts.py`
- **Jira:** [PYPOST-915](https://pypost.atlassian.net/browse/PYPOST-915)
