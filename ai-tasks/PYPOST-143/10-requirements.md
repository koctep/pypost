# PYPOST-143: TemplateService global singleton — design and test seams

## Goals

PYPOST-18 introduced a module-level `template_service` global as an idiomatic Python singleton.
Follow-up work removed the global and added constructor injection, but the lifecycle decision was
never documented for maintainers. This task closes that debt by recording the accepted design and
how tests substitute `TemplateService` without a DI container.

## User Stories

- As a maintainer, I want a single documented lifecycle for `TemplateService` so I know where
  instances are created and why.
- As a developer writing unit tests, I want documented injection and patching seams so I can
  mock template rendering without importing module globals.
- As a tech-debt owner, I want the PYPOST-18 singleton finding marked resolved with rationale
  (composition root + optional injection, not a framework DI container).

## Definition of Done

- [x] Developer docs describe production singleton-at-root vs test-local instances.
- [x] Developer docs list constructor injection points and the hover UI exception.
- [x] `ai-tasks/PYPOST-18/40-tech-debt.md` links PYPOST-143 as resolved.
- [x] No new module-level `template_service` global is introduced.
- [x] Existing tests pass.

## Task Description

**Source:** `ai-tasks/PYPOST-18/40-tech-debt.md` — global `TemplateService` acceptable at current
scale; larger systems might prefer a DI container.

**Prior work (out of re-implementation scope):**

- PYPOST-45 — removed module global; added optional constructor injection in core consumers.
- PYPOST-144 — `HTTPClient` and `MCPServerImpl` no longer import a module singleton.
- PYPOST-378 — `main.py` composition root creates one shared instance for production.

**This ticket:** document the resulting design and test patterns; no DI container, no behavior
change unless a doc gap required a one-line comment.

**Constraints and assumptions:**

- Implementation language: **Python**.
- Desktop client; one shared Jinja2 `Environment` per `TemplateService` instance is sufficient.
- Full `TemplateServiceProtocol` abstraction remains a future option (PYPOST-378 TD-1).

## Q&A

- **Q:** Must we remove every internal `TemplateService()` fallback?
  **A:** No. Production always injects from `main.py`. Leaf fallbacks support isolated unit tests
  (see `testability.md`). Removing them is a separate hardening task.
- **Q:** Why keep `_hover_template_service` in the UI layer?
  **A:** Hover runs from Qt widgets without a presenter-owned service reference. A module-level
  instance plus class-property patching keeps tests ergonomic (PYPOST-129). Documented, not
  hidden debt.
- **Q:** Is a DI container required?
  **A:** No at current project size. Explicit constructor injection from `main.py` is the accepted
  pattern.
