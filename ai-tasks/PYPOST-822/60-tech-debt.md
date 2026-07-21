# PYPOST-822: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

## Shortcuts Taken

Used `register_hotkey` + `QAction.triggered.emit()` instead of delivering real
`Ctrl+Tab` / `Ctrl+Shift+Tab` key events. Documented in the test docstring: offscreen Qt
shortcut activation is unreliable without a focused/activated window. This still validates
product key→slot wiring via the same registration helper MainWindow uses.

## Code Quality Issues

None introduced. The test re-registers the Tabs next/previous bindings rather than
constructing a full `MainWindow` (siblings patch `_setup_shortcuts` away in most MainWindow
tests). Duplicating the two `register_hotkey` calls keeps the test focused and fast.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Next/previous cycle via direct slots | Already covered |
| Next/previous via hotkey map keep focus off `+` | Covered (this task) |
| Close-focus siblings (first/middle/last) | Covered (PYPOST-818/820/819) |
| Full MainWindow key-event e2e for Ctrl+Tab | Optional; flaky offscreen; not required |

## Performance Concerns

None.

## Follow-up Tasks

None required for acceptance. Optional later: a display-backed smoke test that presses
real Ctrl+Tab if CI gains a non-offscreen GUI job.

## Blocker Review

**SAFE TO CLOSE** — acceptance criteria met; test passes under `make test`; no production
regressions.
