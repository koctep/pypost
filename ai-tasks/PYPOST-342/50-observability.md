# PYPOST-342: Observability

## Metric under test

`gui_collection_rename_actions_total{item_type,status}` via
`MetricsManager.track_gui_collection_rename_action(item_type, status)`.

## Statuses covered by new tests

| Status | Test module |
| --- | --- |
| `selected` | `test_collection_tree_rename_context_menu.py`, `test_collections_presenter.py` |
| `cancelled` | `test_collection_tree_rename_context_menu.py`, `test_collection_tree_rename_metrics.py` |
| `succeeded` | `test_collection_tree_rename_context_menu.py` |
| `rejected_empty` | both rename test modules |
| `error` | `test_collection_tree_rename_metrics.py` |
| `not_found` | `test_collection_tree_rename_metrics.py` |

No new logging or metrics instrumentation was added; tests assert existing emission points.
