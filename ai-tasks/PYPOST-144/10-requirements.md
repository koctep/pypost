# PYPOST-144: Direct Global Access — HTTPClient and MCPServerImpl

## Goals

Reduce tight coupling between HTTP transport and MCP server components and the template
rendering layer. Callers and tests should be able to supply a `TemplateService` instance
without relying on a module-level global singleton.

## User Stories

- **As a developer**, I want `HTTPClient` to accept `TemplateService` via its constructor so
  I can mock template rendering in unit tests without monkey-patching module globals.
- **As a developer**, I want `MCPServerImpl` to accept `TemplateService` via its
  constructor so MCP schema generation and request execution share the same injectable
  dependency as the rest of the request pipeline.

## Definition of Done

- [x] `HTTPClient` does not import a module-level `template_service` global.
- [x] `MCPServerImpl` does not import a module-level `template_service` global.
- [x] Both classes accept optional `template_service: TemplateService | None` in
  `__init__` and use `self._template_service` internally.
- [x] `MCPServerImpl` forwards the injected instance to `RequestService` (and thus
  `HTTPClient`).
- [x] Unit tests demonstrate injection works for both classes.
- [x] Existing tests continue to pass.

## Task Description

Source: `ai-tasks/PYPOST-18/40-tech-debt.md`. Previously `HTTPClient` and `MCPServerImpl`
imported `from pypost.core.template_service import template_service`, coupling them to a
module singleton. This debt item scopes constructor injection to those two classes (broader
global removal tracked under PYPOST-45 / PYPOST-143).

## Q&A

- **Is removing the module global in scope?**
  - Partially — this ticket focuses on consumer coupling in `HTTPClient` and
    `MCPServerImpl`. Global removal is covered by PYPOST-45.
- **Must production callers change?**
  - No. Optional parameters with sensible defaults preserve existing call sites.
