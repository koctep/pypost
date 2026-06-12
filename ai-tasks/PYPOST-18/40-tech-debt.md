# PYPOST-18: Technical Debt Analysis


## Shortcuts Taken

- ~~**Global TemplateService** ([PYPOST-143](https://pypost.atlassian.net/browse/PYPOST-143))~~:
  **Resolved.** Module global removed (PYPOST-45); composition-root injection documented
  (PYPOST-378, PYPOST-143). See [template_service.md](../../doc/dev/template_service.md).

## Code Quality Issues

- **template_service imports** ([PYPOST-144](https://pypost.atlassian.net/browse/PYPOST-144)):
  `HTTPClient` and `MCPServerImpl` import the global directly, which tightens coupling; constructor
  injection would help if mocking `HTTPClient` becomes important.

## Missing Tests

- ~~**TemplateService unit tests** ([PYPOST-145](https://pypost.atlassian.net/browse/PYPOST-145))~~:
  **Resolved.** PYPOST-147 broad suite + PYPOST-145 variable-type tests. See
  [template_expression_functions.md](../../doc/dev/template_expression_functions.md).

## Performance Concerns

- **Shared Jinja2 Environment** ([PYPOST-146](https://pypost.atlassian.net/browse/PYPOST-146)):
  One `Environment` helps via Jinja2 caching (note `from_string` vs `get_template` behavior).
  Avoiding redundant `Environment`/`Template` construction versus the old `TemplateEngine` path is
  already an improvement.

## Follow-up Tasks

- Create unit tests for `pypost/core/template_service.py`.
  — [PYPOST-147](https://pypost.atlassian.net/browse/PYPOST-147)
- ~~**Jinja2 `from_string` caching** ([PYPOST-148](https://pypost.atlassian.net/browse/PYPOST-148))~~:
  **Resolved (deferral).** Audit confirmed no bounded compile cache; PYPOST-455 benchmark shows
  sub-ms render cost. Deferral documented in [template_service.md](../../doc/dev/template_service.md).
