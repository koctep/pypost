# PYPOST-18: Unify Jinja2 Environment Usage (TemplateService)

## Goals

Eliminate duplication of Jinja2 `Environment` creation. Currently `MCPServerImpl` creates its own
instance and `TemplateEngine` (used in `HTTPClient`) creates templates ad-hoc. Create a unified
`TemplateService` that will manage Jinja2 configuration and be used across the application.

## User Stories

- **As a developer**, I want template configuration to be centralized so I can easily add custom
  filters or change settings in one place.
- **As a developer**, I want to avoid creating redundant `Environment` objects for resource
  optimization.

## Acceptance Criteria

- [ ] `TemplateService` class is created in `pypost/core/template_service.py` (or
  `template_engine.py` is updated).
- [ ] `TemplateService` initializes and stores a single `jinja2.Environment` instance.
- [ ] `MCPServerImpl` uses `TemplateService` for AST parsing (method `parse` or env access).
- [ ] `HTTPClient` uses `TemplateService` for string rendering.
- [ ] Old `TemplateEngine` is removed or rewritten as a wrapper over `TemplateService`.
- [ ] Request rendering (URL, headers, body) works as before.
- [ ] Variable detection in MCP server works as before.

## Task Description

Current `TemplateEngine` implementation uses a static `render` method that creates a new
`jinja2.Template` on each call. `MCPServerImpl` creates its own `Environment` for variable
analysis.

Required:

1. Create `TemplateService` that encapsulates `jinja2.Environment`.
2. Implement methods `render(template_str, context)` and `parse(template_str)`.
3. Integrate `TemplateService` usage in `MCPServerImpl` and `HTTPClient`.

### Technical Details

- `TemplateService` can be implemented as a Singleton or simply instantiated in `main` and passed
  to dependencies. Given current architecture (where `RequestService` creates `HTTPClient`
  internally), it may be simpler to make `TemplateService` globally available as a singleton or
  module, or pass it through constructors (DI preferred if refactoring is not too complex).
- To start, `TemplateService` can have a `get_instance()` method or simply one instance in the
  module.

## Q&A

- **Is async rendering support needed?**
  - Not yet, current `render` is synchronous.
- **Should custom filters be added now?**
  - No, the task is only for structure refactoring.
