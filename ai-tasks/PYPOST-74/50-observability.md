# PYPOST-74: Observability

## Behavior

No Prometheus metric names, labels, or counter semantics changed. Tracking calls that previously
ran only when `metrics` was injected still run through `NullMetrics` when omitted — a no-op with
zero registry side effects.

## Call-site clarity

Observability calls now sit inline with business logic:

```python
self._metrics.track_request_sent(request.method)
response = self.mcp_client.run(url, operation, call_params)
self._metrics.track_response_received(request.method, str(response.status_code))
```

Domain-specific suppression (e.g. skip error metric on user cancellation) remains explicit.

## Verification

- `tests/test_metrics_protocol.py` — NullMetrics protocol satisfaction and no-op smoke
- `tests/test_storage_environments.py` — encryption/decryption metrics still recorded with mock
