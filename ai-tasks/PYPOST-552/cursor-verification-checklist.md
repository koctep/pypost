# PYPOST-552: Cursor MCP verification checklist

Manual end-to-end verification that a local Cursor agent can connect to PyPost over
Streamable HTTP, discover tools, and invoke them. Automated protocol coverage:
`tests/test_mcp_server_integration.py`.

## Prerequisites

- [ ] PyPost running (`make run` or `python -m pypost.main`)
- [ ] Test collection installed per [config/test/README.md](../../config/test/README.md)
- [ ] **MCP Test** environment selected; top bar shows **MCP: ON**
- [ ] Default ports free: **1080** (request tools), **9080** (metrics)

## PyPost in-app checks

- [ ] Open **List Tools** request (MCP method, URL `http://127.0.0.1:1080/mcp`) and **Send**
- [ ] Response status 200 with JSON body containing `"tools"` array
- [ ] Tool names include `sse_probe_main` and/or `sse_probe_metrics` (if collection loaded)
- [ ] Optional: send **SSE Probe Main** GET — confirms legacy `/sse` stream (separate from
  Cursor transport)

## Cursor MCP configuration

- [ ] Add server URL: `http://127.0.0.1:1080/mcp`
- [ ] Transport type: **Streamable HTTP** (not legacy SSE-only)
- [ ] Server status in Cursor shows **connected** (no handshake / transport errors)

## Cursor agent: list_tools

- [ ] Open Cursor chat with MCP tools enabled for the PyPost server
- [ ] Ask agent to list available MCP tools (or inspect MCP tool picker)
- [ ] Agent sees PyPost tools matching requests with **MCP Tool** checked in active environment
- [ ] Tool names use snake_case (e.g. `sse_probe_main`)

## Cursor agent: call_tool

- [ ] Invoke `sse_probe_main` (or another simple exposed tool)
- [ ] Agent receives `TextContent` whose `text` is a JSON envelope (not raw HTTP body alone)
- [ ] Parsed envelope includes `status`, `error`, and `body` keys
- [ ] `error` is `false` for a successful probe; `status` reflects upstream HTTP code
- [ ] Optional: confirm agent prompt instructs `json.loads` on PyPost tool results
- [ ] No timeout or "tool not found" errors
- [ ] Optional: invoke a second tool to confirm repeat calls work

## Failure triage

| Failure | Check |
| --- | --- |
| Disconnected in Cursor | URL is `/mcp`, not `/sse`; PyPost MCP ON |
| Empty tool list | Environment with MCP enabled; requests saved with MCP Tool checked |
| call_tool timeout | Firewall/localhost; port 1080 listening |
| Unresolved `{{ var }}` in response | Variable defined in active environment |

## Sign-off

| Field | Value |
| --- | --- |
| Verified by | |
| Date | |
| PyPost version / commit | |
| Cursor version | |
| Result | PASS / FAIL |
| Notes | |
