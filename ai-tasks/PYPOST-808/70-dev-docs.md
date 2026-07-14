# PYPOST-808: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/setup.md` | Added version single-source note under Project metadata |

## Key maintainer workflow

1. Bump `__version__` in `pypost/version.py` only.
2. Packaging picks it up via `[tool.setuptools.dynamic]` — no edit to a static TOML version.
3. Run `make check` — `tests/test_pyproject.py` validates dynamic wiring.

## Cross-links

- PEP 621 metadata: PYPOST-785
- Editable install: PYPOST-806
- Pytest config in pyproject: PYPOST-807

## Worklog

role: execution, steps: 1-7, step_name: PYPOST-808 end-to-end, tokens_used: 28000
