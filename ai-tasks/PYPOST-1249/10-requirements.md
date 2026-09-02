# PYPOST-1249: Optimize strict rendering

## Goals

Reduce CPU and allocation overhead when strict rendering handles large templates or error
paths, without changing rendered output or fail-closed conversion behavior.

## User Stories

- As an API user, I want strict request rendering to remain responsive for templates with many
  placeholders.
- As a maintainer, I want strict conversion failures to retain their existing diagnostics.

## Definition of Done

- Template content is scanned once for strict fallback decisions.
- Placeholder evaluation does not perform one compilation per placeholder.
- Existing strict conversion and literal fallback behavior remains unchanged.
- Regression tests cover the optimized path.

## Task Description

The strict rendering error path currently repeats lexical work and evaluates each strict
placeholder independently. Scope is limited to single-pass scanning and batched placeholder
evaluation. No new template syntax or conversion semantics are introduced.

## Q&A

- **Language:** Python, determined from the repository implementation.
