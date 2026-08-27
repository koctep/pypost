# PYPOST-1175: Observability

## Metrics

No new counters. Existing save metrics (`track_gui_save_action`, `track_gui_save_as_action`)
already fire when shortcuts trigger `handle_save_request_shortcut` on `McpClientTab`.

## Logging

Connect/Invoke paths reuse `McpClientPresenter` log tokens (`mcp_client_connect_initiated`,
`mcp_client_call_tool_initiated`) — no new log lines required for shortcut dispatch.

## Help dialog

`gui_hotkeys_*` metrics unchanged; Help → Hotkeys reads tagged actions from the widget tree.
