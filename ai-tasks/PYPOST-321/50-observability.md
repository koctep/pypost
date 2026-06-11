# PYPOST-321: Observability

## Scope

Test-only task; no new logging or metrics.

## Existing Coverage

Save-as flow already logs:

- `save_as_flow_started` with `source_request_id`
- `save_as_flow_completed` with `source_request_id`, `new_request_id`, `target_collection_id`

The regression test guards the invariant those log fields assume: source and new IDs differ and
the source entity is not overwritten.

## Decision

No observability changes required.
