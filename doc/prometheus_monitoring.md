# Prometheus Monitoring

PyPost exposes Prometheus metrics so operators can monitor HTTP traffic, MCP tool usage,
and application errors on the local machine. Metrics stay on your machine — they are not
sent to AI agents.

## Endpoints

PyPost starts an observability server when the application launches (see **Settings** for
host and port):

| Endpoint | Purpose |
| --- | --- |
| `http://127.0.0.1:9080/metrics` | Prometheus text scrape (primary) |
| `http://127.0.0.1:9080/mcp` | MCP Streamable HTTP (read `metrics://all` resource) |

Default port is **9080**. Default host in settings is `0.0.0.0` (listens on all interfaces);
use `127.0.0.1` in scrape URLs when PyPost runs locally.

Change **Metrics Server Host** and **Metrics Server Port** in **Settings** (`Ctrl+,` or
`F12`). After saving, PyPost restarts the metrics server automatically.

## Quick check

With PyPost running:

```bash
curl -s http://127.0.0.1:9080/metrics | head
```

You should see `# HELP` lines and counter names ending in `_total`.

## Metric inventory

PyPost registers **44 Prometheus instruments** in
[`pypost/core/metrics_registry.py`](../pypost/core/metrics_registry.py): **38 counters**, **3
gauges**, and **3 histograms**. Counters and gauges are monotonic or point-in-time values;
histograms record MCP tool call, template render, and MCP WebSocket probe durations.

Verify the registration count:

```bash
rg 'Counter\(|Histogram\(|Gauge\(' pypost/core/metrics_registry.py | wc -l
```

### GUI interaction

| Metric | Type | Labels | Meaning |
| --- | --- | --- | --- |
| `gui_send_clicks_total` | Counter | — | Send button clicked in the request editor |
| `gui_save_actions_total` | Counter | `source` | Save action triggered (`menu`, `shortcut`, `overwrite`, `new`, …) |
| `gui_save_as_actions_total` | Counter | `source` | Save As action triggered (`menu`, `shortcut`, …) |
| `gui_new_tab_actions_total` | Counter | `source`, `protocol` | Completed new-tab choice. `source`: `plus_button`, `shortcut`, `collections_context`, `unknown`. `protocol`: `http`, `websocket`, `mcp_client`, `unknown`. Picker cancel does not increment. |
| `gui_copy_curl_actions_total` | Counter | — | Copy as cURL action triggered |
| `gui_collection_delete_actions_total` | Counter | `item_type`, `status` | Collection tree delete flow (`item_type`: `request`, `collection`; `status`: `selected`, `cancelled`, `succeeded`, `not_found`, `error`) |
| `gui_collection_rename_actions_total` | Counter | `item_type`, `status` | Collection tree rename flow (same `item_type` values; `status`: `selected`, `cancelled`, `rejected_empty`, `succeeded`, `not_found`, `error`) |
| `gui_response_search_actions_total` | Counter | `source`, `has_matches` | Response body search (`source`: `enter`, `next`, `previous`, `typed`; `has_matches`: `true`/`false`) |
| `gui_variable_validation_total` | Counter | `result` | Environment variable name validation attempt (`valid`, `invalid`) |
| `gui_variable_validation_failures_total` | Counter | `reason` | Failed validation (`empty`, `starts_with_digit`, `invalid_chars`) |
| `gui_method_body_autoswitches_total` | Counter | `method` | Body tab auto-selected after HTTP method change |

### HTTP requests, history, and templates

| Metric | Type | Labels | Meaning |
| --- | --- | --- | --- |
| `requests_sent_total` | Counter | `method` | Outbound HTTP request started |
| `responses_received_total` | Counter | `method`, `status_code` | HTTP response received |
| `response_body_truncated_total` | Counter | `method` | Response body truncated by `max_response_bytes` |
| `history_entries_appended_total` | Counter | `method` | Request recorded in history |
| `history_entries_loaded_into_editor_total` | Counter | — | History entry loaded into the request editor |
| `request_errors_total` | Counter | `category` | Request execution error (`network`, `timeout`, `template`, `body`, `script`, `history`, `cancelled`, `unknown`) |
| `yaml_to_json_conversion_failed_total` | Counter | — | YAML body could not be converted to JSON at send time |
| `history_record_errors_total` | Counter | — | History persistence failed |
| `hidden_value_masks_applied_total` | Counter | `surface` | Hidden environment variable masked before persistence (`history`, …) |
| `request_retries_total` | Counter | `method`, `status_category` | Outbound retry attempt (`status_category` matches error category, e.g. `timeout`) |
| `request_retry_exhaustions_total` | Counter | `endpoint` | All configured retries exhausted for a URL |
| `template_expression_render_attempts_total` | Counter | `render_path`, `outcome` | `{{…}}` function placeholder render attempt (`render_path`: `runtime`, `hover`, `curl`, `http`; `outcome`: `success`, `empty_content`, `validation_error`, `render_error`) |
| `template_expression_validation_failures_total` | Counter | `render_path`, `code`, `function_name` | Template function validation failure (`code`: `unknown_function`, `invalid_arity`, …) |
| `template_expression_render_duration_seconds` | Histogram | `render_path` | Jinja compile+render wall time in seconds (`render_path`: `runtime`, `hover`, `curl`, `http`) |

