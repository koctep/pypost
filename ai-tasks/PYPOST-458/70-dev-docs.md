# PYPOST-458: Dev Documentation

## Changes Made

No updates to `doc/dev/`. The developer guide (`template_expression_functions.md`) already
describes `FunctionRegistry` and `register_into_env` at module level; this ticket only
realigns in-code docstrings with that split (class role vs method contract).

## Validation

- [x] External docs remain accurate after docstring trim
- [x] No stale references to removed class-level binding prose in `doc/dev/`
