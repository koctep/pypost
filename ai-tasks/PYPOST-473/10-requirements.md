# PYPOST-473: Tune variable validation debug logging verbosity

## Goals

Reduce DEBUG log noise from environment variable name validation in the UI flow while
preserving observability for failures and Prometheus metrics for all attempts.

## Programming Language

Python 3.10+

## User Stories

- As an operator with DEBUG logging enabled, I want validation logs only when names fail so
  logs are not flooded on every successful variable creation.
- As a maintainer, I want metrics unchanged so dashboards still reflect valid/invalid counts.

## Definition of Done

- `EnvPresenter._is_valid_variable_name` no longer emits DEBUG on successful validation.
- Failed validations still emit DEBUG with `variable_name_validation_attempt` and `error=`.
- `gui_variable_validation_total` and failure counters unchanged.
- Tests assert failure-only DEBUG logging policy.
- `doc/dev/variable_validation.md` documents the policy.

## Task Description

Technical debt follow-up from PYPOST-163 (item 163-4). Per-attempt DEBUG logging was added in
PYPOST-163; this task tunes verbosity to failures only (no separate debug toggle needed).

### In Scope

- `EnvPresenter._is_valid_variable_name` logging
- Presenter tests for log behaviour
- Developer documentation

### Out of Scope

- Core `variable_name_validation.py` (no logging by design)
- New settings flag for validation logging (metrics suffice for success path)
- PYPOST-479 duplicate review ticket (addressed by this change)
