# PYPOST-145: Unit Tests for TemplateService

## Goals

Close the PYPOST-18 missing-test debt item for isolated `TemplateService` coverage beyond
integration paths. Ensure `render_string` behavior is verified for diverse variable value
types and that template syntax/structure errors preserve backward-compatible fallback.

Source: `ai-tasks/PYPOST-18/40-tech-debt.md` →
[PYPOST-145](https://pypost.atlassian.net/browse/PYPOST-145).

## Programming Language

Python (pypost codebase).

## User Stories

- **As a maintainer**, I want unit tests for `render_string` with non-string variable
  values (integers, floats, booleans, null), so HTTP/MCP templates using numeric ports or
  flags render predictably.
- **As a maintainer**, I want confidence that template syntax errors return the original
  content, so broken user templates never corrupt outbound requests silently.

## Definition of Done

1. Gap analysis documents what PYPOST-147 already covers vs. PYPOST-145-specific scope.
2. Focused unit tests added for **variable types** where gaps existed.
3. **Syntax error handling** verified (existing PYPOST-147 tests satisfy this criterion).
4. `tests/test_template_service.py` scoped run passes.
5. Developer docs updated to reference PYPOST-145 closure.

## Task Description

### Problem Statement

PYPOST-18 noted `TemplateService` was only verified integrationally. PYPOST-147 delivered a
broad unit suite; PYPOST-145 closes the narrower debt wording: variable types and explicit
syntax-error fallback assurance.

### Scope

- In scope:
  - Audit gaps in `tests/test_template_service.py`.
  - Add focused tests for non-string variable values in `render_string`.
  - Document syntax-error coverage map (no duplicate tests unless a gap is found).
- Out of scope:
  - Production changes to `template_service.py`.
  - HTTPClient / hover integration tests.
  - Resolver/registry internals.

### Constraints and Assumptions

- Jinja2 stringifies non-string values (`42` → `"42"`, `None` → `"None"`).
- Backward-compatible fallback on validation/render failure is product behavior under test.

## Non-Functional Requirements

- Tests follow existing `unittest` patterns and per-test timeout markers.
- Scoped file run completes in under one second on developer hardware.

## Q&A

- Q: Does PYPOST-147 already cover this ticket?
  - A: Partially. PYPOST-147 closed the broad PYPOST-18 debt; PYPOST-145 adds variable-type
    coverage and formally closes the sibling debt line item.
- Q: Must syntax-error tests be duplicated?
  - A: No. Existing classes (`TestTemplateServiceRenderString`,
    `TestTemplateServiceValidationOutcomes`) already assert fallback; audit only.
