# Test Config for PyPost MCP

Regenerate committed fixtures from the repo root when changing MCP test data definitions:

```bash
.venv/bin/python scripts/generate_mcp_test_fixtures.py
```

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
  - `SSE Probe Metrics` — GET `http://127.0.0.1:9080/sse` (legacy SSE stream on metrics
    server; used by HTTPClient SSE-probe mode)
  - `SSE Probe Main` — GET `http://127.0.0.1:1080/sse` (legacy SSE stream on main MCP
    server)
  - `List Tools` — MCP `http://127.0.0.1:1080/mcp` (`list_tools` via Streamable HTTP)

- **MCP Test** environment with `enable_mcp: true`

## Usage

1. Restart PyPost (or reload collections).
2. Select the "MCP Test" environment.
3. MCP tools `sse_probe_metrics` and `sse_probe_main` will be available for agent calls.
4. Run the **List Tools** request in PyPost to verify `list_tools` over Streamable HTTP.

### Cursor

Connect Cursor to `http://127.0.0.1:1080/mcp` (Streamable HTTP). Then:

- Ask the agent to list MCP tools — expect `sse_probe_metrics`, `sse_probe_main`.
- Call `sse_probe_main` or `sse_probe_metrics` and confirm a connection/summary response.

See [Cursor verification checklist](../../ai-tasks/PYPOST-552/cursor-verification-checklist.md).

## Troubleshooting

- **"Connection established" (SSE probe) or "Timeout after 25s" (List Tools)**:
  1. MCP is enabled (select environment with `enable_mcp: true`).
  2. No firewall blocks localhost/127.0.0.1.
  3. Ports 1080 and 9080 are not used by other apps.
  4. **List Tools** uses `/mcp` — ensure Cursor and in-app MCP requests use Streamable HTTP,
     not legacy `/sse` URLs.
- **Connection refused**: MCP server is not running. Select the MCP Test environment
  and restart PyPost.
