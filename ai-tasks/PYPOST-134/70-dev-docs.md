# PYPOST-134: Dev Docs

## Created

- `doc/dev/template_service.md` — centralization audit, consumer matrix, hover exception,
  injection notes.

## Updated

- `doc/dev/architecture.md` — link to `template_service.md` from `TemplateService` bullet.

## Key points for developers

- Use `TemplateService.render_string` for all runtime `{{...}}` substitution.
- Use `TemplateService.parse` for AST-based variable discovery (MCP secrets).
- Do not create standalone `jinja2.Environment` instances for request rendering.
- Hover plain-variable chains stay in `VariableHoverResolver`; function expressions call
  `TemplateService` with `render_path="hover"`.
