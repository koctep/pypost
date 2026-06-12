# PYPOST-96: Observability

## Summary

No new logging or metrics — existing observability from PYPOST-386 is sufficient.

## Existing signals (verified)

| Level | Event | Location |
| --- | --- | --- |
| DEBUG | `state_manager_save_scheduled debounce_ms=300` | `StateManager._schedule_save()` |
| DEBUG | `state_manager_save_debounced` | `StateManager._on_debounced_save_timeout()` |
| DEBUG | `state_manager_save_immediate` | `StateManager.save()` |
| INFO | `main_window_exit_requested` | `MainWindow.handle_exit()` |

## Verification

Debounced save scheduling and timer-fired persist are observable in debug logs when rapid UI
state changes occur. No additional instrumentation required for this closure.
