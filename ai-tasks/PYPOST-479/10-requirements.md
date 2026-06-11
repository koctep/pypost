# PYPOST-479: Review logging policy for variable validation attempts

## Goals

Confirm whether per-attempt DEBUG logging for variable name validation should remain,
be failure-only, or be configurable — and close this follow-up appropriately.

## Programming Language

Python 3.10+ (review scope only)

## User Stories

- As a maintainer, I want clarity on the validation logging policy so operators are not
  surprised by DEBUG volume in production.
- As an operator, I want failed validations visible in DEBUG logs without noise from every
  successful name entry.

## Definition of Done

- Logging policy reviewed against current implementation and PYPOST-473 resolution.
- Verdict documented: duplicate of PYPOST-473 (failure-only DEBUG already in place).
- `doc/dev/variable_validation.md` references PYPOST-473 resolution and this review.
- No new code required unless policy review finds a gap (none found).

## Task Description

Technical debt follow-up from PYPOST-163 (item 163-10). PYPOST-473 already tuned
`EnvPresenter._is_valid_variable_name` to emit DEBUG only on failed validations while
metrics continue to count all attempts. This ticket reviews that outcome and closes as
duplicate when confirmed.

### In Scope

- Policy review (per-attempt vs failure-only vs configurable)
- Cross-check implementation, tests, and developer documentation
- Documentation update referencing PYPOST-473

### Out of Scope

- New settings flag for validation logging (rejected in PYPOST-473)
- Changes to Prometheus metrics
- Core `variable_name_validation.py` (no logging by design)
