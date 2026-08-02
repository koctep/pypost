# PYPOST-974: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: parametrized combo out-of-range index contract test in
`tests/test_ui_actions.py` mirrors list/tree pattern from PYPOST-942; closes
[PYPOST-942/60-tech-debt.md](../PYPOST-942/60-tech-debt.md) TD-1. No production
code changed.

## Shortcuts Taken

- **Green-on-first-run contract test** — `_select_combo` already raises;
  Step 3 documented N/A (coverage debt only).
- **Substring assertions** — `"option index out of range"` in
  `str(exc_info.value)`, matching list/tree/combo missing-option precedent.
- **Parametrized boundaries** — One test covers `-1` and `3` (combo count).

## Code Quality Issues

None material. New test reuses `_make_fixture`, inherits module `pytestmark`,
and follows established `try`/`finally` teardown.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Combo index `< 0` / `>= count` | Covered (parametrized `-1`, `3`) |
| Combo missing option | Covered (pre-existing) |
| List/tree out-of-range | Covered (PYPOST-942) |
| Live main-window combo OOR via `agent_e2e_session` | Deferred — fixture suite proves API |
| Explicit timeout markers | **Present** — module `pytest.mark.timeout(60)` |

## Performance Concerns

None. Synchronous fixture call; no event-loop polling.

## Deviations from Architecture

None. Test-only change delivered as planned in `20-architecture.md`.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Parent TD-1 (combo OOR index test) | This story (PYPOST-974) |
| List/tree negative select | [PYPOST-942](https://pypost.atlassian.net/browse/PYPOST-942) |
| Live collection-tree negative select | [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) |

### NON-BLOCKER

None. No new unticketed follow-ups from this change.

### Accepted / out of scope (do not ticket)

- Assert full `reason=` / `widget_id=` formatting — substring matches suite
  convention.
- Live `METHOD_COMBO` out-of-range via `agent_e2e_session` — fixture proof is
  the acceptance target.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Broken / incomplete acceptance | None — AC-1–AC-6 met |
| Missing timeout on new tests | Pass — module mark |
| Unsafe relative to DoD | None |

**Phase C verdict: SAFE TO CLOSE**
