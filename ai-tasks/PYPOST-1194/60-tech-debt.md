# PYPOST-1194: Technical Debt Analysis

## Shortcuts Taken

Raised `FILE_CAPS` for `collections_presenter.py` and `tabs_presenter.py`
instead of extracting further presenter logic in this Low/SP-3 debt item.
Matches ticket guidance (intentional growth → raise caps with ~10% headroom)
and prior pattern (PYPOST-735 / PYPOST-1071).

## Code Quality Issues

- `tabs_presenter.py` remains large (1059 / 1165). Extraction into helpers
  should continue before another raise (documented in solid_audit /
  websocket_draft_tab).
- Several `doc/dev/*` pages still described the historical **785** cap as
  current; Step 8 aligns those to the new inventory numbers.

## Missing Tests

- Existing inventory + snapshot freshness tests cover DoD. No new cases
  required.

## Performance Concerns

None.

## Follow-up Tasks

| Item | Priority / class | Notes |
| ---- | ---------------- | ----- |
| Further extract `tabs_presenter.py` toward helper modules to reclaim headroom | Medium / NON-BLOCKER | Prefer extraction before raising 1165 again — tracked as [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184) |
| Historical `maintainability_audit.md` table still shows old 715/785 snapshot | Low / NON-BLOCKER — accept residual, no ticket | Historical audit table; canonical caps live in baseline-metrics + solid_audit |

No blockers relative to PYPOST-1194 acceptance criteria.
