# PYPOST-410: Observability

## Impact

This refactor removes duplicate `TemplateService.render_string` calls. Observability is
**unchanged** — each remaining render still emits the same metrics and logs via
`TemplateService`:

- `template_expression_render_attempts_total{render_path,outcome}`
- `template_expression_validation_failures_total`
- `template_render_fallback_to_original` warning on Jinja errors

## Net effect

- Fewer `render_path=runtime` attempts per HTTP request (URL counted once instead of
  two or three times).
- No new log lines or counters added.
- `request_errors_total{category=template}` unchanged (guard path removed; category was
  only reachable via mocked tests).

## Verification

- [x] No duplicate metric increments from removed guard
- [x] HTTP client error logs still use single resolved `url` variable
