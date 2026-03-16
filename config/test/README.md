# Test Config for PyPost MCP

Copy these files to your PyPost data directory to enable MCP testing.

## Setup

```bash
# Linux/macOS
DATA_DIR=~/.local/share/pypost
mkdir -p "$DATA_DIR/collections"
cp examples/collections/mcp.json "$DATA_DIR/collections/MCP.json"
cp config/test/environments.json "$DATA_DIR/"
```

**Note:** `environments.json` replaces your environments. If you have existing
ones, merge the "MCP Test" entry into your current file instead of overwriting.

## Contents

- **MCP** collection (`examples/collections/mcp.json`) with three requests:
  - `SSE Probe Metrics` — GET http://localhost:9080/sse (MetricsManager)
  - `SSE Probe Main` — GET http://localhost:1080/sse (main MCP server)
  - `List Tools` — MCP http://localhost:1080/sse (list_tools via full MCP protocol)

- **MCP Test** environment with `enable_mcp: true`

## Usage

1. Restart PyPost (or reload collections).
2. Select the "MCP Test" environment.
3. MCP tools `sse_probe_metrics` and `sse_probe_main` will be available.
4. Call them via Cursor MCP: `sse_probe_metrics`, `sse_probe_main`.

## Troubleshooting

- **"Connection established" (SSE probe) or "Timeout after 25s" (List Tools)**: The
  server may not be sending the endpoint event in time. Ensure:
  1. MCP is enabled (select environment with `enable_mcp: true`).
  2. No firewall blocks localhost/127.0.0.1.
  3. Ports 1080 and 9080 are not used by other apps.
- **Connection refused**: MCP server is not running. Select the MCP Test environment
  and restart PyPost.
