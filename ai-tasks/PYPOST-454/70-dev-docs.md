# PYPOST-454: Dev Documentation

## Changes Made

### Updated: `doc/dev/template_expression_functions.md`

- Extended overview and document title to include **PYPOST-454** (PYPOST-450–PYPOST-454).
- Added **"Edge-Case Expression Variants (PYPOST-454)"** section with:
  - Malformed nested matrix (M1–M4) — observed validation codes and render fallback
  - Spacing variant matrix (S1–S5) — valid/invalid forms and parity expectations
  - Runtime/hover parity contract (`TemplateService` `render_path`; table via hover pipeline)
  - Test locations (`test_function_expression_resolver.py`, `test_template_service.py`,
    `MALFORMED_NESTED_EXPRESSION_CASES`)
  - PYPOST-461 boundary (empty-args, multi-placeholder, standalone closing-paren patterns)
- Updated PYPOST-453 nested-policy boundary note — PYPOST-454 edge-case scope marked
  **completed**; points to the new section.

## No New Files

No new files under `doc/dev/`. Edge-case coverage extends the existing template-expression
developer guide rather than splitting into a separate document.

## Validation

- [x] Malformed nested and spacing matrices match `ai-tasks/PYPOST-454/20-architecture.md`
      and observed codes in `60-tech-debt.md`
- [x] Test method names align with `tests/test_function_expression_resolver.py` and
      `tests/test_template_service.py`
- [x] PYPOST-461 boundary noted for remaining out-of-scope patterns
- [x] Line length within project limit (verified via `./scripts/check-line-length.sh`)
