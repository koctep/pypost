# PYPOST-700: Split template_service render helpers

## Research

- `template_service.py` at 204 LOC combined orchestration, Jinja render, and
  observability (metrics + logging).
- Audit cap: 225 LOC (`scripts/audit_baseline_metrics.py`, refreshed PYPOST-717).
- Related modules already split by concern: `template_expression_tokenizer.py`,
  `function_expression_resolver.py`, `template_expression_types.py`.
- Tests in `TestTemplateServiceHelperStages` exercised private fallback helper directly.

## Implementation Plan

1. Create `pypost/core/template_service_render.py` with module-level functions:
   - `validation_message`, `record_empty_render_attempt`
   - `emit_validation_failure_observability`, `render_with_jinja`
   - `emit_render_success_observability`, `fallback_content_after_render_exception`
2. Slim `template_service.py` to orchestration: `__init__`, public API,
   `_validate_template_expressions` (thin resolver delegate).
3. Update tests:
   - Import `fallback_content_after_render_exception` from render module.
   - Patch `pypost.core.template_service.render_with_jinja` for render-error stage test.
4. Update dev docs and mark R-P3-002 Done in `architecture_audit.md`.
5. Run `make check`.

## Architecture

```text
pypost/core/
├── template_service.py          # TemplateService orchestration (~127 LOC)
├── template_service_render.py   # Private render + observability helpers (~115 LOC)
├── template_expression_tokenizer.py
├── function_expression_resolver.py
└── template_expression_types.py
```

`TemplateService.render_string` remains the single public render entry; helpers are
internal to the package (not re-exported).

## Q&A

- **Q:** Why module functions instead of a helper class?
- **A:** Matches existing tokenizer/resolver split; helpers are stateless aside from
  passed-in metrics and compile callable.
