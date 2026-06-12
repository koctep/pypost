# PYPOST-458: Code Cleanup

## Scope

Single-file docstring edit in `pypost/core/function_registry.py`.

## Checks

- [x] `./scripts/check-line-length.sh` — no violations in changed file
- [x] Docstrings remain within project line-length limit
- [x] No logic, imports, or formatting churn beyond docstrings

## Notes

- Overlap called out in PYPOST-451 `40-code-cleanup.md` is resolved.
- `get()` docstring unchanged (PYPOST-452 surface note retained).

## No Further Cleanup Required

Change set is minimal and ready for review.
