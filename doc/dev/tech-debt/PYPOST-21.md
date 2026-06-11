# Technical Debt for Task PYPOST-21

## 1. Global Instance for Singleton
`TemplateService` is implemented as a module with a global instance (`template_service`). This is a "pythonic" way to implement Singleton, but in larger systems, using a Dependency Injection container to manage dependency lifecycles might be preferable. For the current project size, this is acceptable.

## 2. Direct Global Access — **Resolved (PYPOST-144)**

`HTTPClient` and `MCPServerImpl` now accept `template_service: TemplateService | None = None`
via constructor injection and use `self._template_service` internally. See
`tests/test_http_client.py` (`TestHTTPClientInjection`) and
`tests/test_mcp_server_impl.py` (`TestMCPServerImplInjection`).

## 3. Unit Tests for TemplateService
Although functionality is verified integration-wise (application runs and works), isolated unit tests for `TemplateService` are missing (checking `render_string` with different variable types, checking template syntax error handling).

## 4. Improvement
Using a single `Environment` should positively impact performance due to internal Jinja2 caching (although compiled template cache works by default only if using `env.get_template`, and here we use `env.from_string`, which can also cache but depends on settings). In this implementation, we simply avoid creating unnecessary `Environment` and `Template` objects (via old `TemplateEngine`), which is already good.

## Follow-up Tasks
- Create unit tests for `pypost/core/template_service.py`.
- Consider using `lru_cache` or built-in Jinja2 cache for `from_string` if slowdown is noticed when rendering the same strings repeatedly.
