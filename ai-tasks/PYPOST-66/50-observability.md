# PYPOST-66: Observability

## Summary

No observability changes. This is a structural refactor of Qt signal wiring with no new code
paths, metrics, or log statements.

## Existing logging retained

- `main_window_initialized` (INFO) at end of `MainWindow.__init__`
- `main_window_exit_requested` (INFO) in `handle_exit`

No new DEBUG/INFO logs added for wiring — connections are static and fail at import/startup if
misconfigured.
