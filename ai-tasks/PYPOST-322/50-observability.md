# PYPOST-322: Observability

## Logging

Save orchestration log events moved with the code into `RequestSaveOrchestrator`:

| Event | Level | When |
| ----- | ----- | ---- |
| `save_as_flow_started` | INFO | Save-as dialog opens |
| `save_as_flow_cancelled` | INFO | User dismisses dialog |
| `save_as_flow_failed` | WARNING | Missing target collection |
| `save_as_flow_completed` | INFO | New entity persisted |
| `save_request_overwrite_cancelled` | INFO | User declines overwrite |
| `save_request_stale_cancelled` | INFO | User declines stale overwrite |
| `save_request_overwrite_succeeded` | INFO | Overwrite persisted |
| `save_request_new_succeeded` | INFO | First-time save persisted |
| `save_request_failed` | WARNING | Missing target collection |

No new log keys were introduced; behavior is unchanged from the pre-extraction presenter.

## Metrics

`MetricsManager.track_gui_save_action` labels (`overwrite`, `new`) still fire from the
orchestrator. Save-as metrics remain in `RequestWidget.on_save_as`.

## Verification

- Unit tests assert persistence side effects; no manual `/metrics` check required for this
  refactor.
