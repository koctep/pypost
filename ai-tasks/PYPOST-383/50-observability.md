# PYPOST-383: Observability

No new metrics or log events. This task documents existing tree-refresh observability.

## Documented events

| Logger / event | Module | Meaning |
| --- | --- | --- |
| `refresh_tree_completed` | `collections_presenter` | Full O(n) model rebuild |
| `collection_tree_item_removed` | `collections_presenter` | Incremental delete |
| `add_saved_request_to_tree_completed` | `collections_presenter` | Incremental save-as |
| `collection_item_rename_tree_sync_fallback` | `collection_tree_actions` | Rename fell back to full rebuild |

## Rationale

PYPOST-383 closes an audit documentation gap. Operators investigating scale issues should use
the events above before adding new instrumentation.
