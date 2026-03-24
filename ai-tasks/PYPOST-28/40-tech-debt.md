# PYPOST-28: Technical Debt Analysis


## Shortcuts Taken

- **Implicit Context**: We rely on `self.tabs.currentWidget()` as a fallback. This works for the single-window model, but if we had multiple windows or detached tabs, this might be incorrect. Ideally, the signal should pass the tab ID or the tab object itself. — [PYPOST-232](https://pypost.atlassian.net/browse/PYPOST-232)
- No significant shortcuts detected. The solution follows standard PySide6 patterns for thread management. — [PYPOST-233](https://pypost.atlassian.net/browse/PYPOST-233)

## Code Quality Issues

- [FIXED in PYPOST-8] In `MainWindow.on_request_finished` and `on_request_error`, worker cleanup logic is duplicated. In the future, with more complex request completion logic, this could be extracted into a separate `_cleanup_request(tab)` method.

## Missing Tests

- No automated UI tests checking request retry. Testing was done manually. — [PYPOST-234](https://pypost.atlassian.net/browse/PYPOST-234)

## Performance Concerns

- No performance issues. Reference clearing is O(1). — [PYPOST-235](https://pypost.atlassian.net/browse/PYPOST-235)

## Follow-up Tasks

- Refactor signal passing to include context (tab reference). — [PYPOST-236](https://pypost.atlassian.net/browse/PYPOST-236)
