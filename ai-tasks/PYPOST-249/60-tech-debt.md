# PYPOST-249: Technical Debt Analysis

## Shortcuts Taken

- **Shared AppSettings object retained:** Documented as intentional; splitting models deferred.
- **Full JSON rewrite on save:** Retained; partial field persistence deferred.

## Code Quality Issues

None blocking. `_UI_STATE_FIELDS` makes ownership explicit for future refactors.

## Missing Tests

None for this task — behavior unchanged; existing `TestStateManagerPersistence` coverage
remains valid.

## Performance Concerns

None new. Debounce behavior documented in `doc/dev/state_manager.md`.

## Follow-up Tasks

| Item | Priority | Notes |
| --- | --- | --- |
| Split AppSettings into preference vs session models | Low | Only if settings surface grows or ownership bugs recur |
| Partial JSON field updates on disk | Low | Profile first; current file is small |
| Timer-fired persistence without flush in tests | Low | Already noted in PYPOST-386/252 debt |

## Blocker Review Verdict

**SAFE TO CLOSE**

- Debt item addressed by documentation and explicit field ownership constant.
- No behavior regression; tests pass.
- Larger refactors explicitly deferred with rationale.
