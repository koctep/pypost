# PYPOST-143: Technical Debt Analysis

## Shortcuts Taken

- **Leaf-class `TemplateService()` fallbacks** — `HTTPClient` and masking-policy construction in
  `RequestService` still create local instances when `template_service=None`. Accepted for test
  ergonomics; production path always injects from `main.py`.
- **Hover module singleton** — `_hover_template_service` in `mixins.py` remains. Documented
  exception with metaclass patching for tests; full UI DI deferred.

## Code Quality Issues

None blocking. PYPOST-18 global singleton debt is closed.

## Missing Tests

None for this documentation ticket. Injection coverage exists in:

- `tests/test_http_client.py` — `TestHTTPClientInjection`
- `tests/test_request_service.py` — `TestRequestServiceInjection`
- `tests/test_variable_hover.py` — hover `_template_service` patching

## Performance Concerns

None. Single shared `Environment` per production instance unchanged.

## Follow-up Tasks

| Item | Severity | Jira |
| --- | --- | --- |
| `TemplateServiceProtocol` for mock without Jinja2 | Low | Future — PYPOST-378 TD-1 |
| Remove leaf fallbacks; require explicit injection | Low | Future hardening |
| Inject hover `TemplateService` from presenter | Low | Future UI DI |

No new Jira issues created — items are pre-existing accepted trade-offs, now documented.

## Verdict

**SAFE TO CLOSE** — design documented; test seams enumerated; PYPOST-18 pointer resolved.
