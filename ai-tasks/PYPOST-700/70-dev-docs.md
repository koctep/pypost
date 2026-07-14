# PYPOST-700: Developer Documentation

## Summary

Split private render and observability helpers from `template_service.py` into
`template_service_render.py`. Public `TemplateService` API unchanged.

## Files Updated

| File | Change |
| --- | --- |
| `doc/dev/template_service.md` | Added `template_service_render.py` to related modules |
| `doc/dev/architecture.md` | Added render helper module to core tree |
| `doc/dev/architecture_audit.md` | R-P3-002 marked Done |

## Added

| Path | Role |
| --- | --- |
| `pypost/core/template_service_render.py` | Private render + observability helpers |

## Guidance

Import `TemplateService` from `pypost.core.template_service` only. Do not import
render helpers from application code — they are package-internal.
