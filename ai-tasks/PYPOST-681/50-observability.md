# PYPOST-681: Observability

## Impact

No new log lines or metrics. `error_detail` is agent-visible envelope data only.

Existing `call_tool` metrics (`track_mcp_response_sent`) unchanged — still keyed on execution
error flag, not envelope field count.

## Security

`error_detail` may contain upstream or script failure text; sanitization prevents leaking
hidden environment values into agent context.
