# PYPOST-317: Observability

## Scope

Test-only task; no new logging or metrics.

## Existing Coverage

Save-as flow already logs:

- `save_as_flow_started` with `source_request_id`
- `save_as_flow_cancelled` when the dialog is dismissed
- `save_as_flow_failed` when target collection is missing
- `save_as_flow_completed` with source, new, and target collection IDs

Orchestrator tests guard the preconditions those log lines assume (cancel vs complete,
collection resolution, distinct source and new IDs).

## Decision

No observability changes required.
