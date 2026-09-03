# PYPOST-990 Architecture

## Transport selection

```text
CLI
 ├─ default / --attach ─> asyncio.run(_serve_stdio(session))
 └─ --http             ─> AgentUiActionsMcpServer
                           └─ shared /mcp Streamable HTTP route
```

The parser selects exactly one serving mode. Stdio remains the default, and
`--attach` continues to connect to the existing AF_UNIX host before serving
stdio. HTTP is explicit and is intended for the sidecar-owned spawn session;
attach remains a local IPC concern rather than a second remote bridge.

## HTTP application and lifecycle

The bridge's existing `mcp.server.Server` is passed to
`build_streamable_http_route`. A small Starlette application owns the `/mcp`
route and its MCP session-manager lifespan. Uvicorn runs in a dedicated daemon
thread so the process can continue pumping Qt events. Startup publishes a
thread-safe readiness event; shutdown sets `should_exit`, joins with a bound,
and closes the event loop after draining pending tasks.

The HTTP default host is `127.0.0.1`; port `0` requests an ephemeral loopback
port. The CLI logs the resolved endpoint and the server object owns the
listener until the process exits.

## Qt main-thread dispatch

HTTP callbacks execute in the Uvicorn thread. `call_tool` uses a QObject signal
with `QueuedConnection` to post a synchronous job to the QApplication thread.
The caller waits on a threading event with a fixed timeout and receives the
original exception if the action fails. The dispatcher executes directly when
already on the Qt thread, preserving stdio's existing behavior and avoiding a
self-deadlock. Qt event processing stays in the sidecar's main thread while
the optional HTTP listener is active.

```text
HTTP worker ──queued signal──> Qt main thread
     │                              │
     └──── result / exception <─────┘
```

The attach client is unchanged: its desktop-side host already performs the
same queued GUI dispatch over AF_UNIX.

## Failure and trust boundaries

- Bind failure is logged and exits the optional HTTP mode without silently
  falling back to stdio.
- A request timeout becomes a safe MCP tool error and does not leave a worker
  blocked indefinitely.
- HTTP is loopback-only by default and unauthenticated; callers must opt into
  non-loopback binding knowingly.
- No UI fill text or raw tool arguments are included in lifecycle logs.
