# PYPOST-63: Architecture — history render reuse

## Current flow (before)

```
HTTPClient.send_request()
  └─ render url, headers, body  →  HTTP

RequestService.execute() history block
  └─ SensitiveDataMaskingPolicy.build_history_safe_fields()
       └─ render url, headers, body again  ← duplicate
```

## Target flow

```
HTTPClient.send_request()
  └─ render once  →  HTTPRequestResult(response, resolved)

RequestService.execute()
  └─ build_history_safe_fields(..., resolved=resolved)
       ├─ hidden_keys?  → re-render with masked variables
       └─ else          → return resolved as-is
```

MCP: `_execute_mcp()` builds `ResolvedRequestFields` when rendering URL/body (and headers for
history snapshot) and returns them with the response.

## Changes

| Component | Change |
|-----------|--------|
| `http_client.py` | Add `ResolvedRequestFields`, `HTTPRequestResult`; `send_request` returns both |
| `request_service.py` | Thread `resolved_fields` from HTTP/MCP into history |
| `sensitive_data_masking_policy.py` | Optional `resolved` param; skip re-render when safe |
| Tests | `HTTPRequestResult` mocks; no-rerender assertion |

## Backward compatibility

- `HTTPClient.send_request` return type changes to `HTTPRequestResult` (callers updated in-repo).
- Public `RequestService.execute` signature unchanged.
