# PYPOST-316: Observability

## Existing Logging

Save orchestration logs at INFO level (unchanged):

| Event | Location |
| ----- | -------- |
| `save_as_flow_started` | `RequestSaveOrchestrator.save_as_request` |
| `save_as_flow_cancelled` | `RequestSaveOrchestrator.save_as_request` |
| `save_as_flow_completed` | `RequestSaveOrchestrator.save_as_request` |
| `save_request_overwrite_*` | `RequestSaveOrchestrator._save_overwrite` |
| `save_request_new_succeeded` | `RequestSaveOrchestrator._save_new` |

## Existing Metrics

- `gui_save_actions_total{source=...}` — new/overwrite saves via orchestrator
- `gui_save_as_actions_total{source=...}` — save-as triggers in `RequestWidget`

## Changes

None — extraction preserved observability one-to-one from prior MainWindow/TabsPresenter flow.
