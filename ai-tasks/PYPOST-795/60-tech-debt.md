# PYPOST-795: Technical Debt Analysis

## Shortcuts Taken

None. Decision documented; no temporary workarounds.

## Code Quality Issues

None introduced. Pre-existing note: `set_close_button_size` has no production caller by design —
documented as supported opt-in API, not dead code.

## Missing Tests

No new tests required. Existing coverage:

- Default native metrics
- Opt-in override via `set_close_button_size`
- Production `system` theme uses native metrics

## Performance Concerns

None.

## Follow-up Tasks

| Priority | Task | Rationale | Jira |
| --- | --- | --- | --- |
| — | *(none from this task)* | PYPOST-795 closes the PYPOST-792 follow-up | — |

## Blocker Review

**SAFE TO CLOSE** — no blockers. Documentation decision implemented; regression tests unchanged.

## Validation Summary

- `make check` passes.
- Decision: keep API, document when-to-use / when-not-to-use.
- PYPOST-792 native-metrics policy preserved.
