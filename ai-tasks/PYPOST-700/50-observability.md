# PYPOST-700: Observability Implementation

## Logging Implementation

### Moved Logs

Log emission moved from `template_service.py` to `template_service_render.py`:

| Level | Message | Module |
| --- | --- | --- |
| INFO | `template_expression_validation_failed` | `template_service_render` |
| DEBUG | `template_compile_cache` | `template_service_render` |
| DEBUG | `template_expression_render_succeeded` | `template_service_render` |
| WARNING | `template_render_fallback_to_original` | `template_service_render` |

Logger name is now `pypost.core.template_service_render` (was `pypost.core.template_service`).

### Log Structure

Unchanged — same structured key=value fields and outcomes.

## Metrics Implementation

No metric API changes. Helpers still call:

- `track_template_expression_render_attempt`
- `track_template_expression_validation_failure`

via the `MetricsTrackerProtocol` instance passed from `TemplateService`.

## Monitoring Integration

- [x] Existing Prometheus counters unchanged
- [ ] Log aggregation filters may need `template_service_render` logger — optional

## Validation Results

- [x] `TestTemplateServiceObservability` passes
- [x] `TestTemplateServiceRenderStages` passes
- [x] `TestTemplateServiceHelperStages` passes

## Notes

Observability behavior preserved; only module attribution for log source changed.