For strict HTTP integer-conversion failures, use
`template_expression_render_attempts_total{render_path="http",outcome="render_error"}`
to monitor blocked requests. PyPost also emits the bounded ERROR event
`template_integer_conversion_failed`; it contains the HTTP method and a
sanitized request origin only, never the rejected value or request data.

### MCP server

| Metric | Type | Labels | Meaning |
| --- | --- | --- | --- |
| `mcp_requests_received_total` | Counter | `method` | MCP operation received on the request-tool server (e.g. `list_tools`, `call_tool`) or observability server (`read_resource:metrics`) |
| `mcp_responses_sent_total` | Counter | `method`, `status` | MCP response sent (`status`: `success`, `error`) |
| `mcp_server_up` | Gauge | — | Request-tool MCP readiness (`1` while at least one configured endpoint is running, `0` otherwise) |
| `mcp_server_instances` | Gauge | `state` | Aggregate configured MCP endpoints by lifecycle state (`stopped`, `starting`, `running`, `failed`); intentionally has no instance, port, collection, or environment label |
| `mcp_tool_call_duration_seconds` | Histogram | `method`, `status` | MCP tool call wall time in seconds |
| `mcp_active_env_changes_total` | Counter | — | Top-bar active environment changed; retained for compatibility and does not retarget configured MCP endpoints |

The observability server on port 9080 increments `mcp_requests_received_total` and
`mcp_responses_sent_total` when agents read the `metrics://all` resource.

### WebSocket sessions and streams
 
| Metric | Type | Labels | Meaning |
| --- | --- | --- | --- |
| `websocket_sessions_opened_total` | Counter | `outcome` | Opened WebSocket sessions (`outcome`: `success`, `failure`, `timeout`, `tls_rejected`) |
| `websocket_sessions_closed_total` | Counter | `reason` | Closed WebSocket sessions (`reason`: `clean`, `peer_close`, `heartbeat_timeout`, `transport_error`, `reconnect_exhausted`, `forced`) |
| `websocket_messages_total` | Counter | `direction`, `kind` | Transferred WebSocket messages (`direction`: `inbound`, `outbound`; `kind`: `text`, `binary`, `ping`, `pong`) |
| `websocket_message_bytes_total` | Counter | `direction` | Payload volume in bytes transferred (`direction`: `inbound`, `outbound`) |
| `websocket_stream_entries_dropped_total` | Counter | `reason` | Stream buffer entries dropped due to bounds (`reason`: `capacity`, `memory_budget`) |
| `websocket_reconnect_attempts_total` | Counter | `outcome` | Automatic reconnection attempts (`outcome`: `scheduled`, `succeeded`, `exhausted`) |
| `websocket_active_sessions` | Gauge | — | Instantaneous number of active concurrent WebSocket sessions holding concurrency slots |
| `websocket_session_start_refused_total` | Counter | `reason` | Session start attempts refused by concurrency policy (`reason`: `max_concurrent`, `disabled`) |
| `websocket_probe_duration_seconds` | Histogram | `outcome` | MCP WebSocket probe execution wall time in seconds (`outcome`: `success`, `timeout`, `limit_reached`, `error`) |

### Environment encryption

| Metric | Type | Labels | Meaning |
| --- | --- | --- | --- |
| `environment_value_encryptions_total` | Counter | — | Environment value encrypted before save |
| `environment_value_decryptions_total` | Counter | — | Environment value decrypted on load |
| `environment_encryption_errors_total` | Counter | `stage`, `reason` | Encryption flow error (`stage`: `save`, `load`; `reason`: `encrypt_failed`, `decrypt_failed`, `unsupported_format`) |

## Prometheus scrape config

Example `prometheus.yml` job (adjust host/port if you changed settings):

```yaml
scrape_configs:
  - job_name: pypost
    static_configs:
      - targets: ["127.0.0.1:9080"]
    metrics_path: /metrics
    scrape_interval: 15s
```

## MCP resource alternative

Agents or scripts can read the same payload via MCP resource `metrics://all` on
`http://127.0.0.1:9080/mcp` instead of scraping `/metrics`. See
[MCP Integration](mcp_integration.md#connect-agent) for client setup.

## Troubleshooting

| Symptom | What to try |
| --- | --- |
| Connection refused on 9080 | Confirm PyPost is running; check Settings for metrics host/port |
| Empty or stale metrics | Send a request or invoke an MCP tool, then scrape again |
| Port already in use | Change metrics port in Settings or stop the conflicting process |

## Developer reference

Counter definitions, test coverage, and migration notes for operators maintaining dashboards:

- [Developer MCP & metrics stack](dev/mcp_integration.md#7-metrics-observability-stack-pypostcoremetricspy)
- [Prometheus metrics inventory](prometheus_monitoring.md#metric-inventory) — complete operator
  catalog (PYPOST-750)
- [Metric rename migration](dev/metric_rename_migration.md)
- [Testing MCP and metrics](dev/testing.md#mcp-and-metrics-test-coverage)
