# PYPOST-1176 — Code Cleanup

- Removed unused `sys`, `os`, `QApplication` imports from test modules after qapp deduplication.
- Added `TYPE_CHECKING` import for `QApplication` annotations in websocket repro tests.
