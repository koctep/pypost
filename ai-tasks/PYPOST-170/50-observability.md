# PYPOST-170: Observability

Tests-only task; no new logging or metrics in production code.

| Signal | Coverage |
| --- | --- |
| `gui_send_clicks_total` | Send button `QTest.mouseClick` → registry scrape |
| `gui_save_actions_total{source}` | Menu and shortcut save handlers |
| `gui_save_as_actions_total{source}` | Menu and shortcut save-as handlers |
| `gui_copy_curl_actions_total` | Copy cURL menu handler |

Existing coverage retained:

- `tests/test_metrics_manager.py` — direct `track_*` unit assertions
- `tests/test_request_editor_method_tab_switch.py` — autoswitch mock assertions
- `tests/test_collection_tree_*_metrics.py` — collection context-menu metrics

No additional instrumentation required.
