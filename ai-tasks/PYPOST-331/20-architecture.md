# PYPOST-331: Architecture — Delete metric label coverage

## Research

Delete telemetry flows through two entry points:

1. **`show_context_menu`** — emits `selected` when Delete is chosen; `cancelled` on
   confirm No; `succeeded` after successful `handle_delete` on confirm Yes.
2. **`handle_delete`** — emits `error` when `delete_collection_item` raises;
   `not_found` when it returns `False`; `succeeded` on persistence success.

Counter: `gui_collection_delete_actions_total{item_type,status}` via
`MetricsManager.track_gui_collection_delete_action`.

## Existing Coverage (verified)

| Status | Entry point | Test module | Delivered by |
|--------|-------------|-------------|--------------|
| `selected` | `show_context_menu` | `test_collection_tree_delete_confirmation` | PYPOST-330 |
| `cancelled` | `show_context_menu` | `test_collection_tree_delete_confirmation` | PYPOST-330 |
| `succeeded` | `show_context_menu` → `handle_delete` | `test_collection_tree_delete_confirmation` | PYPOST-330 |
| `error` | `handle_delete` | `test_collection_tree_delete_metrics` | PYPOST-339 |
| `not_found` | `handle_delete` | `test_collection_tree_delete_metrics` | PYPOST-339 |

Both modules exercise `collection` and `request` item types.

## Implementation Plan

### Phase 1 — Verify matrix

Run headless unit tests for both modules; confirm all five statuses and both item
types are asserted.

### Phase 2 — Document closure

Create `ai-tasks/PYPOST-331` artifacts referencing existing tests and dev docs.
No new production or test code required.

## Non-goals

- No duplication of PYPOST-330 or PYPOST-339 test modules.
- No Prometheus integration tests.
