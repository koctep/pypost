# PYPOST-146: Dev Docs

## Created

- `ai-tasks/PYPOST-146/` — full top-down workflow artifacts

## Updated

- `doc/dev/template_service.md` — PYPOST-146 section: single Environment verification,
  Jinja2 caching notes, links to PYPOST-455/PYPOST-148

## Key points for developers

- Each `TemplateService` instance owns exactly one `jinja2.Environment` on `self.env`.
- Use injection from `main.py` in production so the request pipeline shares one service (and
  one env).
- Do not instantiate `jinja2.Environment()` in feature code — use `TemplateService`.
- Template compile caching is not enabled; see PYPOST-148 if repeated identical templates
  become a measured bottleneck.
