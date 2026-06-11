# PYPOST-268 / PYPOST-271: Architecture

## Scope

Test-only. No changes to `pypost/core/http_client.py`.

## Target method

`HTTPClient._prepare_request_kwargs(request_data, variables, rendered_url=None)`
→ `(kwargs: dict, resolved: ResolvedRequestFields)`.

## Test placement

Add class `TestHTTPClientPrepareRequestKwargs` in `tests/test_http_client.py`, alongside
existing HTTPClient tests. Reuse module `pytestmark = pytest.mark.timeout(60)`.

## Test strategy

| Area | Approach |
| --- | --- |
| URL | Real `TemplateService`; optional `rendered_url` with mocked TS to assert skip |
| Headers / params | Template substitution including Authorization |
| Defaults | Assert `method`, `stream=True`, `timeout=30.0` |
| JSON body | `json` kwarg; invalid JSON → `data` |
| YAML + flag | `json` kwarg; invalid YAML → `ExecutionError(BODY)` + metrics |
| YAML without flag | `data` kwarg |
| Empty / whitespace body | No `json` or `data` |
| Resolved fields | Match rendered url, headers, body |

## Dependencies

- `RequestData`, `TemplateService`, `ExecutionError`, `ErrorCategory`
- `MagicMock` for metrics and template-service skip test

## Out of scope

- `send_request` transport, SSE, timeouts overridden for SSE probes
- New fixtures or conftest changes
