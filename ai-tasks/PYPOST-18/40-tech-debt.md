# PYPOST-18: Technical Debt Analysis


## Shortcuts Taken

- **Global TemplateService** ([PYPOST-143](https://pypost.atlassian.net/browse/PYPOST-143)):
  Global `template_service` is idiomatic for this codebase size; larger systems might prefer a DI
  container for lifecycle control.

## Code Quality Issues

- **template_service imports** ([PYPOST-144](https://pypost.atlassian.net/browse/PYPOST-144)):
  `HTTPClient` and `MCPServerImpl` import the global directly, which tightens coupling; constructor
  injection would help if mocking `HTTPClient` becomes important.

## Missing Tests

- **TemplateService unit tests** ([PYPOST-145](https://pypost.atlassian.net/browse/PYPOST-145)):
  Behavior is verified at integration level only; no isolated tests for `render_string`, variable
  types, or template error handling.

## Performance Concerns

- **Shared Jinja2 Environment** ([PYPOST-146](https://pypost.atlassian.net/browse/PYPOST-146)):
  One `Environment` helps via Jinja2 caching (note `from_string` vs `get_template` behavior).
  Avoiding redundant `Environment`/`Template` construction versus the old `TemplateEngine` path is
  already an improvement.

## Follow-up Tasks

- Create unit tests for `pypost/core/template_service.py`.
  — [PYPOST-147](https://pypost.atlassian.net/browse/PYPOST-147)
- **Jinja2 `from_string` caching** ([PYPOST-148](https://pypost.atlassian.net/browse/PYPOST-148)):
  Consider `lru_cache` or Jinja2 cache for repeated identical templates if profiling shows need.
