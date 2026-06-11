# PYPOST-386: Technical Debt Analysis

## Shortcuts Taken

None. Debounce uses the same single-shot `QTimer` pattern as other UI controllers
(`FoldController`, `ValidationController`).

## Code Quality Issues

None blocking. `StateManager` is now a `QObject`; tests using `FakeStateManager` remain
valid because they mock the public API only.

## Missing Tests

- Timer-fired persistence without explicit flush is covered indirectly via coalesce + flush
  tests. A future test could drive `QEventLoop` until the debounce timer fires (similar to
  `test_env_storage_responsiveness.py`) if timer timing regressions become a concern.

## Performance Concerns

- **Crash kill / SIGKILL:** Pending UI state within the debounce window may be lost on
  hard termination, same as any debounced write. Normal quit flushes via
  `MainWindow.handle_exit()`. Platform-specific unexpected-close hooks are out of scope.
- **300 ms debounce:** Tunable constant `_UI_STATE_SAVE_DEBOUNCE_MS`; not user-configurable.

## Follow-up Tasks

- **[Informational] PYPOST-392:** Business concern (fewer redundant writes) addressed by
  PYPOST-386; PYPOST-392 can be closed or linked as duplicate when triaged.
- **[Informational] Unexpected close flush:** If users report lost expansion state after
  force-quit within 300 ms of last toggle, consider `aboutToQuit` or platform close hooks
  (currently mitigated by explicit exit path flush).

## Blocker Review Verdict

**SAFE TO CLOSE**

- Definition of Done met: debounced UI-state saves, flush on exit, Settings dialog unchanged,
  tests pass, no missing timeout markers on changed tests.
