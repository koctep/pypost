# PYPOST-1195: Technical Debt Analysis

## Shortcuts Taken

None material. Tests and developer docs were aligned to the existing
`open_tabs_filter` emit rather than renaming production events (would churn
MCP Client shared summary logging).

## Code Quality Issues

- Caplog still uses substring `in` checks rather than a shared helper that
  parses event + fields. Acceptable for this debt ticket; a shared assert
  helper could reduce future event-name drift (NON-BLOCKER).

## Missing Tests

- No additional scenarios required for DoD. Dirty-close WebsocketDraft cases
  already cover keep/discard/clean paths and remained green.

## Performance Concerns

None.

## Follow-up Tasks

| Item | Priority / class | Notes |
| ---- | ---------------- | ----- |
| Shared caplog event-assert helper for structured `event key=value` lines | Low / NON-BLOCKER — accept residual, no ticket | Optional hardening; not required for DoD |
| Sibling Suite Failures Cleanup items | Out of scope | Already ticketed: [PYPOST-1194](https://pypost.atlassian.net/browse/PYPOST-1194), [PYPOST-1196](https://pypost.atlassian.net/browse/PYPOST-1196) |

No blockers relative to PYPOST-1195 acceptance criteria.
