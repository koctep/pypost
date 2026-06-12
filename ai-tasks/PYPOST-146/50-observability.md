# PYPOST-146: Observability

## Scope

Verification-only task. No observability changes required.

## Existing coverage (unchanged)

`TemplateService` already exports render and validation metrics (see PYPOST-134). Single
`Environment` reuse does not alter metric labels or log fields.

`main.py` logs `template_service_created id=%d` at startup for injection verification.

## Result

No new logging or metrics. Performance benefit is structural (one env per service instance),
not a new observability surface.
