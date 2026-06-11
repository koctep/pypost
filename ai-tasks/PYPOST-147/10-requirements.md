# PYPOST-147: Create unit tests for `pypost/core/template_service.py`

## Goals

Close the missing-test debt from PYPOST-18 by ensuring `TemplateService` behavior is verified
in isolated unit tests — not only through HTTPClient, hover, or request-service integration
paths.

Source: `ai-tasks/PYPOST-18/40-tech-debt.md` →
[PYPOST-147](https://pypost.atlassian.net/browse/PYPOST-147).

## Programming Language

Python (pypost codebase).

## User Stories

- **As a maintainer**, I want focused unit tests for `TemplateService`, so changes to
  rendering, validation, and fallback behavior are caught without running full integration
  suites.
- **As a maintainer**, I want tests for variable substitution, catalog functions, invalid
  expressions, and error handling, so regressions in the template pipeline are visible early.
- **As a security reviewer**, I want unit tests confirming disallowed Jinja constructs are
  rejected, so template rendering cannot widen beyond the approved function catalog.

## Definition of Done

1. `tests/test_template_service.py` exists and exercises `TemplateService` in isolation.
2. **Render path** (`render_string`): plain variables, catalog functions (`urlencode`, `md5`,
   `base64`), nested chains, invalid/unknown forms, empty content, and backward-compatible
   fallback to original content on failure.
3. **Validation API** (`validate_function_expressions`): unknown functions, arity/argument/
   syntax errors, security negatives (filters, attribute access), and plain identifiers.
4. **Parse API** (`parse`): valid template returns a Jinja AST.
5. **Observability**: metrics outcomes (`success`, `validation_error`, `render_error`,
   `empty_content`) and staged helper behavior when metrics are injected.
6. **Runtime/hover parity** for representative expression forms via `render_path` parameter.
7. Full scoped test run passes with no regressions.

## Task Description

### Problem Statement

PYPOST-18 introduced `TemplateService` as the central template engine. Initial coverage
relied on integration tests. PYPOST-450+ added substantial unit tests incrementally; this
ticket formalizes closure of the PYPOST-18 debt item and fills any remaining API gaps.

### Scope

- In scope:
  - Unit tests in `tests/test_template_service.py` for all public `TemplateService` methods.
  - Documentation of test classes and coverage map in dev docs.
  - Audit of gaps; add tests only where public API behavior lacks direct assertions.
- Out of scope:
  - Production changes to `template_service.py` (unless a test proves a defect).
  - HTTPClient integration tests (covered in `tests/test_http_client.py`).
  - Resolver/registry internals (covered in dedicated test modules).

### Constraints and Assumptions

- Backward-compatible fallback (return original content on validation/render failure) is
  product behavior under test, not a defect.
- Incremental tests from PYPOST-450, PYPOST-454, and PYPOST-459 are retained; this task
  consolidates acceptance under PYPOST-147.

## Non-Functional Requirements

- Tests follow existing `unittest` patterns and project line-length limits.
- Tests run in under one second for the scoped file on developer hardware.

## Q&A

- Q: Were tests already partially delivered?
  - A: Yes — PYPOST-450+ added most coverage. PYPOST-147 audits, documents, and closes the
    PYPOST-18 follow-up with any remaining gaps filled.
- Q: Must every private helper be tested directly?
  - A: No. Helpers are covered through public `render_string` paths and targeted helper tests
    where metrics branching is non-obvious.
