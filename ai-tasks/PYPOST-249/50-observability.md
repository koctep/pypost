# PYPOST-249: Observability

## Existing logging

`StateManager` already emits debug logs (unchanged):

- `state_manager_save_scheduled` — debounce timer started/restarted
- `state_manager_save_debounced` — timer-fired persist
- `state_manager_save_immediate` — explicit `save()` / flush path

## Changes in this task

No new log lines. Documentation clarifies when each path runs so operators can correlate
debug output with UI vs Settings dialog saves.

## Metrics

None required — settings save frequency is not a production metric target.
