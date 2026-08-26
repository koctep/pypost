# PYPOST-1162: Observability

## Existing signals (unchanged)

WebSocket save actions continue to log via PYPOST-1161:

- `ws_save_action_triggered source=%s`
- `ws_save_as_action_triggered source=%s`

Connect/send paths reuse existing presenter logging:

- `websocket_connect_initiated`, `websocket_disconnect_initiated`
- `composer_send_blocked_not_open`, `composer_format_validation_failed`

## Step 4 additions

- `composer_format_json_failed error=%s` — logged when Format JSON shortcut
  encounters invalid JSON in the composer payload.

No new metrics counters; hotkey dispatch is thin routing only.
