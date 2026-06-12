# PYPOST-789: [Bug] make test fails: 7 regression tests (SOLID caps + theme isolation)

## Goals

Restore the fast test suite (`make test`) to a completely green passing state by resolving all 7 regression/order-dependent failures.

## User Stories

As a PyPost developer,
I want the core test suite to execute successfully with 0 failures
So that I can confidently integrate changes and maintain the health of our project.

## Definition of Done

- `make test` runs successfully with 0 failures in the fast suite.
- Both the SOLID baseline limits and StyleManager test pollution issues are addressed.

## Task Description

The test suite fails with 7 errors, consisting of two separate root causes:
1. SOLID baseline cap violations (3 failures in `test_solid_audit_baseline.py`).
2. Order-dependence and style pollution in `test_style_manager_theme.py` (4 failures).

These issues are resolved under:
- `PYPOST-717`: Update SOLID audit baseline caps.
- `PYPOST-722`: Isolate Qt style state in theme tests.

## Q&A

- **Q**: Is there any additional coding required for this ticket?
- **A**: No, this is an umbrella tracking ticket. Resolving PYPOST-717 and PYPOST-722 covers the entire implementation.
