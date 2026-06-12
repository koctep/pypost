# PYPOST-621: Observability

## New Log Events

| Event | Level | Location |
| --- | --- | --- |
| `alert_manager_reloaded` | INFO | `MainWindow._reload_alert_manager` — logs `log_path` and `webhook_url_set` boolean |

Auth header is not logged (boolean pattern consistent with `main.py`).

## Operator Notes

After saving alert settings, grep for `alert_manager_reloaded` to confirm the live instance
was rebuilt.
