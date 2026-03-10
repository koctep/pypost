# Testing via MCP and Prometheus

## Overview

PyPost can be tested by the AI assistant in Cursor using the embedded MCP server and
Prometheus metrics. Rules for the AI are defined in `.cursor/lsr/do-testing.md`.

## Prerequisites

- **PyPost running** — `make run` or `python -m pypost.main`
- **MCP enabled** — in Manage Environments, check "Enable MCP Server"
- **Cursor connected** — add SSE server URL `http://<host>:1080/sse` (or `http://<host>:1080/sse/`)
- **Host** — use the host from PyPost settings (e.g. `localhost`, `dev.int`)

## Testing via MCP

The AI calls MCP tools (requests with "MCP Tool" checked) and verifies responses.
See [do-testing.md](../../.cursor/lsr/do-testing.md) for the full procedure.

## Verification via Prometheus

Metrics: `http://<host>:9080/metrics/` (host from settings, default port 9080).

Key metrics for MCP testing:

| Metric | Labels | Description |
|--------|--------|--------------|
| `mcp_requests_received_total` | `method` | MCP tool invocations |
| `mcp_responses_sent_total` | `method`, `status` | MCP responses (success/error) |
| `requests_sent_total` | `method` | HTTP requests sent |
| `responses_received_total` | `method`, `status_code` | HTTP responses received |

## References

- [.cursor/lsr/do-testing.md](../../.cursor/lsr/do-testing.md) — AI assistant rules
- [MCP Integration](mcp_integration.md) — MCP setup
- [pypost/core/metrics.py](../../pypost/core/metrics.py) — metric definitions
