# PYPOST-143: Observability Implementation

## Logging Implementation

No new logs. Existing DEBUG injection traces remain the diagnostic surface:

```
INFO  pypost.main                 template_service_created id=<N>
DEBUG pypost.core.http_client     HTTPClient: using injected TemplateService id=<N>
DEBUG pypost.core.request_service RequestService: using injected TemplateService id=<N>
```

When `id()` values differ across hops, a caller omitted injection or used a test-local fallback.

## Metrics Implementation

No changes. `TemplateService(metrics=...)` at the composition root ensures hover and runtime paths
share metrics when wired via `VariableHoverResolver.set_metrics()` from the UI layer.

## Validation Results

- [x] Observability behavior unchanged
- [x] Documented how to verify shared instance via DEBUG logs

## Notes

Documentation-only task. Refer to `doc/dev/template_service.md` — Lifecycle section.
