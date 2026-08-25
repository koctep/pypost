# PYPOST-1176 — Tech Debt

| Priority | Item | Notes |
| --- | --- | --- |
| NON-BLOCKER | Parallel Qt segfault in `tests/test_main_window.py` | exit_code=-11 under parallel runner; passes in isolation |
| NON-BLOCKER | Flaky parallel failures in MCP registry / WS lifecycle tests | Intermittent under load; pass in isolation |
