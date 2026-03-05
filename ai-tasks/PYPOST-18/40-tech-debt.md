# PYPOST-18: Technical Debt Analysis

## Shortcuts Taken

- **Global Instance for Singleton**: `TemplateService` is implemented as a module with global
  instance (`template_service`). This is the "pythonic" way to implement Singleton, but in larger
  systems a Dependency Injection container for managing dependency lifecycle may be preferable. For
  current project size this is acceptable.

## Code Quality Issues

- **Direct Global Access**: `HTTPClient` and `MCPServerImpl` import global `template_service`
  directly. This creates tight coupling. In the future, passing `TemplateService` through the
  constructor (DI) could be considered if mocking is needed for `HTTPClient` unit tests.

## Missing Tests

- **Unit Tests for TemplateService**: Although functionality is verified integrationally
  (application starts and works), there are no isolated unit tests for `TemplateService` (testing
  `render_string` with different variable types, testing template syntax error handling).

## Performance Concerns

- **Improvement**: Using a single `Environment` should positively affect performance via Jinja2
  internal caching (though by default compiled template cache works only with `env.get_template`,
  and here we use `env.from_string` which can also cache depending on settings). In this
  implementation we simply avoid creating redundant `Environment` and `Template` objects (via old
  `TemplateEngine`), which is already good.

## Follow-up Tasks

- Create unit tests for `pypost/core/template_service.py`.
- Consider using `lru_cache` or built-in Jinja2 cache for `from_string` if slowdown is observed
  when rendering the same strings repeatedly.
