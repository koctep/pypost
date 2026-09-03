# PYPOST-1105 Architecture

## Process topology

```text
pytest process
   | loopback TCP
   v
proxy Uvicorn process (MCPProxyServerImpl)
   | loopback TCP
   v
upstream Uvicorn process (MCP Server + /mcp + /sse)
```

The test module owns a small process harness. Each child receives only simple
configuration values and constructs its own MCP server, Starlette app, event
loop, and Uvicorn server. No mocked session or in-process ASGI transport is
used for the wire assertions.

## Upstream application

The upstream process registers one deterministic tool using the public MCP
server API. Its handler returns a large text payload for the Streamable HTTP
case and a small identifiable payload for the SSE case. The same app exposes
the production `/mcp` route and legacy `/sse` mount so the proxy can select each
transport without changing fixtures.

## Proxy application

The proxy process constructs `MCPProxyServerImpl` with the upstream URL and
transport selected by the test. It exposes the normal production app. The test
client always connects to the proxy's Streamable HTTP route, proving that the
production proxy bridges the downstream request to each upstream transport.

## Lifecycle and failure handling

- A dynamically allocated loopback port is selected before each process starts.
- The parent waits for the TCP port with a bounded timeout and checks child
  liveness while waiting.
- Context-manager teardown requests termination, joins within a bound, and
  force-terminates only the exact child if it remains alive.
- The test client uses bounded MCP/HTTP timeouts and closes all async contexts.

## Verification boundaries

The tests assert the downstream tool list and returned payload. This covers
MCP initialization, route dispatch, transport framing, proxy upstream selection,
socket I/O, and process teardown. Existing fast unit/in-process tests remain
responsible for detailed error mapping, header resolution, and activity/metric
behavior.
