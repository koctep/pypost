# PYPOST-458: Architecture

## Scope

Documentation-only change in `pypost/core/function_registry.py`. No call sites, tests, or
public API signatures change.

## Current State

- Class docstring repeats binding semantics already described on `register_into_env`.
- Method docstring is shorter than the class docstring but should own the contract.

## Plan

1. **Class docstring** — keep one line: single source of truth for allowed names and
   callables.
2. **Method docstring** — absorb the removed class detail:
   - Normal path: `TemplateService.__init__` calls once.
   - Catalog keys only (`urlencode`, `md5`, `base64`) set or replaced on `env.globals`.
   - Repeat calls re-bind catalog keys only; unrelated globals untouched.

## Validation

- Run `tests/test_function_registry.py` (unchanged behavior).
- Line-length check on edited file.

## Risk

None — docstrings only.
