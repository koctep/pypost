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

## Counter families

PyPost registers counters (not gauges or histograms). Values only increase. Common series:

### HTTP requests (GUI and MCP tools)

| Metric | Labels | Meaning |
| --- | --- | --- |
| `requests_sent_total` | `method` | Outbound HTTP requests started |
| `responses_received_total` | `method`, `status_code` | HTTP responses received |
| `request_errors_total` | `category` | Execution failures (timeout, connection, etc.) |
| `request_retries_total` | `method`, `status_category` | Retry attempts |
| `request_retry_exhaustions_total` | `endpoint` | All retries exhausted for an endpoint |

### MCP server (request tools on port 1080)

| Metric | Labels | Meaning |
| --- | --- | --- |
| `mcp_requests_received_total` | `method` | MCP operations received (`list_tools`, `call_tool`, …) |
| `mcp_responses_sent_total` | `method`, `status` | MCP responses (`success` or `error`) |

The observability MCP server (port 9080) increments these when agents read `metrics://all`.

### GUI activity (optional dashboards)

Examples: `gui_send_clicks_total`, `gui_save_actions_total{source="toolbar"}`,
`gui_response_search_actions_total`, `history_entries_appended_total{method="GET"}`.

These help correlate operator actions with HTTP/MCP volume; they are not required for basic
monitoring.

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

- [Developer MCP & metrics stack](dev/mcp_integration.md#4-metrics-observability-stack-pypostcoremetricspy)
- [Metric rename migration](dev/metric_rename_migration.md)
- [Testing MCP and metrics](dev/testing.md#mcp-and-metrics-test-coverage)
