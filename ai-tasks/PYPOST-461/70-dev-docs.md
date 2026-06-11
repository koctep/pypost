# PYPOST-461: Dev Documentation

## Changes Made

### Updated: `doc/dev/template_expression_functions.md`

- Replaced **PYPOST-461 boundary (out of scope)** with **PYPOST-461 boundary (completed)**.
- Added **Edge-Case Expression Variants (PYPOST-461)** section with:
  - Empty-argument matrix (E1–E3) — `invalid_argument` semantics
  - Standalone extra-closing-paren matrix (P1–P2)
  - **First-failure validation ordering** (F1–F5, V1–V2) — left-to-right scan contract
  - Test locations and case constant names in `tests/test_function_expression_resolver.py`

## No New Files

No new files under `doc/dev/`. PYPOST-461 extends the existing template-expression developer
guide alongside the PYPOST-454 section.

## Validation

- [x] Matrices match `ai-tasks/PYPOST-461/20-architecture.md` observed codes
- [x] Test method names align with `tests/test_function_expression_resolver.py`
- [x] First-failure behavior documented for `validate_content` and `validate_expressions`
- [x] Line length within project limit (verified via `./scripts/check-line-length.sh`)
