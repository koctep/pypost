# PYPOST-801: Code Cleanup

## Lint and format

- `make lint` (flake8 on `pypost/`) — no new issues; two string literal changes only.
- No unused imports, dead code, or formatting drift introduced.

## Scope discipline

- Touched only `pypost/main.py` (application code) and `doc/dev/logging.md` (catalog).
- No unrelated refactors in composition root.

## Verification

`make check` run after changes (see Step 3 / Step 6 validation).
