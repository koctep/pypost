# PYPOST-171: Code Cleanup

## Scope

Verification task — no production code edits.

## Checks

| Check | Result |
| --- | --- |
| `server_lock` defined once in `MetricsServer` | OK |
| Lifecycle methods acquire lock consistently | OK (`start_server`, `stop_server`) |
| No stray `threading.Lock` in `metrics.py` facade | OK |
| Line length / trailing whitespace on reviewed files | OK |

## Files Reviewed

- `pypost/core/metrics_server.py`
- `pypost/core/metrics.py`
- `pypost/main.py`
- `pypost/ui/main_window.py`

No lint or format changes required.
