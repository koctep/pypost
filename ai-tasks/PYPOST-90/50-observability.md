# PYPOST-90: Observability

## Summary

Observability for debounced UI-state saves was implemented in PYPOST-386. No new log lines in
this closure task.

## Existing signals (PYPOST-386)

| Level | Event | Location |
| --- | --- | --- |
| DEBUG | `state_manager_save_scheduled` (includes `debounce_ms`) | `state_manager.py` |
| DEBUG | `state_manager_save_debounced` | `state_manager.py` |
| DEBUG | `state_manager_save_immediate` | `state_manager.py` |

## Verification

Confirmed log statements present and unchanged. No new metrics required for this debt closure.
