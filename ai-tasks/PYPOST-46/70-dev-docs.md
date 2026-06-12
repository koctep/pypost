# PYPOST-46 — Developer Documentation

## Summary

`RequestService` now depends on `HTTPClientProtocol` instead of the concrete `HTTPClient`
class. Production behavior is unchanged: when no client is injected, `RequestService`
constructs `HTTPClient(metrics=..., template_service=...)`.

## Files updated

| File | Purpose |
| --- | --- |
| `pypost/core/http_client_protocol.py` | `@runtime_checkable` protocol with `send_request` |
| `pypost/core/request_service.py` | `http_client: HTTPClientProtocol \| None` |
| `tests/test_http_client_protocol.py` | Compliance and mock substitution tests |
| `doc/dev/testability.md` | HTTPClientProtocol section; removed from out-of-scope |
| `doc/dev/solid_audit.md` | DIP note references PYPOST-46 |

## Testing

```bash
.venv/bin/python -m pytest tests/test_http_client_protocol.py tests/test_request_service.py -v
```

## Related

- [PYPOST-382](https://pypost.atlassian.net/browse/PYPOST-382) — constructor injection seams
- [PYPOST-73](https://pypost.atlassian.net/browse/PYPOST-73) — `MetricsTrackerProtocol` pattern
