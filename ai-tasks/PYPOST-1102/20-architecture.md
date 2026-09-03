# PYPOST-1102 Architecture

## Decision

Use a single private async `_dispatch_proxy_operation` method in
`MCPProxyServerImpl` as the lifecycle boundary for all six forwarded MCP
operations. Each public protocol method supplies a small operation callback
that invokes the matching `ClientSession` method and normalizes collection
results where required.

## Responsibilities

The shared boundary will:

1. Start one monotonic timer and emit the operation-start debug event.
2. Resolve dynamic headers before opening an upstream session.
3. Open and close the configured upstream transport through `_connect_upstream`.
4. Execute the operation callback and return its result unchanged, except for
   the existing list normalization performed by the public wrapper.
5. Map timeout and network failures to the existing public exception types.
6. Record success or error metrics exactly once for each dispatched operation.
7. Record one sanitized activity entry with operation, outcome, duration, and
   applicable tool or item metadata.
8. Emit bounded completion or failure logs without raw exception payloads,
   resolved headers, or upstream URL values.

## Data flow

```text
MCP handler
   -> public proxy method
   -> _dispatch_proxy_operation(operation, callback, metadata)
      -> resolve headers
      -> _connect_upstream(resolved headers)
      -> callback(ClientSession)
      -> metrics + activity + bounded log
   -> normalized or upstream result
```

The callback is the only operation-specific part of the network call. This
keeps protocol method signatures stable while ensuring all transport methods
share the same cleanup and failure behavior.

## Error behavior

- `McpUnresolvedVariableError` is recorded as an error and re-raised without
  opening an upstream connection.
- `httpx.TimeoutException` and `TimeoutError` become `TimeoutError` with the
  existing timeout diagnostic.
- `httpx.ConnectError` and `httpx.NetworkError` become `httpx.ConnectError`
  with the existing connection diagnostic.
- Other exceptions are recorded as generic operation errors and re-raised.
- Error activity details use fixed safe categories; exception text is not
  copied into logs or activity entries.

## Observability contract

Every dispatch records one request and response metric. Tool calls additionally
record the existing tool-duration histogram using the result's `isError`
outcome. Activity entries use the existing ring buffer and sanitization rules;
tool arguments and resolved header values are never included.

## Compatibility and boundaries

- Public methods and their argument/return shapes remain unchanged.
- Streamable HTTP, legacy SSE, route paths, timeout configuration, and
  per-request upstream connection behavior remain unchanged.
- No connection pooling, shared session cache, new dependency, or new setting
  is introduced.
- List methods continue returning concrete lists; prompt/resource result
  objects and tool call result objects remain upstream objects.

## Test design

Focused tests will verify that all six methods use the shared boundary, that
each operation records one success or failure lifecycle, that timeout/network
mapping and unresolved-header short-circuiting remain intact, and that tool
metrics/activity are not duplicated. Existing proxy tests cover transport
creation, result forwarding, and secret masking.
