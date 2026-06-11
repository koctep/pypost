# PYPOST-410: Architecture — render-once

## Current flow (before)

```
RequestService.execute()
  ├─ render_string(url)          ← guard (duplicate)
  └─ HTTPClient.send_request()
       ├─ render_string(url)     ← SSE probe
       └─ _prepare_request_kwargs()
            └─ render_string(url) ← duplicate
```

MCP path: guard + `_execute_mcp()` each render URL.

## Target flow

```
RequestService.execute()
  └─ HTTPClient.send_request()
       ├─ url = render_string(url)   ← once
       └─ _prepare_request_kwargs(..., rendered_url=url)
```

MCP: `_execute_mcp()` renders URL and body once each (no guard).

## Changes

| Component | Change |
|-----------|--------|
| `request_service.py` | Delete lines 301–315 guard block; renumber execute steps |
| `http_client.py` | Add `rendered_url` optional param to `_prepare_request_kwargs`; pass from `send_request` |
| Tests | Replace guard raise test with no-pre-render test; add HTTP single-render test |

## Error handling

- No change to `ExecutionError` mapping in HTTP/MCP clients.
- Worker `except ExecutionError` in `run()` becomes unreachable for template guard
  (documented as follow-up PYPOST-412).

## Backward compatibility

- Public method signatures unchanged.
- History masking still renders templates independently (acceptable; not on hot retry path).
