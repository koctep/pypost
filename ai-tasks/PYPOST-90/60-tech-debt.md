# PYPOST-90: Technical Debt Analysis

## Resolution

Debt **closed**. Debounced UI-state persistence implemented in PYPOST-386:

- `pypost/core/state_manager.py` — `_UI_STATE_SAVE_DEBOUNCE_MS = 300`; `_schedule_save()` /
  `_on_debounced_save_timeout()`; `flush_pending_save()` on exit
- `pypost/ui/presenters/collections_presenter.py` — expand/collapse via `StateManager`
- `tests/test_settings_persistence.py` — coalescing, debounce timer, flush tests

## Shortcuts Taken

None for this closure task.

## Code Quality Issues

None blocking closure.

## Missing Tests

None blocking — PYPOST-252 covers debounce paths. Optional future test: timer-fired path
without `flush_pending_save` in integration context (noted in PYPOST-386 debt).

## Performance Concerns

- Environment switch still saves immediately via `EnvPresenter` — intentional, out of scope.
- Hard kill within 300 ms debounce window may lose last UI toggle — same as any debounced write;
  normal quit flushes.

## Blocker Review

**Verdict: SAFE TO CLOSE** — expand/collapse no longer saves synchronously on every click;
debounce in place and tested.

## Follow-up Tasks

None.
