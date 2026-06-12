# PYPOST-599: Observability

## Logging

No new log events required. This change is a maintainability refactor of a read-only help
dialog and shortcut registration metadata.

Existing shortcut-triggered flows retain their metrics and log events:

- `RequestEditor` save/send actions still call `logger.info` and `MetricsManager` trackers.
- `MainWindow` exit and settings paths unchanged.

## Metrics

No new Prometheus counters. GUI action metrics (`gui_save_actions_total`, etc.) are unchanged
because handler entry points are the same.

## Tracing / diagnostics

If shortcut help appears wrong in the field, inspect `QAction` children of `MainWindow` with
`pypost_hotkey_*` properties via `collect_hotkey_rows(main_window)` in a REPL.
