# PYPOST-167: Code Cleanup

## Scope

Verification task — no production code edits.

## Checks

| Check | Result |
| --- | --- |
| `MetricsManager.__new__` singleton | Absent |
| `MetricsManager()` in `pypost/` (production) | Only `main.py:30` |
| Inline `MetricsManager()` in presenters/services | Absent (PYPOST-44) |
| `MetricsTrackerProtocol` at consumer call sites | Present (PYPOST-73) |
| Line length / trailing whitespace on touched files | OK |

## Files Reviewed

- `pypost/core/metrics.py`
- `pypost/main.py`
- `pypost/ui/main_window.py`
- `pypost/core/metrics_protocol.py`

No lint or format changes required.
