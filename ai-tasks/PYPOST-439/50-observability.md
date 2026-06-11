# PYPOST-439: Observability

## Summary

No new log lines or metrics. This ticket is Settings UI only.

## Existing Observability (unchanged)

| Event | Level | Location |
| --- | --- | --- |
| `alert_manager_created` | INFO | `main.py` — logs `log_path` and `webhook_url_set` boolean |
| `alert_emitted` | WARNING | `AlertManager` |
| `alert_webhook_ok` / `alert_webhook_failed` | DEBUG / WARNING | `AlertManager` |

Auth header is never logged in plaintext (boolean or absent only).

## Operator Notes

Changing alert settings in the dialog updates `settings.json` but does **not** reconfigure
the running `AlertManager` until application restart (pre-existing behavior).
