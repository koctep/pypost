# PYPOST-453: Dev Documentation

## Changes Made

### Updated: `doc/dev/template_expression_functions.md`

- Extended overview to include **PYPOST-453** and nested-policy summary.
- Document title now references PYPOST-450–PYPOST-453.
- Added examples for deep nested chains and nested invalid forms in Usage/API.
- Added **"Nested Function Call Policy (PYPOST-453)"** section with policy table,
  `NESTED_FUNCTION_CALLS_ALLOWED` semantics, `function_name` propagation note, and
  PYPOST-454 boundary.

STEP 3 already removed the "Known Deviation" callout and updated Architecture bullets;
STEP 7 consolidates maintainer-facing policy documentation in one place.

### Updated in STEP 3 (referenced here)

- `ai-tasks/PYPOST-450/20-architecture.md` — nested calls documented as supported.
- `ai-tasks/PYPOST-450/60-tech-debt.md` — PYPOST-453 follow-up marked completed.

## No New Files

No new files under `doc/dev/`. Nested policy extends the existing template-expression
developer guide rather than splitting into a separate document.

## Validation

- [x] Policy table matches `ai-tasks/PYPOST-453/20-architecture.md` and requirements
- [x] Examples align with policy-guard tests in `tests/test_function_expression_resolver.py`
      and `tests/test_template_service.py`
- [x] PYPOST-454 boundary noted for edge-case scope
- [x] Line length within project limit (verified via existing doc conventions)
