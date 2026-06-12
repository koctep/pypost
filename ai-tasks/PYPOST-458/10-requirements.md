# PYPOST-458: Trim FunctionRegistry docstring overlap with register_into_env

## Goals

Reduce duplicated documentation between the `FunctionRegistry` class docstring and the
`register_into_env` method docstring. The class should state its role in one line; binding
semantics belong on the method only.

## Programming Language

Python (pypost codebase).

## User Stories

- **As a maintainer**, I want registry binding contract documented once on
  `register_into_env`, so I do not chase overlapping prose in two docstrings.
- **As a reviewer**, I want the class docstring to describe purpose only, so method-level
  contracts stay authoritative for behavior.

## Definition of Done

1. `FunctionRegistry` class docstring is a single-line role statement.
2. `register_into_env` docstring retains the full binding contract (one normal call from
   `TemplateService.__init__`, catalog-only keys, repeat-call semantics).
3. No runtime behavior changes.
4. Existing tests pass.

## Out of Scope

- API changes to `FunctionRegistry` or `TemplateService`.
- Rewriting `doc/dev/template_expression_functions.md` (module-level guide unchanged).
- Other PYPOST-451 debt items (e.g. PYPOST-459).

## Source

Follow-up from [PYPOST-451 technical debt](ai-tasks/PYPOST-451/60-tech-debt.md) — Code Quality;
see also [PYPOST-451 code cleanup](ai-tasks/PYPOST-451/40-code-cleanup.md).
