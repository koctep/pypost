# PYPOST-405: Observability

## Logging
- Added an `INFO` level log in `CollectionsPresenter._show_context_menu` when a user selects the "New tab" action.
  - Event: `collection_request_open_new_tab`
  - Parameters tracked: `request_id`, `request_name`

## Metrics
- Re-used the existing Prometheus metric counter `gui_new_tab_actions_total` to track new tabs opened from the context menu.
  - Parameter: `source="collections_context"`
  - This allows us to measure how often users discover and use this new action compared to opening tabs via other means (e.g. keyboard shortcuts, plus button).

## Tracing / Diagnostics
- The new tab is backed by a deep copy of the request, keeping the original `request_id`. Existing request-scoped observability features (such as `request_saved`, `request_send_initiated`) will transparently continue to function and correctly attribute actions back to the original request entity.