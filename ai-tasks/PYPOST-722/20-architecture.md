# PYPOST-722: Isolate Qt style state in theme tests

## Research

We investigated how QApplication's stylesheet affects the returned style.
In Qt/PySide6:
- Setting a stylesheet on `QApplication` wraps the current style.
- `app.style().objectName().lower()` returns `""` under a stylesheet instead of `"fusion"` or other base style.
- By using a module-scoped fixture that backs up and restores the original stylesheet, palette, and style, we can completely isolate the theme tests without affecting the rest of the suite.

## Implementation Plan

1. In `tests/test_style_manager_theme.py`, update `qapp` fixture:
   - Save `app.style()`, `app.palette()`, `app.styleSheet()`.
   - Clear stylesheet: `app.setStyleSheet("")`.
   - Yield the application instance.
   - Restore the original values on teardown.
2. Run pytest on `tests/test_style_manager_theme.py` to verify it passes.

## Architecture

No changes to core production code are required. This is a testing architecture/isolation improvement.

## Q&A

- **Q**: Does the fixture affect other tests?
- **A**: No, since it is module-scoped and meticulously restores the state back to its original values on teardown.
