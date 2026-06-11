# PYPOST-457: Add test — template catalog allow-list matches Jinja env globals

## Goals

After PYPOST-451 centralized the template function catalog in `FunctionRegistry`, validation
and Jinja rendering both depend on the same allow-list. Today that parity is implied by
integration tests and partial `register_into_env` coverage, not asserted in one place.

This task adds an explicit acceptance check so future catalog changes cannot drift between
`allowed_names()` and `env.globals` bindings.

## Programming Language

Python (pypost codebase).

## User Stories

- **As a maintainer**, I want a single test that every catalog allow-list name is bound on
  `env.globals` after registration, so validation and render paths cannot diverge silently.
- **As a security reviewer**, I want parity between the validation allow-list and Jinja
  globals documented and guarded by tests, so users cannot call functions that validation
  would reject (or vice versa).

## Definition of Done

1. After `FunctionRegistry.register_into_env`, every name in `allowed_names()` exists on
   `env.globals` and points to the same callable as `registry.get(name)`.
2. After `TemplateService` construction, the same parity holds for its Jinja environment.
3. No production behavior changes unless a parity bug is discovered and fixed.
4. Developer documentation notes the new test coverage and removes PYPOST-457 from known gaps.

## Out of Scope

- Custom registry injection into `TemplateService` (no public API today).
- New catalog functions or dynamic registration.
- Resolver or expression-parser changes.

## Source

Follow-up from [PYPOST-451 technical debt](ai-tasks/PYPOST-451/60-tech-debt.md) — Missing Tests.
